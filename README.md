# VoiceMonitor

Real Time Vocal Fatigue Monitoring for Continuous Speech Analytics

VoiceMonitor is a Python library for real time vocal fatigue monitoring built on top of the auralis_vfs vocal fatigue scoring framework. It enables continuous microphone monitoring, fatigue scoring using sliding audio windows, personal baseline calibration, a vocal load impulse response model for recovery time estimation, and session level analytics for voice health monitoring.

The system is designed for researchers, speech engineers, and voice professionals who require automated analysis of vocal strain during prolonged speech activity.

## Overview

Prolonged speaking can lead to vocal fatigue, a condition characterized by strain, reduced vocal efficiency, and potential long term damage to vocal health.

VoiceMonitor provides a real time monitoring pipeline that:

- captures microphone audio streams
- processes sliding audio windows
- computes vocal fatigue scores using the ECAPA-TDNN-VHE model via auralis_vfs
- smooths the fatigue signal with an exponential moving average
- models accumulating vocal load with a two component impulse response model, estimating a recovery time
- calibrates a personal baseline for the current speaker
- extracts auxiliary acoustic features (jitter, shimmer, harmonics to noise ratio, CPPS)
- generates session analytics, per window records, and warnings

## Key Features

- Real time microphone audio monitoring
- Continuous vocal fatigue scoring
- Sliding window fatigue analysis
- Exponential moving average smoothing of the raw fatigue signal
- Vocal load impulse response model with acute and chronic load components and recovery time estimation
- Personal baseline calibration during the first portion of a session
- Auxiliary acoustic feature extraction (jitter, shimmer, HNR, CPPS)
- Fatigue threshold warnings
- Session level analytics and reports, including per window detail
- Chunk based audio processing pipeline
- JSON session export for downstream analysis
- Lightweight CLI interface for quick experiments

## Architecture

VoiceMonitor uses a sliding window inference pipeline for continuous analysis.

```
Microphone Input
        |
        v
Audio Stream Buffer
        |
        v
Sliding Window Segmentation (5s)
        |
        v
auralis_vfs Preprocessing
        |
        v
Vocal Fatigue Scoring (ECAPA-TDNN-VHE)
        |
        v
Acoustic Feature Extraction (auxiliary)
        |
        v
Personal Baseline Calibration
        |
        v
EMA Smoothing + Impulse Response Model (acute/chronic load, recovery ETA)
        |
        v
Session Analytics Engine
        |
        v
Fatigue Alerts + Reports
```

Each processed window produces a raw fatigue score, a smoothed score, acute and chronic load values, an estimated recovery time, baseline calibration state, and auxiliary acoustic features, all recorded per window and summarized at the session level.

## Installation

### Requirements

- Python 3.10 or newer
- FFmpeg installed on system
- Microphone access

### Install from PyPI

```
pip install voicemonitor
```

### Install from source

```
git clone https://github.com/Inference-LAB/voiceMonitor.git
cd voiceMonitor
pip install -e .
```

### Dependencies

VoiceMonitor relies on the following core libraries:

- auralis_vfs
- numpy
- sounddevice
- soundfile
- pydub
- tqdm
- praat-parselmouth (for acoustic feature extraction)

FFmpeg must be installed for audio processing.

## Quick Start

### CLI Usage

Start real time vocal fatigue monitoring:

```
voicemonitor
```

Monitor for a fixed duration:

```
voicemonitor --duration 120
```

Set a custom fatigue warning threshold:

```
voicemonitor --threshold 65
```

Example output:

```
[20260312_182001] Score: 22.51
[20260312_182006] Score: 31.02
[20260312_182011] Score: 45.44
[20260312_182016] Score: 72.90

⚠ fatigue threshold crossed
```

After the session completes, a report is generated:

```
session_report.json
```

### Python API

```python
from voiceMonitor import VoiceMonitor

monitor = VoiceMonitor(threshold=70)

session = monitor.start(duration_sec=120)

session.export_json("session_report.json")
```

## Session Analytics

Each monitoring session records, per window:

- raw fatigue score
- exponentially smoothed fatigue score
- acute load (short term strain, fast decay)
- chronic load (strain accumulating across the session, slow decay)
- readiness_experimental, an unvalidated exploratory metric (chronic minus acute)
- recovery_eta_sec, estimated seconds until acute load returns to a safe level
- baseline, the speaker's calibrated fatigue baseline
- baseline_adjusted_score, the raw score minus the calibrated baseline
- baseline_is_provisional, true while the baseline is still being calibrated
- auxiliary acoustic features (jitter, shimmer, HNR, CPPS), where available
- timestamp and chunk file path

At the session level, the summary includes:

- average and maximum raw fatigue score
- number of readings
- most recent smoothed fatigue score
- most recent acute load, chronic load, and readiness_experimental
- most recent recovery_eta_sec

Example report:

```json
{
  "summary": {
    "average_fatigue": 38.2,
    "max_fatigue": 74.1,
    "readings": 25,
    "smoothed_fatigue": 41.7,
    "acute_load": 58.3,
    "chronic_load": 44.1,
    "readiness_experimental": -14.2,
    "recovery_eta_sec": 33.9
  },
  "records": [
    {
      "timestamp": "20260312_182001",
      "chunk": "chunks/20260312_182001.wav",
      "score": 22.51,
      "features": {
        "jitter_local": 0.012,
        "shimmer_local": 0.041,
        "hnr": 14.2,
        "cpps": 7.8
      },
      "smoothed_score": 22.51,
      "acute_load": 22.51,
      "chronic_load": 22.51,
      "readiness_experimental": 0.0,
      "recovery_eta_sec": 0.0,
      "baseline": 30,
      "baseline_adjusted_score": 0,
      "baseline_is_provisional": true
    }
  ]
}
```

Note that auxiliary acoustic features and baseline adjusted scores are collected for inspection and future analysis. They do not currently influence the raw fatigue score or the warning threshold logic.

## Configuration

`voicemonitor/config.py` exposes the following tunable values:

| Setting | Default | Description |
|---|---|---|
| SAMPLE_RATE | 16000 | Audio capture sample rate |
| WINDOW_SEC | 5 | Sliding window size in seconds |
| STEP_SEC | 4 | Step size between windows in seconds |
| DEFAULT_THRESHOLD | 70 | Default fatigue warning threshold (0 to 100 scale) |
| SAVE_CHUNKS | True | Whether to persist raw audio chunks to disk |
| CHUNK_DIR | "chunks" | Directory for saved audio chunks |
| EMA_ALPHA | 0.3 | Smoothing weight given to the newest window (0 to 1) |
| TAU_FAST | 90 | Acute component decay constant, in seconds |
| TAU_SLOW | 1500 | Chronic component decay constant, in seconds (25 minutes) |
| SAFE_RECOVERY_LEVEL | 40 | Acute load level considered recovered |
| EXTRACT_ACOUSTIC_FEATURES | True | Whether to extract auxiliary acoustic features per window |
| BASELINE_CALIBRATION_SEC | 45 | Length of the personal baseline calibration window, in seconds |
| DEFAULT_POPULATION_BASELINE | 30 | Fallback baseline used before calibration completes |

## Vocal Load Impulse Response Model

Vocal load is modeled using two parallel leaky integrators, adapted from the Banister impulse response framework used in sports science to model athletic training load and recovery. Each fatigue score is treated as an impulse applied to a fast decaying acute component and a slow decaying chronic component. Readiness (chronic minus acute) mirrors how the athletic model computes freshness as fitness minus fatigue, though this reinterpretation is exploratory and has not yet been empirically validated for vocal fatigue, hence the `readiness_experimental` field name. Acute and chronic load are exposed separately so they can be used independently of the readiness metric.

Because voice has no direct positive equivalent to athletic fitness, both components here represent strain at different timescales rather than fitness and fatigue. Elapsed time for decay is derived from actual audio samples processed, not a wall clock, so it stays consistent with the session's own timestamps regardless of processing latency between windows.

## Personal Baseline Calibration

During the first `BASELINE_CALIBRATION_SEC` seconds of a session, a personal fatigue baseline is estimated from the scores seen so far, with readings flagged as provisional. After the calibration window closes, the baseline locks and stays fixed for the rest of the session. If too little data is available, a conservative population default is used instead. The baseline adjusted score is stored per window but does not currently drive the fatigue warning threshold.

## Research Background

VoiceMonitor is built upon the auralis_vfs vocal fatigue scoring framework, which was developed as part of research on automated vocal fatigue detection. The underlying fatigue estimation model is the ECAPA-TDNN-VHE architecture.

Research paper:

Modeling Vocal Fatigue as Embedding-Space Deviation Using Contrastively Trained ECAPA-TDNNs

Model repository:

huggingface.co/Khubaib01/ECAPA-TDNN-VHE

## Applications

VoiceMonitor can be used in a variety of speech intensive environments:

- speech research
- voice health monitoring
- call center voice analytics
- teacher vocal load monitoring
- podcast and streaming voice tracking
- speech therapy experiments
- human computer interaction studies

## Project Structure

```
voiceMonitor/
├── voiceMonitor/
│   ├── audio_stream.py
│   ├── analytics.py
│   ├── baseline.py
│   ├── session.py
│   ├── utils.py
│   ├── config.py
│   └── cli.py
│
├── examples/
│   └── live.py
│
├── tests/
│   ├── test_analytics_impulse.py
│   ├── test_acoustic_features.py
│   ├── test_audio_stream.py
│   ├── test_baseline.py
│   ├── test_cli.py
│   ├── test_session.py
│   ├── test_session_report.py
│   └── test_utils.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── LICENSE
├── setup.cfg
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Future Development

Planned enhancements include:

- integrating baseline adjusted scores and acoustic features into the fatigue score and warning logic, once validated
- empirical validation of the readiness metric before promoting it out of experimental status
- real time visualization dashboard
- web API for remote monitoring
- desktop GUI interface
- voice activity detection integration
- speaker aware monitoring for multi speaker sessions

## Citation

If you use VoiceMonitor in research, please cite the underlying work:

Ahmad, M. K. (2026). Modeling Vocal Fatigue as Embedding-Space Deviation Using Contrastively Trained ECAPA-TDNNs. Zenodo. https://doi.org/10.5281/zenodo.18366305

## License

This project is released under the MIT License.

## Author

Muhammad Khubaib Ahmad
AI / ML Engineer, Speech Intelligence and Audio AI Systems

## Contributors

Sarib Azim, Core Engineer (Research, Implementation and Evaluation), INFERENCE Lab Engineering Fellowship Cohort 01