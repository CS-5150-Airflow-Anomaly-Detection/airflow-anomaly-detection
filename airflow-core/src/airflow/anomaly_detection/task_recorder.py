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

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from airflow.models.task_instance_anomaly import TaskInstanceAnomaly

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def record_task_instance_anomaly(
    *,
    session: Session,
    task_instance: Any,
    is_anomalous: bool,
    detector_name: str,
    reason: str | None,
) -> None:
    """Insert or update the TaskInstanceAnomaly row for the given TaskInstance."""
    # #region agent log
    import json
    import os
    import time

    try:
        from airflow import settings

        db_url = str(settings.get_engine().url) if settings.get_engine() else "unknown"
        tables = []
        try:
            from sqlalchemy import inspect

            tables = inspect(session.get_bind()).get_table_names()
        except Exception:
            pass
        migration_exists = False
        try:
            versions_dir = os.path.join(os.path.dirname(__file__), "..", "..", "migrations", "versions")
            abs_versions = os.path.abspath(versions_dir)
            if os.path.isdir(abs_versions):
                migration_exists = any("task_instance_anomaly" in f for f in os.listdir(abs_versions))
        except Exception:
            pass
        with open("/home/alexjoos/airflow-anomaly-detection/.cursor/debug-e7dad0.log", "a") as f:
            f.write(
                json.dumps(
                    {
                        "sessionId": "e7dad0",
                        "hypothesisId": "H1",
                        "location": "task_recorder.py:record_task_instance_anomaly",
                        "message": "DB and migration state",
                        "data": {
                            "db_url": db_url[:80],
                            "has_task_instance_anomaly_table": "task_instance_anomaly" in tables,
                            "table_count": len(tables),
                            "migration_file_exists": migration_exists,
                        },
                        "timestamp": int(time.time() * 1000),
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion
    dag_id = task_instance.dag_id
    run_id = task_instance.run_id
    task_id = task_instance.task_id
    map_index = getattr(task_instance, "map_index", -1)
    try_number = getattr(task_instance, "try_number", 0)

    row = session.scalar(
        select(TaskInstanceAnomaly).where(
            TaskInstanceAnomaly.dag_id == dag_id,
            TaskInstanceAnomaly.run_id == run_id,
            TaskInstanceAnomaly.task_id == task_id,
            TaskInstanceAnomaly.map_index == map_index,
            TaskInstanceAnomaly.try_number == try_number,
        )
    )

    if row is None:
        session.add(
            TaskInstanceAnomaly(
                dag_id=dag_id,
                run_id=run_id,
                task_id=task_id,
                map_index=map_index,
                try_number=try_number,
                is_anomalous=is_anomalous,
                detector_name=detector_name,
                reason=reason,
            )
        )
    else:
        row.is_anomalous = is_anomalous
        row.detector_name = detector_name
        row.reason = reason
