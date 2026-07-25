import math

from voiceMonitor.analytics import EMAFatigue, ImpulseResponseFatigue, SessionAnalytics


def test_ema_first_value_passthrough():
    ema = EMAFatigue(alpha=0.3)
    assert ema.update(50) == 50


def test_ema_smooths_toward_new_value():
    ema = EMAFatigue(alpha=0.5)
    ema.update(0)
    result = ema.update(100)
    assert result == 50  # 0.5 * 100 + 0.5 * 0


def test_ema_default_alpha_from_config():
    ema = EMAFatigue()
    assert ema.alpha > 0 and ema.alpha <= 1


def test_impulse_accumulates_with_no_elapsed_time():
    model = ImpulseResponseFatigue(tau_fast=90, tau_slow=1500)
    state1 = model.update(20, elapsed_seconds=0)
    state2 = model.update(20, elapsed_seconds=0)
    assert state2["acute"] == 40
    assert state2["chronic"] == 40


def test_impulse_acute_decays_faster_than_chronic():
    model = ImpulseResponseFatigue(tau_fast=10, tau_slow=1000)
    model.update(100, elapsed_seconds=0)
    # advance a long time relative to tau_fast but short relative to tau_slow
    state = model.update(0, elapsed_seconds=50)
    assert state["acute"] < state["chronic"]


def test_impulse_readiness_is_chronic_minus_acute():
    model = ImpulseResponseFatigue(tau_fast=10, tau_slow=1000)
    model.update(100, elapsed_seconds=0)
    state = model.update(0, elapsed_seconds=50)
    assert math.isclose(
        state["readiness_experimental"], state["chronic"] - state["acute"]
    )


def test_recovery_eta_zero_when_already_safe():
    model = ImpulseResponseFatigue(tau_fast=90, tau_slow=1500)
    model.update(10, elapsed_seconds=0)
    eta = model.recovery_eta_seconds(safe_level=40)
    assert eta == 0.0


def test_recovery_eta_positive_when_above_safe_level():
    model = ImpulseResponseFatigue(tau_fast=90, tau_slow=1500)
    model.update(100, elapsed_seconds=0)
    eta = model.recovery_eta_seconds(safe_level=40)
    assert eta > 0


def test_recovery_eta_matches_manual_formula():
    model = ImpulseResponseFatigue(tau_fast=90, tau_slow=1500)
    model.update(200, elapsed_seconds=0)
    expected = 90 * math.log(200 / 40)
    assert math.isclose(model.recovery_eta_seconds(safe_level=40), expected)


def test_session_analytics_summary_shape():
    sa = SessionAnalytics()
    sa.add(20, "ts0", 0)
    sa.add(80, "ts1", 5)
    summary = sa.summary
    for key in [
        "average_fatigue", "max_fatigue", "readings", "smoothed_fatigue",
        "acute_load", "chronic_load", "readiness_experimental", "recovery_eta_sec",
    ]:
        assert key in summary


def test_session_analytics_average_and_max():
    sa = SessionAnalytics()
    sa.add(20, "ts0", 0)
    sa.add(80, "ts1", 5)
    assert sa.average == 50
    assert sa.maximum == 80


def test_session_analytics_empty_defaults():
    sa = SessionAnalytics()
    assert sa.average == 0
    assert sa.maximum == 0
    assert sa.summary["readings"] == 0