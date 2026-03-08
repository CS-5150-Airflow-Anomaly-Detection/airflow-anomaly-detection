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

from pluggy import hookimpl

from airflow.anomaly_detection.detector import detect_task_instance_anomaly
from airflow.anomaly_detection.task_recorder import record_task_instance_anomaly
from airflow.utils.session import create_session


def _on_task_instance_completed(previous_state, task_instance, error=None):
    """Shared logic for on_task_instance_success and on_task_instance_failed."""
    try:
        is_anomalous, detector_name, reason = detect_task_instance_anomaly(task_instance)
        with create_session() as session:
            record_task_instance_anomaly(
                session=session,
                task_instance=task_instance,
                is_anomalous=is_anomalous,
                detector_name=detector_name,
                reason=reason,
            )
    except Exception:
        import structlog

        structlog.get_logger(__name__).exception("Error in anomaly detection listener")


@hookimpl
def on_task_instance_success(previous_state, task_instance):
    """Record anomaly status when a task completes successfully."""
    _on_task_instance_completed(previous_state, task_instance)


@hookimpl
def on_task_instance_failed(previous_state, task_instance, error):
    """Record anomaly status when a task fails."""
    _on_task_instance_completed(previous_state, task_instance, error)
