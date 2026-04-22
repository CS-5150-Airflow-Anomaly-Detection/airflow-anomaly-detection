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

from fastapi import Depends
from sqlalchemy import select

from airflow.api_fastapi.common.db.common import SessionDep, paginated_select
from airflow.api_fastapi.common.parameters import QueryLimit, QueryOffset
from airflow.api_fastapi.common.router import AirflowRouter
from airflow.api_fastapi.core_api.datamodels.task_instance_anomaly import (
    TaskInstanceAnomalyCollectionResponse,
)
from airflow.api_fastapi.core_api.security import requires_access_dag
from airflow.models.task_instance_anomaly import TaskInstanceAnomaly

task_instance_anomaly_router = AirflowRouter(tags=["TaskInstanceAnomaly"], prefix="/task_instance_anomaly")


@task_instance_anomaly_router.get(
    "",
    dependencies=[Depends(requires_access_dag(method="GET"))],
)
def get_task_instance_anomalies(
    limit: QueryLimit,
    offset: QueryOffset,
    session: SessionDep,
    dag_id: str | None = None,
    task_id: str | None = None,
    run_id: str | None = None,
) -> TaskInstanceAnomalyCollectionResponse:
    """Get all Task Instance anomalies."""
    statement = select(TaskInstanceAnomaly)

    # Optional filtering
    if dag_id:
        statement = statement.where(TaskInstanceAnomaly.dag_id == dag_id)
    if task_id:
        statement = statement.where(TaskInstanceAnomaly.task_id == task_id)
    if run_id:
        statement = statement.where(TaskInstanceAnomaly.run_id == run_id)

    statement = statement.order_by(TaskInstanceAnomaly.start_date.desc())

    map_select, total_entries = paginated_select(
        statement=statement,
        filters=[],
        order_by=None,
        offset=offset,
        limit=limit,
        session=session,
    )
    anomalies = list(session.scalars(map_select).all())

    return TaskInstanceAnomalyCollectionResponse(
        task_instance_anomalies=anomalies,
        total_entries=total_entries,
    )
