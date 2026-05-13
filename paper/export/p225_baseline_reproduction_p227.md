# P227 P225 Baseline Reproduction

Status: `baseline_reproduction_passed_neutral`

Claim boundary: Bounded DROID-SLAM trajectory smoke and ORB feature sanity only. No improvement claim unless APE/RPE support it; ORB dynamic-region counts use predicted-mask-region proxy, not GT dynamic masks.

## Trajectory Metrics

| Run | Frames | APE RMSE (m) | APE mean (m) | RPE RMSE (m) | RPE mean (m) |
|---|---:|---:|---:|---:|---:|
| raw RGB | 60 | 0.088504 | 0.077594 | 0.076145 | 0.071417 |
| masked RGB (P225 learned predicted-mask package) | 60 | 0.084529 | 0.073688 | 0.076226 | 0.071460 |

Delta masked-minus-raw: APE RMSE `-0.003975 m`, RPE RMSE `0.000081 m`.

16-frame stability gate:

- Status: `ok`.
- Raw APE/RPE RMSE: `0.025810` / `0.092888` m.
- Masked APE/RPE RMSE: `0.025066` / `0.092770` m.
- Delta masked-minus-raw APE/RPE RMSE: `-0.000744` / `-0.000118` m.

## ORB Feature Sanity

This is a predicted-mask-region proxy because independent GT dynamic masks are not available for this sequence.

- Raw total keypoints: `60000`.
- Masked total keypoints: `60000`.
- Raw keypoints in predicted-mask regions: `21030`.
- Masked keypoints in predicted-mask regions: `18617`.
- Predicted-region keypoint delta masked-minus-raw: `-2413`.

## Interpretation

The P225 learned-mask raw/masked DROID-SLAM smoke reproduced successfully. Masked trajectory error is neutral within the bounded smoke tolerance, so this is baseline reproduction evidence, not an improvement claim.

## Commands

```bash
/home/rui/miniconda3/envs/tram/bin/python tools/prepare_p227_p225_backend_pack.py --source-dir outputs/temporal_masked_sequence_p225/sequence --output-dir outputs/dynamic_slam_backend_input_pack_p227_p225_learned_mask
timeout 240s /home/rui/miniconda3/envs/tram/bin/python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_p227_p225_learned_mask --output-dir outputs/dynamic_slam_backend_smoke_p227_p225_learned_mask_16 --frame-limit 16
/home/rui/miniconda3/envs/tram/bin/python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_p227_p225_learned_mask --output-dir outputs/dynamic_slam_backend_smoke_p227_p225_learned_mask_16 --artifact 'P227 16-frame P225 learned-mask DROID-SLAM smoke metrics' --scope 'P227 bounded local reproduction: first 16 frames from Oct. 12 2022 Aisle_CW P225 learned-mask package, source indices 480-495.' --masked-label 'masked RGB (P225 learned predicted-mask package)' --output-prefix p227_p225_learned_mask_metrics
timeout 600s /home/rui/miniconda3/envs/tram/bin/python tools/run_dynamic_slam_backend_smoke.py --input-dir outputs/dynamic_slam_backend_input_pack_p227_p225_learned_mask --output-dir outputs/dynamic_slam_backend_smoke_p227_p225_learned_mask --frame-limit 60
/home/rui/miniconda3/envs/tram/bin/python tools/evaluate_dynamic_slam_metrics.py --input-dir outputs/dynamic_slam_backend_input_pack_p227_p225_learned_mask --output-dir outputs/dynamic_slam_backend_smoke_p227_p225_learned_mask --artifact 'P227 60-frame P225 learned-mask DROID-SLAM smoke metrics' --scope 'P227 bounded local reproduction: 60 frames from Oct. 12 2022 Aisle_CW P225 learned-mask package, source indices 480-539.' --masked-label 'masked RGB (P225 learned predicted-mask package)' --output-prefix p227_p225_learned_mask_metrics
```
