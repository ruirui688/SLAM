# Dynamic SLAM Stage 2 Expanded Metrics — P173

Bounded 64-frame DROID-SLAM raw-vs-masked diagnostics. No navigation-gain or full-session benchmark claim.

## Result

| Session | Category | Masked Frames | Max Coverage | APE Raw | APE Masked | ΔAPE | RPE Raw | RPE Masked | ΔRPE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Jun23 Aisle_CW_Run_2 | cross-day CW pair | 4/64 | 0.88954% | 0.021933 | 0.021932 | -0.001 mm | 0.015269 | 0.015269 | 0.000 mm |
| Oct12 Aisle_CW | cross-month CW (already covered by P172 Stage 2) | 2/64 | 4.8852% | 0.049081 | 0.049081 | 0.000 mm | 0.039889 | 0.039888 | -0.001 mm |
| Jun15 Aisle_CCW_Run_1 | same-day opposite direction high-coverage | 5/64 | 17.324544% | 0.010632 | 0.010746 | 0.114 mm | 0.015133 | 0.015127 | -0.006 mm |
| Oct12 Aisle_CCW | cross-month opposite direction | 3/64 | 5.377713% | 0.020350 | 0.020350 | 0.000 mm | 0.016609 | 0.016611 | 0.002 mm |
| Jun15 Hallway_Full_CW | Hallway scene-transfer | 7/64 | 0.895182% | 0.004561 | 0.004538 | -0.023 mm | 0.010586 | 0.010590 | 0.004 mm |

## Interpretation

The expanded Stage 2 set supports a refined boundary: selective low/moderate masks are trajectory-neutral; a high-coverage selective CCW sample produces only sub-millimetre APE shift (+0.114 mm), far below aggressive-mask failures but not exactly zero. Selectivity is necessary and coverage magnitude matters.

## Boundary Update

- P172 replication sessions remain exactly trajectory-neutral at the rounded evo precision.
- P173 adds three more neutral/near-neutral sessions and one high-coverage boundary case.
- Jun15 Aisle_CCW_Run_1 reaches 17.32% per-frame mask coverage and shifts APE by +0.114 mm, which is far smaller than aggressive-mask failures but no longer exactly zero.
- The paper should avoid wording that selectivity alone guarantees neutrality; the tighter claim is selectivity plus coverage magnitude defines the perturbation regime.
