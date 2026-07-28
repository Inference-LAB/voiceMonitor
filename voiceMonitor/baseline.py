from .config import Config


class BaselineCalibrator:
    """
    Establishes a personal fatigue baseline for the current speaker during
    the first portion of a session, rather than comparing everyone against
    one fixed population level. Fatigue is then reported as a deviation
    from that speaker's own baseline, so a naturally breathy or otherwise
    atypical voice is not mistaken for fatigue.

    During calibration (elapsed_seconds below the configured calibration
    window), the baseline is estimated from whatever scores have been seen
    so far, and readings are flagged as provisional since the estimate is
    still forming. If a session ends before enough calibration data has
    been collected, or before the calibration window closes, a conservative
    population default is used instead of an unstable partial estimate
    computed from very little data.

    After the calibration window closes, the baseline is locked to the
    average of the scores collected during calibration and does not change
    for the rest of the session, so later fatigue readings are compared
    against a stable reference point rather than one that keeps drifting.
    """

    def __init__(self, calibration_sec=None, default_baseline=None):
        self.calibration_sec = (
            calibration_sec
            if calibration_sec is not None
            else Config.BASELINE_CALIBRATION_SEC
        )
        self.default_baseline = (
            default_baseline
            if default_baseline is not None
            else Config.DEFAULT_POPULATION_BASELINE
        )
        self._scores = []
        self._locked_baseline = None

    @property
    def is_locked(self):
        return self._locked_baseline is not None

    def _current_estimate(self):
        if not self._scores:
            return self.default_baseline
        return sum(self._scores) / len(self._scores)

    def update(self, score, elapsed_seconds):
        """
        Returns a dict with the baseline used for this reading, the score
        adjusted for that baseline (never negative, since a fatigue level
        below one's own baseline is reported as zero rather than negative),
        and whether the reading falls inside the still forming calibration
        window.

        The very first reading in a session has no prior data at all, so
        it is compared against the population default rather than against
        itself, which would otherwise always report zero deviation. Once
        at least one prior reading exists, the baseline reflects the
        running average including the current reading.
        """
        still_calibrating = elapsed_seconds < self.calibration_sec

        if still_calibrating:
            if not self._scores:
                baseline = self.default_baseline
                self._scores.append(score)
            else:
                self._scores.append(score)
                baseline = self._current_estimate()
        else:
            if self._locked_baseline is None:
                self._locked_baseline = self._current_estimate()
            baseline = self._locked_baseline

        adjusted_score = max(0.0, score - baseline)

        return {
            "baseline": baseline,
            "adjusted_score": adjusted_score,
            "is_provisional": still_calibrating,
        }