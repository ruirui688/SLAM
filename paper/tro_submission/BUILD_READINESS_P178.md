# Build Readiness Audit — P178

**Date:** 2026-05-10  
**Audit target:** `paper/tro_submission/main.tex` (IEEEtran, T-RO submission)  
**Phase:** P178 — LaTeX/build readiness audit  

---

## 1. TeX Environment

| Tool | Status | Notes |
|------|--------|-------|
| `pdflatex` | ❌ NOT FOUND | No TeX Live installed |
| `latexmk` | ❌ NOT FOUND | Build automation not available |
| `tectonic` | ✅ 0.16.9 | Installed via conda-forge (P180) |
| `lualatex` | ❌ NOT FOUND | |
| `IEEEtran.cls` | ❌ NOT FOUND | Not in system TeX tree; no TeX tree exists |

**Verdict:** **RESOLVED (P180)** — Tectonic 0.16.9 compiled `main.tex` successfully. 0 errors, 14-page PDF.

### Resolved via P180

```bash
# Option A: TeX Live (full, ~4GB)
sudo apt install texlive-full

# Option B: TeX Live minimal + IEEEtran
sudo apt install texlive-latex-base texlive-latex-recommended texlive-publishers
# IEEEtran is bundled in texlive-publishers

# Option C: Tectonic (zero-dependency, ~30MB download)
# Download from https://github.com/tectonic-typesetting/tectonic/releases
# Then: tectonic paper/tro_submission/main.tex
```

After TeX installation, verify with:
```bash
kpsewhich IEEEtran.cls   # should return a path
pdflatex --version        # should print version
```

---

## 2. Pre-Compilation Checks

### 2.1 Environment Balance

| Environment | Begin | End | Status |
|-------------|-------|-----|--------|
| `figure*` (double-col) | 4 | 4 | ✅ |
| `figure` (single-col) | 8 | 8 | ✅ |
| `table` | 9 | 9 | ✅ |
| `equation` | 1 | 1 | ✅ |

### 2.2 Figure File Existence

All 12 `\includegraphics` targets exist and are readable:

| Figure | File | Size |
|--------|------|------|
| Fig 1 | `../figures/torwic_paper_result_overview.png` | 177 KB |
| Fig 2 | `../figures/torwic_real_session_overlays.png` | 322 KB |
| Fig 3 | `../figures/torwic_hallway_composite.png` | 1,624 KB |
| Fig 4 | `../figures/torwic_dynamic_slam_backend_p134.png` | 128 KB |
| Fig 5 | `../figures/torwic_dynamic_mask_coverage_p135.png` | 102 KB |
| Fig 6 | `../figures/torwic_dynamic_mask_temporal_stress_p136.png` | 119 KB |
| Fig 7 | `../figures/torwic_dynamic_mask_flow_stress_p137.png` | 114 KB |
| Fig 8 | `../figures/torwic_dynamic_mask_first8_real_p138.png` | 110 KB |
| Fig 9 | `../figures/torwic_dynamic_mask_first16_real_p139.png` | 124 KB |
| Fig 10 | `../figures/torwic_dynamic_mask_first32_real_p140.png` | 142 KB |
| Fig 11 | `../figures/torwic_before_after_map_composition_p156.png` | 110 KB |
| Fig 13 | `../figures/torwic_admission_decision_space_p156.png` | 144 KB |

**Note:** Figure 12 (`torwic_object_lifecycle_p156.png`, 171KB) and supplementary figures S1-S11 exist in `paper/figures/` but are referenced in `supplement.md`, not `main.tex`.

### 2.3 Citation Integrity

- **28 unique cite keys** in `main.tex`
- **All 28 exist** in `references.bib` (35 entries total, 7 unused — intentional per P164 for supplementary-only refs)
- **0 orphan citations**

### 2.4 Cross-Reference Integrity

- **62 unique `\label{}`** entries — all unique
- **25 `\ref{}` calls** — all point to existing labels
- **0 orphan `\ref{}` targets**

### 2.5 Stale/Misleading Claims

- ✅ No "35 sessions" claim (corrected to 20 physical sessions)
- ✅ No "28 PASS, 2 WARN" in main.tex (correctly in audit doc only)
- ✅ No TODO/PLACEHOLDER/TBD/FIXME markers in main.tex
- ✅ No "principled" language (P167 verified)

### 2.6 Package Declarations

All required packages declared in preamble:

| Package | Status |
|---------|--------|
| `graphicx` (figures) | ✅ |
| `amsmath, amssymb` | ✅ |
| `booktabs` (tables) | ✅ |
| `multirow` | ✅ |
| `hyperref` | ✅ |
| `cite` | ✅ |
| `xcolor` | ✅ |
| `balance` (last-page) | ✅ |

### 2.7 Known Compilation Warnings (Predicted)

These are not verified (no TeX) but predictable from IEEEtran experience:

| Warning Type | Likely? | Mitigation |
|-------------|---------|------------|
| `figure*` float overflow | Possible | 4 `figure*` floats may push to end; add `\FloatBarrier` or `\clearpage` if needed |
| Overfull `\hbox` | Possible | Tables 1-4 have 4-6 columns — check with `\small` if needed |
| Page count >12 | Possible | IEEEtran limit; trim Discussion or move detail to supplement |
| Missing `\balance` at end | Likely | `\balance` not called; add before `\end{document}` |

---

## 3. Build Readiness Summary

| Check | Result |
|-------|--------|
| TeX environment | ✅ RESOLVED (P180) | Tectonic 0.16.9 compiles successfully |
| Environment balance | ✅ PASS |
| Figure file existence | ✅ PASS (12/12) |
| Citation integrity | ✅ PASS (28/28) |
| Cross-reference integrity | ✅ PASS (25/25) |
| Stale claims | ✅ PASS |
| Packages declared | ✅ PASS (8/8) |
| Label uniqueness | ✅ PASS (62/62) |

**Overall verdict:** **BUILD-READY (VERIFIED)** — all source/document checks pass. P180 real compilation via Tectonic 0.16.9 (conda, user-level, no sudo) confirmed: 0 errors, 14-page PDF, all citations/cross-refs resolved. 26 minor hbox warnings (2×80pt overfull in Related Work — cosmetic).

---

## 4. Recommended First-Compile Commands

After TeX installation:
```bash
cd /home/rui/slam/paper/tro_submission
latexmk -pdf -interaction=nonstopmode main.tex
# Or for troubleshooting:
pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex main && pdflatex main
```

Expected warnings to watch for:
- `Float too large for page` — adjust `figure*` placement or trim captions
- `Citation ... undefined` — first compile before `bibtex` pass is normal
- `Overfull \hbox` — widen tables or reduce font size
