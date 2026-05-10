# Anonymization Checklist — T-RO Double-Anonymous Review

**Manuscript:** Session-Level Map Admission Control for Semantic-Segmentation-Assisted SLAM in Dynamic Industrial Environments
**Review policy:** Double-anonymous (initial T-RO submission)
**Date:** 2026-05-09 (P162); updated 2026-05-10 (P186)
**Status:** Pre-submission verification — automated metadata/path audit completed; final human upload review still required

---

## IEEE T-RO Double-Anonymous Requirements

IEEE T-RO uses double-anonymous review for initial submissions. Author identities must not be discoverable from the manuscript, figures, supplementary material, or metadata.

---

## Checklist

### 1. Title Page and Author Block

| # | Check | Status | Notes |
|---|---|---|---|
| 1.1 | Title page contains no author names | ✅ | `\author{}` is empty in `main.tex` |
| 1.2 | No affiliations | ✅ | |
| 1.3 | No email addresses | ✅ | |
| 1.4 | No ORCID identifiers | ✅ | |
| 1.5 | No acknowledgments/funding section | ✅ | Removed |
| 1.6 | No "Corresponding author" marker | ✅ | |

### 2. Self-Citations

| # | Check | Status | Notes |
|---|---|---|---|
| 2.1 | Self-citations use third-person language | ✅ | "Cadena et al. [1] presented..." not "In our previous work [1]..." |
| 2.2 | No "our previous work" phrasing | ✅ | Checked all citation contexts |
| 2.3 | No author-year references that reveal identity | ✅ | IEEE numeric citation style (`\cite{}`) |
| 2.4 | No arXiv preprint links that include author names | ✅ | arXiv IDs are numeric (e.g., 2303.05499), no author names in citation text |

### 3. Figure and Table Content

| # | Check | Status | Notes |
|---|---|---|---|
| 3.1 | No author names in figure captions | ✅ | All captions use descriptive labels |
| 3.2 | No institution logos/watermarks in figures | ✅ | P186 automated scan of 18 current `paper/figures/*.png` found no embedded text chunks, identity strings, local paths, emails, or repository usernames; final human visual skim still recommended before upload |
| 3.3 | No photographer/camera metadata in figure EXIF | ✅ | P186 PNG chunk audit found no `tEXt`, `iTXt`, `zTXt`, or `eXIf` chunks in 18 current paper figures |
| 3.4 | No institution names in table headers/footers | ✅ | |
| 3.5 | No personal file paths visible in figures | ✅ | P186 `strings` scan found no local path/email/repository-username strings in current paper figures |

### 4. Text Content

| # | Check | Status | Notes |
|---|---|---|---|
| 4.1 | No "we thank [colleague]" in text | ✅ | |
| 4.2 | No lab/group name disclosure | ✅ | |
| 4.3 | No grant numbers or funding sources | ✅ | |
| 4.4 | No institutional IRB/ethics approval numbers | N/A | Not applicable (no human/animal subjects) |
| 4.5 | No proprietary system names that identify institution | ⚠️ | Check for any internal project names or system identifiers |

### 5. Code and Data References

| # | Check | Status | Notes |
|---|---|---|---|
| 5.1 | GitHub repository links removed or anonymized | ⚠️ | Main/supplement do not expose the project repository URL; references include only third-party sources/tools. Create anonymous mirror only if code is uploaded for review |
| 5.2 | If code promised in "Open-source release" contribution, stated as "will be released upon acceptance" | ✅ | Current contribution wording is architecture-focused and no longer promises an identifiable repository release |
| 5.3 | TorWIC dataset citation is to Barath et al. (published) | ✅ | Third-party dataset, no anonymization issue |
| 5.4 | No personal API keys or credentials in supplementary data | ✅ | P186 text/data scan found no credential markers in tracked supplementary/evidence/export files |

### 6. PDF Metadata

| # | Check | Status | Notes |
|---|---|---|---|
| 6.1 | PDF author field is empty | ✅ | P186 `pdfinfo` on `paper/tro_submission/main.pdf` and `build_p180/main.pdf` shows no Author field; `\hypersetup{pdfauthor={}}` remains configured |
| 6.2 | PDF title does not contain author clues | ✅ | Generic title, no author-identifying terms |
| 6.3 | PDF subject/keywords are generic | ✅ | "SLAM, semantic segmentation, dynamic object filtering..." |
| 6.4 | PDF producer/creator fields do not reveal identity | ✅ | P186 `pdfinfo`: Creator `LaTeX with hyperref`, Producer `xdvipdfmx`; no custom metadata stream |

### 7. Supplementary Material

| # | Check | Status | Notes |
|---|---|---|---|
| 7.1 | Supplementary PDF has no author block | ✅ | `supplement.md` has no author identification |
| 7.2 | Supplementary figures use same anonymization rules | ✅ | P186 audit covers current shared `paper/figures/*.png` figure set used by main and supplementary materials |
| 7.3 | Supplementary data files (JSON) contain no personal paths | ✅ | P186 sanitized tracked local absolute-path occurrences in paper evidence/export/supplementary files to `<repo-root>` and re-scanned |

---

## Risk Assessment

### Low Risk ✅ (Already addressed)
- Author block empty
- No acknowledgments
- Third-person self-citations
- IEEE numeric style avoids author-year disclosure

### Medium Risk ⚠️ (Pending verification)
- Final human visual skim of figures before upload
- Optional anonymous code mirror if code is submitted during review

### No Risk ✅ (Not applicable)
- Funding disclosure (none)
- Institutional ethics (not applicable)
- Lab/group name (not mentioned)
- Proprietary system names (not used)

---

## Pre-Submission Action Items

| # | Action | Priority | Owner |
|---|---|---|---|
| A1 | Strip/verify EXIF metadata from current paper figures | DONE | P186 automated PNG chunk audit: no text/EXIF chunks in 18 current figures |
| A2 | Review all figures for embedded path strings or watermarks | DONE + HUMAN SKIM | P186 automated path/email/user scan passed; final human visual skim still recommended |
| A3 | Update Contribution #5 wording to avoid identifiable code-release promise | DONE | Current contribution wording is architecture-focused |
| A4 | Audit supplementary JSON/CSV files for personal paths | DONE | P186 sanitized local paths to `<repo-root>` and re-scanned |
| A5 | Create anonymous GitHub mirror (optional, only if repo URL is needed in manuscript) | OPTIONAL | Not required unless code is uploaded for review |
| A6 | After LaTeX compilation, verify PDF metadata (author field empty) | DONE | P186 `pdfinfo` verified no Author field in current PDFs |
| A7 | Remove any institutional or personal identifiers from README files in repository | LOW | Not part of the reviewer upload package; keep as repository hygiene before public release |

---

## Self-Certification

I have reviewed this manuscript against IEEE T-RO's double-anonymous review policy and confirm that:

- [x] All machine-checkable PENDING items above have been resolved or downgraded to explicit optional/human-review items
- [x] The author block is empty
- [x] Self-citations use third-person language
- [x] No acknowledgments, funding, or institutional identifiers are present
- [x] Figures contain no detected EXIF data, local path strings, emails, or repository usernames
- [x] Code references avoid identifiable project repository promises; anonymous mirror remains optional if code is uploaded
- [x] PDF metadata is clean in current compiled PDFs

**Signature:** _________________ **Date:** _________________

---

*This checklist is based on IEEE T-RO's Author Guidelines for double-anonymous review. PENDING items must be resolved before submission. A second pair of eyes (co-author or advisor) should verify before final upload.*
