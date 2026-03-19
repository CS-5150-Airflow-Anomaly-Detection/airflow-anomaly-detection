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
from dataclasses import dataclass, field
from typing import Any

import structlog

from airflow.sdk.execution_time import task_runner
from airflow.sdk.execution_time.comms import RecordTaskAnomaly


class BaseAnomalyAlgorithm:
    """Declarative algorithm definition evaluated by the server."""

    algorithm_name: str

    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class AlwaysAnomaly(BaseAnomalyAlgorithm):
    """Debugger/testing algorithm that always marks the current TI as anomalous."""

    algorithm_name: str = field(init=False, default="always")

    def serialize(self) -> dict[str, Any]:
        return {}


@dataclass
class ThresholdAnomaly(BaseAnomalyAlgorithm):
    """Flag a TI when its runtime falls outside an allowed duration range."""

    min_runtime: float = float("-inf")
    max_runtime: float = float("inf")
    algorithm_name: str = field(init=False, default="threshold")

    def serialize(self) -> dict[str, Any]:
        min_runtime = None if math.isinf(self.min_runtime) and self.min_runtime < 0 else self.min_runtime
        max_runtime = None if math.isinf(self.max_runtime) and self.max_runtime > 0 else self.max_runtime
        return {
            "min_runtime": min_runtime,
            "max_runtime": max_runtime,
        }


@dataclass
class AnomalyDetector:
    """DAG-facing anomaly detector configuration."""

    min_runs: int
    max_runs: int
    algorithm: BaseAnomalyAlgorithm = field(default_factory=AlwaysAnomaly)

    def __post_init__(self) -> None:
        if self.min_runs < 1:
            raise ValueError("min_runs must be at least 1")
        if self.max_runs < self.min_runs:
            raise ValueError("max_runs must be greater than or equal to min_runs")

    def __call__(self, context) -> None:
        """
        Entry point called after a task instance completes successfully.

        The worker emits a declarative request and the API server performs both
        historical lookup and metadata DB writes.
        """
        log = structlog.get_logger(logger_name="task")
        ti = context.get("ti")
        if ti is None:
            return

        comms = getattr(task_runner, "SUPERVISOR_COMMS", None)
        if comms is None:
            log.debug("Supervisor comms unavailable; skipping anomaly evaluation")
            return

        try:
            comms.send(
                RecordTaskAnomaly(
                    min_runs=self.min_runs,
                    max_runs=self.max_runs,
                    algorithm_name=self.algorithm.algorithm_name,
                    algorithm_config=self.algorithm.serialize(),
                )
            )
        except Exception:
            log.exception("Failed to emit anomaly evaluation request")
