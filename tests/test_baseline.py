from voiceMonitor.baseline import BaselineCalibrator


def test_first_reading_uses_population_default():
    calib = BaselineCalibrator(calibration_sec=45, default_baseline=30)
    result = calib.update(score=50, elapsed_seconds=0)
    assert result["baseline"] == 30
    assert result["is_provisional"] is True


def test_baseline_updates_as_more_scores_seen_during_calibration():
    calib = BaselineCalibrator(calibration_sec=45, default_baseline=30)
    calib.update(score=20, elapsed_seconds=0)
    result = calib.update(score=40, elapsed_seconds=10)
    # average of 20 and 40 is 30, matches the running estimate
    assert result["baseline"] == 30
    assert result["is_provisional"] is True


def test_baseline_locks_after_calibration_window_closes():
    calib = BaselineCalibrator(calibration_sec=10, default_baseline=30)
    calib.update(score=20, elapsed_seconds=0)
    calib.update(score=40, elapsed_seconds=5)
    # window closes here; locked baseline should be avg(20, 40) = 30
    result = calib.update(score=100, elapsed_seconds=15)
    assert result["baseline"] == 30
    assert result["is_provisional"] is False


def test_locked_baseline_does_not_change_after_lock():
    calib = BaselineCalibrator(calibration_sec=10, default_baseline=30)
    calib.update(score=20, elapsed_seconds=0)
    calib.update(score=40, elapsed_seconds=5)
    calib.update(score=100, elapsed_seconds=15)  # locks here at 30
    result = calib.update(score=5, elapsed_seconds=20)
    # even though a very low score comes in post lock, baseline stays fixed
    assert result["baseline"] == 30


def test_adjusted_score_is_score_minus_baseline():
    calib = BaselineCalibrator(calibration_sec=10, default_baseline=30)
    result = calib.update(score=50, elapsed_seconds=0)
    assert result["adjusted_score"] == 20  # 50 - 30


def test_adjusted_score_never_negative():
    calib = BaselineCalibrator(calibration_sec=10, default_baseline=30)
    result = calib.update(score=10, elapsed_seconds=0)
    assert result["adjusted_score"] == 0


def test_falls_back_to_population_default_with_no_calibration_data():
    # session ends with only one instantaneous reading right at elapsed=0
    calib = BaselineCalibrator(calibration_sec=45, default_baseline=30)
    result = calib.update(score=60, elapsed_seconds=0)
    assert result["baseline"] == 30
    assert result["adjusted_score"] == 30


def test_is_locked_property_reflects_state():
    calib = BaselineCalibrator(calibration_sec=10, default_baseline=30)
    assert calib.is_locked is False
    calib.update(score=20, elapsed_seconds=0)
    assert calib.is_locked is False
    calib.update(score=20, elapsed_seconds=15)
    assert calib.is_locked is True