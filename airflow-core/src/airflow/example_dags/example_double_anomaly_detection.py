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

"""Example DAG allowing you to interactively choose the times for each TaskInstance run.

The TaskInstances simply sleep for the specified amount of time
"""

from __future__ import annotations

import datetime
import time
from pathlib import Path

from airflow.sdk import DAG, AlwaysAnomaly, AnomalyDetector, Param, ThresholdAnomaly, TriggerRule, task

# [START params_trigger]
with DAG(
    dag_id=Path(__file__).stem,
    dag_display_name="Double Anomaly Detection",
    description=__doc__.partition(".")[0],
    doc_md=__doc__,
    schedule=None,
    start_date=datetime.datetime(2022, 3, 4),
    catchup=False,
    tags=["example", "params"],
    params={
        "times": Param(
            [1, 2, 3],
            type="array",
            items={"type": "number"},
            description="Define the list of times to run the task for, in seconds. Note that real runtimes may be higher due to task overhead.",
            title="Runtimes",
        ),
    },
) as dag:

    @task(task_id="get_times", task_display_name="Retrieve times from params")
    def get_times(**kwargs) -> list[float]:
        params = kwargs["params"]
        if "times" not in params:
            print("No times given, was no UI used to trigger?")
            return []
        return params["times"]

    anomaly_detector1 = AnomalyDetector(min_runs=2, max_runs=4, algorithm=ThresholdAnomaly(max_runtime=1))
    anomaly_detector2 = AnomalyDetector(min_runs=2, max_runs=4, algorithm=AlwaysAnomaly())

    @task(
        task_id="run_for_time",
        task_display_name="Run for time",
        on_success_callback=[anomaly_detector1, anomaly_detector2],
    )
    def run_for_time(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Paused for {n_seconds}")
        return n_seconds

    @task(task_id="print_runtimess", task_display_name="Print runtimes", trigger_rule=TriggerRule.ALL_DONE)
    def print_runtimes(runtimes) -> None:
        for r in runtimes:
            print(r)

    times_to_run = get_times()
    times_run = run_for_time.expand(n_seconds=times_to_run)
    results_print = print_runtimes(times_run)
# [END]
