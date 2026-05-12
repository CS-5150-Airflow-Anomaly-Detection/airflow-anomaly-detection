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

import builtins
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from airflow.sdk.definitions.anomaly_detection import (
    AlwaysAnomaly,
    AnomalyDetector,
    AnomalyResult,
    MovingAverageAnomaly,
    ThresholdAnomaly,
    ZScoreAnomaly,
)


class TestAlwaysAnomaly:
    def test_flags_final_runtime(self) -> None:
        result = AlwaysAnomaly()([1.0, 2.0])
        assert isinstance(result, AnomalyResult)
        assert result.is_anomaly is True


class TestThresholdAnomaly:
    def test_no_anomaly_when_latest_inside_bounds(self) -> None:
        algo = ThresholdAnomaly(min_runtime=0.0, max_runtime=10.0)
        result = algo([1.0, 2.0, 5.0])
        assert result.is_anomaly is False

    def test_anomaly_when_latest_below_min(self) -> None:
        algo = ThresholdAnomaly(min_runtime=5.0, max_runtime=100.0)
        result = algo([10.0, 3.0])
        assert result.is_anomaly is True

    def test_anomaly_when_latest_above_max(self) -> None:
        algo = ThresholdAnomaly(min_runtime=0.0, max_runtime=1.0)
        result = algo([0.5, 2.0])
        assert result.is_anomaly is True

    def test_default_bounds_are_reported_as_unbounded(self) -> None:
        result = ThresholdAnomaly()([1.0, 2.0])

        assert result.is_anomaly is False
        assert result.details == {
            "current_runtime": 2.0,
            "min_runtime": None,
            "max_runtime": None,
        }

    def test_flags_all_runtimes_when_min_is_greater_than_max(self) -> None:
        algo = ThresholdAnomaly(min_runtime=10.0, max_runtime=5.0)
        result = algo([7.0])

        assert result.is_anomaly is True
        assert result.details["min_runtime"] == 10.0
        assert result.details["max_runtime"] == 5.0


class TestZScoreAnomaly:
    def test_no_anomaly_when_latest_within_threshold(self) -> None:
        algo = ZScoreAnomaly(z_threshold=2.0)
        result = algo([10.0, 12.0, 11.0, 13.0])
        assert result.is_anomaly is False

    def test_anomaly_when_latest_outside_threshold(self) -> None:
        algo = ZScoreAnomaly(z_threshold=1.0)
        result = algo([10.0, 12.0, 11.0, 15.0])
        assert result.is_anomaly is True

    def test_no_anomaly_when_not_enough_historical_runtimes(self) -> None:
        algo = ZScoreAnomaly(z_threshold=1.0)
        result = algo([10.0, 12.0])
        assert result.is_anomaly is False

    def test_anomaly_when_latest_differs_from_constant_mean(self) -> None:
        algo = ZScoreAnomaly(z_threshold=1.0)
        result = algo([5.0, 5.0, 8.0])
        assert result.is_anomaly is True

    def test_no_anomaly_when_latest_matches_constant_mean(self) -> None:
        algo = ZScoreAnomaly(z_threshold=1.0)
        result = algo([5.0, 5.0, 5.0])
        assert result.is_anomaly is False

    def test_raises_when_z_threshold_is_zero(self) -> None:
        with pytest.raises(ValueError, match="z_threshold must be > 0"):
            ZScoreAnomaly(z_threshold=0)

    def test_raises_when_z_threshold_is_negative(self) -> None:
        with pytest.raises(ValueError, match="z_threshold must be > 0"):
            ZScoreAnomaly(z_threshold=-1.0)

    def test_no_anomaly_when_latest_equals_z_threshold(self) -> None:
        algo = ZScoreAnomaly(z_threshold=2**-0.5)
        result = algo([10.0, 12.0, 12.0])

        assert result.is_anomaly is False
        assert result.details["z_score"] == pytest.approx(2**-0.5)


class TestMovingAverageAnomaly:
    def test_no_anomaly_when_latest_inside_moving_average_range(self) -> None:
        algo = MovingAverageAnomaly(min_ratio=0.75, max_ratio=1.25)
        result = algo([10.0, 12.0, 11.0, 13.0])
        assert result.is_anomaly is False

    def test_anomaly_when_latest_outside_moving_average_range(self) -> None:
        algo = MovingAverageAnomaly(min_ratio=0.75, max_ratio=1.25)
        result = algo([10.0, 12.0, 11.0, 20.0])
        assert result.is_anomaly is True

    def test_no_anomaly_when_not_enough_historical_runtimes(self) -> None:
        algo = MovingAverageAnomaly(min_ratio=0.75, max_ratio=1.25)
        result = algo([10.0])
        assert result.is_anomaly is False

    def test_anomaly_when_latest_differs_from_zero_moving_average(self) -> None:
        algo = MovingAverageAnomaly(min_ratio=0.75, max_ratio=1.25)
        result = algo([0.0, 0.0, 1.0])
        assert result.is_anomaly is True

    def test_no_anomaly_when_latest_matches_zero_moving_average(self) -> None:
        algo = MovingAverageAnomaly(min_ratio=0.75, max_ratio=1.25)
        result = algo([0.0, 0.0, 0.0])
        assert result.is_anomaly is False

    def test_raises_when_min_ratio_is_zero(self) -> None:
        with pytest.raises(ValueError, match="min_ratio must be between 0 and 1"):
            MovingAverageAnomaly(min_ratio=0.0, max_ratio=1.25)

    def test_raises_when_min_ratio_is_one(self) -> None:
        with pytest.raises(ValueError, match="min_ratio must be between 0 and 1"):
            MovingAverageAnomaly(min_ratio=1.0, max_ratio=1.25)

    def test_raises_when_min_ratio_is_greater_than_one(self) -> None:
        with pytest.raises(ValueError, match="min_ratio must be between 0 and 1"):
            MovingAverageAnomaly(min_ratio=1.5, max_ratio=1.25)

    def test_raises_when_max_ratio_is_one(self) -> None:
        with pytest.raises(ValueError, match="max_ratio must be > 1"):
            MovingAverageAnomaly(min_ratio=0.75, max_ratio=1.0)

    def test_raises_when_max_ratio_is_less_than_one(self) -> None:
        with pytest.raises(ValueError, match="max_ratio must be > 1"):
            MovingAverageAnomaly(min_ratio=0.75, max_ratio=0.5)

    def test_no_anomaly_when_latest_is_on_moving_average_bounds(self) -> None:
        algo = MovingAverageAnomaly(min_ratio=0.5, max_ratio=1.5)

        lower_bound = algo([10.0, 20.0, 7.5])
        upper_bound = algo([10.0, 20.0, 22.5])

        assert lower_bound.is_anomaly is False
        assert upper_bound.is_anomaly is False
        assert lower_bound.details["min_runtime"] == 7.5
        assert upper_bound.details["max_runtime"] == 22.5


class FakeTaskInstance:
    def __init__(self, *, previous_tis=None, start_date=None, end_date=None, map_index=3):
        self.previous_tis = previous_tis or []
        self.start_date = start_date
        self.end_date = end_date
        self.map_index = map_index
        self.dag_id = "dag"
        self.run_id = "run"
        self.task_id = "task"
        self.try_number = 2
        self.get_previous_ti_calls = []

    def get_previous_ti(self, *, state, logical_date, map_index):
        self.get_previous_ti_calls.append(
            {"state": state, "logical_date": logical_date, "map_index": map_index}
        )
        if logical_date is None:
            return self.previous_tis[0] if self.previous_tis else None

        for index, previous_ti in enumerate(self.previous_tis):
            if previous_ti.logical_date == logical_date:
                next_index = index + 1
                if next_index < len(self.previous_tis):
                    return self.previous_tis[next_index]
                return None

        return None


def make_previous_ti(duration, logical_date):
    return SimpleNamespace(duration=duration, logical_date=logical_date)


class RecordingAlgorithm:
    def __init__(self, result=None):
        self.result = result or AnomalyResult(
            True,
            message="runtime changed",
            details={"score": 1.5},
        )
        self.runtimes = None

    def __call__(self, runtimes):
        self.runtimes = runtimes
        return self.result


class FailingAlgorithm:
    def __call__(self, runtimes):
        raise RuntimeError("broken algorithm")


class RecordingComms:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


class FailingComms:
    def send(self, message):
        raise RuntimeError("cannot send")


class TestAnomalyDetector:
    def test_defaults_to_always_anomaly_algorithm(self) -> None:
        detector = AnomalyDetector(min_runs=1, max_runs=1)

        assert isinstance(detector.algorithm, AlwaysAnomaly)

    @pytest.mark.parametrize(
        ("min_runs", "max_runs", "message"),
        [
            (0, 1, "min_runs must be at least 1"),
            (1, 0, "max_runs must be at least 1"),
            (3, 2, "max_runs must be greater than or equal to min_runs"),
        ],
    )
    def test_raises_when_run_configuration_is_invalid(self, min_runs, max_runs, message) -> None:
        with pytest.raises(ValueError, match=message):
            AnomalyDetector(min_runs=min_runs, max_runs=max_runs)

    def test_get_historical_runtimes_returns_oldest_first_and_stops_on_missing_logical_date(
        self,
    ) -> None:
        logical_dates = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        ti = FakeTaskInstance(
            previous_tis=[
                make_previous_ti(3.0, logical_dates[0]),
                make_previous_ti(None, logical_dates[1]),
                make_previous_ti(1.0, None),
            ],
            map_index=7,
        )
        detector = AnomalyDetector(min_runs=1, max_runs=5)

        assert detector._get_historical_runtimes(ti) == [1.0, 3.0]
        assert [call["logical_date"] for call in ti.get_previous_ti_calls] == [
            None,
            logical_dates[0],
            logical_dates[1],
        ]
        assert {call["map_index"] for call in ti.get_previous_ti_calls} == {7}

    def test_call_skips_when_context_has_no_task_instance(self) -> None:
        algorithm = RecordingAlgorithm()
        detector = AnomalyDetector(min_runs=1, max_runs=1, algorithm=algorithm)

        detector({})

        assert algorithm.runtimes is None

    @pytest.mark.parametrize(
        ("start_date", "end_date"),
        [
            (None, datetime(2026, 1, 1, tzinfo=timezone.utc)),
            (datetime(2026, 1, 1, tzinfo=timezone.utc), None),
        ],
    )
    def test_call_skips_when_task_instance_timing_is_incomplete(self, start_date, end_date) -> None:
        algorithm = RecordingAlgorithm()
        detector = AnomalyDetector(min_runs=1, max_runs=1, algorithm=algorithm)
        ti = FakeTaskInstance(start_date=start_date, end_date=end_date)

        detector({"ti": ti})

        assert algorithm.runtimes is None

    def test_call_skips_when_not_enough_runs_are_available(self) -> None:
        algorithm = RecordingAlgorithm()
        detector = AnomalyDetector(min_runs=3, max_runs=3, algorithm=algorithm)
        ti = FakeTaskInstance(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=5),
        )

        detector({"ti": ti})

        assert algorithm.runtimes is None

    def test_call_skips_emit_when_runtime_imports_are_unavailable(self, monkeypatch) -> None:
        algorithm = RecordingAlgorithm()
        detector = AnomalyDetector(min_runs=1, max_runs=1, algorithm=algorithm)
        ti = FakeTaskInstance(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=5),
        )
        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "airflow.sdk.execution_time.comms":
                raise ImportError("missing comms")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        detector({"ti": ti})

        assert algorithm.runtimes == [5.0]

    def test_call_swallows_algorithm_errors(self) -> None:
        detector = AnomalyDetector(min_runs=1, max_runs=1, algorithm=FailingAlgorithm())
        ti = FakeTaskInstance(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=5),
        )

        detector({"ti": ti})

    def test_call_emits_anomaly_payload(self, monkeypatch) -> None:
        from airflow.sdk.execution_time import task_runner

        algorithm = RecordingAlgorithm()
        detector = AnomalyDetector(min_runs=2, max_runs=3, algorithm=algorithm)
        comms = RecordingComms()
        logical_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
        ti = FakeTaskInstance(
            previous_tis=[make_previous_ti(7.0, logical_date)],
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=5),
            map_index=9,
        )
        monkeypatch.setattr(task_runner, "SUPERVISOR_COMMS", comms, raising=False)

        detector({"ti": ti})

        assert algorithm.runtimes == [7.0, 5.0]
        assert len(comms.sent) == 1
        message = comms.sent[0]
        assert message.dag_id == "dag"
        assert message.run_id == "run"
        assert message.task_id == "task"
        assert message.map_index == 9
        assert message.try_number == 2
        assert message.is_anomalous is True
        assert message.detector_name == "RecordingAlgorithm"
        assert message.reason == "runtime changed"
        assert message.historic_runs_count == 1
        assert message.used_equal_map_index is True

    def test_call_swallows_payload_emit_errors(self, monkeypatch) -> None:
        from airflow.sdk.execution_time import task_runner

        detector = AnomalyDetector(min_runs=1, max_runs=1, algorithm=RecordingAlgorithm())
        ti = FakeTaskInstance(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=5),
        )
        monkeypatch.setattr(task_runner, "SUPERVISOR_COMMS", FailingComms(), raising=False)

        detector({"ti": ti})
