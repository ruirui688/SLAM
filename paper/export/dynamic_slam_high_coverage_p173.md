# P173 high-coverage dynamic SLAM diagnostic

Scope: High-coverage selective semantic mask pressure test; not a full benchmark.

| Input | APE RMSE (m) | APE mean (m) | RPE RMSE (m) | RPE mean (m) |
|---|---:|---:|---:|---:|
| raw RGB | 0.010632 | 0.006707 | 0.015133 | 0.008336 |
| masked RGB | 0.010746 | 0.006816 | 0.015127 | 0.008315 |

Delta masked-minus-raw: APE RMSE `0.000114 m`, RPE RMSE `-0.000006 m`.

Mask coverage:

- Masked frames: `5/64`.
- Mean coverage: `0.567534%`.
- Temporal propagation radius: `0`.
- Temporal propagation mode: `nearest`.
- Mask dilation: `0` px.

Interpretation: Jun15 Aisle_CCW_Run_1 has selective semantic masks with max 17.324544% coverage and mean 0.567722%; interpret raw-vs-masked deltas as a pressure test of mask selectivity.


## Paper-facing interpretation

This result is a useful boundary case. Unlike the P172 replication sessions, the selective mask is no longer extremely sparse in every dynamic frame: frames 000005 and 000007 exceed 16% coverage. The resulting APE change is small (+0.114 mm) and far below the aggressive-mask failures from P171 (0.92-7.52 mm), but it is not exactly trajectory-neutral. The paper should therefore state that selectivity is necessary and coverage magnitude also matters.
