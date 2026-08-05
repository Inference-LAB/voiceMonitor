# Changelog

## [1.1.0]

### Added
- Personal baseline calibration during the first portion of a session (baseline.py)
- Vocal load impulse response model with acute and chronic load components and recovery time estimation (analytics.py), adapted from the Banister impulse response framework used in sports science
- Exponential moving average smoothing of the raw fatigue score
- Auxiliary acoustic feature extraction (jitter, shimmer, harmonics to noise ratio, CPPS) via Praat/parselmouth
- Automated test suite covering EMA smoothing, impulse response calculations, baseline calibration, acoustic feature extraction, session reporting, CLI, and utility functions
- Continuous integration workflow running the test suite with coverage on every push and pull request to main

### Changed
- Elapsed time for decay calculations is now derived from actual audio samples processed rather than a wall clock, keeping temporal load calculations consistent with session timestamps
- Session records now include per window smoothed score, acute load, chronic load, an experimental readiness metric, recovery ETA, and baseline calibration state, in addition to the raw score
- praat-parselmouth added as a formal project dependency in pyproject.toml, rather than only appearing in requirements.txt

### Fixed
- Backward compatibility maintained for existing callers of SessionAnalytics.add and SessionReport.add_record that do not supply elapsed_seconds
- Acoustic feature extraction failures and a missing parselmouth installation now log a warning instead of failing silently

### Documentation
- README updated to document all additions above, including a corrected architecture diagram, configuration table, and sample session report
- Added CONTRIBUTORS.md and this CHANGELOG.md