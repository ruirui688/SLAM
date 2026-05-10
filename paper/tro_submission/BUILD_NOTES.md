# BUILD_NOTES.md — T-RO LaTeX Build Environment

**Date:** 2026-05-09  
**Status:** ⚠️ LaTeX unavailable on build host — scaffold-only

## Current Environment

```
Host: ubuntu (x64)
LaTeX: NOT INSTALLED
  - pdflatex: not found
  - tectonic: not found
  - texlive-latex-base: not installed
  - IEEEtran.cls: not available locally
```

## Blocker Record

**Blocker ID:** BLOCKER-TRO-LATEX-001  
**Severity:** Non-blocking for scaffold phase (P161). Must be resolved before P161 completion or delegated to P161b.  
**Description:** `pdflatex` and `IEEEtran.cls` are not available on the build host. The `main.tex` scaffold is syntactically complete but cannot be compiled.  
**Resolution options:**
1. Install texlive on build host: `sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra` (requires root, ~500 MB)
2. Use a minimal TeX distribution: `tectonic` (single-binary, ~30 MB, downloads packages on-demand)
3. Use Overleaf for compilation while keeping source in git (recommended for collaboration)
4. Delegate compilation to a separate machine with LaTeX installed

**Recommendation:** Option 3 (Overleaf) is the pragmatic path for advisor collaboration. The git repo remains the source of truth; Overleaf syncs via git or manual upload.

## Build Commands (when LaTeX is available)

```bash
cd <repo-root>/paper/tro_submission

# Option A: traditional pdflatex + bibtex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Option B: latexmk (recommended, handles cross-refs and bibtex automatically)
latexmk -pdf main.tex

# Option C: tectonic (single pass, auto-downloads packages)
tectonic main.tex
```

## Dependency Checklist

- [ ] IEEEtran.cls (IEEE Transactions class file, v1.8)
- [ ] graphicx (included in texlive-latex-recommended)
- [ ] amsmath, amssymb (included in texlive-latex-recommended)
- [ ] booktabs (included in texlive-latex-recommended)
- [ ] multirow (included in texlive-latex-recommended)
- [ ] hyperref (included in texlive-latex-recommended)
- [ ] cite (included in texlive-latex-base)
- [ ] xcolor (included in texlive-latex-recommended)
- [ ] balance (included in texlive-latex-extra)

All packages are standard IEEEtran dependencies. No exotic packages are required.

## Known Issues

1. **IEEEtran.cls not bundled.** IEEEtran is distributed with texlive but may need explicit installation: `tlmgr install ieeetran` (if using TeX Live). Overleaf includes it by default.
2. **Figure paths.** All `\includegraphics` paths in `main.tex` are relative to `paper/tro_submission/figures/`. PNG files must be copied or symlinked from `paper/figures/`.
3. **Double-anonymous mode.** The `\author{}` block is empty. Self-citations use `\cite{...}` with no author-year formatting that would reveal identity. The acknowledgments section is removed.
4. **Abstract as separate file.** `main.tex` uses `\input{abstract}` to keep the abstract in a separate file for easier reuse. Create `abstract.tex` in this directory, or replace `\input{abstract}` with inline abstract text.

## Rebuild Triggers

Regenerate the full T-RO PDF after:
- P164: Related work expansion (new references → new citations in text)
- Any manuscript content changes
- Figure regeneration at 300 dpi

## Supplementary Material (P163)

Supplementary material should be a separate PDF. Options:
- Create `supplementary.tex` using `\documentclass{article}` and the same IEEEtran bibliography style
- Or assemble a portable supplementary package with figures and tables in a self-contained document
