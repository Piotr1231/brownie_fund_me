# Proof of Antiquity in one offline experiment: why “consistent with drift” matters

RustChain’s Proof-of-Antiquity idea starts from a different premise than conventional proof-of-work: **one physical CPU is one vote, then that vote can be weighted by verified hardware antiquity**. The network therefore needs more than a self-reported CPU model. A miner has to provide evidence that its claimed machine behaves like real hardware rather than a cheap virtual machine, emulator, or fabricated software profile.

The RustChain project describes a six-check fingerprinting approach covering **clock drift, cache timing, SIMD identity, thermal drift, instruction jitter, and anti-emulation signals**. See the upstream project here: <https://github.com/Scottcjn/Rustchain>. The point is not that any single timing number uniquely identifies a computer. The useful signal comes from several independent measurements and from how those measurements behave over time.

This tutorial builds a tiny offline experiment that demonstrates one part of that intuition: **temporal stability**. It does not copy RustChain’s production scoring logic and it must not be used as a security validator. Instead, it gives you a reproducible model for understanding why a physical machine can look different from two simplistic spoofing strategies.

## Three fingerprints to compare

Imagine that a hardware check produces a timing-derived value around `100` units. We collect ten readings from three hypothetical sources:

1. **Real-like physical hardware.** Measurements are close to one another but not identical. Temperature, scheduler noise, clock behavior, cache state, and other physical effects introduce small variation.
2. **Frozen emulator.** A naive emulator returns exactly the same synthetic value every time. That looks “too perfect.”
3. **Naive randomizer.** A spoofing script knows identical readings are suspicious, so it injects large random variation. That creates the opposite problem: the profile moves far more than a stable physical system normally would.

A convenient summary statistic is the **coefficient of variation (CV)**:

```text
CV = population standard deviation / absolute mean
```

CV is useful here because it expresses variability relative to the scale of the measurement. In the demo, an exactly frozen series gets `CV = 0`, a tightly drifting series gets a small positive CV, and a deliberately noisy sequence gets a much larger value.

## Runnable code

The complete runnable file is in [`examples/proof_of_antiquity_demo.py`](../examples/proof_of_antiquity_demo.py). It uses only Python’s standard library, so there are no packages to install.

Run it with:

```bash
python examples/proof_of_antiquity_demo.py
```

The core classifier is intentionally small:

```python
def classify(name: str, samples: list[float]) -> ProfileResult:
    mean = fmean(samples)
    cv = coefficient_of_variation(samples)
    if cv == 0:
        verdict = "frozen: suspiciously identical readings"
    elif cv > 0.08:
        verdict = "noisy: unusually variable readings"
    else:
        verdict = "drifting: plausible physical-style variation"
    return ProfileResult(name, mean, cv, verdict)
```

The `0.08` threshold is **an educational choice for this toy dataset**, not a RustChain consensus constant. A production verifier would need calibration from real machines, architecture-aware distributions, tolerance for environmental changes, multiple independent channels, and careful false-positive analysis.

## What I actually ran

I executed the script with Python and also compiled it with `python -m py_compile` to verify that the checked-in example parses correctly. The captured output is stored in [`evidence/proof_of_antiquity_demo_output.txt`](../evidence/proof_of_antiquity_demo_output.txt):

```text
Proof-of-Antiquity temporal-stability demo
NOTE: educational model, not RustChain production scoring.

real_like        mean= 100.36 cv=0.0038 -> drifting: plausible physical-style variation
frozen_emulator  mean= 100.00 cv=0.0000 -> frozen: suspiciously identical readings
naive_randomizer mean= 104.10 cv=0.2192 -> noisy: unusually variable readings
```

This result illustrates the central pattern: **realistic measurements can be stable without being perfectly constant**. The frozen profile has no variance at all. The randomizer has dramatically more variance than the real-like sequence. A verifier can use this kind of temporal information as one signal among many rather than trusting one measurement or one claimed CPU string.

## How this connects to RustChain’s six checks

Temporal analysis becomes more useful when combined with heterogeneous signals. Clock drift and instruction jitter are naturally timing-oriented. Cache timing can reveal architecture- and hierarchy-dependent behavior. SIMD identity provides a more categorical check because different architectures expose different instruction families. Thermal drift adds a physical response that software must imitate consistently. Anti-emulation checks then look for evidence that the environment itself is virtualized.

The important design principle is **cross-checking**. A sophisticated attacker might fake one value, but maintaining a coherent story across timing, cache behavior, instruction support, thermal response, repeated observations, and system-level anti-emulation signals is harder.

That does not make fingerprinting magically unforgeable. Software-only attestation has real limitations, and RustChain’s own repository contains ongoing security discussions about replay resistance, binding, fingerprint quality, and architecture validation. The responsible way to explain Proof of Antiquity is therefore not “old CPUs cannot be spoofed.” It is: **the protocol tries to make cheap mass emulation less attractive by requiring multiple mutually consistent signs of real physical hardware**.

## Trying the real project

If you want to move from this offline mental model to RustChain itself, start with the upstream repository and its current documentation: <https://github.com/Scottcjn/Rustchain>. The ecosystem also exposes the `clawrtc` package, whose documented quick-start command is:

```bash
pip install clawrtc
```

Read the current repository instructions before running a miner, because network endpoints and command-line options can change. The offline example in this article is deliberately safe: it makes no network calls, does not mine, and does not create a wallet.

## AI assistance disclosure

This tutorial and the accompanying example were developed with substantial assistance from OpenAI GPT-5.6 Sol. The example was executed locally, its output was captured, and the claims above distinguish the educational model from RustChain’s production implementation.
