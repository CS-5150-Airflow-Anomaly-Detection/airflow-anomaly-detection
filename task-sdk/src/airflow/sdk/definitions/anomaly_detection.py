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

import math

import structlog

from airflow.sdk import TaskInstanceState

__all__ = [
    "AlwaysAnomaly",
    "AnomalyDetector",
    "AnomalyResult",
    "ThresholdAnomaly",
]


class AnomalyResult:
    """Result of anomaly detection."""

    def __init__(
        self,
        is_anomaly: bool,
        message: str = "",
    ):
        self.is_anomaly = is_anomaly
        self.message = message


class AlwaysAnomaly:
    """Debugger/testing anomaly type that marks all TI as anomalies."""

    def __init__(self):
        pass

    def __call__(self, runtimes):
        return AnomalyResult(True)


class ThresholdAnomaly:
    """Anomaly type: if the latest runtime is outside [min_runtime, max_runtime], flag an anomaly."""

    def __init__(self, min_runtime=-math.inf, max_runtime=math.inf):
        self.min_runtime = min_runtime
        self.max_runtime = max_runtime

    def __call__(self, runtimes):
        cur_runtime = runtimes[-1]
        if cur_runtime >= self.min_runtime and cur_runtime <= self.max_runtime:
            return AnomalyResult(False)
        return AnomalyResult(True)


class AnomalyDetector:
    """
    Base class for anomaly detection strategies.

    Subclasses should override detect_anomalies().
    """

    def __init__(self, min_runs: int, max_runs: int, algorithm=AlwaysAnomaly()):
        """
        Initialize an anomaly detector configuration.

        Parameters
        ----------
        min_runs : int
            Minimum number of historical runs required before
            anomaly detection is attempted.

        max_runs : int
            Maximum number of historical runs to consider.
            Older runs should be discarded.

        algorithm : callable object/function
            Must implement algorithm(runtimes) -> AnomalyResult
            returning an AnomalyResult showing whether an anomaly was detected for the last runtime, and associated information.
        """
        self.min_runs = min_runs
        self.max_runs = max_runs
        self.algorithm = algorithm

    def _get_historical_runtimes(self, ti) -> list[float]:
        """Fetch durations from prior successful task instances via supervisor comms."""
        runtimes: list[float] = []
        cursor_logical_date = None
        map_index = getattr(ti, "map_index", -1)

        while len(runtimes) < max(self.max_runs - 1, 0):
            previous_ti = ti.get_previous_ti(
                state=TaskInstanceState.SUCCESS,
                logical_date=cursor_logical_date,
                map_index=map_index,
            )
            if previous_ti is None:
                break

            if previous_ti.duration is not None:
                runtimes.append(previous_ti.duration)

            # Move the cursor back so the next request finds an older TI.
            cursor_logical_date = previous_ti.logical_date
            if cursor_logical_date is None:
                break

        runtimes.reverse()
        return runtimes

    def __call__(self, context):
        """
        Entry point called after a task instance completes successfully.

        This runs in the worker process. Airflow 3 forbids direct ORM access from
        the worker, so we emit the anomaly payload to the API server via the
        supervisor comms channel, which then performs the metadata DB write.

        Imports are deferred to runtime so DAG parsing does not load execution modules.
        """
        log = structlog.get_logger(logger_name="task")

        ti = context.get("ti")
        if ti is None:
            return

        start_date = getattr(ti, "start_date", None)
        end_date = getattr(ti, "end_date", None)
        if start_date is None or end_date is None:
            return

        current_duration = (end_date - start_date).total_seconds()
        historical_runtimes = self._get_historical_runtimes(ti)
        historic_runs_count = len(historical_runtimes)
        runtimes = [*historical_runtimes, current_duration]

        log.info("Retrieved runtimes:", found_runs=len(runtimes), runtimes=runtimes)

        if len(runtimes) < self.min_runs:
            log.debug(
                "Skipping anomaly detection due to insufficient successful runs",
                found_runs=len(runtimes),
                required_runs=self.min_runs,
            )
            return

        result = self.algorithm(runtimes)

        try:
            # Import runtime dependencies
            from airflow.sdk.execution_time.comms import RecordTaskAnomaly
            from airflow.sdk.execution_time.task_runner import SUPERVISOR_COMMS
        except Exception:
            log.debug("Supervisor comms unavailable; skipping anomaly emit")
            return

        try:
            SUPERVISOR_COMMS.send(
                RecordTaskAnomaly(
                    dag_id=getattr(ti, "dag_id", ""),
                    run_id=getattr(ti, "run_id", ""),
                    task_id=getattr(ti, "task_id", ""),
                    map_index=getattr(ti, "map_index", -1),
                    try_number=getattr(ti, "try_number", 0),
                    is_anomalous=bool(getattr(result, "is_anomaly", False)),
                    detector_name=type(self.algorithm).__name__,
                    reason=(getattr(result, "message", "") or None),
                    historic_runs_count=historic_runs_count,
                    used_equal_map_index=True,  # historical runtimes always use same map index right now
                )
            )
        except Exception:
            log.exception("Failed to emit anomaly payload")
