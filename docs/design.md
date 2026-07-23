# voiceMonitor Design Document

**Prepared by:** Sarib Azim
**Role:** Core Engineer, Research, Implementation and Evaluation
**Fellowship:** INFERENCE Lab Engineering Fellowship, Cohort 01

This document presents the design for an extension to voiceMonitor's real time vocal fatigue monitoring pipeline. It introduces smoothing and personal baseline calibration to the existing fatigue signal, along with a novel vocal load impulse response model that estimates both accumulated strain and expected recovery time, adapted from the Banister impulse response framework used in sports science. This design document fulfills the Week 1 requirement of the fellowship and precedes any implementation work.

## Table of Contents

1. [Project Summary](#1-project-summary)
2. [Problem Statement](#2-problem-statement)
3. [Technical Approach](#3-technical-approach)
   - [3.1 Smoothing the Fatigue Signal](#31-smoothing-the-fatigue-signal)
   - [3.2 Additional Acoustic Features](#32-additional-acoustic-features)
   - [3.3 Personal Baseline Calibration](#33-personal-baseline-calibration)
   - [3.4 Vocal Load Impulse Response Model (Novel Module)](#34-vocal-load-impulse-response-model-novel-module)
   - [3.5 Inputs, Outputs, and Scope](#35-inputs-outputs-and-scope)
4. [Evaluation Plan](#4-evaluation-plan)
5. [Module Ownership Table](#5-module-ownership-table)
6. [Known Risks](#6-known-risks)
7. [Definition of Done](#7-definition-of-done)

## 1. Project Summary

voiceMonitor is a real time vocal fatigue monitoring library that listens to a person's voice while they speak, and estimates how strained or tired their voice is becoming over the course of a session. It works by breaking incoming microphone audio into short five second windows, running each window through the auralis_vfs scoring framework built on the ECAPA-TDNN-VHE vocal fatigue estimation model, and producing a fatigue score for that moment. This document proposes an extension to the existing pipeline that makes the fatigue signal smoother, more personalized, and predictive rather than purely reactive, so the tool can tell a user not just that their voice is under strain right now, but how much strain has actually accumulated and how long they need to recover.

## 2. Problem Statement

The current voiceMonitor pipeline computes an independent fatigue score for every five second window and compares it against a single fixed threshold. This has three practical limitations that this project addresses.

First, a single window score reacts to short lived events, such as a cough, a loud word, or a brief pause, causing the reported fatigue level to jump around in ways that do not reflect real vocal condition. Second, a fixed threshold does not account for the fact that different speakers have different natural vocal characteristics, so a threshold that is meaningful for one voice may be too sensitive or not sensitive enough for another. Third, and most importantly, the current design only reports fatigue as it exists right now. It cannot tell a user how much of that fatigue is a passing spike versus a genuine accumulating strain, and it cannot estimate how long a person needs to rest before it is safe to continue speaking heavily.

Solving this matters both for the lab, since it turns voiceMonitor from a simple monitoring script into a tool with genuine predictive value worth publishing on, and for the fellow completing this work, since it produces a concrete, demonstrable piece of applied signal processing research suitable for a portfolio and a lab note.

## 3. Technical Approach

### 3.1 Smoothing the Fatigue Signal

Rather than reporting each five second window's raw score independently, the pipeline will maintain an exponential moving average of the fatigue score, updated after each window. This requires carrying forward only a single number between windows, so the pipeline remains lightweight and does not need to store or reprocess the full session history to produce a stable trend.

### 3.2 Additional Acoustic Features

Alongside the existing auralis_vfs embedding score, the pipeline will extract a small set of acoustic features that are established in speech pathology research as markers of vocal fatigue: jitter and shimmer, which measure cycle to cycle instability in pitch and amplitude, harmonics to noise ratio, which measures breathiness and roughness in the voice, and smoothed cepstral peak prominence, which is a robust general purpose marker of vocal effort. These features will be logged alongside the primary fatigue score to support both better alerting and future model improvement work.

### 3.3 Personal Baseline Calibration

During the first thirty to sixty seconds of a session, the system will establish a personal baseline for the speaker rather than comparing everyone against one fixed population level. Fatigue will then be reported as a deviation from that speaker's own baseline. This avoids false alerts for speakers whose natural voice already carries characteristics, such as breathiness, that could otherwise be mistaken for fatigue.

### 3.4 Vocal Load Impulse Response Model (Novel Module)

The central new contribution of this project is an impulse response model of vocal fatigue, adapted from the Banister impulse response framework used in sports science to model athletic training load and recovery. Each fatigue reading produced by auralis_vfs is treated as an impulse of vocal load, which is passed through two parallel leaky integrators with different decay time constants: a fast component that decays over roughly ninety seconds, representing acute short term strain, and a slow component that decays over roughly twenty to thirty minutes, representing chronic strain that builds across the session.

The difference between the chronic and acute components produces a vocal readiness signal, and because both decay constants are known, the system can directly solve for how many seconds or minutes remain until the acute component decays back under a safe level. This allows voiceMonitor to report an estimated recovery time rather than only a binary alert, and to distinguish a person who spoke intensely for a short burst from a person whose strain is genuinely accumulating across the whole session even through short pauses.

This module directly extends an item already listed under Future Development in the project's own documentation, fatigue trend prediction, and to the best of available research knowledge has not previously been applied to vocal fatigue monitoring, making it a genuinely novel and potentially publishable contribution rather than only an engineering improvement.

It is worth noting explicitly that this adapts rather than directly copies the original Banister framework. In the source model, the slow decaying component represents accumulated fitness, a positive adaptation, while the fast component represents fatigue. Since voice has no direct positive equivalent to athletic fitness, both components here are reinterpreted as strain at different timescales, acute and chronic, with readiness computed the same way the athletic model computes freshness, as the slow component minus the fast component.

Implementation sits as a new stage in the existing pipeline, placed immediately after Vocal Fatigue Scoring and before the Session Analytics Engine, so it extends the current architecture rather than replacing it.

Reference sketch for the core update logic:

```python
class ImpulseResponseFatigue:
    def __init__(self, tau_fast=90, tau_slow=1500):
        self.tau_fast = tau_fast
        self.tau_slow = tau_slow
        self.acute = 0.0
        self.chronic = 0.0
        self.last_t = None

    def update(self, score, timestamp):
        if self.last_t is not None:
            dt = timestamp - self.last_t
            self.acute *= math.exp(-dt / self.tau_fast)
            self.chronic *= math.exp(-dt / self.tau_slow)
        self.acute += score
        self.chronic += score
        self.last_t = timestamp
        return self.acute, self.chronic, self.chronic - self.acute

    def recovery_eta(self, safe_level):
        if self.acute <= safe_level:
            return 0
        return self.tau_fast * math.log(self.acute / safe_level)
```

### 3.5 Inputs, Outputs, and Scope

Input to this module is the existing per window fatigue score and its timestamp, already produced by auralis_vfs. Output is three values per window: the acute component, the chronic component, and an estimated recovery time in seconds. In scope for this phase is single speaker, single session monitoring. Out of scope for this phase is multi speaker diarization and cross session historical trend modeling, both of which are listed as candidates for future work beyond this six week engagement.

## 4. Evaluation Plan

Done, for this project, means the following criteria are all met. The exponential moving average and impulse response outputs are validated against manually reviewed test sessions, where a reviewer, using their own judgment, agrees that reported recovery time estimates behave sensibly, decreasing during pauses and increasing during sustained heavy speech. Acoustic feature extraction (jitter, shimmer, harmonics to noise ratio, cepstral peak prominence) is unit tested against known synthetic audio samples with expected value ranges. The baseline calibration module is tested against at least three different speakers to confirm it produces different, speaker appropriate baselines rather than a single fixed value. All new modules meet the fellowship wide requirement of ninety percent or higher test coverage. The updated package continues to install cleanly via pip install in a clean Python 3.10 environment, preserving full backward compatibility with the existing command line interface and Python API.

The test dataset will consist of short recorded sessions gathered during development, covering calm speech, sustained loud speech, and speech with natural pauses, since no public benchmark dataset for vocal fatigue currently exists.

## 5. Module Ownership Table

Since this engagement covers a single fellow filling the Research, Implementation, and Evaluation roles together rather than a three person group, all modules below are owned by the same person, with target completion weeks spread across the six week fellowship.

| File | Owner | Depends On | Target Week |
|---|---|---|---|
| voicemonitor/analytics.py (impulse response module) | Sarib Azim | auralis_vfs, session.py | Week 2 |
| voicemonitor/audio_stream.py (feature extraction extension) | Sarib Azim | auralis_vfs, numpy | Week 2 |
| voicemonitor/baseline.py (new file, calibration) | Sarib Azim | audio_stream.py | Week 3 |
| voicemonitor/session.py (recovery ETA integration) | Sarib Azim | analytics.py | Week 3 |
| voicemonitor/config.py (new tunables) | Sarib Azim | none | Week 2 |
| tests/test_analytics_impulse.py | Sarib Azim | analytics.py | Week 4 |
| tests/test_baseline.py | Sarib Azim | baseline.py | Week 4 |
| docs/design.md (this document) | Sarib Azim | none | Week 1 |
| README.md (usage section update) | Sarib Azim | all above | Week 5 |

## 6. Known Risks

| Risk | Why It Could Happen | Mitigation |
|---|---|---|
| Personal baseline calibration is inaccurate for short sessions | If a user speaks for less than 30 to 60 seconds before scoring starts, the baseline window has too little data to represent their natural voice. | Fall back to a conservative population default baseline until the calibration window is complete, and flag readings taken during calibration as provisional in the session report. |
| Fast and slow decay constants do not generalize across speakers | Vocal fatigue physiology varies by age, vocal training, and prior vocal load, so a single tau_fast and tau_slow pair may not fit everyone equally well. | Ship reasonable initial defaults, based loosely on analogous physiological recovery timescales, pending empirical calibration, expose both constants as configurable parameters in config.py, and log enough session data to allow future per speaker fitting rather than blocking the initial release on it. |
| Real time performance degrades on lower end hardware | Adding acoustic feature extraction (jitter, shimmer, HNR, CPPS) alongside the existing auralis_vfs scoring increases per window compute cost, which could cause the 5 second sliding window to fall behind real time on slower machines. Additionally, handcrafted feature libraries can carry dependency and version mismatch issues across environments. | Profile the added feature extraction cost early in Week 2, and if needed, compute the additional acoustic features on every second or third window rather than every window, since fatigue trends change slowly enough that this does not meaningfully harm accuracy. All new dependencies will be tested inside an isolated virtual environment before integration to catch version conflicts early. |

## 7. Definition of Done

- All planned modules listed in the Module Ownership Table are implemented and merged to main through the standard PR review process.
- Ninety percent or higher automated test coverage is achieved across all new and modified modules.
- The package installs cleanly via pip install in a clean Python 3.10 or newer environment on a machine other than the one used for development.
- All new public functions have complete docstrings.
- Recovery time estimation has been manually validated against at least five recorded test sessions with sensible, reviewer confirmed behavior.
- The README is updated to document the new configuration options, the impulse response model, and the updated session report format.
- A five hundred word lab note describing the impulse response module, the technical decisions behind it, and what was learned, is drafted and submitted for review.