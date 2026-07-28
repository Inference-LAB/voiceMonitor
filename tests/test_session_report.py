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


def test_add_record_exposes_recovery_eta_per_window():
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 100, elapsed_seconds=0)
    record = report.records[0]

    assert "recovery_eta_sec" in record
    assert "acute_load" in record
    assert "chronic_load" in record
    assert "readiness_experimental" in record
    assert "smoothed_score" in record
    assert record["recovery_eta_sec"] > 0


def test_recovery_eta_decreases_as_session_recovers():
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 100, elapsed_seconds=0)
    first_eta = report.records[0]["recovery_eta_sec"]

    # a long pause with low scores should let the acute load decay,
    # reducing the estimated recovery time on the next reading
    report.add_record("ts2", "chunks/ts2.wav", 0, elapsed_seconds=120)
    second_eta = report.records[1]["recovery_eta_sec"]

    assert second_eta < first_eta


def test_recovery_eta_is_zero_for_low_scores():
    report = SessionReport()
    report.add_record("ts1", "chunks/ts1.wav", 5, elapsed_seconds=0)
    assert report.records[0]["recovery_eta_sec"] == 0