# P192 GPU Admission-Scorer Training Smoke

**Status:** CUDA-only PyTorch smoke completed. This run used GPU and would fail rather than falling back to CPU if CUDA were unavailable.
**Environment basis:** README.md §0.3: use LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram <command>
**Actual command:** `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram python tools/train_admission_scorer_gpu_p192.py --dataset paper/evidence/admission_scorer_dataset_p190.csv --p191-json paper/evidence/admission_scorer_smoke_p191.json --output-json paper/evidence/admission_scorer_gpu_p192.json --output-md paper/export/admission_scorer_gpu_p192.md`
**Python executable:** `/home/rui/miniconda3/envs/tram/bin/python`
**Torch:** `2.4.0+cu118`; CUDA runtime `11.8`; device `cuda`; GPU `NVIDIA GeForce RTX 3060`.
**Dataset:** `paper/evidence/admission_scorer_dataset_p190.csv` (51 cluster samples).

## GPU Evidence

- cuda_available: `True`
- device_count: `1`
- memory_before: allocated=0 bytes, reserved=0 bytes
- memory_after: allocated=17043968 bytes, reserved=23068672 bytes
- memory_peak: allocated=18105344 bytes, reserved=23068672 bytes

## Metrics: GPU MLP vs GPU Logistic vs Rule Baseline

### train
- GPU MLP: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.
- GPU logistic: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.
- Rule baseline: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.

### val
- GPU MLP: accuracy=0.8571, precision=1.0000, recall=0.7143, F1=0.8333, fp=0, fn=2.
- GPU logistic: accuracy=0.8571, precision=1.0000, recall=0.7143, F1=0.8333, fp=0, fn=2.
- Rule baseline: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.

### test
- GPU MLP: accuracy=0.6875, precision=0.7000, recall=0.7778, F1=0.7368, fp=3, fn=2.
- GPU logistic: accuracy=0.6250, precision=0.6667, recall=0.6667, F1=0.6667, fp=3, fn=3.
- Rule baseline: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.

## P191 CPU Baseline Comparison

- train: P191 CPU all-features acc/F1=1.0000/1.0000; P192 GPU MLP acc/F1=1.0000/1.0000.
- val: P191 CPU all-features acc/F1=0.8571/0.8333; P192 GPU MLP acc/F1=0.8571/0.8333.
- test: P191 CPU all-features acc/F1=0.6875/0.7368; P192 GPU MLP acc/F1=0.6875/0.7368.

## Training Runtime

- GPU MLP training time: 0.295921 s
- GPU logistic training time: 0.255770 s

## Risk / Interpretation

- This really used CUDA, but it remains a pipeline validation step: 51 cluster samples are too few for a publishable GPU model claim.
- Rule baseline remains artificially strong because P190 labels are weak labels derived from the same rule gate.
- Dynamic ratio, label purity, and label/category flags may leak the rule decision; do not claim learned superiority until independent labels exist.
- The right next step is larger real-data dataset construction from existing TorWIC manifests/tracklets/map objects, not more epochs on 51 clusters.

## P193 Real-Data Expansion Plan

### Frame-level admission dataset
- Source globs: `outputs/torwic_*/frontend_output/all_instances_manifest.json, outputs/torwic_*/observation_output/observations_index.json`
- Command: `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram python tools/build_admission_frame_dataset_p193.py --outputs-root outputs --cluster-labels paper/evidence/admission_scorer_dataset_p190.csv --output-json paper/evidence/admission_frame_dataset_p193.json --output-csv paper/evidence/admission_frame_dataset_p193.csv`

### Pairwise cross-session association dataset
- Source globs: `outputs/torwic_*/tracklet_output/tracklets_index.json, outputs/torwic_*/map_output/map_objects.json, outputs/torwic_*selection_v5.json`
- Command: `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram python tools/build_association_pair_dataset_p193.py --outputs-root outputs --selection-glob 'outputs/torwic_*selection_v5.json' --output-json paper/evidence/association_pair_dataset_p193.json --output-csv paper/evidence/association_pair_dataset_p193.csv`

**Recommendation:** Implement the frame-level dataset builder first because manifests already exist and it expands admission supervision without changing the model target; then build pairwise association labels as P194 if admission still underfits.
