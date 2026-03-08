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

from typing import TYPE_CHECKING

from sqlalchemy import select

from airflow.models.dagrun_anomaly import DagRunAnomaly

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from airflow.models.dagrun import DagRun


def record_dagrun_anomaly(
    *,
    session: Session,
    dag_run: DagRun,
    is_anomalous: bool,
    detector_name: str,
    reason: str | None,
) -> None:
    """Insert or update the DagRunAnomaly row for the given DagRun."""
    row = session.scalar(
        select(DagRunAnomaly).where(
            DagRunAnomaly.dag_id == dag_run.dag_id,
            DagRunAnomaly.run_id == dag_run.run_id,
        )
    )

    if row is None:
        session.add(
            DagRunAnomaly(
                dag_id=dag_run.dag_id,
                run_id=dag_run.run_id,
                is_anomalous=is_anomalous,
                detector_name=detector_name,
                reason=reason,
            )
        )
    else:
        row.is_anomalous = is_anomalous
        row.detector_name = detector_name
        row.reason = reason
