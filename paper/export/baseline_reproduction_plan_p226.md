# P226 Baseline Reproduction Plan

**Status:** `P226_BASELINE_REPRODUCTION_SMOKE_COMPLETE`

**Boundary:** this is a baseline-selection and bounded reproduction artifact. It verifies that the local raw-vs-masked backend path runs, but it does not claim a full benchmark improvement or a new network result.

## Baseline Candidates

| Candidate | Local repro | Metrics | Use as main? | Notes |
|---|---:|---|---|---|
| DROID-SLAM raw vs semantic/dynamic masked frontend | yes | APE/RPE RMSE, mean, mask coverage | yes | Best paper-level baseline: same backend/runtime, raw vs masked input is a fair frontend comparison. |
| ORB-SLAM3 raw vs masked cross-check | partial | sparse keyframe APE | secondary | Useful independent check, but sparse tracking and monocular scale ambiguity make it weaker. |
| P218 compact binary dynamic-mask segmentation | yes | dynamic IoU/F1, precision, recall, balanced accuracy | module baseline | Best network baseline for the replacement/addition story. Avoid overwriting fixed P218 evidence paths before variants. |
| P155/P176 admission B0/B1/B2 | yes | admission rate, phantom risk, McNemar | no | Useful context only. B1 differs between `run_baseline_comparison.py` and P176 supplement-derived stats. |

Do not use P193/P195 weak-label admission as the learned baseline: P193 has proxy-leakage risk and P195 remains blocked.

## Reproduced Minimal Baseline

Baseline: DROID-SLAM raw vs masked frontend, 8 frames, `Jun. 23, 2022/Aisle_CW_Run_1`, repository example forklift mask on frame `000002`.

| Metric | Raw | Masked | Delta masked-raw |
|---|---:|---:|---:|
| APE RMSE (m) | 0.001242 | 0.001243 | +0.000001 |
| RPE RMSE (m) | 0.002250 | 0.002255 | +0.000005 |

Mask coverage: `1/8` frames, mean coverage `0.021593%`.

Outputs:

- `outputs/dynamic_slam_backend_input_pack_p226_repro8/`
- `outputs/dynamic_slam_backend_smoke_p226_repro8/p226_repro8_metrics.json`
- `outputs/dynamic_slam_backend_smoke_p226_repro8/p226_repro8_metrics.md`
- `paper/evidence/baseline_reproduction_results_p226.csv`

Interpretation: the baseline is locally reproducible and trajectory-neutral at the expected scale for a sparse example mask. This is the right sanity check before adding learned/temporal mask modules.

## Recommended Main Baseline

Use **DROID-SLAM raw vs masked temporal/dynamic frontend** as the main paper baseline. It has local reproducibility, explicit APE/RPE metrics, and a fair comparison surface: same sequence, frame count, DROID weights, calibration, and runtime, with only frontend masking changed.

Use **P218 compact binary dynamic-mask segmentation** as the network baseline that receives module changes. The story becomes:

1. baseline DROID raw vs dataset/predicted masks is reproducible;
2. compact P218 mask network has measurable segmentation metrics;
3. add a lightweight temporal/boundary/gating module;
4. feed improved masks into the same DROID/ORB evaluation path.

## Module Plan

| Module | Files | Expected proof | Main risk |
|---|---|---|---|
| Confidence-gated mask dilation | `tools/build_dynamic_slam_backend_input_pack.py` | APE/RPE stays within tolerance while dynamic-mask coverage and feature suppression improve | over-dilation removes static texture |
| P218 temporal consistency head | `tools/train_dynamic_mask_p218.py`, P225/P227 sequence tooling | dynamic IoU/F1 improves over P218 baseline, then learned masks work in DROID smoke | temporal smoothing damages boundaries |
| Boundary refinement head | `tools/train_dynamic_mask_p218.py` | boundary F1 improves and dynamic IoU/F1 stays at or near P218 | small dataset overfit |
| Learned mask gating in SLAM frontend | `tools/build_dynamic_slam_backend_input_pack.py`, new P218 prediction export tool | predicted-mask DROID run is baseline-or-slightly-lower APE/RPE and better dynamic feature suppression than raw | still-image masks may not transfer to sequence frames |

## Commands Run

```bash
/home/rui/miniconda3/envs/tram/bin/python tools/build_dynamic_slam_backend_input_pack.py --frame-count 8 --output-dir outputs/dynamic_slam_backend_input_pack_p226_repro8
timeout 180s /home/rui/miniconda3/envs/tram/bin/python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_p226_repro8 --output-dir outputs/dynamic_slam_backend_smoke_p226_repro8 --frame-limit 8
/home/rui/miniconda3/envs/tram/bin/python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_p226_repro8 --output-dir outputs/dynamic_slam_backend_smoke_p226_repro8 --artifact "P226 reproduced 8-frame DROID-SLAM raw-vs-masked smoke metrics" --scope "P226 bounded local reproduction: 8 frames, Jun. 23 2022 Aisle_CW_Run_1, repository example forklift mask on frame 000002 only." --masked-label "masked RGB (example forklift frame 000002)" --output-prefix p226_repro8_metrics --interpretation "Both raw and masked 8-frame DROID-SLAM runs completed locally. This is a smoke reproduction, not the main 64-frame benchmark; the mask is sparse and expected to be trajectory-neutral."
python3 tools/run_baseline_comparison.py
```

## Next Step

Add output-path overrides or a P227 variant wrapper for `tools/train_dynamic_mask_p218.py`, then implement the smallest safe module: either confidence-gated mask dilation in the backend pack builder or a boundary head in the compact UNet. Run 8-frame smoke first, then reuse the existing 64-frame DROID sessions for the actual comparison.
