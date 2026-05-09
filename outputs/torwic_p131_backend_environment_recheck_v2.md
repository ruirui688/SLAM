# Dynamic SLAM Backend Environment Recheck v2

Status: **ready_for_p132_smoke_run**

## Runtime

- Python: `/home/rui/miniconda3/envs/tram/bin/python`
- DROID-SLAM root: `/home/rui/tram/thirdparty/DROID-SLAM` (ok)
- DROID weights: `/home/rui/tram/data/pretrain/droid.pth` (ok)
- Backend input pack: `/home/rui/slam/outputs/dynamic_slam_backend_input_pack/backend_input_manifest.json` (ok)

## Components

- torch: ok 2.4.0+cu118, cuda=11.8, cuda_available=True, cudnn=90100, device=NVIDIA GeForce RTX 3060
- torchvision: ok 0.19.0+cu118
- torchaudio: ok 2.4.0+cu118
- droid_backends: ok
- lietorch: ok
- evo: ok v1.31.1

## Operational Note

Use `make dynamic-slam-backend-env-check` or run downstream P132 commands with
`conda run -n tram` and `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH`.
A sandboxed probe may not see `/dev/nvidia*` and can falsely report CUDA unavailable.
