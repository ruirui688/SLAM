# P228 Paper Story and Result Table

**Status:** paper-facing result snapshot
**Date:** 2026-05-13
**Scope:** P225-P228 learned dynamic-mask frontend, DROID baseline reproduction,
and confidence/coverage-gated mask module. This is bounded smoke evidence, not
a full dynamic-SLAM benchmark claim.

## Story

The paper story is now fixed as a baseline-to-module progression:

1. P218 establishes a compact dataset-mask-supervised dynamic/non-static mask
   network on TorWIC semantic masks.
2. P225 turns that network route into a 60-frame timestamped raw-vs-masked
   TorWIC sequence package with calibration and aligned ground truth.
3. P227 reproduces the raw-vs-learned-mask DROID baseline on that exact
   sequence.
4. P228 adds a small confidence/coverage-gated post-network mask module and
   evaluates it with the same DROID/evo and ORB proxy path.

The claim is deliberately narrow: P228 keeps the trajectory smoke effectively
neutral relative to P227 while concentrating ORB feature suppression in the
predicted gated regions. It is a viable frontend filtering module seed, not a
navigation-gain claim.

## Result Table

| Variant | Frames | APE RMSE Raw -> Masked (m) | RPE RMSE Raw -> Masked (m) | ORB Region Keypoints Raw -> Masked | Interpretation |
|---|---:|---:|---:|---:|---|
| P227 learned-mask baseline | 60 | 0.088504 -> 0.084529 | 0.076145 -> 0.076226 | 21030 -> 18617 | Baseline reproduction passed/neutral |
| P228 confidence/coverage-gated module | 60 | 0.088496 -> 0.084705 | 0.076145 -> 0.076224 | 8969 -> 5073 | Viable story seed; stronger gated-region suppression |

## P228 Module Parameters

- Probability threshold: `0.50`
- Dilation: `1 px`
- Minimum connected-component area: `128 px`
- Max coverage / target coverage: `0.22 / 0.18`
- Mean gated mask coverage: `14.127053%`
- Coverage-capped frames: `53-59`

## Careful Wording

Allowed:

- "P227 reproduces a bounded raw-vs-learned-mask DROID-SLAM baseline."
- "P228 is trajectory-neutral relative to P227 in the 60-frame smoke."
- "P228 improves the ORB predicted-region feature suppression proxy."
- "The module is a controlled frontend filtering story seed."

Not allowed:

- "P228 proves trajectory improvement."
- "P228 is a full dynamic-SLAM benchmark result."
- "P228 provides independent dynamic segmentation ground truth."
- "P228 solves learned persistent-map admission."

## Evidence Anchors

- P225 package: `paper/export/temporal_masked_sequence_p225.md`
- P226 baseline plan: `paper/export/baseline_reproduction_plan_p226.md`
- P227 baseline reproduction: `paper/export/p225_baseline_reproduction_p227.md`
- P228 module: `paper/export/confidence_gated_mask_module_p228.md`
- P228 JSON evidence: `paper/evidence/confidence_gated_mask_module_p228.json`
