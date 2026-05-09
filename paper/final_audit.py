#!/usr/bin/env python3
"""final_audit.py — P151: Final submission package audit across all dimensions."""

import os, re, json, subprocess
from pathlib import Path
from datetime import datetime

SLAM = Path("/home/rui/slam")
PAPER = SLAM / "paper"
OUTPUTS = SLAM / "outputs"
FIGURES = PAPER / "figures"
EXPORT = PAPER / "export"

results = {"timestamp": datetime.now().isoformat(), "checks": []}

def c(name, ok, detail=""):
    results["checks"].append({"check": name, "pass": ok, "detail": detail})
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("P151 Final Submission Package Audit")
print("=" * 60)

# 1. Manuscript presence
print("\n[1] Manuscript Files")
en_md = PAPER / "manuscript_en_thick.md"
zh_md = PAPER / "manuscript_zh_thick.md"
c("EN thick manuscript exists", en_md.exists(), f"{en_md.stat().st_size} bytes" if en_md.exists() else "MISSING")
c("ZH thick manuscript exists", zh_md.exists(), f"{zh_md.stat().st_size} bytes" if zh_md.exists() else "MISSING")

# 2. Line counts and section counts
if en_md.exists() and zh_md.exists():
    en_lines = len(en_md.read_text().split('\n'))
    zh_lines = len(zh_md.read_text().split('\n'))
    en_sections = len(re.findall(r'^#{1,3} ', en_md.read_text(), re.M))
    zh_sections = len(re.findall(r'^#{1,3} ', zh_md.read_text(), re.M))
    c("EN manuscript lines (~495)", 485 <= en_lines <= 510, f"{en_lines} lines")
    c("ZH manuscript lines (~490)", 485 <= zh_lines <= 510, f"{zh_lines} lines")
    c("EN sections (~47)", 44 <= en_sections <= 52, f"{en_sections} sections")
    c("ZH sections (~47)", 44 <= zh_sections <= 52, f"{zh_sections} sections")
    c("EN/ZH line parity", abs(en_lines - zh_lines) < 20, f"Δ={abs(en_lines-zh_lines)}")

# 3. Exports
print("\n[2] Export Files")
for f in ["manuscript_en_thick.html", "manuscript_en_thick.pdf", "manuscript_zh_thick.html", "manuscript_zh_thick.pdf", "build_log.json"]:
    p = EXPORT / f
    c(f"Export: {f}", p.exists(), f"{p.stat().st_size/1024:.0f} KB" if p.exists() else "MISSING")

# 4. Figures
print("\n[3] Figure Files")
fig_map = {
    "Fig.1": "torwic_paper_result_overview.png",
    "Fig.2": "torwic_real_session_overlays.png",
    "Fig.3": "torwic_hallway_composite.png",
    "Fig.4": "torwic_dynamic_slam_backend_p134.png",
    "Fig.5": "torwic_dynamic_mask_coverage_p135.png",
    "Fig.6": "torwic_dynamic_mask_temporal_stress_p136.png",
    "Fig.7": "torwic_dynamic_mask_flow_stress_p137.png",
    "Fig.8": "torwic_dynamic_mask_first8_real_p138.png",
    "Fig.9": "torwic_dynamic_mask_first16_real_p139.png",
    "Fig.10": "torwic_dynamic_mask_first32_real_p140.png",
}
all_fig_ok = True
for fig, fname in fig_map.items():
    p = FIGURES / fname
    ok = p.exists()
    if not ok: all_fig_ok = False
    c(f"  {fig} = {fname}", ok, f"{p.stat().st_size/1024:.0f} KB" if ok else "MISSING")
c("All 10 figures present", all_fig_ok)

# 5. Figure references in manuscript
print("\n[4] Figure Cross-References")
en_text = en_md.read_text()
all_fig_refs_ok = True
for i in range(1, 11):
    fig_ref = re.search(rf'(Fig\.?\s*{i}[^.]*\.|Fig\.?\s*{i}\b)', en_text)
    if fig_ref:
        c(f"  Fig.{i} in EN body", True, fig_ref.group(0)[:60])
    else:
        all_fig_refs_ok = False
        c(f"  Fig.{i} in EN body", False, "NOT FOUND in body")
c("All 10 figures referenced in EN body", all_fig_refs_ok)

# 6. Table references
print("\n[5] Table Cross-References")
all_tab_ok = True
for i in range(1, 7):
    tab_ref = re.search(rf'Table\s*{i}\b', en_text)
    c(f"  Table {i} in EN body", bool(tab_ref), tab_ref.group(0) if tab_ref else "NOT FOUND")
    if not tab_ref: all_tab_ok = False
c("All 6 tables referenced", all_tab_ok)

# 7. Citation completeness
print("\n[6] Citation Audit")
all_cite_ok = True
for i in range(1, 11):
    cite = re.search(rf'\[{i}\]', en_text)
    c(f"  [{i}] in EN body", bool(cite), cite.group(0) if cite else "NOT FOUND")
    if not cite: all_cite_ok = False
c("All [1]-[10] cited in body", all_cite_ok)

has_evo = re.search(r'\[S\]', en_text)
c("evo software ref [S] in body", bool(has_evo))

# 8. Reference list completeness
print("\n[7] Reference List Completeness")
refs_section = en_text.split("## References")[1].split("---")[0] if "## References" in en_text else ""
for i in range(1, 11):
    ref_entry = re.search(rf'^\[{i}\]', refs_section, re.M)
    c(f"  [{i}] entry in References", bool(ref_entry))
has_evo_entry = "Michael Grupp" in refs_section and "evo" in refs_section
c("evo entry in References", has_evo_entry)

# 9. Limitations
print("\n[8] Limitations Section")
lim_sec = en_text.split("## IX")[1].split("## X")[0] if "## IX" in en_text else ""
num_lims = len(re.findall(r'^\d+\.\s+', lim_sec, re.M))
c("Limitations section exists", bool(lim_sec), f"{num_lims} items" if lim_sec else "MISSING")
c("Limitation 6 (citations resolved)", bool(re.search(r'Back-end model.*provided|引用已补充', en_text)))

# 10. Dynamic SLAM chapter
print("\n[9] Dynamic SLAM Chapter (§VII.E-F)")
has_dslam_evidence = "Table 6" in en_text and "10 DROID-SLAM" in en_text
has_boundary = "boundary condition" in en_text.lower() and "5%" in en_text
has_negative = "negative-result" in en_text or "negative result" in en_text.lower()
c("Evidence chain (Table 6 + 10 configs)", has_dslam_evidence)
c("Boundary conditions (>5%)", has_boundary)
c("Negative-result framing", has_negative)
c("Cross-window audit (P143)", "cross-window" in en_text.lower())

# 11. Evidence files
print("\n[10] Evidence & Data Files")
ev_json = PAPER / "evidence" / "dynamic_slam_backend_metrics.json"
c("dynamic_slam_backend_metrics.json", ev_json.exists())
dslam_dirs = list(OUTPUTS.glob("*dynamic_slam_backend_smoke*"))
c("Dynamic SLAM backend dirs", len(dslam_dirs) >= 10, f"{len(dslam_dirs)} directories")

# 12. Package docs
print("\n[11] Package Documentation")
pkg_v10 = OUTPUTS / "torwic_submission_ready_package_index_v10.md"
checklist = OUTPUTS / "torwic_submission_readiness_checklist_v1.md"
c("Package index v10", pkg_v10.exists())
c("Submission checklist v1", checklist.exists())

# 13. Build script
print("\n[12] Build Script")
build_py = PAPER / "build_paper.py"
c("build_paper.py exists", build_py.exists())
c("build_paper.py has 'weasyprint'", "weasyprint" in build_py.read_text() if build_py.exists() else False)

# 14. Bilingual consistency
print("\n[13] Bilingual Consistency Checks")
zh_text = zh_md.read_text()
key_sections = [
    ("Grounding DINO cited in ZH", r"Grounding DINO \[7\]"),
    ("SAM2 cited in ZH", r"SAM2 \[8\]"),
    ("OpenCLIP cited in ZH", r"OpenCLIP \[9\]"),
    ("DROID-SLAM cited in ZH", r"DROID-SLAM \[10\]"),
    ("evo cited in ZH", r"\[S\]"),
    ("§VII.F in ZH", r"七\.[EF]"),
    ("§X Conclusion in ZH", r"## 十"),
    ("Appendix in ZH", r"## 附录"),
]
for name, pat in key_sections:
    match = re.search(pat, zh_text)
    c(f"  {name}", bool(match), match.group(0)[:40] if match else "MISSING")

# 15. README coverage
print("\n[14] README Completeness")
readme = (SLAM / "README.md").read_text()
phases_doc = ["P148", "P149", "P150"]
for p in phases_doc:
    c(f"  {p} in README", p in readme)

# 16. No placeholders/TODOs
print("\n[15] Placeholder/TODO Scan")
todos = re.findall(r'(TODO|FIXME|XXX|PLACEHOLDER)', en_text)
c("No TODOs/FIXMEs in EN manuscript", len(todos) == 0, f"{len(todos)} found: {todos}" if todos else "none")

# Summary
total = len(results["checks"])
passed = sum(1 for ch in results["checks"] if ch["pass"])
results["total"] = total
results["passed"] = passed
results["failed"] = total - passed

print(f"\n{'='*60}")
print(f"FINAL: {passed}/{total} checks passed ({100*passed/total:.0f}%)")
print(f"{'='*60}")

with open(EXPORT / "final_audit_p151.json", 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nAudit report: {EXPORT / 'final_audit_p151.json'}")
