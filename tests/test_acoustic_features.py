import logging

from voiceMonitor.audio_stream import extract_acoustic_features


def test_extraction_returns_empty_dict_on_missing_file(caplog):
    """
    A nonexistent/invalid wav path should trigger the failure path and
    return an empty dict rather than raising, and the failure should be
    logged as a warning rather than silently swallowed.
    """
    with caplog.at_level(logging.WARNING):
        result = extract_acoustic_features("/tmp/this_file_does_not_exist.wav")

    assert result == {}
    assert any("Acoustic feature extraction failed" in message for message in caplog.messages)


def test_extraction_returns_dict_type_even_on_failure():
    result = extract_acoustic_features("/tmp/another_missing_file.wav")
    assert isinstance(result, dict)