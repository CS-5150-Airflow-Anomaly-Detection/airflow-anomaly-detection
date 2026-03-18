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

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

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
