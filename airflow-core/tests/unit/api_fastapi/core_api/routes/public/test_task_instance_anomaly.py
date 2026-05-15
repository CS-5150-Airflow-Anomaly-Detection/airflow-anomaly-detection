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

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from airflow.models.task_instance_anomaly import TaskInstanceAnomaly

pytestmark = pytest.mark.db_test

DAG_A = "anomaly_test_dag_a"
DAG_B = "anomaly_test_dag_b"
RUN_ID = "test_run"
TASK_A = "task_a"
TASK_B = "task_b"


@pytest.fixture(autouse=True)
def _clean_task_instance_anomalies(session: Session) -> None:
    session.execute(delete(TaskInstanceAnomaly))
    session.commit()


class TestGetTaskInstanceAnomalies:
    def test_returns_empty_collection(self, test_client) -> None:
        response = test_client.get("/task_instance_anomaly")

        assert response.status_code == 200
        body = response.json()
        assert body["task_instance_anomalies"] == []
        assert body["total_entries"] == 0

    def test_filters_by_dag_task_and_run(self, test_client, session: Session) -> None:
        session.add_all(
            [
                TaskInstanceAnomaly(
                    dag_id=DAG_A,
                    run_id=RUN_ID,
                    task_id=TASK_A,
                    map_index=-1,
                    try_number=1,
                    is_anomalous=True,
                    detector_name="AlwaysAnomaly",
                    reason="first",
                ),
                TaskInstanceAnomaly(
                    dag_id=DAG_B,
                    run_id=RUN_ID,
                    task_id=TASK_B,
                    map_index=-1,
                    try_number=1,
                    is_anomalous=False,
                    detector_name="ThresholdAnomaly",
                    reason=None,
                ),
            ]
        )
        session.commit()

        by_dag = test_client.get("/task_instance_anomaly", params={"dag_id": DAG_A})
        assert by_dag.status_code == 200
        payload = by_dag.json()
        assert payload["total_entries"] == 1
        assert len(payload["task_instance_anomalies"]) == 1
        row = payload["task_instance_anomalies"][0]
        assert row["dag_id"] == DAG_A
        assert row["task_id"] == TASK_A
        assert row["is_anomalous"] is True

        by_task = test_client.get(
            "/task_instance_anomaly",
            params={"dag_id": DAG_B, "task_id": TASK_B},
        )
        assert by_task.status_code == 200
        assert by_task.json()["total_entries"] == 1

        by_run = test_client.get(
            "/task_instance_anomaly",
            params={"dag_id": DAG_B, "run_id": RUN_ID},
        )
        assert by_run.status_code == 200
        assert by_run.json()["total_entries"] == 1
