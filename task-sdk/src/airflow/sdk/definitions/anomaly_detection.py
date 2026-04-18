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
import statistics
from typing import Any

import structlog

from airflow.sdk import TaskInstanceState

__all__ = [
    "AlwaysAnomaly",
    "AnomalyDetector",
    "AnomalyResult",
    "MovingAverageAnomaly",
    "ThresholdAnomaly",
    "ZScoreAnomaly",
]


class AnomalyResult:
    """
    Result of anomaly detection.

    Parameters
    ----------
    is_anomaly : bool
        Whether the latest runtime should be flagged as anomalous.

    message : str
        Human-readable summary of the anomaly evaluation. This is used in
        parent detector logging and when emitting the anomaly payload.

    details : dict[str, Any] | None
        Optional structured fields supplied by the anomaly algorithm for the
        parent detector to include in its logs.
    """

    def __init__(
        self,
        is_anomaly: bool,
        message: str = "",
        details: dict[str, Any] | None = None,
    ):
        self.is_anomaly = is_anomaly
        self.message = message
        self.details = details or {}


class AlwaysAnomaly:
    """Debugger/testing anomaly type that marks all TI as anomalies."""

    def __init__(self):
        pass

    def __call__(self, runtimes):
        return AnomalyResult(
            True,
            message="AlwaysAnomaly marks every task instance as anomalous.",
            details={"current_runtime": runtimes[-1]},
        )


class ThresholdAnomaly:
    """Anomaly type: if the latest runtime is outside [min_runtime, max_runtime], flag an anomaly."""

    def __init__(self, min_runtime=-math.inf, max_runtime=math.inf):
        self.min_runtime = min_runtime
        self.max_runtime = max_runtime

    def __call__(self, runtimes):
        cur_runtime = runtimes[-1]
        if cur_runtime >= self.min_runtime and cur_runtime <= self.max_runtime:
            return AnomalyResult(
                False,
                message="Runtime is within the configured threshold range.",
                details={
                    "current_runtime": cur_runtime,
                    "min_runtime": None if math.isinf(self.min_runtime) else self.min_runtime,
                    "max_runtime": None if math.isinf(self.max_runtime) else self.max_runtime,
                },
            )
        return AnomalyResult(
            True,
            message="Runtime is outside the configured threshold range.",
            details={
                "current_runtime": cur_runtime,
                "min_runtime": None if math.isinf(self.min_runtime) else self.min_runtime,
                "max_runtime": None if math.isinf(self.max_runtime) else self.max_runtime,
            },
        )


class ZScoreAnomaly:
    """
    Anomaly type: if the latest runtime is more than z_threshold stddev from the historical mean, flag an anomaly.

    Constraints:
    * Requires min_runs > 2.
    """

    def __init__(self, z_threshold=3.0):
        """
        Initialize the anomaly type threshold in standard deviations from the historical mean.

        Parameters
        ----------
        z_threshold
            Number of standard deviations the latest runtime may differ from the
            historical mean before being flagged as anomalous.
        """
        self.z_threshold = z_threshold

    def __call__(self, runtimes):
        historical_runtimes = runtimes[:-1]
        cur_runtime = runtimes[-1]
        details = {
            "current_runtime": cur_runtime,
            "historical_run_count": len(historical_runtimes),
            "z_threshold": self.z_threshold,
        }

        if len(historical_runtimes) < 2:
            details["required_historical_run_count"] = 2
            return AnomalyResult(
                False,
                "Not enough historical runtimes to calculate standard deviation.",
                details=details,
            )

        mean = statistics.mean(historical_runtimes)
        stddev = statistics.stdev(historical_runtimes)
        details["historical_mean"] = mean
        details["historical_stddev"] = stddev

        if stddev == 0:
            is_anomaly = cur_runtime != mean
            message = (
                f"Latest runtime {cur_runtime:.2f}s differs from the constant historical mean {mean:.2f}s."
                if is_anomaly
                else "Latest runtime matches the constant historical mean."
            )
            return AnomalyResult(
                is_anomaly,
                message,
                details=details,
            )

        z_score = abs(cur_runtime - mean) / stddev
        details["z_score"] = z_score
        if z_score <= self.z_threshold:
            return AnomalyResult(
                False,
                "Latest runtime is within the z-score threshold.",
                details=details,
            )

        return AnomalyResult(
            True,
            f"Latest runtime {cur_runtime:.2f}s is {z_score:.2f} standard deviations from "
            f"the historical mean {mean:.2f}s.",
            details=details,
        )


class MovingAverageAnomaly:
    """
    Anomaly type: if the latest runtime deviates from a rolling mean by more than the configured bounds.

    Constraints:
    * Requires min_runs > 1.
    """

    def __init__(self, window_size=5, min_ratio=0.5, max_ratio=1.5):
        """
        Initialize the anomaly type rolling window and allowed deviation range from the moving average.

        Parameters
        ----------
        window_size
            Number of most recent historical runtimes used to compute the
            moving-average baseline.
        min_ratio
            Lower bound multiplier applied to the moving-average baseline.
        max_ratio
            Upper bound multiplier applied to the moving-average baseline.
        """
        self.window_size = window_size
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio

    def __call__(self, runtimes):
        historical_runtimes = runtimes[:-1]
        cur_runtime = runtimes[-1]
        details = {
            "current_runtime": cur_runtime,
            "historical_run_count": len(historical_runtimes),
            "window_size": self.window_size,
            "min_ratio": self.min_ratio,
            "max_ratio": self.max_ratio,
        }

        if not historical_runtimes:
            return AnomalyResult(
                False,
                "Not enough historical runtimes to calculate a moving average.",
                details=details,
            )

        window = historical_runtimes[-self.window_size :]
        moving_average = statistics.mean(window)
        details["window_size"] = len(window)
        details["moving_average"] = moving_average

        if moving_average == 0:
            is_anomaly = cur_runtime != 0
            message = (
                f"Latest runtime {cur_runtime:.2f}s differs from the zero moving-average baseline."
                if is_anomaly
                else "Latest runtime matches the zero moving-average baseline."
            )
            return AnomalyResult(
                is_anomaly,
                message,
                details=details,
            )

        min_runtime = moving_average * self.min_ratio
        max_runtime = moving_average * self.max_ratio
        details["min_runtime"] = min_runtime
        details["max_runtime"] = max_runtime

        if cur_runtime >= min_runtime and cur_runtime <= max_runtime:
            return AnomalyResult(
                False,
                "Latest runtime is within the moving-average range.",
                details=details,
            )

        return AnomalyResult(
            True,
            f"Latest runtime {cur_runtime:.2f}s is outside the moving-average range "
            f"[{min_runtime:.2f}s, {max_runtime:.2f}s] computed from the last {len(window)} runs.",
            details=details,
        )


class AnomalyDetector:
    """
    Base class for anomaly detection strategies.

    Subclasses should override detect_anomalies().
    """

    def __init__(self, min_runs: int, max_runs: int, algorithm=None):
        """
        Initialize an anomaly detector configuration.

        Parameters
        ----------
        min_runs : int
            Minimum number of runtimes required before anomaly detection is
            attempted, including historical runs and the current runtime being
            evaluated. Requires min_runs >= 1.

        max_runs : int
            Maximum number of historical runs to consider.
            Older runs should be discarded. Requires max_runs >= 1 and max_runs >= min_runs.

        algorithm : callable object/function
            Must implement algorithm(runtimes) -> AnomalyResult
            returning an AnomalyResult showing whether an anomaly was detected for the last runtime, and associated information.
        """
        if min_runs < 1:
            raise ValueError("min_runs must be at least 1")
        if max_runs < 1:
            raise ValueError("max_runs must be at least 1")
        if max_runs < min_runs:
            raise ValueError("max_runs must be greater than or equal to min_runs")

        self.min_runs = min_runs
        self.max_runs = max_runs
        self.algorithm = algorithm or AlwaysAnomaly()

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
        detector_name = type(self.algorithm).__name__

        ti = context.get("ti")
        if ti is None:
            log.debug("Skipping anomaly detection due to missing task instance context")
            return

        start_date = getattr(ti, "start_date", None)
        end_date = getattr(ti, "end_date", None)
        if start_date is None or end_date is None:
            log.debug(
                "Anomaly detection skipped due to incomplete task instance timing",
                has_start_date=start_date is not None,
                has_end_date=end_date is not None,
            )
            return

        log.info(
            "Anomaly detection started",
            detector_name=detector_name,
            min_runs=self.min_runs,
            max_runs=self.max_runs,
        )

        current_duration = (end_date - start_date).total_seconds()
        historical_runtimes = self._get_historical_runtimes(ti)
        runtimes = [*historical_runtimes, current_duration]

        log.debug(
            "Anomaly detection retrieved historical runtimes",
            runs_considered=len(runtimes),
            runtimes=runtimes,
        )

        if len(runtimes) < self.min_runs:
            log.info(
                "Anomaly detection skipped due to insufficient run count",
                found_runs=len(runtimes),
                required_runs=self.min_runs,
            )
            return

        try:
            result = self.algorithm(runtimes)
        except Exception:
            log.exception("Anomaly detection evaluation failed", detector_name=detector_name)
            return

        log.info(
            "Anomaly detection evaluated",
            is_anomaly=str(result.is_anomaly),
            reason=result.message,
            **result.details,
        )

        try:
            # Import runtime dependencies
            from airflow.sdk.execution_time.comms import RecordTaskAnomaly
            from airflow.sdk.execution_time.task_runner import SUPERVISOR_COMMS
        except Exception:
            log.info("Anomaly detection emit skipped", reason="supervisor_comms_unavailable")
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
                    detector_name=detector_name,
                    reason=(getattr(result, "message", "") or None),
                )
            )
            log.info(
                "Anomaly payload emitted",
                detector_name=detector_name,
                is_anomaly=bool(getattr(result, "is_anomaly", False)),
            )
        except Exception:
            log.exception(
                "Failed to emit anomaly payload",
                detector_name=detector_name,
                is_anomaly=bool(getattr(result, "is_anomaly", False)),
            )
