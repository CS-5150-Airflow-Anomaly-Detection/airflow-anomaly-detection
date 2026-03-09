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

from airflow.anomaly_detection.detector import detect_task_instance_anomaly
from airflow.anomaly_detection.task_recorder import record_task_instance_anomaly
from airflow.listeners import hookimpl
from airflow.utils.session import create_session


def _on_task_instance_completed(previous_state, task_instance, error=None):
    """Shared logic for on_task_instance_success and on_task_instance_failed."""
    # #region agent log
    import json
    import time

    def _debug_log(hypothesis_id: str, message: str, data: dict):
        try:
            with open("/home/alexjoos/airflow-anomaly-detection/.cursor/debug-e7dad0.log", "a") as f:
                f.write(
                    json.dumps(
                        {
                            "sessionId": "e7dad0",
                            "hypothesisId": hypothesis_id,
                            "location": "listener.py:_on_task_instance_completed",
                            "message": message,
                            "data": data,
                            "timestamp": int(time.time() * 1000),
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass

    _debug_log(
        "H5",
        "Listener invoked on task completion",
        {
            "dag_id": getattr(task_instance, "dag_id", None),
            "task_id": getattr(task_instance, "task_id", None),
        },
    )
    # #endregion
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
        # #region agent log
        _debug_log("H4", "Record succeeded - table exists and write completed", {})
        # #endregion
    except Exception as e:
        # #region agent log
        _debug_log(
            "H4",
            "Record failed - exception in anomaly listener",
            {
                "exc_type": type(e).__name__,
                "exc_msg": str(e),
                "no_such_table": "no such table" in str(e).lower(),
            },
        )
        # #endregion
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
