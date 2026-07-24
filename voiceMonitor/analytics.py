import math

from .config import Config


class EMAFatigue:
    """
    Smooths the raw per window fatigue score using an exponential moving
    average, so a single noisy window (a cough, a loud word, a pause) does
    not cause the reported fatigue level to jump around. Only the previous
    smoothed value is kept, so this stays lightweight and does not require
    the full session history.
    """

    def __init__(self, alpha=None):
        self.alpha = alpha if alpha is not None else Config.EMA_ALPHA
        self.value = None

    def update(self, score):
        if self.value is None:
            self.value = score
        else:
            self.value = self.alpha * score + (1 - self.alpha) * self.value
        return self.value


class ImpulseResponseFatigue:
    """
    Models accumulating vocal load using two parallel leaky integrators,
    adapted from the Banister impulse response framework used in sports
    science for athletic training load and recovery.

    Each incoming fatigue score is treated as an impulse applied to a
    fast decaying "acute" component (short term strain) and a slow decaying
    "chronic" component (strain accumulating across the session).

    NOTE on the readiness metric: "readiness" (chronic minus acute) mirrors
    how the athletic model computes freshness as fitness minus fatigue.
    Because voice has no direct positive equivalent to athletic fitness,
    both components here are reinterpreted as strain at different
    timescales rather than as fitness and fatigue. This reinterpretation,
    and the readiness formulation itself, has not yet been empirically
    validated for vocal fatigue. Treat "readiness" as an experimental,
    exploratory metric. The acute and chronic components are exposed
    separately precisely so they can be inspected and used independently
    until readiness is validated against real session data.

    Elapsed time for decay is passed in explicitly by the caller as
    elapsed_seconds, rather than measured internally with a wall clock.
    This keeps the decay math on the same deterministic time base as the
    audio stream itself (samples processed divided by sample rate), so it
    cannot drift apart from the session's recorded timestamps due to
    variable processing latency between windows.
    """

    def __init__(self, tau_fast=None, tau_slow=None):
        self.tau_fast = tau_fast if tau_fast is not None else Config.TAU_FAST
        self.tau_slow = tau_slow if tau_slow is not None else Config.TAU_SLOW
        self.acute = 0.0
        self.chronic = 0.0
        self._last_elapsed = None

    def update(self, score, elapsed_seconds):
        """
        score: raw fatigue score for this window
        elapsed_seconds: cumulative elapsed time of the audio stream, in
        seconds, at the moment this window was captured. Must come from
        the same deterministic clock used elsewhere in the session (audio
        samples processed divided by sample rate), not a separate wall
        clock, so temporal load calculations stay consistent with the
        session's own timestamps.
        """
        if self._last_elapsed is not None:
            dt = max(0.0, elapsed_seconds - self._last_elapsed)
            self.acute *= math.exp(-dt / self.tau_fast)
            self.chronic *= math.exp(-dt / self.tau_slow)

        self.acute += score
        self.chronic += score
        self._last_elapsed = elapsed_seconds

        return {
            "acute": self.acute,
            "chronic": self.chronic,
            "readiness_experimental": self.chronic - self.acute,
        }

    def recovery_eta_seconds(self, safe_level=None):
        """
        Estimated seconds until the acute component decays back under the
        safe level. Returns 0 if already at or below it.
        """
        safe_level = (
            safe_level if safe_level is not None else Config.SAFE_RECOVERY_LEVEL
        )
        if safe_level <= 0 or self.acute <= safe_level:
            return 0.0
        return self.tau_fast * math.log(self.acute / safe_level)


class SessionAnalytics:
    def __init__(self):
        self.scores = []
        self.timestamps = []
        self.smoothed_scores = []
        self.impulse_records = []

        self._ema = EMAFatigue()
        self._impulse = ImpulseResponseFatigue()

    def add(self, score, ts, elapsed_seconds):
        """
        ts: the human readable session timestamp string (e.g. from
        utils.timestamp()), used for record labeling and display only.
        elapsed_seconds: the deterministic, audio stream derived elapsed
        time in seconds, used for all decay and load calculations. Keeping
        these two separate but both required makes explicit that display
        timestamps and temporal math must not be conflated.
        """
        self.scores.append(score)
        self.timestamps.append(ts)

        smoothed = self._ema.update(score)
        self.smoothed_scores.append(smoothed)

        impulse_state = self._impulse.update(score, elapsed_seconds)
        impulse_state["recovery_eta_sec"] = self._impulse.recovery_eta_seconds()
        self.impulse_records.append(impulse_state)

        return smoothed, impulse_state

    @property
    def average(self):
        return sum(self.scores) / len(self.scores) if self.scores else 0

    @property
    def maximum(self):
        return max(self.scores) if self.scores else 0

    @property
    def summary(self):
        latest = self.impulse_records[-1] if self.impulse_records else {}
        return {
            "average_fatigue": self.average,
            "max_fatigue": self.maximum,
            "readings": len(self.scores),
            "smoothed_fatigue": self.smoothed_scores[-1] if self.smoothed_scores else 0,
            "acute_load": latest.get("acute", 0),
            "chronic_load": latest.get("chronic", 0),
            "readiness_experimental": latest.get("readiness_experimental", 0),
            "recovery_eta_sec": latest.get("recovery_eta_sec", 0),
        }