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
from airflow.api_fastapi.core_api.datamodels.dag_anomaly import (
    DagAnomalyCollectionResponse,
)
from airflow.api_fastapi.core_api.security import requires_access_dag
from airflow.models.dagrun_anomaly import DagRunAnomaly

# Initialize router with appropriate tagging for the OpenAPI/Swagger docs
dag_anomaly_router = AirflowRouter(tags=["DagAnomaly"], prefix="/dag_anomaly")


@dag_anomaly_router.get(
    "",
    dependencies=[Depends(requires_access_dag(method="GET"))],
)
def get_dag_anomalies(
    limit: QueryLimit,
    offset: QueryOffset,
    session: SessionDep,
    dag_id: str | None = None,
) -> DagAnomalyCollectionResponse:
    """Get all DAG anomalies."""
    # Base selection
    statement = select(DagRunAnomaly)

    # Apply optional filtering by dag_id
    if dag_id:
        statement = statement.where(DagRunAnomaly.dag_id == dag_id)

    # Apply pagination and retrieve total count
    map_select, total_entries = paginated_select(
        statement=statement,
        filters=[],
        order_by=None,
        offset=offset,
        limit=limit,
        session=session,
    )

    # Execute and return results wrapped in the collection schema
    anomalies = list(session.scalars(map_select).all())

    return DagAnomalyCollectionResponse(
        dag_anomalies=anomalies,
        total_entries=total_entries,
    )
