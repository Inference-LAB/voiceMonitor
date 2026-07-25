import os
import re
import shutil
import tempfile

from voiceMonitor.utils import timestamp, ensure_dir


def test_timestamp_format():
    ts = timestamp()
    # expected format: YYYYMMDD_HHMMSS
    assert re.match(r"^\d{8}_\d{6}$", ts)


def test_ensure_dir_creates_missing_directory():
    tmp_root = tempfile.mkdtemp()
    try:
        target = os.path.join(tmp_root, "nested", "chunks")
        assert not os.path.exists(target)
        ensure_dir(target)
        assert os.path.exists(target)
        assert os.path.isdir(target)
    finally:
        shutil.rmtree(tmp_root)


def test_ensure_dir_is_idempotent_on_existing_directory():
    tmp_root = tempfile.mkdtemp()
    try:
        # should not raise when the directory already exists
        ensure_dir(tmp_root)
        ensure_dir(tmp_root)
        assert os.path.exists(tmp_root)
    finally:
        shutil.rmtree(tmp_root)