# P230 Thick Manuscript Quality Gate

Status: PASS with minor copy fixes.

Files reviewed:
- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`

Files changed:
- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`
- `paper/export/thick_manuscript_quality_gate_p230.md`

Checks performed:
- Searched for stale P112/P119/P120-era wording, brief-draft maintenance wording, and `Generated 2026-05-09` residue.
- Checked P195 remains BLOCKED.
- Checked P217-P228 required numbers in both thick drafts.
- Compared English/Chinese major sections and P225-P228 result/boundary content.
- Checked DROID-SLAM citation presence, figure paths, export paths, and table-caption consistency.

Fixes made:
- Removed manuscript-internal brief-draft maintenance wording from the English dynamic-mask protocol section.
- Tightened P228 boundary language so it reads as bounded frontend smoke, viable story seed, and ORB predicted/gated-region proxy only.
- Rephrased negative boundary statements that used over-broad terms such as full benchmark/navigation gain where not needed.
- Rephrased conclusion wording from qualitative feature-suppression improvement to the supported ORB-count decrease inside predicted/gated regions.
- Added the missing Chinese Table 6 caption corresponding to the English P225-P228 bounded DROID smoke caption.

Numeric gate:
- P217: 237 rows, 156/51/30 split, zero frame overlap, positive pixel rate 0.374176.
- P218: validation IoU/F1 0.671304/0.803329; test IoU/F1 0.578580/0.733038.
- P219: precision/recall/F1/IoU 0.556007/0.789669/0.604636/0.443210.
- P220: ORB GT dynamic 4795 -> 2192, 54.2857%.
- P225: 60 frames, Oct. 12, 2022 Aisle_CW indices 480-539, bounded retrained SmallUNet because the P218 checkpoint was unavailable.
- P227: APE 0.088504 -> 0.084529; RPE 0.076145 -> 0.076226; ORB 21030 -> 18617; neutral.
- P228: threshold 0.50, dilation 1 px, min component 128 px, max/target coverage 0.22/0.18, mean coverage 14.127053%; APE 0.088496 -> 0.084705; RPE 0.076145 -> 0.076224; ORB 8969 -> 5073; viable story seed.

Residual risks:
- Citation style remains venue-deferred, as already stated in the limitations.
- The word `benchmarks` remains only inside the POV-SLAM paper title/reference context and is not used as a P228 claim.
