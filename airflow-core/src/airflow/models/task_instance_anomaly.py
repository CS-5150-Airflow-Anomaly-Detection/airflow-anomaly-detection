#
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

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from airflow._shared.timezones import timezone
from airflow.models.base import Base
from airflow.utils.sqlalchemy import UtcDateTime


class TaskInstanceAnomaly(Base):
    """ORM model storing unique anomaly columns for a TaskInstance."""

    __tablename__ = "task_instance_anomaly"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dag_id: Mapped[str] = mapped_column(String(250), nullable=False)
    run_id: Mapped[str] = mapped_column(String(250), nullable=False)
    task_id: Mapped[str] = mapped_column(String(250), nullable=False)
    map_index: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    try_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_anomalous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detector_name: Mapped[str] = mapped_column(String(100), nullable=False, default="always_true")
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        nullable=False,
        default=timezone.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime,
        nullable=False,
        default=timezone.utcnow,
        onupdate=timezone.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "dag_id",
            "run_id",
            "task_id",
            "map_index",
            "try_number",
            name="uq_task_instance_anomaly_dag_run_task_map_try",
        ),
    )


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
