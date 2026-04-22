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

"""Example DAG demonstrating runtime anomaly detection for mapped tasks.

Trigger the DAG repeatedly with the same ``dagruns`` parameter to step through a
multi-run demo sequence. Each list inside ``dagruns`` becomes the runtime inputs
for one DAG run, which makes it easy to see that anomaly history is tracked per
map index rather than across all mapped task instances together.
"""

from __future__ import annotations

import datetime
import time
from pathlib import Path

from airflow.sdk import (
    DAG,
    AlwaysAnomaly,
    AnomalyDetector,
    MovingAverageAnomaly,
    Param,
    TaskInstanceState,
    ThresholdAnomaly,
    TriggerRule,
    ZScoreAnomaly,
    task,
)

# [START params_trigger]
with DAG(
    dag_id=Path(__file__).stem,
    dag_display_name="example_anomaly_detection_per_map_index",
    description=__doc__.partition(".")[0],
    doc_md=__doc__,
    schedule=None,
    max_active_runs=1,
    start_date=datetime.datetime(2022, 3, 4),
    catchup=False,
    tags=["example", "params"],
    params={
        "dagruns": Param(
            [
                [1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0],
                [10.0, 1.2, 1.0],
                [0.8, 0.8, 1.0],
                [3.0, 1.0, 2.0],
            ],
            type="array",
            items={"type": "array", "items": {"type": "number"}},
            description=(
                "Define the runtime inputs for successive DAG runs. Trigger the DAG multiple times with the same value; "
                "run 1 uses the first list, run 2 uses the second list, and so on. Each position in the inner list is "
                "a stable map index with its own anomaly history."
            ),
            title="DAG Run Runtime Sequence",
        ),
    },
) as dag:

    @task(task_id="get_times", task_display_name="Retrieve times for this DAG run")
    def get_times(**kwargs) -> list[float]:
        params = kwargs["params"]
        dagruns = params.get("dagruns", [])
        if not dagruns:
            print("No dagruns sequence was provided.")
            return []

        ti = kwargs["ti"]
        previous_run_count = 0
        cursor_logical_date = None
        while True:
            previous_ti = ti.get_previous_ti(
                state=TaskInstanceState.SUCCESS,
                logical_date=cursor_logical_date,
                map_index=-1,
            )
            if previous_ti is None:
                break

            previous_run_count += 1
            cursor_logical_date = previous_ti.logical_date
            if cursor_logical_date is None:
                break

        dagrun_index = min(previous_run_count, len(dagruns) - 1)
        current_times = dagruns[dagrun_index]

        print(
            f"Using dagruns[{dagrun_index}] for this DAG run after {previous_run_count} prior successful get_times runs: "
            f"{current_times}"
        )
        for map_index, history in enumerate(zip(*dagruns, strict=False)):
            print(f"Map index {map_index} planned history: {list(history)}")

        return current_times

    always_anomaly_detector = AnomalyDetector(min_runs=1, max_runs=4, algorithm=AlwaysAnomaly())
    threshold_anomaly_detector = AnomalyDetector(
        min_runs=2,
        max_runs=4,
        algorithm=ThresholdAnomaly(max_runtime=1),
    )
    zscore_anomaly_detector = AnomalyDetector(
        min_runs=3,
        max_runs=6,
        algorithm=ZScoreAnomaly(z_threshold=1.0),
    )
    moving_average_anomaly_detector = AnomalyDetector(
        min_runs=2,
        max_runs=6,
        algorithm=MovingAverageAnomaly(window_size=3, min_ratio=0.75, max_ratio=1.25),
    )

    @task(
        task_id="run_for_time_always_anomaly",
        task_display_name="Run for time with AlwaysAnomaly",
        on_success_callback=always_anomaly_detector,
    )
    def run_for_time_always_anomaly(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Paused for {n_seconds}")
        return n_seconds

    @task(
        task_id="run_for_time_threshold_anomaly",
        task_display_name="Run for time with ThresholdAnomaly",
        on_success_callback=threshold_anomaly_detector,
    )
    def run_for_time_threshold_anomaly(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Paused for {n_seconds}")
        return n_seconds

    @task(
        task_id="run_for_time_zscore_anomaly",
        task_display_name="Run for time with ZScoreAnomaly",
        on_success_callback=zscore_anomaly_detector,
    )
    def run_for_time_zscore_anomaly(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Paused for {n_seconds}")
        return n_seconds

    @task(
        task_id="run_for_time_moving_average_anomaly",
        task_display_name="Run for time with MovingAverageAnomaly",
        on_success_callback=moving_average_anomaly_detector,
    )
    def run_for_time_moving_average_anomaly(n_seconds: float) -> float:
        time.sleep(n_seconds)
        print(f"Paused for {n_seconds}")
        return n_seconds

    @task(task_id="print_runtimess", task_display_name="Print runtimes", trigger_rule=TriggerRule.ALL_DONE)
    def print_runtimes(
        always_runtimes,
        threshold_runtimes,
        zscore_runtimes,
        moving_average_runtimes,
    ) -> None:
        runtime_groups = {
            "AlwaysAnomaly": always_runtimes,
            "ThresholdAnomaly": threshold_runtimes,
            "ZScoreAnomaly": zscore_runtimes,
            "MovingAverageAnomaly": moving_average_runtimes,
        }
        for algorithm_name, runtimes in runtime_groups.items():
            print(f"{algorithm_name} runtimes:")
            for runtime in runtimes:
                print(runtime)

    times_for_current_dagrun = get_times()
    always_times_run = run_for_time_always_anomaly.expand(n_seconds=times_for_current_dagrun)
    threshold_times_run = run_for_time_threshold_anomaly.expand(n_seconds=times_for_current_dagrun)
    zscore_times_run = run_for_time_zscore_anomaly.expand(n_seconds=times_for_current_dagrun)
    moving_average_times_run = run_for_time_moving_average_anomaly.expand(n_seconds=times_for_current_dagrun)
    print_runtimes(
        always_runtimes=always_times_run,
        threshold_runtimes=threshold_times_run,
        zscore_runtimes=zscore_times_run,
        moving_average_runtimes=moving_average_times_run,
    )
# [END]
