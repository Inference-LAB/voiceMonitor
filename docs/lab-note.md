# Building a Vocal Load Impulse Response Model for voiceMonitor

voiceMonitor's pipeline originally reported vocal fatigue as a single, independent score per audio window. This described only the present moment: it could not distinguish a passing spike from accumulating strain, and it offered no way to estimate how long a speaker might need before continuing safely. This project set out to close that gap.

**What changed.** The pipeline moved from independent window level scores to a layered process: exponential smoothing stabilizes the raw signal, an impulse response model converts the smoothed signal into separate acute and chronic strain components, and a signal level recovery estimate is derived from how the acute component decays over time. Personal baseline calibration and auxiliary acoustic feature extraction (jitter, shimmer, harmonics to noise ratio, and CPPS) were added alongside this core pipeline.

**The impulse response model.** To move beyond a single instantaneous score, I adapted a framework from sports science, where athletic training load is modeled using two parallel leaky integrators, a fast decaying acute component and a slow decaying chronic component, whose difference is used to estimate an athlete's readiness to train again. The vocal fatigue adaptation borrows this two timescale structure but is not a direct transfer of the original formulation. Training load research treats the slow component as accumulated fitness, a genuine positive counterpart to fatigue, while voice has no equivalent. Both components here are instead reinterpreted as strain at different timescales, and the resulting output is a model derived, signal level estimate rather than a measurement of physiological recovery. This reinterpretation is experimental, and to my knowledge has not previously been applied to vocal fatigue in this form, though a systematic literature review was outside this project's scope.

**Engineering outcomes.** Automated test coverage grew from a single existing test file to 44 tests across eight files, raising overall coverage from 60 to 93 percent. These tests caught two real defects before review, a backward compatibility break in an existing test and a missing dependency step in continuous integration, both resolved prior to merge. A CI workflow now runs the full suite with coverage reporting on every push and pull request.

**What I learned.** Working through review cycles reinforced concrete engineering habits: keeping decay calculations on the audio stream's own deterministic clock rather than a wall clock that could drift, logging failures instead of swallowing them silently, and shipping small, single purpose pull requests rather than bundling unrelated changes together.

Baseline calibration changed how I approached the underlying problem itself. A fixed threshold treats every voice identically, but a naturally breathy voice and a genuinely strained one can appear identical to a population level model. A calibration window that locks onto a speaker's own baseline, falling back safely when insufficient data is available, was a reminder that a technically correct model can still produce a misleading result if it ignores who it is actually listening to.

Adapting an impulse response framework to a signal it was never designed for, while being explicit about where that adaptation is validated and where it remains experimental, was the central engineering contribution of this work.

Sarib Azim
Core Engineer, Research, Implementation and Evaluation
INFERENCE Lab Engineering Fellowship, Cohort 01