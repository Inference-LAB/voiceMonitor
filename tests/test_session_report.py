import json
import os
import tempfile

from voiceMonitor.session import SessionReport


def test_add_record_stores_fields():
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 42.5, elapsed_seconds=0)

    assert len(report.records) == 1
    record = report.records[0]
    assert record["timestamp"] == "ts1"
    assert record["chunk"] == "chunks/ts1.wav"
    assert record["score"] == 42.5
    assert record["features"] == {}


def test_add_record_stores_features_when_given():
    report = SessionReport()
    features = {"jitter_local": 0.01, "shimmer_local": 0.02, "hnr": 15.0, "cpps": 8.0}
    report.add_record("ts1", "chunks/ts1.wav", 42.5, elapsed_seconds=0, features=features)

    assert report.records[0]["features"] == features


def test_add_record_defaults_elapsed_seconds_when_omitted():
    # backward compatible call, mirrors pre-existing callers
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 10)
    report.add_record("ts2", "chunks/ts2.wav", 20)
    assert report.analytics.average == 15
    assert report.analytics.maximum == 20


def test_add_record_updates_analytics():
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 10, elapsed_seconds=0)
    report.add_record("ts2", "chunks/ts2.wav", 30, elapsed_seconds=5)

    assert report.analytics.average == 20
    assert report.analytics.maximum == 30
    assert report.analytics.summary["readings"] == 2


def test_export_json_writes_expected_structure():
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 50, elapsed_seconds=0)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, "session_report.json")
        report.export_json(out_path)

        assert os.path.exists(out_path)
        with open(out_path) as fp:
            data = json.load(fp)

        assert "summary" in data
        assert "records" in data
        assert data["records"][0]["timestamp"] == "ts1"
        assert data["summary"]["readings"] == 1