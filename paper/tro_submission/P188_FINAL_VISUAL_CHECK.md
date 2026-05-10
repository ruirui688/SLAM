# P188 Final Visual Check

**Date:** 2026-05-10 13:40+08
**Scope:** Machine skim follow-up for final PDF warnings. No new data, no training, no system package installation.

## Inputs

- `paper/tro_submission/main.pdf`
- `paper/tro_submission/main.tex`
- `paper/tro_submission/build_p186_final/tectonic_compile_log_p186_final.txt`
- `paper/tro_submission/build_p188/tectonic_compile_log_p188.txt`

## Build / Command Result

- Previous async Tectonic build completed successfully; it emitted only underfull/overfull hbox/vbox warnings.
- Recompiled after fixes with `/home/rui/miniconda3/bin/tectonic --reruns 2 main.tex --outdir build_p188`.
- Exit code: **0**. Output PDF: `paper/tro_submission/build_p188/main.pdf`, 15 pages.
- Copied final PDF to `paper/tro_submission/main.pdf`.

## WARN Review and Resolution

### Page 5 Table III right truncation

- Verdict: **REAL → FIXED**
- Evidence: Pre-fix extraction showed `Deci`/`Reta` truncation and rendered content touched the right page edge. Fixed by resizing Table II/III tabulars to column width. Post-fix extraction shows full `Decision` / `Retain` / `Reject`; rendered right margin is 109 px.

### Page 6 VII-G title-only

- Verdict: **REAL STRUCTURAL WEAKNESS → FIXED**
- Evidence: Added a body paragraph under VII-G before floats. Post-fix extraction shows the heading plus explanatory text.

### Page 9 suspected blank

- Verdict: **FALSE POSITIVE**
- Evidence: Text extraction sees only the page number because content is image/table-heavy. Rendered page 9 has non-white content covering 76.38% of the page and visual inspection confirms visible content.

### Pages 10–14 figures

- Verdict: **PASS**
- Evidence: Rendered pages 10–14 show figures/captions visible and not clipped. Bbox margins remain away from page edges.

### Page 6 top-table crowding

- Verdict: **MINOR REAL RISK → ACCEPTABLE**
- Evidence: Shortened Table VII caption and resized Table V. Remaining TeX warnings are cosmetic hbox/vbox warnings, not fatal errors.

## Remaining Human Items

- final human visual skim before upload
- optional anonymous code mirror only if code is uploaded for double-anonymous review

## Final Verdict

**PASS after fixes.** The machine-skim warnings were either fixed (Table III, VII-G body, page-6 table crowding) or shown to be extraction/visual false positives (page 9, pages 10–14 figure clipping).
