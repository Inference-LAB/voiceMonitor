import json
from .analytics import SessionAnalytics

class SessionReport:
    def __init__(self):
        self.analytics = SessionAnalytics()
        self.records = []

    def add_record(self, timestamp, chunk_file, score, elapsed_seconds, features=None):
        """
        features: acoustic markers (jitter, shimmer, HNR, CPPS) collected
        alongside the primary auralis_vfs score. These are currently
        auxiliary data, stored for future analysis, and do not yet
        influence the fatigue score, warning logic, or any analytics
        computed in this module. Integrating them into the fatigue model
        itself is planned as future work, not part of this change.
        """
        self.records.append({
            "timestamp": timestamp,
            "chunk": chunk_file,
            "score": score,
            "features": features or {},
        })
        self.analytics.add(score, timestamp, elapsed_seconds)

    def export_json(self, path):
        data = {
            "summary": self.analytics.summary,
            "records": self.records,
        }
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)