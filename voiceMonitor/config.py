class Config:
    # audio capture
    SAMPLE_RATE = 16000
    WINDOW_SEC = 5
    STEP_SEC = 4

    # fatigue warnings
    DEFAULT_THRESHOLD = 70  # out of 0 to 100 scale

    # session metadata
    SAVE_CHUNKS = True
    CHUNK_DIR = "chunks"

    # signal smoothing (exponential moving average)
    EMA_ALPHA = 0.3  # weight given to the newest window, 0 to 1

    # vocal load impulse response model
    TAU_FAST = 90        # seconds, acute component decay constant
    TAU_SLOW = 1500      # seconds, chronic component decay constant (25 min)
    SAFE_RECOVERY_LEVEL = 40  # acute level considered recovered

    # acoustic feature extraction
    EXTRACT_ACOUSTIC_FEATURES = True