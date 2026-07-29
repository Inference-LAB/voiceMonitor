import json
from .analytics import SessionAnalytics

class SessionReport:
    def __init__(self):
        self.analytics = SessionAnalytics()
        self.records = []

    def add_record(
        self, timestamp, chunk_file, score, elapsed_seconds=None,
        features=None, baseline_info=None,
    ):
        """
        features: acoustic markers (jitter, shimmer, HNR, CPPS) collected
        alongside the primary auralis_vfs score. These are currently
        auxiliary data, stored for future analysis, and do not yet
        influence the fatigue score, warning logic, or any analytics
        computed in this module. Integrating them into the fatigue model
        itself is planned as future work, not part of this change.

        baseline_info: output of BaselineCalibrator.update (baseline,
        adjusted_score, is_provisional), stored alongside the raw score for
        the same reason as features above. The raw score and warning
        threshold logic are unchanged by this; baseline adjusted values are
        exposed for inspection and future use, not yet wired into alerting.
        """
        smoothed, impulse_state = self.analytics.add(score, timestamp, elapsed_seconds)
        baseline_info = baseline_info or {}

        self.records.append({
            "timestamp": timestamp,
            "chunk": chunk_file,
            "score": score,
            "features": features or {},
            "smoothed_score": smoothed,
            "acute_load": impulse_state["acute"],
            "chronic_load": impulse_state["chronic"],
            "readiness_experimental": impulse_state["readiness_experimental"],
            "recovery_eta_sec": impulse_state["recovery_eta_sec"],
            "baseline": baseline_info.get("baseline"),
            "baseline_adjusted_score": baseline_info.get("adjusted_score"),
            "baseline_is_provisional": baseline_info.get("is_provisional"),
        })

    def export_json(self, path):
        data = {
            "summary": self.analytics.summary,
            "records": self.records,
        }
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)