# COMPILE ATTEMPT — P180

**Date:** 2026-05-10  
**Engine:** Tectonic 0.16.9 (conda-forge, user-level, no sudo)  
**Target:** `paper/tro_submission/main.tex`  
**Status:** ✅ **SUCCESS** — PDF generated (14 pages, 3.09 MB)

---

## 1. Environment

| Component | Value |
|-----------|-------|
| TeX engine | Tectonic 0.16.9 |
| Installation | `conda install -c conda-forge tectonic` |
| Permissions | User-level only, no sudo |
| Document class | IEEEtran.cls (auto-downloaded) |
| Font | Latin Modern (auto-downloaded) |
| Output dir | `paper/tro_submission/build_p180/` |

## 2. Compilation Commands

```bash
# First run (package downloads, OOM-killed):
tectonic main.tex 2>&1 | tee build_p180/tectonic_compile_log.txt

# Second run (cached packages, success):
tectonic --keep-intermediates --reruns 2 main.tex --outdir build_p180
```

**Note:** First run was OOM-killed during initial TeX format generation + font downloads (expected for first-ever tectonic run on this machine). Second run with cached bundles completed successfully.

## 3. Compile Result

- **Errors:** 0
- **Warnings:** 26 (all Underfull/Overfull hbox, expected for IEEEtran two-column)
- **BibTeX:** Passed (28 citations, all resolved)
- **Cross-references:** All resolved (no `??` markers)
- **Figures:** All 12 `\includegraphics` resolved
- **Output:** `build_p180/main.pdf` (3,090,418 bytes, 14 pages, US letter)
- **Aux files:** `main.aux` (22 KB), `main.bbl` (8 KB), `main.out` (8 KB)

## 4. Warning Analysis (Overfull Hboxes)

| Line Range | Severity | Overfull | Section | Root Cause |
|------------|----------|----------|---------|------------|
| 295–306 | Low | 16.75pt | VII.A (table env) | 6-col table in narrow column |
| 323–341 | **High** | **80.29pt** | III.B (Dynamic SLAM) | Long citation paragraph in 2-col |
| 348–365 | **High** | **80.29pt** | III.B/C | Long citation paragraph in 2-col |
| 412–434 | Medium | 40.27pt | III.C (Long-Term) | Citation-heavy paragraph |
| 515–526 | Medium | 29.35pt | VII.F | Dense text in narrow column |
| 553–566 | Low | 17.39pt | VII.G | Table/paragraph boundary |

### Root Cause for 80pt Overfulls

IEEEtran two-column format has ~252pt column width. Citation-heavy paragraphs in Related Work (III.B, III.C) contain multiple `\cite{...}` entries within single sentences, creating inline boxes that TeX cannot hyphenate. The 80pt overflows push text into the inter-column gutter or margin.

### Fix Difficulty

- **Easy fix:** Add `\linebreak` or re-break long sentences — but this requires rewriting the affected paragraphs and risks introducing new underfull hboxes.
- **Recommended:** Final copyediting pass on III.B and III.C once the submission PDF is close to final. The overfull is cosmetic (text bleeds into margin by ~7mm at 80pt) but does not affect readability of the full-width broader column.

## 5. Recommendation

**The manuscript is compile-ready.** Overfull hboxes are cosmetic and typical for citation-dense IEEEtran submissions. The 80pt hboxes in III.B/III.C should be addressed in final copyediting but are not a submission blocker.

## 6. Next Steps

1. Copy `build_p180/main.pdf` to a distribution path for preview
2. Human copyediting pass on III.B and III.C long paragraphs
3. Figure 300dpi regeneration
4. EXIF strip + PDF metadata anonymization
5. Final `tectonic` re-compile after copyediting
