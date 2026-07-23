import sounddevice as sd
import numpy as np
import os
from tqdm import tqdm
from auralis.processing import preprocess_audio
from auralis.scorer import score_audio

from .config import Config
from .utils import timestamp, ensure_dir
from .session import SessionReport

try:
    import parselmouth
    from parselmouth.praat import call
    _PARSELMOUTH_AVAILABLE = True
except ImportError:
    _PARSELMOUTH_AVAILABLE = False


def extract_acoustic_features(wav_path):
    """
    Extracts jitter, shimmer, harmonics to noise ratio, and smoothed
    cepstral peak prominence from a short audio segment using Praat, via
    parselmouth. These are established speech pathology markers of vocal
    fatigue, used alongside the primary auralis_vfs score rather than in
    place of it. Returns an empty dict if parselmouth is unavailable or if
    extraction fails on a short or silent window, so a single bad window
    does not interrupt the monitoring session.
    """
    if not _PARSELMOUTH_AVAILABLE:
        return {}

    try:
        sound = parselmouth.Sound(wav_path)
        point_process = call(sound, "To PointProcess (periodic, cc)", 75, 500)

        jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer = call(
            [sound, point_process],
            "Get shimmer (local)",
            0, 0, 0.0001, 0.02, 1.3, 1.6,
        )

        harmonicity = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        hnr = call(harmonicity, "Get mean", 0, 0)

        cepstrogram = call(sound, "To PowerCepstrogram", 60, 0.002, 5000, 50)
        cpps = call(
            cepstrogram, "Get CPPS", True, 0.02, 0.0005, 60, 330,
            0.05, "Parabolic", 0.001, 0, "Straight", "Robust",
        )

        return {
            "jitter_local": jitter,
            "shimmer_local": shimmer,
            "hnr": hnr,
            "cpps": cpps,
        }
    except Exception:
        return {}


class VoiceMonitor:

    def __init__(self, threshold=None, chunk_dir=None):
        self.threshold = threshold or Config.DEFAULT_THRESHOLD
        self.chunk_dir = chunk_dir or f"{Config.CHUNK_DIR}_{timestamp()}"
        ensure_dir(self.chunk_dir)
        self.session = SessionReport()

    def _save_chunk(self, audio_arr: np.ndarray, ts: str):
        """Write raw audio to temporary wav"""
        fname = f"{self.chunk_dir}/{ts}.wav"
        import soundfile as sf
        sf.write(fname, audio_arr, Config.SAMPLE_RATE)
        return fname

    def _process_chunk(self, wav_path: str, ts: str):
        # run auralis preprocessing (standardize)
        out_files = preprocess_audio(wav_path, self.chunk_dir)
        if not out_files:
            return None
        processed = out_files[-1]
        score = score_audio(processed)

        features = {}
        if Config.EXTRACT_ACOUSTIC_FEATURES:
            features = extract_acoustic_features(processed)

        self.session.add_record(ts, processed, score, features=features)
        return score

    def start(self, duration_sec=None):
        """Start real-time monitoring"""
        # compute sample count for window/step
        win_samples = Config.SAMPLE_RATE * Config.WINDOW_SEC
        step_samples = Config.SAMPLE_RATE * Config.STEP_SEC

        # grab raw audio buffer
        buffer = np.zeros((0,), dtype="float32")

        # backfill for live view
        remaining = duration_sec or float("inf")
        print("Start Speaking...")
        with sd.InputStream(channels=1, samplerate=Config.SAMPLE_RATE) as stream:
            while remaining > 0:
                block, _ = stream.read(step_samples)
                buffer = np.concatenate([buffer, block.flatten()])

                if len(buffer) >= win_samples:
                    ts = timestamp()
                    # write raw to wav
                    raw_file = self._save_chunk(buffer[:win_samples], ts)
                    score = self._process_chunk(raw_file, ts)

                    # slide buffer
                    buffer = buffer[int(step_samples):]

                    # warnings & prints
                    print(f"[{ts}] Score: {score:.2f}")
                    if score >= self.threshold:
                        print("⚠ fatigue threshold crossed")

                    remaining -= Config.STEP_SEC

        print("Session ended.")
        return self.session