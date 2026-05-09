# Build Notes — T-RO LaTeX Scaffold

## BLOCKER: No LaTeX on This Host

This machine does not have `pdflatex`, `latexmk`, `bibtex`, `kpsewhich`, or
any TeX Live installation. **The scaffold will not compile locally** in its
current state.

```bash
$ which pdflatex || echo "NOT FOUND"
# NOT FOUND

$ which latexmk || echo "NOT FOUND"
# NOT FOUND

$ kpsewhich IEEEtran.cls || echo "NOT FOUND"
# NOT FOUND
```

## Compile Options (Do Not Install Now)

1. **Overleaf (recommended for draft iterations):**
   - Upload the entire `paper/tro_submission/` directory to an Overleaf project.
   - Select `IEEEtran` as the document class (Overleaf provides it by default).
   - Set compiler to `pdfLaTeX` (NOT XeLaTeX or LuaLaTeX for IEEEtran).
   - `references.bib` will be auto-processed by Overleaf's BibTeX backend.

2. **Local TeX Live (after explicit user approval):**
   ```bash
   sudo apt install texlive-full   # ~6 GB — user approval required
   # OR minimal:
   sudo apt install texlive-base texlive-latex-recommended texlive-latex-extra
   ```
   The minimal install is sufficient for IEEEtran + basic journal compilation.

3. **Docker (alternative):**
   ```bash
   docker run --rm -v $(pwd):/workdir -w /workdir texlive/texlive:latest \
     pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
   ```

## Expected Compile Sequence

```bash
cd paper/tro_submission/
pdflatex main.tex    # first pass: figure/table placeholders, citation keys
bibtex main           # resolve \cite{} → BibTeX entries
pdflatex main.tex    # second pass: bibliography insertion
pdflatex main.tex    # third pass: cross-reference stabilization
```

Or with `latexmk`:
```bash
latexmk -pdf main.tex
```

## Known Issues to Fix Before First Real Compile

- Figure file paths: the `main.tex` skeleton uses `../figures/<file>.png`
  relative paths. Overleaf will need adjusted paths or symlinks.
- IEEEtran figure sizing: `.png` exports from Python pipelines are high-DPI;
  scaling with `\includegraphics[width=\columnwidth]{...}` should be adjusted.
- Bibliography style: currently `\bibliographystyle{IEEEtran}`; verify with
  IEEE T-RO author guidelines for any custom `.bst` requirement.
- Double-column figure placement: `figure*` (wide) vs `figure` (column-width)
  needs per-figure tuning after real content is filled in.
- `\today` in the blind header placeholder should be removed before final
  submission — T-RO does not use submission-date headers.
