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

import pytest

from airflow.sdk.definitions.anomaly_detection import (
    AlwaysAnomaly,
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
