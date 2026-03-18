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
    identity = {
        "dag_id": task_instance.dag_id,
        "run_id": task_instance.run_id,
        "task_id": task_instance.task_id,
        "map_index": getattr(task_instance, "map_index", -1),
        "try_number": getattr(task_instance, "try_number", 0),
    }
    anomaly_values = {
        "is_anomalous": is_anomalous,
        "detector_name": detector_name,
        "reason": reason,
    }

    row = session.scalar(
        select(TaskInstanceAnomaly).where(
            TaskInstanceAnomaly.dag_id == identity["dag_id"],
            TaskInstanceAnomaly.run_id == identity["run_id"],
            TaskInstanceAnomaly.task_id == identity["task_id"],
            TaskInstanceAnomaly.map_index == identity["map_index"],
            TaskInstanceAnomaly.try_number == identity["try_number"],
        )
    )

    if row is None:
        session.add(TaskInstanceAnomaly(**identity, **anomaly_values))
    else:
        for field, value in anomaly_values.items():
            setattr(row, field, value)
