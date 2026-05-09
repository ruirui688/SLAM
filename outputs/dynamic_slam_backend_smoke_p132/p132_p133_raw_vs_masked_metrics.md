# P132/P133 Raw-vs-Masked DROID-SLAM Smoke Metrics

Status: backend smoke and evo evaluation path executed.

Scope: 8-frame bounded TorWIC `Aisle_CW_Run_1` window. DROID-SLAM ran in the verified `tram` conda runtime on RTX 3060. Global BA was disabled because the smoke window is too short for DROID proximity edges; this is a frontend/trajectory-filler smoke run, not a full benchmark.

| Input | APE RMSE (m) | APE mean (m) | RPE RMSE (m) | RPE mean (m) |
|---|---:|---:|---:|---:|
| raw RGB | 0.001242 | 0.001212 | 0.002250 | 0.002109 |
| masked RGB | 0.001243 | 0.001212 | 0.002255 | 0.002115 |
| masked - raw | +0.000001 | 0.000000 | +0.000005 | +0.000006 |

Interpretation: raw and masked are effectively tied on this tiny smoke window. The result proves that the raw-vs-masked backend and evo ATE/RPE path is executable, but it does not prove masked input improves full-trajectory SLAM, map quality, or navigation.
