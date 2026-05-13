# P243 Interactive Independent Dynamic-Label Annotation Web Tool

## Purpose

`paper/export/independent_dynamic_label_web_p243.html` is a local, single-file HTML/JavaScript annotation tool for the 18-sample P239/P242 independent dynamic-label packet. It is designed for direct reviewer use: inspect the images, click labels, save progress in the browser, and export a filled CSV or JSON.

## How To Use

1. Open `paper/export/independent_dynamic_label_web_p243.html` locally in a browser from the repository checkout.
2. Review each sample using the raw image as primary evidence.
3. Use probability overlay, soft-mask overlay, and region crop only as context.
4. Fill the form fields for each sample. Progress is saved automatically to `localStorage`.
5. Use `Download filled CSV` when finished.
6. Save the exported CSV as the reviewer-completed label sheet, then run `tools/audit_interactive_dynamic_labels_p243.py` against that exported CSV before revisiting P195.

## Controls

- `Previous` / `Next`, `A` / `D`, or arrow keys move between samples.
- `1`, `2`, `3` set `dynamic_region_present` to `yes`, `no`, or `uncertain`.
- `S` saves the current sample.
- Click any image to open a larger preview.
- `Download filled CSV`, `Download JSON`, and `Copy CSV` export the current local labels.
- Paste or upload a previous CSV to restore labels.

## Claim Boundary

This tool does not create independent validation by itself. Model overlays are context only, not ground truth. Reviewers must not inspect admission labels while labeling. P195 remains `BLOCKED` until non-empty exported labels are audited for coverage, conflicts, and independence.
