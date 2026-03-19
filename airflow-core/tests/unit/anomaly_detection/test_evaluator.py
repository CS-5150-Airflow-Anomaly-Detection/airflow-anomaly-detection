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
from types import SimpleNamespace

from airflow.anomaly_detection.evaluator import evaluate_task_instance_anomaly


def test_evaluate_task_instance_anomaly_uses_prior_runs(monkeypatch):
    ti = SimpleNamespace(start_date=datetime(2024, 1, 1, 0, 0, 0))

    monkeypatch.setattr(
        "airflow.anomaly_detection.evaluator._load_previous_task_durations",
        lambda **_: [4.0, 5.0],
    )

    result = evaluate_task_instance_anomaly(
        session=None,
        task_instance=ti,
        end_date=datetime(2024, 1, 1, 0, 0, 7),
        min_runs=2,
        max_runs=4,
        algorithm_name="threshold",
        algorithm_config={"min_runtime": 1.0, "max_runtime": 6.0},
    )

    assert result.is_anomalous is True
    assert result.detector_name == "threshold"
    assert result.reason is not None


def test_evaluate_task_instance_anomaly_short_circuits_when_not_enough_runs(monkeypatch):
    ti = SimpleNamespace(start_date=datetime(2024, 1, 1, 0, 0, 0))

    monkeypatch.setattr(
        "airflow.anomaly_detection.evaluator._load_previous_task_durations",
        lambda **_: [],
    )

    result = evaluate_task_instance_anomaly(
        session=None,
        task_instance=ti,
        end_date=datetime(2024, 1, 1, 0, 0, 3),
        min_runs=2,
        max_runs=4,
        algorithm_name="always",
        algorithm_config={},
    )

    assert result.is_anomalous is False
    assert result.reason == "insufficient_runs:1/2"
