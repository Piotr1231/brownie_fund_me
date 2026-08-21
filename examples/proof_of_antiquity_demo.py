#!/usr/bin/env python3
"""Educational offline demo of temporal fingerprint stability.

This is NOT RustChain's production scoring code. It illustrates why a physical
CPU can be expected to show small measurement drift, while a frozen emulator or
naive randomizer can look statistically different.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev


@dataclass(frozen=True)
class ProfileResult:
    name: str
    mean: float
    cv: float
    verdict: str


def coefficient_of_variation(samples: list[float]) -> float:
    if not samples:
        raise ValueError("samples must not be empty")
    mean = fmean(samples)
    if mean == 0:
        raise ValueError("sample mean must be non-zero")
    return pstdev(samples) / abs(mean)


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


def main() -> None:
    profiles = {
        "real_like": [100.0, 100.7, 99.8, 100.4, 101.0, 100.2, 99.9, 100.5, 100.8, 100.3],
        "frozen_emulator": [100.0] * 10,
        "naive_randomizer": [81.0, 126.0, 94.0, 117.0, 73.0, 135.0, 88.0, 121.0, 76.0, 130.0],
    }

    print("Proof-of-Antiquity temporal-stability demo")
    print("NOTE: educational model, not RustChain production scoring.\n")
    for name, samples in profiles.items():
        result = classify(name, samples)
        print(f"{result.name:16} mean={result.mean:7.2f} cv={result.cv:0.4f} -> {result.verdict}")


if __name__ == "__main__":
    main()
