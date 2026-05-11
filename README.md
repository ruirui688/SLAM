# Dynamic Industrial Semantic-Segmentation-Assisted SLAM

This repository supports a research project on semantic front-end masking and
object-map maintenance for dynamic industrial SLAM. The core problem is not
"can a detector segment an object in one frame?", but "which semantic evidence
should affect a SLAM front end or enter a long-term object map in a warehouse
where forklifts, carts, goods, people, racks, barriers, and work tables coexist?"

The current project has two separate research lines:

- **Active valid line:** dataset-mask-supervised dynamic/non-static front-end
  masking from TorWIC/AnnotatedSemanticSet masks, followed by bounded feature
  and SLAM-front-end checks.
- **Blocked line:** learned persistent-map admission control. This remains
  blocked because independent `human_admit_label` and
  `human_same_object_label` supervision is absent.

Detailed phase history is in [RESEARCH_PROGRESS.md](RESEARCH_PROGRESS.md). The
latest synchronized summary is
[paper/export/latest_progress_summary_p221.md](paper/export/latest_progress_summary_p221.md).

## Current Scientific Boundary

Safe current claims:

- Dataset-provided TorWIC/AnnotatedSemanticSet masks can supervise a compact
  binary dynamic/non-static mask front end.
- P218 masks produce measurable held-out segmentation quality and suppress ORB
  features inside ground-truth dynamic regions in a small held-out package.
- The object-map maintenance layer remains an auditable rule-based admission
  system for stable-object retention and dynamic-contamination rejection.

Claims **not** supported yet:

- Learned persistent-map admission control.
- Learned cross-session same-object association.
- P193 weak-label admission training as claim-worthy admission supervision.
- Raw-vs-masked SLAM trajectory improvement from P218 masks.
- ATE/RPE, map-quality, or navigation benefit from the six-frame P219/P220
  front-end masking package.

The decisive admission-control gate is P195:

- `human_admit_label`: `0/32` valid labels.
- `human_same_object_label`: `0/160` valid labels.
- Status: `BLOCKED`.

## Key Results

### Dynamic-Mask Dataset and Training

P217 builds the no-manual dynamic/non-static mask dataset from
dataset-provided TorWIC/AnnotatedSemanticSet semantic/indexed masks:

| Quantity | Value |
|---|---:|
| Rows | 237 |
| Frame groups | 79 |
| Train / val / test rows | 156 / 51 / 30 |
| Frame overlap across splits | 0 |
| Overall positive pixel rate | 0.374176 |

P218 trains a compact UNet-style binary dynamic-mask model in the `tram` CUDA
environment on an NVIDIA RTX 3060:

| Split | IoU | F1 | Precision | Recall |
|---|---:|---:|---:|---:|
| Validation | 0.671304 | 0.803329 | 0.716614 | 0.913920 |
| Test | 0.578580 | 0.733038 | 0.601953 | 0.937109 |

Training configuration: resize `320x180`, 5 epochs, batch size 8,
`BCEWithLogitsLoss(pos_weight=1.489919) + 0.5 * DiceLoss`, threshold `0.40`
selected by validation F1.

### Front-End Masking Evaluation

P219 packages six held-out validation/test samples and reports mask-quality
proxies:

| Metric | Mean |
|---|---:|
| Predicted masked pixel rate | 0.208691 |
| Ground-truth dynamic pixel rate | 0.137248 |
| Precision / recall / F1 / IoU | 0.556007 / 0.789669 / 0.604636 / 0.443210 |

P220 audits ORB feature-level effects using OpenCV in the `tram` environment:

| Quantity | Value |
|---|---:|
| Raw ORB keypoints | 10059 |
| Masked ORB keypoints | 9972 |
| Raw keypoints in GT dynamic regions | 4795 |
| Masked keypoints in GT dynamic regions | 2192 |
| GT dynamic-region keypoint reduction | 54.2857% |

P220 intentionally does **not** report trajectory ATE/RPE. The P219 package is
six held-out frames, not a timestamped SLAM sequence with calibration and
aligned trajectory ground truth.

## Repository Layout

```text
README.md                         Project-facing overview and usage
RESEARCH_PROGRESS.md              Phase-by-phase research log
tools/                            Reproducible dataset, training, audit scripts
paper/evidence/                   Tracked JSON/CSV evidence digests
paper/export/                     Paper-ready Markdown summaries
paper/manuscript_en.md            Current English manuscript draft
paper/tro_submission/             IEEE/T-RO LaTeX submission scaffold
examples/                         Minimal demo and visual examples
outputs/                          Ignored generated outputs, masks, checkpoints
```

Raw data, derived images, model checkpoints, and large generated outputs are
kept out of Git. Tracked evidence files summarize the reproducible state.

## Environment

### Minimal Demo

The minimal object-map demo uses only Python standard library code and does not
need CUDA, PyTorch, model weights, TorWIC data, or network access.

```bash
python --version
python tools/run_minimal_demo.py
# or
make demo
```

Outputs are written under `outputs/minimal_demo/`.

### Research / CUDA Environment

The documented local research environment is the existing conda environment
`tram`:

```bash
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH \
  conda run -n tram <command>
```

Documented P218/P220 runtime:

- NVIDIA GeForce RTX 3060.
- PyTorch `2.4.0+cu118`.
- CUDA/cuDNN available through `tram`.
- OpenCV available in `tram` for ORB proxy checks.
- Default Python OpenCV may fail locally because of a NumPy ABI mismatch; use
  `tram` for OpenCV-dependent checks.

General dependency shape for a new research machine:

```bash
conda create -n slam-research python=3.10 -y
conda activate slam-research
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install evo opencv-python pillow numpy scipy matplotlib tqdm pyyaml
```

Do not download data or model weights unless the experiment protocol explicitly
requires and records the source/version.

## Reproducibility Commands

These commands rebuild or inspect tracked evidence using existing local data.
They do not require creating labels.

```bash
# P195 independent supervision gate; expected status is BLOCKED.
python3 tools/prepare_independent_supervision_p195.py

# P217 dataset manifest from dataset-provided masks.
python3 tools/build_dynamic_mask_dataset_p217.py

# P218 training command used for the recorded CUDA smoke.
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH \
  /home/rui/miniconda3/bin/conda run -n tram \
  python tools/train_dynamic_mask_p218.py \
    --epochs 5 --batch-size 8 --resize-width 320 --resize-height 180

# P219 held-out front-end masking package.
python3 tools/prepare_frontend_masking_eval_p219.py

# P220 feature-level masking audit; use tram because OpenCV works there.
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH \
  /home/rui/miniconda3/bin/conda run -n tram \
  python tools/audit_frontend_masking_slam_p220.py
```

For documentation-only work, prefer reading the tracked reports:

- [paper/export/dynamic_mask_dataset_p217.md](paper/export/dynamic_mask_dataset_p217.md)
- [paper/export/dynamic_mask_training_p218.md](paper/export/dynamic_mask_training_p218.md)
- [paper/export/frontend_masking_eval_p219.md](paper/export/frontend_masking_eval_p219.md)
- [paper/export/frontend_masking_slam_smoke_p220.md](paper/export/frontend_masking_slam_smoke_p220.md)
- [paper/export/independent_supervision_gate_p195.md](paper/export/independent_supervision_gate_p195.md)

## Data Layout

The dynamic-mask training route reads local TorWIC/AnnotatedSemanticSet assets:

- `source_image.png`
- `combined_indexedImage.png`
- `raw_labels_2d.json`

P217 derives RGB copies and binary dynamic/non-static masks under ignored
`outputs/dynamic_mask_dataset_p217/` and writes tracked manifests under
`paper/evidence/`.

Positive mask categories are:

```text
cart_pallet_jack
fork_truck
goods_material
misc_dynamic_feature
misc_non_static_feature
person
pylon_cone
```

These are front-end dynamic/non-static mask targets. They are **not**
persistent-map admission labels.

## Current Blockers and Next Steps

- P195 remains blocked until independent human admission and same-object labels
  are collected/imported through the existing protocol.
- P219/P220 cannot support trajectory claims because the package lacks a
  timestamped image sequence, calibration, and aligned trajectory ground truth.
- The next valid experiment should build a temporally aligned held-out
  raw-vs-P218-masked sequence package from existing local data before running
  ORB-SLAM3 or DROID-SLAM trajectory evaluation.
- Any future ATE/RPE result must first report trajectory availability and
  alignment validity.

Historical phase details, including earlier DROID/ORB smoke results and
evidence-governance artifacts, remain available in
[RESEARCH_PROGRESS.md](RESEARCH_PROGRESS.md) and `paper/export/`.
