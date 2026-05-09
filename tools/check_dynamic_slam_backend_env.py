#!/usr/bin/env python3
"""Check the dynamic SLAM backend runtime environment.

This probe is intentionally runtime-oriented: it verifies the conda environment
and dynamic library path used by the DROID-SLAM smoke run, not the repository's
CPU-only virtualenv.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "outputs" / "torwic_p131_backend_environment_recheck_v2.json"
OUTPUT_MD = ROOT / "outputs" / "torwic_p131_backend_environment_recheck_v2.md"
DROID_ROOT = Path("/home/rui/tram/thirdparty/DROID-SLAM")
DROID_WEIGHTS = Path("/home/rui/tram/data/pretrain/droid.pth")
BACKEND_PACK = ROOT / "outputs" / "dynamic_slam_backend_input_pack" / "backend_input_manifest.json"


def module_status(name: str) -> dict:
    try:
        module = import_module(name)
        version = getattr(module, "__version__", None)
        return {"status": "ok", "version": version}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    result: dict = {
        "artifact": "P131 Dynamic SLAM Backend Environment Recheck v2",
        "created": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "python": sys.executable,
        "ld_library_path": os.environ.get("LD_LIBRARY_PATH", ""),
        "paths": {
            "droid_root": str(DROID_ROOT),
            "droid_weights": str(DROID_WEIGHTS),
            "backend_input_manifest": str(BACKEND_PACK),
        },
        "path_exists": {
            "droid_root": DROID_ROOT.exists(),
            "droid_weights": DROID_WEIGHTS.exists(),
            "backend_input_manifest": BACKEND_PACK.exists(),
        },
    }

    torch_status = module_status("torch")
    if torch_status["status"] == "ok":
        import torch

        torch_status.update(
            {
                "cuda_version": torch.version.cuda,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count(),
                "cudnn_available": torch.backends.cudnn.is_available(),
                "cudnn_version": torch.backends.cudnn.version(),
                "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            }
        )

    result["components"] = {
        "torch": torch_status,
        "torchvision": module_status("torchvision"),
        "torchaudio": module_status("torchaudio"),
        "droid_backends": module_status("droid_backends"),
        "lietorch": module_status("lietorch"),
        "evo": module_status("evo"),
    }

    required_ok = [
        result["path_exists"]["droid_root"],
        result["path_exists"]["droid_weights"],
        result["path_exists"]["backend_input_manifest"],
        result["components"]["torch"].get("cuda_available") is True,
        result["components"]["torch"].get("cudnn_available") is True,
        result["components"]["droid_backends"]["status"] == "ok",
        result["components"]["lietorch"]["status"] == "ok",
        result["components"]["evo"]["status"] == "ok",
    ]
    result["status"] = "ready_for_p132_smoke_run" if all(required_ok) else "blocked"
    result["claim_boundary"] = (
        "Runtime environment is ready for a bounded DROID-SLAM raw-vs-masked "
        "smoke run; this probe does not itself report ATE/RPE."
    )

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Dynamic SLAM Backend Environment Recheck v2",
        "",
        f"Status: **{result['status']}**",
        "",
        "## Runtime",
        "",
        f"- Python: `{result['python']}`",
        f"- DROID-SLAM root: `{DROID_ROOT}` ({'ok' if DROID_ROOT.exists() else 'missing'})",
        f"- DROID weights: `{DROID_WEIGHTS}` ({'ok' if DROID_WEIGHTS.exists() else 'missing'})",
        f"- Backend input pack: `{BACKEND_PACK}` ({'ok' if BACKEND_PACK.exists() else 'missing'})",
        "",
        "## Components",
        "",
    ]
    for name, status in result["components"].items():
        detail = status.get("version") or status.get("error") or ""
        extra = ""
        if name == "torch" and status["status"] == "ok":
            extra = (
                f", cuda={status.get('cuda_version')}, "
                f"cuda_available={status.get('cuda_available')}, "
                f"cudnn={status.get('cudnn_version')}, "
                f"device={status.get('device_name')}"
            )
        suffix = f" {detail}" if detail else ""
        lines.append(f"- {name}: {status['status']}{suffix}{extra}")
    lines.extend(
        [
            "",
            "## Operational Note",
            "",
            "Use `make dynamic-slam-backend-env-check` or run downstream P132 commands with",
            "`conda run -n tram` and `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH`.",
            "A sandboxed probe may not see `/dev/nvidia*` and can falsely report CUDA unavailable.",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
