# Minimal Runnable SLAM Demo

This directory contains a tiny, Git-tracked example dataset for the repository
smoke demo. It is not TorWIC raw data. It is a hand-sized object-observation
fixture that mirrors the paper's core data model:

```text
ObjectObservation -> cross-session cluster -> stable MapObject or rejection
```

Run from the repository root:

```bash
python tools/run_minimal_demo.py
```

Expected result:

- output directory: `outputs/minimal_demo/`;
- `summary.json`: machine-readable counts;
- `map_objects.json`: retained stable semantic landmarks;
- `rejected_clusters.json`: rejected dynamic/transient evidence;
- `report.md`: human-readable demo report.

The demo uses only the Python standard library and should run without GPU,
model weights, TorWIC downloads, or network access.
