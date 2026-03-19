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

from airflow.sdk.anomaly_detection import AnomalyDetector, ThresholdAnomaly


def test_anomaly_detector_emits_declarative_request(monkeypatch):
    sent = []

    class FakeComms:
        def send(self, msg):
            sent.append(msg)

    monkeypatch.setattr("airflow.sdk.execution_time.task_runner.SUPERVISOR_COMMS", FakeComms(), raising=False)

    detector = AnomalyDetector(min_runs=2, max_runs=5, algorithm=ThresholdAnomaly(max_runtime=12.0))
    detector({"ti": object()})

    assert len(sent) == 1
    assert sent[0].algorithm_name == "threshold"
    assert sent[0].max_runs == 5
    assert sent[0].algorithm_config == {"min_runtime": None, "max_runtime": 12.0}
