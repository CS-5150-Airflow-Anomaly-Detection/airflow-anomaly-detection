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

"""Example DAG that uses different anomaly detectors for different tasks.

The API check task uses a fixed runtime threshold because it has a clear service
level expectation. The report task uses a moving-average detector because its
runtime is expected to scale with recent workload size. The transform task uses
a custom anomaly detector defined in this DAG file.
"""

from __future__ import annotations

import datetime
import time
from pathlib import Path

from airflow.sdk import (
    DAG,
    AnomalyDetector,
    AnomalyResult,
    MovingAverageAnomaly,
    Param,
    ThresholdAnomaly,
    TriggerRule,
    task,
)


class EvenRunCountAnomaly:
    """Flag a task instance when the anomaly detector receives an even number of runtimes."""

    def __call__(self, runtimes: list[float]) -> AnomalyResult:
        run_count = len(runtimes)
        is_anomaly = run_count % 2 == 0
        details = {
            "run_count": run_count,
            "current_runtime": runtimes[-1],
        }
        message = "Even number of runtimes observed." if is_anomaly else "Odd number of runtimes observed."
        return AnomalyResult(is_anomaly, message, details=details)


with DAG(
    dag_id=Path(__file__).stem,
    dag_display_name="Multiple Anomaly Detectors",
    description=__doc__.partition(".")[0],
    doc_md=__doc__,
    schedule=None,
    start_date=datetime.datetime(2022, 3, 4),
    catchup=False,
    max_active_runs=1,
    tags=["example", "anomaly-detection"],
    params={
        "api_check_time": Param(
            0.5,
            type="number",
            description="Runtimes, in seconds, for the API check task.",
            title="API check runtime",
        ),
        "report_time": Param(
            2.0,
            type="number",
            description="Runtimes, in seconds, for the report generation task.",
            title="Report runtime",
        ),
        "transform_time": Param(
            1.0,
            type="number",
            description="Runtimes, in seconds, for the data transform task.",
            title="Transform runtime",
        ),
    },
) as dag:
    api_latency_detector = AnomalyDetector(
        min_runs=2,
        max_runs=4,
        algorithm=ThresholdAnomaly(max_runtime=1.0),
    )

    report_runtime_detector = AnomalyDetector(
        min_runs=3,
        max_runs=6,
        algorithm=MovingAverageAnomaly(min_ratio=0.5, max_ratio=1.75),
    )

    even_run_count_detector = AnomalyDetector(
        min_runs=1,
        max_runs=8,
        algorithm=EvenRunCountAnomaly(),
    )

    @task(task_id="get_api_check_time", task_display_name="Retrieve API check time")
    def get_api_check_time(**kwargs) -> float:
        return kwargs["params"]["api_check_time"]

    @task(task_id="get_report_time", task_display_name="Retrieve report time")
    def get_report_time(**kwargs) -> float:
        return kwargs["params"]["report_time"]

    @task(task_id="get_transform_time", task_display_name="Retrieve transform time")
    def get_transform_time(**kwargs) -> float:
        return kwargs["params"]["transform_time"]

    @task(
        task_id="check_api_latency",
        task_display_name="Check API latency",
        on_success_callback=api_latency_detector,
    )
    def check_api_latency(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"API check completed in {n_seconds} seconds")
        return n_seconds

    @task(
        task_id="generate_report",
        task_display_name="Generate report",
        on_success_callback=report_runtime_detector,
    )
    def generate_report(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Report generated in {n_seconds} seconds")
        return n_seconds

    @task(
        task_id="transform_data",
        task_display_name="Transform data",
        on_success_callback=even_run_count_detector,
    )
    def transform_data(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Data transformed in {n_seconds} seconds")
        return n_seconds

    @task(task_id="print_results", task_display_name="Print results", trigger_rule=TriggerRule.ALL_DONE)
    def print_results(
        api_runtime: float,
        report_runtime: float,
        transform_runtime: float,
    ) -> None:
        print(f"API check runtime: {api_runtime}")
        print(f"Report runtime: {report_runtime}")
        print(f"Transform runtime: {transform_runtime}")

    api_time = get_api_check_time()
    report_time = get_report_time()
    transform_time = get_transform_time()
    api_results = check_api_latency(api_time)
    report_results = generate_report(report_time)
    transform_results = transform_data(transform_time)
    print_results(api_results, report_results, transform_results)
