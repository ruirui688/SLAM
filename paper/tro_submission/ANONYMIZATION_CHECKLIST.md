# Anonymization Checklist — T-RO Double-Anonymous Review

**Manuscript:** Session-Level Map Admission Control for Semantic-Segmentation-Assisted SLAM in Dynamic Industrial Environments  
**Review policy:** Double-anonymous (initial T-RO submission)  
**Date:** 2026-05-09 (P162)  
**Status:** Pre-submission verification — pending author review

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
| 3.2 | No institution logos/watermarks in figures | ⚠️ | PENDING: Review all 16 figures for watermarks, timestamps, or path strings that could reveal identity |
| 3.3 | No photographer/camera metadata in figure EXIF | ⚠️ | PENDING: Strip EXIF from all PNG files before submission |
| 3.4 | No institution names in table headers/footers | ✅ | |
| 3.5 | No personal file paths visible in figures | ⚠️ | Figures generated from `/home/rui/slam/` — check if path strings appear in any figure |

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
| 5.1 | GitHub repository links removed or anonymized | ⚠️ | PENDING: Either remove repo URLs or create anonymous mirror for review |
| 5.2 | If code promised in "Open-source release" contribution, stated as "will be released upon acceptance" | ⚠️ | Update Contribution #5 wording to use conditional future tense |
| 5.3 | TorWIC dataset citation is to Barath et al. (published) | ✅ | Third-party dataset, no anonymization issue |
| 5.4 | No personal API keys or access tokens in supplementary data | ⚠️ | PENDING: Audit supplementary JSON/CSV files |

### 6. PDF Metadata

| # | Check | Status | Notes |
|---|---|---|---|
| 6.1 | PDF author field is empty | ⚠️ | PENDING: Cannot verify until LaTeX compilation; `\hypersetup{pdfauthor={}}` configured in preamble |
| 6.2 | PDF title does not contain author clues | ✅ | Generic title, no author-identifying terms |
| 6.3 | PDF subject/keywords are generic | ✅ | "SLAM, semantic segmentation, dynamic object filtering..." |
| 6.4 | PDF producer/creator fields do not reveal identity | ⚠️ | PENDING: pdflatex includes texlive version; acceptable |

### 7. Supplementary Material

| # | Check | Status | Notes |
|---|---|---|---|
| 7.1 | Supplementary PDF has no author block | ✅ | `supplement.md` has no author identification |
| 7.2 | Supplementary figures use same anonymization rules | ⚠️ | Same PENDING items as main figures (watermarks, EXIF, path strings) |
| 7.3 | Supplementary data files (JSON) contain no personal paths | ⚠️ | PENDING: Audit JSON files for `/home/rui/` paths or similar |

---

## Risk Assessment

### Low Risk ✅ (Already addressed)
- Author block empty
- No acknowledgments
- Third-person self-citations
- IEEE numeric style avoids author-year disclosure

### Medium Risk ⚠️ (Pending verification)
- Figure EXIF metadata (strip before submission)
- Figure path strings (check all 16 figures)
- GitHub repo URL in Contribution #5 (update wording)
- Supplementary JSON file paths

### No Risk ✅ (Not applicable)
- Funding disclosure (none)
- Institutional ethics (not applicable)
- Lab/group name (not mentioned)
- Proprietary system names (not used)

---

## Pre-Submission Action Items

| # | Action | Priority | Owner |
|---|---|---|---|
| A1 | Strip EXIF metadata from all 16 figures + 11 supplementary figures | HIGH | Author |
| A2 | Review all figures for embedded path strings or watermarks | HIGH | Author |
| A3 | Update Contribution #5 wording to "will be released upon acceptance" | HIGH | Author |
| A4 | Audit supplementary JSON/CSV files for personal paths | MEDIUM | Author |
| A5 | Create anonymous GitHub mirror (optional, only if repo URL is needed in manuscript) | MEDIUM | Author |
| A6 | After LaTeX compilation, verify PDF metadata (author field empty) | HIGH | Author |
| A7 | Remove any institutional or personal identifiers from README files in repository | LOW | Author |

---

## Self-Certification

I have reviewed this manuscript against IEEE T-RO's double-anonymous review policy and confirm that:

- [ ] All PENDING items above have been resolved
- [ ] The author block is empty
- [ ] Self-citations use third-person language
- [ ] No acknowledgments, funding, or institutional identifiers are present
- [ ] Figures contain no watermarks, EXIF data, or path strings
- [ ] Code references use conditional future tense or anonymous mirrors
- [ ] PDF metadata is clean

**Signature:** _________________ **Date:** _________________

---

*This checklist is based on IEEE T-RO's Author Guidelines for double-anonymous review. PENDING items must be resolved before submission. A second pair of eyes (co-author or advisor) should verify before final upload.*
