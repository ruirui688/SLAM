# P228 Confidence-Gated Mask Module

Status: `viable_story_seed`

Claim boundary: Small frontend mask post-processing smoke on the P225 sequence only; not a full benchmark, navigation claim, or independent dynamic segmentation claim. P195 remains BLOCKED.

## Module

- Probability threshold: `0.5`.
- Dilation: `1` px.
- Min connected component area: `128` px.
- Coverage cap / target: `0.22` / `0.18`.
- Mean gated mask coverage: `14.127053%`.

## Trajectory Metrics

| Run | Frames | Raw APE | Masked APE | Raw RPE | Masked RPE | Delta APE | Delta RPE |
|---|---:|---:|---:|---:|---:|---:|---:|
| P228 gate | 16 | 0.025810 | 0.025180 | 0.092888 | 0.092865 | -0.000630 | -0.000023 |
| P228 full | 60 | 0.088496 | 0.084705 | 0.076145 | 0.076224 | -0.003791 | 0.000079 |

## P227 Comparison

- P227 16f raw/masked APE: `0.025810` / `0.025066`; RPE: `0.092888` / `0.092770`.
- P227 60f raw/masked APE: `0.088504` / `0.084529`; RPE: `0.076145` / `0.076226`.

## ORB Feature Proxy

This uses the P228 predicted-mask region, not independent dynamic GT.

- Raw total keypoints: `60000`.
- Masked total keypoints: `60000`.
- Raw keypoints in gated regions: `8969`.
- Masked keypoints in gated regions: `5073`.
- Region keypoint delta masked-minus-raw: `-3896`.
- P227 predicted-region delta baseline: `-2413`.

## Interpretation

The confidence-gated module stayed within the bounded trajectory smoke tolerance and preserved/improved the P227 ORB predicted-region suppression proxy. This is only a small frontend mask-module smoke, but it is a viable story seed.

## Commands

```bash
/home/rui/miniconda3/envs/tram/bin/python tools/apply_confidence_gated_mask_module_p228.py build --source-dir outputs/temporal_masked_sequence_p225/sequence --sequence-output outputs/temporal_masked_sequence_p228_conf_gated --pack-output outputs/dynamic_slam_backend_input_pack_p228_conf_gated --probability-threshold 0.50 --dilation-px 1 --min-component-area-px 128 --max-coverage 0.22 --target-coverage 0.18
timeout 240s /home/rui/miniconda3/envs/tram/bin/python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_p228_conf_gated --output-dir outputs/dynamic_slam_backend_smoke_p228_conf_gated_16 --frame-limit 16
/home/rui/miniconda3/envs/tram/bin/python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_p228_conf_gated --output-dir outputs/dynamic_slam_backend_smoke_p228_conf_gated_16 --artifact "P228 16-frame confidence-gated P225 mask DROID-SLAM smoke metrics" --scope "P228 bounded local module smoke: first 16 frames from Oct. 12 2022 Aisle_CW P225 package, confidence/coverage-gated probability-mask post-processing." --masked-label "masked RGB (P228 confidence-gated P225 probability masks)" --output-prefix p228_conf_gated_metrics --interpretation "P228 16-frame gate for confidence-gated mask module; use only as bounded smoke evidence."
timeout 600s /home/rui/miniconda3/envs/tram/bin/python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_p228_conf_gated --output-dir outputs/dynamic_slam_backend_smoke_p228_conf_gated --frame-limit 60
/home/rui/miniconda3/envs/tram/bin/python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_p228_conf_gated --output-dir outputs/dynamic_slam_backend_smoke_p228_conf_gated --artifact "P228 60-frame confidence-gated P225 mask DROID-SLAM smoke metrics" --scope "P228 bounded local module smoke: 60 frames from Oct. 12 2022 Aisle_CW P225 package, confidence/coverage-gated probability-mask post-processing." --masked-label "masked RGB (P228 confidence-gated P225 probability masks)" --output-prefix p228_conf_gated_metrics --interpretation "P228 60-frame smoke for confidence-gated mask module; use only as bounded module evidence."
```
