# T-RO Submission Directory

**Target Venue:** IEEE Transactions on Robotics (T-RO)  
**Submission Type:** Regular Paper  
**Template:** IEEEtran.cls (V1.8, 2015/08/26)  
**Page Budget:** ≤20 pages (mandatory overlength charge >12 pages)  
**Review Policy:** Double-anonymous (initial submission — no author block)

## Directory Structure

```
paper/tro_submission/
├── README.md           ← This file
├── main.tex            ← LaTeX scaffold with section placeholders
├── references.bib      ← BibTeX entries for current 11 refs + expansion slots
├── FIGURE_PLAN.md      ← Which figures go where in 2-column layout
├── BUILD_NOTES.md      ← Build environment, blocker status, workarounds
├── figures/            ← Symlinks or copies of paper/figures/*.png
├── main.pdf            ← Compiled output (when build succeeds)
└── supplementary/      ← Supplementary material (P163)
```

## Current Claim Status

P224 synchronized the T-RO manuscript path with the current P217-P220
dataset-mask-supervised dynamic/non-static front-end route. `abstract.tex` and
`main.tex` now include the dataset construction, compact CUDA mask-model
metrics, held-out mask-quality metrics, ORB feature-level dynamic-region
suppression proxy, and explicit boundaries: no learned admission-control claim
and no P217-P220 ATE/RPE or trajectory-improvement claim.

## Conversion Checklist

- [ ] `main.tex` scaffold with correct \documentclass and all sections
- [ ] All 10 core figures placed (Figs 1-10 in Results; Figs 11,13 in §VII.G; Figs 12,14-16 in supplement)
- [ ] 6 table floats placed (Tables 1-6)
- [ ] All 35 references in references.bib (BibTeX format, DOI-verified; 7 supplementary-only)
- [ ] Double-anonymous: \author{} block stripped, self-citations anonymized
- [ ] Overlength page-count audit (target ≤18 pages)
- [ ] Figure/table/equation cross-references using \label/\ref
- [ ] LaTeX compilation succeeds (requires texlive + IEEEtran.cls)

## Quick Start

```bash
# Install dependencies (if not present):
# sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra

# Compile:
cd paper/tro_submission
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Or single-pass:
latexmk -pdf main.tex
```

## Reference: T-RO Author Guidelines

- **Page limit:** 20 pages for regular papers. Pages 13-20 incur mandatory overlength charges.
- **Format:** Two-column IEEE Transactions format.
- **Review:** Double-anonymous for initial submission.
- **Submission:** IEEE PaperCept (https://ras.papercept.net/).
- **ORCID:** Required for all authors.
- **Data availability:** Encouraged but not mandatory (optional data availability statement).
