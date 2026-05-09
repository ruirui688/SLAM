# PDF Layout Audit — P182

**Date:** 2026-05-10
**Target:** `paper/tro_submission/main.pdf`
**Render artifacts:** `paper/tro_submission/layout_audit_p182/`
**Status:** PASS WITH COSMETIC WARNINGS

## Summary

P182 performed a page-level audit of the compiled T-RO PDF using `pdfinfo`,
`pdftotext`, `pdftoppm`, and Tectonic recompilation.

The initial P182 attempt exposed a real ordering defect: references appeared
before pending figure floats, so the final pages contained main-body figures
after the bibliography. This was fixed by replacing the bibliography preamble
with:

```tex
\clearpage
\balance
\bibliographystyle{IEEEtran}
\bibliography{references}
```

After recompilation, the PDF has 15 pages, all figures render, references are
last, and metadata remains double-anonymous.

## PDF Metadata

| Field | Result |
|---|---|
| Pages | 15 |
| Page size | US Letter, 612 x 792 pt |
| Author metadata | Empty |
| Custom metadata | None |
| JavaScript | None |
| Encryption | None |
| File size | 3.09 MB |

## Page-Level Verdict

| Page | Content | Verdict |
|---:|---|---|
| 1 | Title, abstract, introduction | PASS |
| 2 | Related work / method | PASS |
| 3 | Method / protocol | PASS |
| 4 | Results, Table 1-3 | PASS |
| 5 | Hallway and backend tables | PASS |
| 6 | Dynamic SLAM results | PASS |
| 7 | Admission defense / discussion | PASS |
| 8 | Limitations and conclusion | PASS |
| 9 | Figure/table evidence page | PASS; dense but readable |
| 10 | Protocol overview figure | PASS |
| 11 | Hallway composite figure | PASS |
| 12 | Dynamic SLAM figure group | PASS |
| 13 | Map composition figure | PASS; sparse float page but acceptable |
| 14 | Decision-space figure | PASS |
| 15 | References | PASS; references are now last |

## Warning Map

Tectonic compiles with 0 errors. Remaining warnings are hbox warnings:

- Overfull table warnings at the 6-column tables in §VII.
- Underfull paragraph warnings in dense IEEEtran two-column text.
- No unresolved citations or unresolved references were observed.

These are cosmetic layout warnings, not content or build blockers. The rendered
pages show no missing figures, blank pages, or post-reference main-body content.

## Stale-Claim Scan

`pdftotext` checks found no hits for:

- `TODO`
- `PLACEHOLDER`
- `35 sessions`
- `28 PASS`
- `2 WARN`
- author-identifying name strings

## Deliverables

- `paper/tro_submission/main.pdf`
- `paper/tro_submission/build_p180/main.pdf`
- `paper/tro_submission/layout_audit_p182/page-01.png` through `page-15.png`
- `paper/tro_submission/layout_audit_p182/pdfinfo.txt`
- `paper/tro_submission/layout_audit_p182/main.txt`

## Remaining Human Check

Before final submission, visually skim pages 9, 12, and 13 in a PDF viewer.
They are float-heavy pages; the current render is acceptable, but those pages
are where a human reviewer will most easily notice figure density or excess
white space.
