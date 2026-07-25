from unittest.mock import MagicMock, patch

from voiceMonitor import cli


@patch("voiceMonitor.cli.VoiceMonitor")
def test_main_parses_args_and_runs_session(mock_voice_monitor_cls, monkeypatch):
    mock_instance = MagicMock()
    mock_report = MagicMock()
    mock_instance.start.return_value = mock_report
    mock_voice_monitor_cls.return_value = mock_instance

    monkeypatch.setattr(
        "sys.argv", ["voicemonitor", "--duration", "30", "--threshold", "65"]
    )

    cli.main()

    mock_voice_monitor_cls.assert_called_once_with(threshold=65.0)
    mock_instance.start.assert_called_once_with(duration_sec=30)
    mock_report.export_json.assert_called_once_with("session_report.json")


@patch("voiceMonitor.cli.VoiceMonitor")
def test_main_uses_defaults_when_no_args_given(mock_voice_monitor_cls, monkeypatch):
    mock_instance = MagicMock()
    mock_instance.start.return_value = MagicMock()
    mock_voice_monitor_cls.return_value = mock_instance

    monkeypatch.setattr("sys.argv", ["voicemonitor"])

    cli.main()

    mock_voice_monitor_cls.assert_called_once_with(threshold=None)
    mock_instance.start.assert_called_once_with(duration_sec=None)