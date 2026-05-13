# P232 Thick Export Refresh

Status: refreshed thick manuscript exports only.

## Commands

- `git status --short`
- `sed -n '1,260p' paper/build_paper.py`
- `find paper/export -maxdepth 1 -type f -printf '%f\n' | sort`
- `python3 paper/build_paper.py`
- `rg -n "P217|P218|P219|P220|P221|P222|P223|P224|P225|P226|P227|P228|P231|P195|BLOCKED|Generated 2026-05-09|2026-05-09" paper/export/manuscript_en_thick.html paper/export/manuscript_zh_thick.html`
- `pdftotext paper/export/manuscript_en_thick.pdf - | rg -n "P217|P218|P219|P220|P225|P226|P227|P228|P231|P195|BLOCKED|Generated 2026-05-09|2026-05-09|0\.088496|0\.084705|14\.127053|8969|5073"`
- `pdftotext paper/export/manuscript_zh_thick.pdf - | rg -n "P217|P218|P219|P220|P225|P226|P227|P228|P231|P195|BLOCKED|Generated 2026-05-09|2026-05-09|0\.088496|0\.084705|14\.127053|8969|5073"`

## Rebuilt Artifacts

- `paper/export/manuscript_en_thick.html`
- `paper/export/manuscript_en_thick.pdf`
- `paper/export/manuscript_zh_thick.html`
- `paper/export/manuscript_zh_thick.pdf`
- `paper/export/build_log.json`

The build script targets only `paper/manuscript_en_thick.md` and `paper/manuscript_zh_thick.md`; the brief manuscripts were not rebuilt or modified.

## Verification

- HTML and PDF generation completed with `status: ok`.
- The refreshed HTML/PDF exports contain the locked P217-P220, P225, P227, and P228 values from the P231 lock, including P228 mean coverage `14.127053%`, raw/masked APE `0.088496/0.084705`, raw/masked RPE `0.076145/0.076224`, and ORB gated-region keypoints `8969 -> 5073`.
- The exports state that P195 remains `BLOCKED`.
- No `Generated: 2026-05-09` or `2026-05-09` residue was found in refreshed thick HTML/PDF exports.
- P228 remains framed as a bounded frontend smoke/story seed only, with no full benchmark, navigation, independent-label, or learned-admission claim.

## Residual Risks

- The thick manuscript source does not print the exact P226 8-frame reproduction numbers or a literal `P231` label, although the P231 lock artifact records those values and states that the thick manuscripts are locked. This refresh did not edit manuscript source text.
- Existing timestamp-only P197-P205 evidence JSON diffs, untracked `thirdparty/`, and untracked ORB wrapper/headless files were left unstaged.
