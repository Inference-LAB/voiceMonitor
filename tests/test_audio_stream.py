import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from voiceMonitor.audio_stream import VoiceMonitor
from voiceMonitor.config import Config


def test_voice_monitor_init_creates_chunk_dir(tmp_path):
    chunk_dir = tmp_path / "chunks_test"
    vm = VoiceMonitor(chunk_dir=str(chunk_dir))
    assert chunk_dir.exists()
    assert vm.threshold == Config.DEFAULT_THRESHOLD


def test_voice_monitor_init_custom_threshold(tmp_path):
    vm = VoiceMonitor(threshold=55, chunk_dir=str(tmp_path / "chunks_test2"))
    assert vm.threshold == 55


def test_save_chunk_writes_wav_file(tmp_path):
    vm = VoiceMonitor(chunk_dir=str(tmp_path / "chunks_test3"))
    audio = np.zeros((Config.SAMPLE_RATE,), dtype="float32")
    path = vm._save_chunk(audio, "20260101_000000")
    assert os.path.exists(path)
    assert path.endswith(".wav")


@patch("voiceMonitor.audio_stream.extract_acoustic_features")
@patch("voiceMonitor.audio_stream.score_audio")
@patch("voiceMonitor.audio_stream.preprocess_audio")
def test_process_chunk_calls_scoring_and_records_result(
    mock_preprocess, mock_score, mock_features, tmp_path
):
    mock_preprocess.return_value = ["processed_chunk.wav"]
    mock_score.return_value = 66.6
    mock_features.return_value = {"jitter_local": 0.01}

    vm = VoiceMonitor(chunk_dir=str(tmp_path / "chunks_test4"))
    audio = np.zeros((Config.SAMPLE_RATE,), dtype="float32")
    raw_file = vm._save_chunk(audio, "20260101_000000")

    score = vm._process_chunk(raw_file, "20260101_000000", elapsed_seconds=0)

    assert score == 66.6
    assert len(vm.session.records) == 1
    assert vm.session.records[0]["score"] == 66.6
    assert vm.session.records[0]["features"] == {"jitter_local": 0.01}


@patch("voiceMonitor.audio_stream.preprocess_audio")
def test_process_chunk_returns_none_when_preprocessing_yields_nothing(
    mock_preprocess, tmp_path
):
    mock_preprocess.return_value = []
    vm = VoiceMonitor(chunk_dir=str(tmp_path / "chunks_test5"))
    audio = np.zeros((Config.SAMPLE_RATE,), dtype="float32")
    raw_file = vm._save_chunk(audio, "20260101_000000")

    result = vm._process_chunk(raw_file, "20260101_000000", elapsed_seconds=0)
    assert result is None
    assert len(vm.session.records) == 0


@patch("voiceMonitor.audio_stream.extract_acoustic_features", return_value={})
@patch("voiceMonitor.audio_stream.score_audio", return_value=30.0)
@patch("voiceMonitor.audio_stream.preprocess_audio", return_value=["processed.wav"])
@patch("voiceMonitor.audio_stream.sd.InputStream")
def test_start_runs_for_fixed_duration_and_returns_session(
    mock_input_stream, mock_preprocess, mock_score, mock_features, tmp_path, monkeypatch
):
    # use small, fast values so the test does not depend on real audio timing
    monkeypatch.setattr(Config, "SAMPLE_RATE", 10)
    monkeypatch.setattr(Config, "WINDOW_SEC", 1)
    monkeypatch.setattr(Config, "STEP_SEC", 1)

    fake_stream = MagicMock()
    fake_stream.read.return_value = (np.zeros((10, 1), dtype="float32"), False)
    mock_input_stream.return_value.__enter__.return_value = fake_stream

    vm = VoiceMonitor(chunk_dir=str(tmp_path / "chunks_test6"))
    session = vm.start(duration_sec=2)

    assert session is vm.session
    # two one-second steps should have produced two processed windows
    assert len(session.records) == 2
    assert mock_score.call_count == 2