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

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from airflow.models.taskinstance import TaskInstance
from airflow.utils.state import TaskInstanceState


@dataclass
class AnomalyEvaluation:
    """Result of a TI anomaly evaluation containing detector name and reason string."""

    is_anomalous: bool
    detector_name: str
    reason: str | None = None


def evaluate_task_instance_anomaly(
    *,
    session,
    task_instance: TaskInstance,
    end_date: datetime,
    min_runs: int,
    max_runs: int,
    algorithm_name: str,
    algorithm_config: dict[str, Any],
) -> AnomalyEvaluation:
    """Evaluate anomaly status using historical successful runs plus the current TI runtime."""
    if task_instance.start_date is None:
        return AnomalyEvaluation(
            is_anomalous=False,
            detector_name=algorithm_name,
            reason="missing_start_date",
        )

    current_duration = (end_date - task_instance.start_date).total_seconds()
    previous_durations = _load_previous_task_durations(
        session=session,
        task_instance=task_instance,
        max_runs=max_runs - 1,
    )
    runtimes = [*previous_durations, current_duration]

    if len(runtimes) < min_runs:
        return AnomalyEvaluation(
            is_anomalous=False,
            detector_name=algorithm_name,
            reason=f"insufficient_runs:{len(runtimes)}/{min_runs}",
        )

    return _evaluate_algorithm(
        algorithm_name=algorithm_name, runtimes=runtimes, algorithm_config=algorithm_config
    )


def _load_previous_task_durations(*, session, task_instance: TaskInstance, max_runs: int) -> list[float]:
    if max_runs <= 0:
        return []

    query = (
        select(TaskInstance.duration)
        .where(
            TaskInstance.dag_id == task_instance.dag_id,
            TaskInstance.task_id == task_instance.task_id,
            TaskInstance.map_index == task_instance.map_index,
            TaskInstance.run_id != task_instance.run_id,
            TaskInstance.state == TaskInstanceState.SUCCESS,
            TaskInstance.duration.is_not(None),
        )
        .order_by(TaskInstance.start_date.desc())
        .limit(max_runs)
    )
    return [float(duration) for duration in session.scalars(query) if duration is not None]


def _evaluate_algorithm(
    *,
    algorithm_name: str,
    runtimes: list[float],
    algorithm_config: dict[str, Any],
) -> AnomalyEvaluation:
    current_runtime = runtimes[-1]

    if algorithm_name == "always":
        return AnomalyEvaluation(is_anomalous=True, detector_name=algorithm_name)

    if algorithm_name == "threshold":
        min_runtime_value = algorithm_config.get("min_runtime")
        max_runtime_value = algorithm_config.get("max_runtime")
        min_runtime = float(min_runtime_value) if min_runtime_value is not None else float("-inf")
        max_runtime = float(max_runtime_value) if max_runtime_value is not None else float("inf")
        is_anomalous = not (min_runtime <= current_runtime <= max_runtime)
        if is_anomalous:
            reason = (
                f"runtime {current_runtime:.3f}s outside allowed range "
                f"[{min_runtime:.3f}s, {max_runtime:.3f}s]"
            )
        else:
            reason = None
        return AnomalyEvaluation(
            is_anomalous=is_anomalous,
            detector_name=algorithm_name,
            reason=reason,
        )

    raise ValueError(f"Unsupported anomaly algorithm: {algorithm_name}")
