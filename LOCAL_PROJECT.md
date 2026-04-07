# TorWIC-SLAM Local Project

This directory is the unified local project root.

## Included parts

- `TorWIC SLAM Dataset/`: downloaded TorWIC-SLAM dataset files
- Grounded-SAM-2 codebase files and source directories at the project root
- `checkpoints/sam2.1_hiera_large.pt`: local SAM 2 checkpoint
- `download_slam.ps1`: helper script for continuing dataset downloads
- `run_grounded_sam2.ps1`: runs Python from the configured `grounded-sam2` environment

## Working root

Use `D:\TorWIC-SLAM` as the main project directory.

## Environment

- Conda environment: `D:\miniconda3\envs\grounded-sam2`
- `sam2` import path now resolves to `D:\TorWIC-SLAM\sam2`
- `groundingdino` import path now resolves to `D:\TorWIC-SLAM\grounding_dino\groundingdino`

## Example usage

```powershell
cd D:\TorWIC-SLAM
.\run_grounded_sam2.ps1 -c "import sam2, groundingdino; print(sam2.__file__); print(groundingdino.__file__)"
```

## Notes

- The original source folder `D:\Downloads\Grounded-SAM-2` was used as the import source.
- The active editable Python mappings were redirected to this root, so the configured environment now points here.
