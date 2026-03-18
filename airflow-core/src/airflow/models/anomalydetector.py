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


class AnomalyResult:
    """Result of anomaly detection."""

    def __init__(
        self,
        is_anomaly: bool,
        message: str = "",
    ):
        self.is_anomaly = is_anomaly
        self.message = message
        # TODO: optionally extend with other information


class AlwaysAnomaly:
    """This is the debugger/testing anomaly type that marks all TI as anomalies."""

    def __init__(self):
        pass

    def __call__(self, runtimes):
        return AnomalyResult(True)


class ThresholdAnomaly:
    """This anomaly type defineds a threshold that if a TI surpasses will propagate an anomaly."""

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
        self.detect_anomalies = algorithm

    def __call__(self, context):
        """
        Entry point called after a task instance completes.

        This method implements the shared workflow:
        1. Fetch historical task instances.
        2. Extract runtimes.
        3. Check whether there are enough runs.
        4. Call the algorithm-specific anomaly detection.
        """
        # TODO: Take this out and replace with better logging messages as needed.
        log = structlog.get_logger(logger_name="task")
        log.info("***Inside of Task anomaly detection***")

        # 1. Query Airflow metadata DB for historical task instances
        #    associated with this task.
        ti = context["ti"]
        _ = ti

        runs = []  # placeholder
        _ = runs

        # 2. Extract runtimes (or durations)
        # runtimes = [ti.duration for ti in runs] or similar
        runtimes = []

        # 3. Enforce max_runs limit
        # runtimes = runtimes[-self.max_runs:]

        # 4. Ensure enough data exists
        if len(runtimes) < self.min_runs:
            # Not enough history to perform anomaly detection
            return

        # 5. Delegate to algorithm implementation
        result = self.detect_anomalies(runtimes)
        _ = result

        # 6. Handle anomalies (log, raise alert, etc.)
        # if anomalies:
        #     log or notify
        pass

    def detect_anomalies(self, runtimes: list[float]) -> AnomalyResult:
        """
        Algorithm-specific anomaly detection.  Override in subclasses.

        Parameters
        ----------
        runtimes : List[float]
            Historical task runtimes.

        Returns
        -------
        AnomalyResult
            Information about detected anomalies
        """
        raise NotImplementedError()


# def attach_anomaly_detector(task, detector: AnomalyDetector):
#     existing_callback = task.on_success_callback
#     def callback(context):
#         if existing_callback:
#             existing_callback(context)

#         detector.trigger_anomaly_detection(context)

#     task.on_success_callback = callback
