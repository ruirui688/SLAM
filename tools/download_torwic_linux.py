#!/usr/bin/env python3
"""Download TorWIC SLAM dataset files on Linux.

Default mode downloads the minimal long-term experiment subset:
- Jun. 15, 2022 / Aisle_CW_Run_1.zip
- Jun. 23, 2022 / Aisle_CW_Run_1.zip
- Oct. 12, 2022 / Aisle_CW.zip

Requires: pip install gdown
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    file_id: str
    group: str
    relative_path: str


ITEMS = [
    Item("1nNVQRZc4c1FNLjyKdueJ_bsBySCoVKRc", "minimal", "Jun. 15, 2022/Aisle_CW_Run_1.zip"),
    Item("1NymBUWtHWLL15bYaXBJiDJa74gnNHgmR", "minimal", "Jun. 23, 2022/Aisle_CW_Run_1.zip"),
    Item("1_ESM_9B_Xgqe1hDJmvqn83U6Dx-efarb", "minimal", "Oct. 12, 2022/Aisle_CW.zip"),

    Item("15-6AxGxLR7CbbiHlMwFk0GxG_x7XTgyN", "trajectory", "Jun. 15, 2022/Aisle_CCW_Run_1.zip"),
    Item("1qOBEsoLn0P8NGUUaUXst95WHF_gqr4z7", "trajectory", "Jun. 15, 2022/Aisle_CCW_Run_2.zip"),
    Item("1nNVQRZc4c1FNLjyKdueJ_bsBySCoVKRc", "trajectory", "Jun. 15, 2022/Aisle_CW_Run_1.zip"),
    Item("1CVGFmK8wf1atpnj_3XQegpCgVESozJn6", "trajectory", "Jun. 15, 2022/Aisle_CW_Run_2.zip"),
    Item("1acVszk2ZxZ-HZ1wlthNXHOHV5tSihJVp", "trajectory", "Jun. 15, 2022/Hallway_Full_CCW.zip"),
    Item("1F6FR8DhX9VJ7l70Drs4EiSqtglb1-L_p", "trajectory", "Jun. 15, 2022/Hallway_Full_CW.zip"),
    Item("1mV0j0ysm7Za1CIXSzMbsIzHu090RCbPs", "trajectory", "Jun. 15, 2022/Hallway_Straight_CCW.zip"),

    Item("1T-n-6Ou3SPM3zT863ArohAUa768ufr0c", "trajectory", "Jun. 23, 2022/Aisle_CCW_Run_1.zip"),
    Item("1a5KcRGQO9QY-JUlZPDLcFu4LRS5sZrxj", "trajectory", "Jun. 23, 2022/Aisle_CCW_Run_2.zip"),
    Item("1NymBUWtHWLL15bYaXBJiDJa74gnNHgmR", "trajectory", "Jun. 23, 2022/Aisle_CW_Run_1.zip"),
    Item("16xeV4qeKWKk9zNv-BUykC-A8GRrJP8Ak", "trajectory", "Jun. 23, 2022/Aisle_CW_Run_2.zip"),
    Item("1cMxZeduI_TQPUpfFpOVBDtES0H6Mgpt2", "trajectory", "Jun. 23, 2022/Hallway_Full_CW.zip"),
    Item("1oke7tQJrshs9M9i7in-PzpCgaW7mh9Y-", "trajectory", "Jun. 23, 2022/Hallway_Straight_CCW.zip"),
    Item("1x0xrfXZAlpjuvtfvtCPbbKzaFMi9jgMu", "trajectory", "Jun. 23, 2022/Hallway_Straight_CW.zip"),

    Item("1hplx0_5tDKz4zF6iRgTfwuQNIund0URn", "trajectory", "Oct. 12, 2022/Aisle_CCW.zip"),
    Item("1_ESM_9B_Xgqe1hDJmvqn83U6Dx-efarb", "trajectory", "Oct. 12, 2022/Aisle_CW.zip"),
    Item("1cpQ2VvbJsgQWtX0HTz9nGLoAl-pQbx2I", "trajectory", "Oct. 12, 2022/Hallway_Full_CW_Run_1.zip"),
    Item("1tcHtf7QqNzmgYyX60qiyaWkWNngbB6Nn", "trajectory", "Oct. 12, 2022/Hallway_Full_CW_Run_2.zip"),
    Item("11MlBaWifh8Leh35vEaTpKb9EEC8KNe94", "trajectory", "Oct. 12, 2022/Hallway_Straight_CCW.zip"),
    Item("1nIXeky1OmbQ2V1ROtBoBirlIPZ6h3ArJ", "trajectory", "Oct. 12, 2022/Hallway_Straight_CW.zip"),

    Item("1NVnNEi-9QDoeyrnkxtlv8dHZl4Sc79zw", "support", "Oct. 12, 2022/calibrations.txt"),
    Item("1SsgnWfJeK9Hly5yfrq461MSXcdgyectN", "support", "Oct. 12, 2022/groundtruth_map.ply"),
    Item("1ovm4ycVrQfpuseI2Kc8TofS-LI0Nly_I", "support", "Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("/home/rui/slam/data/TorWIC_SLAM_Dataset"))
    p.add_argument("--mode", choices=["minimal", "minimal-support", "all-zips", "trajectories-only"], default="minimal")
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--extract", action="store_true", help="Extract downloaded zip files next to the zip.")
    p.add_argument("--verify-zip", action="store_true", help="Verify existing/downloaded zip archives before accepting them.")
    p.add_argument("--keep-going", action="store_true", help="Continue other items even if one item fails validation or download.")
    p.add_argument("--inventory-json-out", type=Path, help="Write the selected inventory items to JSON for downstream protocol/config tooling.")
    p.add_argument("--list-only", action="store_true", help="Only emit inventory metadata, do not download anything.")
    p.add_argument("--proxy", default=os.environ.get("TORWIC_DOWNLOAD_PROXY") or os.environ.get("DOWNLOAD_PROXY"))
    return p.parse_args()


def selected_items(mode: str) -> list[Item]:
    if mode == "all-zips":
        return [item for item in ITEMS if item.group in {"minimal", "trajectory", "support"}]
    if mode == "trajectories-only":
        return [item for item in ITEMS if item.group == "trajectory"]
    if mode == "minimal-support":
        return [item for item in ITEMS if item.group in {"minimal", "support"}]
    return [item for item in ITEMS if item.group == "minimal"]


def item_to_dict(item: Item) -> dict[str, str]:
    return {
        "file_id": item.file_id,
        "group": item.group,
        "relative_path": item.relative_path,
    }


def verify_zip_file(path: Path) -> tuple[bool, str | None]:
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            return bad is None, bad
    except Exception as exc:
        return False, str(exc)


def run_gdown(file_id: str, target: Path, retries: int, proxy: str | None, verify_zip: bool) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        if not verify_zip or target.suffix.lower() != ".zip":
            print(f"SKIP existing: {target} ({target.stat().st_size / 1e6:.1f} MB)")
            return True
        ok, bad = verify_zip_file(target)
        if ok:
            print(f"SKIP existing valid zip: {target} ({target.stat().st_size / 1e6:.1f} MB)")
            return True
        print(f"Existing zip invalid, re-downloading {target}: {bad}")
        target.unlink(missing_ok=True)

    cmd = [sys.executable, "-m", "gdown", "--continue", "-O", str(target)]
    if proxy:
        cmd.extend(["--proxy", proxy])
    cmd.append(file_id)
    for attempt in range(1, retries + 1):
        print(f"[{attempt}/{retries}] downloading {target}")
        rc = subprocess.call(cmd)
        if rc == 0 and target.exists() and target.stat().st_size > 0:
            if not verify_zip or target.suffix.lower() != ".zip":
                return True
            ok, bad = verify_zip_file(target)
            if ok:
                return True
            print(f"Downloaded zip invalid: {target} ({bad})")
        target.unlink(missing_ok=True)
    return False


def extract_zip(path: Path) -> None:
    if path.suffix.lower() != ".zip":
        return
    out_dir = path.with_suffix("")
    marker = out_dir / ".extract_done"
    if marker.exists():
        print(f"SKIP extracted: {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"extracting {path} -> {out_dir}")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(out_dir)
    marker.write_text("ok\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    chosen = selected_items(args.mode)

    if args.inventory_json_out:
        payload = {
            "generated_by": "download_torwic_linux.py",
            "root": str(args.root),
            "mode": args.mode,
            "count": len(chosen),
            "items": [item_to_dict(item) for item in chosen],
        }
        args.inventory_json_out.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_json_out.write_text(__import__("json").dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.list_only:
        print(f"LIST_ONLY mode={args.mode} count={len(chosen)}")
        for item in chosen:
            print(f"{item.group}\t{item.file_id}\t{item.relative_path}")
        return

    failed: list[Path] = []
    for item in chosen:
        target = args.root / item.relative_path
        ok = run_gdown(item.file_id, target, args.retries, args.proxy, args.verify_zip)
        if not ok:
            failed.append(target)
            if args.keep_going:
                continue
            break
        if args.extract:
            extract_zip(target)
    print("\nSummary")
    print(f"root: {args.root}")
    print(f"failed: {len(failed)}")
    for path in failed:
        print(f"FAILED {path}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
