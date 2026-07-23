import json
from .analytics import SessionAnalytics

class SessionReport:
    def __init__(self):
        self.analytics = SessionAnalytics()
        self.records = []

    def add_record(self, timestamp, chunk_file, score, features=None):
        self.records.append({
            "timestamp": timestamp,
            "chunk": chunk_file,
            "score": score,
            "features": features or {},
        })
        self.analytics.add(score, timestamp)

    def export_json(self, path):
        data = {
            "summary": self.analytics.summary,
            "records": self.records,
        }
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)