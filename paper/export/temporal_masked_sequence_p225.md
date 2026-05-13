# P225 Temporal Raw-vs-P218-Masked Sequence Package

**Status:** P225_TEMPORAL_RAW_VS_P218_MASKED_SEQUENCE_PACKAGE_COMPLETE

## Claim Boundary

This package is trajectory-ready input material for raw-vs-P218-masked feasibility testing. It does not claim ORB-SLAM3/DROID ATE/RPE improvement.

## Sequence

- Source: `data/TorWIC_SLAM_Dataset/Oct. 12, 2022/Aisle_CW`
- Window: `480` to `539` inclusive
- Frames: `60`
- Timestamp span seconds: `5.894061`
- Raw package: `outputs/temporal_masked_sequence_p225/sequence/raw`
- Masked package: `outputs/temporal_masked_sequence_p225/sequence/masked`

## Mask Model Route

- Mode: `retrained_bounded_smoke_no_prior_p218_checkpoint_found`
- Checkpoint: `outputs/temporal_masked_sequence_p225/model/p225_retrained_p218_smallunet.pt`
- Threshold: `0.4`
- Training labels: P217 dataset-provided semantic binary dynamic/non-static masks only.
- Target sequence semantic masks were not used as labels or copied into masked outputs.

## Masked Window Stats

- Mean predicted dynamic pixel rate: `0.241929`
- Min/max predicted dynamic pixel rate: `0.084028` / `0.37217`
- Mean probability: `0.35203`

## Trajectory Readiness

- `rgb.txt`: `['outputs/temporal_masked_sequence_p225/sequence/raw/rgb.txt', 'outputs/temporal_masked_sequence_p225/sequence/masked/rgb.txt']`
- `frame_times.txt`: `['outputs/temporal_masked_sequence_p225/sequence/raw/frame_times.txt', 'outputs/temporal_masked_sequence_p225/sequence/masked/frame_times.txt']`
- `groundtruth.txt`: `['outputs/temporal_masked_sequence_p225/sequence/raw/groundtruth.txt', 'outputs/temporal_masked_sequence_p225/sequence/masked/groundtruth.txt']`
- `calibrations.txt`: `['outputs/temporal_masked_sequence_p225/sequence/raw/calibrations.txt', 'outputs/temporal_masked_sequence_p225/sequence/masked/calibrations.txt']`
- ORB YAML reference: `['outputs/temporal_masked_sequence_p225/sequence/raw/TorWIC_mono_left.yaml', 'outputs/temporal_masked_sequence_p225/sequence/masked/TorWIC_mono_left.yaml']`

## Outputs

- JSON: `paper/evidence/temporal_masked_sequence_p225.json`
- CSV: `paper/evidence/temporal_masked_sequence_p225.csv`
- Markdown: `paper/export/temporal_masked_sequence_p225.md`

## Boundary Notes

- This is a trajectory-ready packaging/feasibility step, not an ATE/RPE result.
- P195 status remains `BLOCKED`.
