# P193 Frame-Level Admission-Scorer GPU Training

**Status:** CUDA-only PyTorch smoke completed. This run used GPU and would fail rather than falling back to CPU if CUDA were unavailable.
**Environment basis:** README.md §0.3: use LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram <command>
**Actual command:** `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram python tools/train_admission_scorer_gpu_p192.py --dataset paper/evidence/admission_frame_dataset_p193.csv --dataset-kind frame-observation-level-deduplicated --p191-json paper/evidence/admission_scorer_smoke_p191.json --p192-json paper/evidence/admission_scorer_gpu_p192.json --output-json paper/evidence/admission_scorer_frame_gpu_p193.json --output-md paper/export/admission_scorer_frame_gpu_p193.md --phase P193-frame-level-gpu-training --report-title 'P193 Frame-Level Admission-Scorer GPU Training'`
**Python executable:** `/home/rui/miniconda3/envs/tram/bin/python`
**Torch:** `2.4.0+cu118`; CUDA runtime `11.8`; device `cuda`; GPU `NVIDIA GeForce RTX 3060`.
**Dataset:** `paper/evidence/admission_frame_dataset_p193.csv` (110 samples; dataset kind `frame-observation-level-deduplicated`).

## GPU Evidence

- cuda_available: `True`
- device_count: `1`
- memory_before: allocated=0 bytes, reserved=0 bytes
- memory_after: allocated=17046528 bytes, reserved=23068672 bytes
- memory_peak: allocated=18110976 bytes, reserved=23068672 bytes

## Metrics: GPU MLP vs GPU Logistic vs Rule Baseline

### train
- GPU MLP: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.
- GPU logistic: accuracy=0.9524, precision=0.9333, recall=1.0000, F1=0.9655, fp=2, fn=0.
- Rule baseline: accuracy=0.3333, precision=0.0000, recall=0.0000, F1=0.0000, fp=0, fn=28.

### val
- GPU MLP: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.
- GPU logistic: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.
- Rule baseline: accuracy=0.5000, precision=0.0000, recall=0.0000, F1=0.0000, fp=0, fn=4.

### test
- GPU MLP: accuracy=0.9500, precision=0.9250, recall=1.0000, F1=0.9610, fp=3, fn=0.
- GPU logistic: accuracy=0.9500, precision=0.9250, recall=1.0000, F1=0.9610, fp=3, fn=0.
- Rule baseline: accuracy=0.3833, precision=0.0000, recall=0.0000, F1=0.0000, fp=0, fn=37.

## P191 CPU Baseline Comparison

- train: P191 CPU all-features acc/F1=1.0000/1.0000; current GPU MLP acc/F1=1.0000/1.0000.
- val: P191 CPU all-features acc/F1=0.8571/0.8333; current GPU MLP acc/F1=1.0000/1.0000.
- test: P191 CPU all-features acc/F1=0.6875/0.7368; current GPU MLP acc/F1=0.9500/0.9610.

## P192 51-Cluster GPU Baseline Comparison

- train: P192 cluster GPU MLP acc/F1=1.0000/1.0000; current GPU MLP acc/F1=1.0000/1.0000.
- val: P192 cluster GPU MLP acc/F1=0.8571/0.8333; current GPU MLP acc/F1=1.0000/1.0000.
- test: P192 cluster GPU MLP acc/F1=0.6875/0.7368; current GPU MLP acc/F1=0.9500/0.9610.

## Training Runtime

- GPU MLP training time: 0.340215 s
- GPU logistic training time: 0.237784 s

## Risk / Interpretation

- This really used CUDA, but remains a bounded experiment: dataset kind `frame-observation-level-deduplicated` and labels are still weak labels unless independently reviewed.
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

## P193 Dataset Expansion Summary

- Raw joined observation samples: 154.
- Deduplicated frame/observation samples used for CUDA training: 110.
- Split distribution: train 42 (28 admit / 14 reject), val 8 (4 / 4), test 60 (37 / 23).
- Source files retained: 24 TorWIC observation-index files; 20 backend input manifests were inventoried.
- Dedup strategy: `physical_session(session_id)::frame_index::object_name`; 44 duplicate physical keys removed; cross-split overlap after dedup is 0.
- Full dataset report: `paper/export/admission_frame_dataset_p193.md` and `paper/evidence/admission_frame_dataset_p193.json`.

## P194 Required Follow-Up

The P193 GPU metrics are better than the P192 51-cluster baseline, but they are not yet a contribution claim. The labels are inherited from `selection_v5`, the validation split is only 8 samples after de-duplication, and forklift/category features can act as target proxies. P194 should build at least one independent supervision source: (1) human boundary-label sheet for false admits/false rejects and near-threshold observations, or (2) pairwise cross-session association labels from tracklet/map-object lineage.
