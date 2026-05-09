# P134 64-frame DROID-SLAM Global-BA Metrics

Status: 64-frame raw-vs-masked DROID-SLAM run with global BA executed.

Scope: bounded TorWIC `Aisle_CW_Run_1` window, 64 frames, verified `tram` conda runtime, RTX 3060, DROID-SLAM weights at `/home/rui/tram/data/pretrain/droid.pth`. evo uses Sim(3) alignment with scale correction.

| Input | APE RMSE (m) | APE mean (m) | RPE RMSE (m) | RPE mean (m) |
|---|---:|---:|---:|---:|
| raw RGB | 0.051135 | 0.043453 | 0.032713 | 0.019346 |
| masked RGB | 0.051136 | 0.043453 | 0.032713 | 0.019345 |
| masked - raw | +0.000001 | 0.000000 | 0.000000 | -0.000001 |

Interpretation: raw and masked are effectively tied on this 64-frame bounded global-BA run. The result proves a larger backend run is executable, but it does not support a masked-input improvement claim.
