# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import structlog
from sqlalchemy import or_, select

from airflow.anomaly_detection.task_recorder import record_task_instance_anomaly
from airflow.listeners import hookimpl
from airflow.models.anomalydetector import AnomalyDetector
from airflow.models.taskinstance import TaskInstance
from airflow.utils.session import create_session
from airflow.utils.state import TaskInstanceState

log = structlog.get_logger(__name__)


def _get_task_instance_anomaly_detectors(task_instance: Any) -> list[AnomalyDetector]:
    """
    Return DAG-declared anomaly detectors attached to the reconstructed task.

    Temporary architecture note:
    We currently recover detector configuration directly from the runtime task
    attached to the task instance. This works for the listener-based MVP, but
    a future implementation may propagate detector configuration through a more
    explicit persisted/internal execution interface instead of rediscovering it
    from callback fields at listener time.
    """
    task = getattr(task_instance, "task", None)
    callbacks = getattr(task, "on_success_callback", None)
    if not isinstance(callbacks, Sequence):
        return []
    return [callback for callback in callbacks if isinstance(callback, AnomalyDetector)]


def _get_current_duration(task_instance: Any) -> float | None:
    """
    Compute the current task-instance runtime from in-memory execution fields.

    Temporary architecture note:
    This calculation is intentionally duplicated here because the listener runs
    at task-success time and may need runtime data before there is a separate,
    authoritative on-demand anomaly-writing layer elsewhere in the metadata
    stack. Long term, anomaly evaluation should ideally read finalized timing
    data from the durable persistence path instead of recomputing it here.
    """
    start_date = getattr(task_instance, "start_date", None)
    end_date = getattr(task_instance, "end_date", None)
    if start_date is None or end_date is None:
        return None
    return (end_date - start_date).total_seconds()


def _get_historical_runtimes(task_instance: Any, detector: AnomalyDetector, session) -> list[float]:
    """
    Load prior successful runtimes for the same task-instance identity slice.

    Temporary architecture note:
    This helper is part of the listener-side MVP that performs anomaly writes
    on demand at task-success time. It exists because there is not yet a later
    metadata-layer writer that can combine persisted task-instance state with
    anomaly history after the final task-instance row has been durably handled.
    """
    current_map_index = getattr(task_instance, "map_index", -1)
    current_try_number = getattr(task_instance, "try_number", 0)

    query = (
        select(TaskInstance.duration)
        .where(TaskInstance.dag_id == task_instance.dag_id)
        .where(TaskInstance.task_id == task_instance.task_id)
        .where(TaskInstance.map_index == current_map_index)
        .where(TaskInstance.state == TaskInstanceState.SUCCESS)
        .where(TaskInstance.duration.is_not(None))
        .where(
            or_(
                TaskInstance.run_id != task_instance.run_id,
                TaskInstance.try_number != current_try_number,
            )
        )
        .order_by(TaskInstance.start_date.desc())
        .limit(max(detector.max_runs - 1, 0))
    )
    return list(reversed(list(session.scalars(query))))


def _run_task_instance_anomaly_detection(task_instance: Any) -> None:
    """
    Evaluate and persist task-instance anomaly information from the listener.

    Temporary architecture note:
    Having the listener both evaluate anomaly status and write to the metadata
    DB is an interim design. The likely future direction is for the listener to
    capture runtime-only information and hand work off to a later internal
    persistence layer, instead of acting as the final anomaly writer itself.
    """
    detectors = _get_task_instance_anomaly_detectors(task_instance)
    if not detectors:
        return

    detector = detectors[0]
    if len(detectors) > 1:
        log.warning(
            "Multiple anomaly detectors configured; only the first will be used",
            task_id=getattr(task_instance, "task_id", None),
            dag_id=getattr(task_instance, "dag_id", None),
            configured=len(detectors),
        )

    current_duration = _get_current_duration(task_instance)
    if current_duration is None:
        return

    with create_session() as session:
        runtimes = _get_historical_runtimes(task_instance, detector, session)
        runtimes.append(current_duration)
        if len(runtimes) < detector.min_runs:
            return

        result = detector.detect_anomalies(runtimes)
        record_task_instance_anomaly(
            session=session,
            task_instance=task_instance,
            is_anomalous=result.is_anomaly,
            detector_name=type(detector.detect_anomalies).__name__,
            reason=result.message or None,
        )


@hookimpl
def on_task_instance_success(previous_state, task_instance):
    """
    Persist anomaly information for successful task instances.

    Temporary architecture note:
    This listener currently acts as the trigger point for on-demand anomaly
    writes because Airflow does not yet expose a dedicated post-persist hook for
    finalized task-instance rows. A future implementation may keep the listener
    as the trigger, but schedule or delegate the final anomaly write to a later
    metadata-layer component instead of doing it directly here.
    """
    _ = previous_state
    try:
        _run_task_instance_anomaly_detection(task_instance)
    except Exception:
        log.exception(
            "Failed to evaluate task instance anomaly from listener",
            task_id=getattr(task_instance, "task_id", None),
            dag_id=getattr(task_instance, "dag_id", None),
            run_id=getattr(task_instance, "run_id", None),
        )


@hookimpl
def on_task_instance_failed(previous_state, task_instance, error):
    """Task-instance anomaly handling is only evaluated on success for now."""
    _ = (previous_state, task_instance, error)
