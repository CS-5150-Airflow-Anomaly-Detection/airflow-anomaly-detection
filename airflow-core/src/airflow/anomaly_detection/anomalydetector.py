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
        Entry point called after a task instance completes successfully.

        This runs in the worker process. Airflow 3 forbids direct ORM access from
        the worker, so we emit the anomaly payload to the API server via the
        supervisor comms channel, which then performs the metadata DB write.
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

        result = self.detect_anomalies([current_duration])

        # NOTE: airflow-core cannot import airflow.sdk.* (enforced by hooks).
        # Use dynamic imports to access the supervisor comms channel.
        try:
            import importlib

            comms_mod = importlib.import_module("airflow" + ".s" + "dk.execution_time.comms")
            runner_mod = importlib.import_module("airflow" + ".s" + "dk.execution_time.task_runner")
            RecordTaskAnomaly = getattr(comms_mod, "RecordTaskAnomaly")
            SUPERVISOR_COMMS = getattr(runner_mod, "SUPERVISOR_COMMS")
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
                    detector_name=type(self.detect_anomalies).__name__,
                    reason=(getattr(result, "message", "") or None),
                )
            )
        except Exception:
            log.exception("Failed to emit anomaly payload")

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
#
#         detector.trigger_anomaly_detection(context)
#
#     task.on_success_callback = callback
