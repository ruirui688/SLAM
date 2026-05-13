#!/usr/bin/env python3
"""Build a local interactive annotation web tool for the P242 review template."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "paper/evidence/independent_dynamic_label_review_template_p242.csv"
OUTPUT_HTML = ROOT / "paper/export/independent_dynamic_label_web_p243.html"
DOC_MD = ROOT / "paper/export/interactive_annotation_web_p243.md"

LABEL_FIELDS = [
    "dynamic_region_present",
    "dynamic_region_type",
    "boundary_quality",
    "false_positive_region",
    "false_negative_region",
    "label_confidence",
    "reviewer_id",
    "reviewed_at_utc",
    "reviewer_notes",
]

CSV_FIELDS = [
    "packet_id",
    "window_id",
    "source_phase",
    "sequence_label",
    "sequence_family",
    "source_window_start_index",
    "frame_index",
    "source_frame_index",
    "timestamp",
    "selection_reason",
    "raw_image",
    "probability_overlay",
    "soft_mask_overlay",
    "region_crop",
    "model_context_note",
    "admission_label_visibility",
] + LABEL_FIELDS


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def rel_from_export(path_text: str) -> str:
    return os.path.relpath(ROOT / path_text, ROOT / "paper/export")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 18:
        raise ValueError(f"expected 18 rows, found {len(rows)}")
    for row in rows:
        for field in LABEL_FIELDS:
            if row.get(field, "").strip():
                raise ValueError(f"{row.get('packet_id')} has non-empty label field {field}")
        for field in ["raw_image", "probability_overlay", "soft_mask_overlay", "region_crop"]:
            if not (ROOT / row[field]).exists():
                raise FileNotFoundError(f"{row.get('packet_id')} missing {field}: {row[field]}")


def web_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in rows:
        item = {field: row.get(field, "") for field in CSV_FIELDS}
        item["images"] = {
            "raw": rel_from_export(row["raw_image"]),
            "probability": rel_from_export(row["probability_overlay"]),
            "soft_mask": rel_from_export(row["soft_mask_overlay"]),
            "crop": rel_from_export(row["region_crop"]),
        }
        items.append(item)
    return items


def write_html(path: Path, rows: list[dict[str, str]]) -> None:
    samples_json = json.dumps(web_rows(rows), ensure_ascii=False)
    csv_fields_json = json.dumps(CSV_FIELDS)
    label_fields_json = json.dumps(LABEL_FIELDS)
    text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>P243 Independent Dynamic-Label Annotation Tool</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #18212f;
      --muted: #5f6b7a;
      --line: #d7dee8;
      --accent: #2358a6;
      --accent-soft: #e8f0fe;
      --danger: #9f1d1d;
      --ok: #1f7a4d;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--ink); }}
    header {{ position: sticky; top: 0; z-index: 20; background: var(--panel); border-bottom: 1px solid var(--line); padding: 12px 18px; }}
    h1 {{ font-size: 20px; margin: 0 0 8px; }}
    button, select, input, textarea {{ font: inherit; }}
    button {{ border: 1px solid var(--line); background: var(--panel); color: var(--ink); padding: 8px 10px; cursor: pointer; }}
    button:hover {{ border-color: var(--accent); }}
    button.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    button.selected {{ background: var(--accent-soft); border-color: var(--accent); color: #123c78; }}
    .topbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }}
    .notice {{ color: var(--danger); font-size: 13px; margin-top: 8px; max-width: 1200px; }}
    .layout {{ display: grid; grid-template-columns: 260px minmax(0, 1fr) 360px; min-height: calc(100vh - 94px); }}
    aside, main, section.formpanel {{ padding: 16px; }}
    aside {{ border-right: 1px solid var(--line); background: #fbfcfd; overflow-y: auto; max-height: calc(100vh - 94px); }}
    .sample-list {{ display: flex; flex-direction: column; gap: 8px; }}
    .sample-item {{ text-align: left; border-radius: 4px; padding: 9px; line-height: 1.3; }}
    .sample-item.reviewed {{ border-left: 4px solid var(--ok); }}
    .sample-item.active {{ border-color: var(--accent); background: var(--accent-soft); }}
    .sample-meta {{ color: var(--muted); font-size: 12px; }}
    main {{ overflow-y: auto; max-height: calc(100vh - 94px); }}
    .viewer-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 12px; }}
    .viewer-head h2 {{ margin: 0; font-size: 18px; }}
    .metadata {{ color: var(--muted); font-size: 13px; margin-top: 5px; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
    .image-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .image-card {{ background: var(--panel); border: 1px solid var(--line); padding: 8px; }}
    .image-card.hidden {{ display: none; }}
    .image-card h3 {{ margin: 0 0 8px; font-size: 14px; }}
    .image-card img {{ width: 100%; max-height: 46vh; object-fit: contain; display: block; background: #111; cursor: zoom-in; }}
    .hint {{ color: var(--muted); font-size: 12px; margin-top: 6px; }}
    .formpanel {{ border-left: 1px solid var(--line); background: #fbfcfd; overflow-y: auto; max-height: calc(100vh - 94px); }}
    .field {{ background: var(--panel); border: 1px solid var(--line); padding: 10px; margin-bottom: 10px; }}
    .field label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
    .choices {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .field input[type="text"], .field textarea {{ width: 100%; border: 1px solid var(--line); padding: 8px; }}
    .field textarea {{ min-height: 86px; resize: vertical; }}
    .actions {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }}
    .import-box {{ width: 100%; min-height: 120px; border: 1px solid var(--line); padding: 8px; }}
    dialog {{ border: 0; padding: 0; max-width: 96vw; max-height: 96vh; background: #000; }}
    dialog img {{ max-width: 96vw; max-height: 90vh; display: block; }}
    dialog form {{ text-align: right; background: #111; padding: 8px; }}
    dialog button {{ color: #fff; background: #222; border-color: #555; }}
    .small {{ font-size: 12px; color: var(--muted); }}
    @media (max-width: 1080px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside, main, section.formpanel {{ max-height: none; border: 0; }}
      .image-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>P243 Independent Dynamic-Label Annotation Tool</h1>
    <div class="topbar">
      <button id="prevBtn">Previous</button>
      <button id="nextBtn">Next</button>
      <span id="progressText"></span>
      <button id="downloadCsvBtn" class="primary">Download filled CSV</button>
      <button id="downloadJsonBtn">Download JSON</button>
      <button id="copyCsvBtn">Copy CSV</button>
      <button id="clearBtn">Clear local labels</button>
    </div>
    <div class="notice">Model overlays are context only, not ground truth. Do not inspect admission labels. P195 remains BLOCKED until non-empty exported labels are audited for coverage, conflicts, and independence.</div>
  </header>
  <div class="layout">
    <aside>
      <strong>Samples</strong>
      <div class="small">Reviewed means required fields have values.</div>
      <div id="sampleList" class="sample-list"></div>
    </aside>
    <main>
      <div class="viewer-head">
        <div>
          <h2 id="sampleTitle"></h2>
          <div id="sampleMeta" class="metadata"></div>
        </div>
        <div class="small">Keys: A/D or ArrowLeft/Right navigate; 1/2/3 set present yes/no/uncertain; S saves current.</div>
      </div>
      <div class="tabs">
        <button class="tab selected" data-view="all">All</button>
        <button class="tab" data-view="raw">Raw</button>
        <button class="tab" data-view="probability">Probability</button>
        <button class="tab" data-view="soft_mask">Soft mask</button>
        <button class="tab" data-view="crop">Crop</button>
      </div>
      <div id="imageGrid" class="image-grid"></div>
    </main>
    <section class="formpanel">
      <div class="actions">
        <button id="saveBtn" class="primary">Save current</button>
        <button id="markTimeBtn">Set reviewed time</button>
      </div>
      <div class="field">
        <label>reviewer_id</label>
        <input id="reviewer_id" type="text" autocomplete="off">
      </div>
      <div class="field">
        <label>dynamic_region_present</label>
        <div class="choices" data-field="dynamic_region_present" data-values="yes,no,uncertain"></div>
      </div>
      <div class="field">
        <label>dynamic_region_type</label>
        <div class="choices" data-field="dynamic_region_type" data-values="moving_object,static_structure,reflection,shadow,unknown,not_applicable"></div>
      </div>
      <div class="field">
        <label>boundary_quality</label>
        <div class="choices" data-field="boundary_quality" data-values="good,acceptable,poor,not_applicable"></div>
      </div>
      <div class="field">
        <label>false_positive_region</label>
        <div class="choices" data-field="false_positive_region" data-values="yes,no,uncertain"></div>
      </div>
      <div class="field">
        <label>false_negative_region</label>
        <div class="choices" data-field="false_negative_region" data-values="yes,no,uncertain"></div>
      </div>
      <div class="field">
        <label>label_confidence</label>
        <div class="choices" data-field="label_confidence" data-values="high,medium,low"></div>
      </div>
      <div class="field">
        <label>reviewed_at_utc</label>
        <input id="reviewed_at_utc" type="text" autocomplete="off">
      </div>
      <div class="field">
        <label>reviewer_notes</label>
        <textarea id="reviewer_notes"></textarea>
      </div>
      <div class="field">
        <label>Import existing CSV</label>
        <textarea id="importText" class="import-box" placeholder="Paste exported CSV here"></textarea>
        <div class="actions" style="margin-top:8px">
          <button id="importBtn">Import pasted CSV</button>
          <button id="fileImportBtn">Upload CSV</button>
        </div>
        <input id="fileInput" type="file" accept=".csv,text/csv" style="display:none">
      </div>
    </section>
  </div>
  <dialog id="zoomDialog">
    <img id="zoomImage" alt="Zoomed image">
    <form method="dialog"><button>Close</button></form>
  </dialog>
  <script>
    const SAMPLES = {samples_json};
    const CSV_FIELDS = {csv_fields_json};
    const LABEL_FIELDS = {label_fields_json};
    const STORAGE_KEY = 'p243_independent_dynamic_labels_v1';
    let currentIndex = 0;
    let currentView = 'all';
    let annotations = loadAnnotations();

    function defaultAnnotation() {{
      return {{
        dynamic_region_present: '',
        dynamic_region_type: '',
        boundary_quality: '',
        false_positive_region: '',
        false_negative_region: '',
        label_confidence: '',
        reviewer_id: '',
        reviewed_at_utc: '',
        reviewer_notes: ''
      }};
    }}

    function loadAnnotations() {{
      try {{
        const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
        return parsed && typeof parsed === 'object' ? parsed : {{}};
      }} catch (err) {{
        return {{}};
      }}
    }}

    function saveAnnotations() {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(annotations));
      renderList();
      updateProgress();
    }}

    function annotationFor(sample) {{
      if (!annotations[sample.packet_id]) annotations[sample.packet_id] = defaultAnnotation();
      return annotations[sample.packet_id];
    }}

    function isReviewed(sample) {{
      const a = annotationFor(sample);
      return Boolean(a.dynamic_region_present && a.boundary_quality && a.label_confidence && a.reviewer_id && a.reviewed_at_utc);
    }}

    function updateProgress() {{
      const reviewed = SAMPLES.filter(isReviewed).length;
      document.getElementById('progressText').textContent = `${{reviewed}} / ${{SAMPLES.length}} reviewed`;
    }}

    function renderChoices() {{
      document.querySelectorAll('.choices').forEach(box => {{
        box.innerHTML = '';
        box.dataset.values.split(',').forEach(value => {{
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.textContent = value;
          btn.dataset.value = value;
          btn.addEventListener('click', () => {{
            const sample = SAMPLES[currentIndex];
            annotationFor(sample)[box.dataset.field] = value;
            saveAnnotations();
            renderForm();
          }});
          box.appendChild(btn);
        }});
      }});
    }}

    function renderList() {{
      const list = document.getElementById('sampleList');
      list.innerHTML = '';
      SAMPLES.forEach((sample, idx) => {{
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'sample-item';
        if (idx === currentIndex) btn.classList.add('active');
        if (isReviewed(sample)) btn.classList.add('reviewed');
        btn.innerHTML = `<strong>${{idx + 1}}. ${{escapeHtml(sample.packet_id)}}</strong><div class="sample-meta">${{escapeHtml(sample.window_id)}} | frame ${{escapeHtml(sample.source_frame_index)}}</div>`;
        btn.addEventListener('click', () => {{ saveCurrentForm(); currentIndex = idx; render(); }});
        list.appendChild(btn);
      }});
    }}

    function renderViewer() {{
      const sample = SAMPLES[currentIndex];
      document.getElementById('sampleTitle').textContent = sample.packet_id;
      document.getElementById('sampleMeta').textContent = `${{sample.sequence_label}} | ${{sample.window_id}} | source frame ${{sample.source_frame_index}} | ${{sample.selection_reason}}`;
      const grid = document.getElementById('imageGrid');
      grid.innerHTML = '';
      const entries = [
        ['raw', 'Raw image'],
        ['probability', 'Probability overlay context'],
        ['soft_mask', 'Soft mask overlay context'],
        ['crop', 'Region crop']
      ];
      entries.forEach(([key, label]) => {{
        const card = document.createElement('div');
        card.className = 'image-card';
        if (currentView !== 'all' && currentView !== key) card.classList.add('hidden');
        const img = document.createElement('img');
        img.src = sample.images[key];
        img.alt = label;
        img.addEventListener('click', () => zoomImage(img.src));
        card.innerHTML = `<h3>${{escapeHtml(label)}}</h3>`;
        card.appendChild(img);
        const hint = document.createElement('div');
        hint.className = 'hint';
        hint.textContent = key === 'raw' ? 'Primary evidence' : 'Context only, not ground truth';
        card.appendChild(hint);
        grid.appendChild(card);
      }});
    }}

    function renderForm() {{
      const sample = SAMPLES[currentIndex];
      const a = annotationFor(sample);
      document.getElementById('reviewer_id').value = a.reviewer_id || '';
      document.getElementById('reviewed_at_utc').value = a.reviewed_at_utc || '';
      document.getElementById('reviewer_notes').value = a.reviewer_notes || '';
      document.querySelectorAll('.choices').forEach(box => {{
        const selected = a[box.dataset.field] || '';
        box.querySelectorAll('button').forEach(btn => btn.classList.toggle('selected', btn.dataset.value === selected));
      }});
    }}

    function saveCurrentForm() {{
      const sample = SAMPLES[currentIndex];
      const a = annotationFor(sample);
      a.reviewer_id = document.getElementById('reviewer_id').value.trim();
      a.reviewed_at_utc = document.getElementById('reviewed_at_utc').value.trim();
      a.reviewer_notes = document.getElementById('reviewer_notes').value.trim();
      saveAnnotations();
    }}

    function render() {{
      renderList();
      renderViewer();
      renderForm();
      updateProgress();
    }}

    function go(delta) {{
      saveCurrentForm();
      currentIndex = Math.max(0, Math.min(SAMPLES.length - 1, currentIndex + delta));
      render();
    }}

    function setPresent(value) {{
      annotationFor(SAMPLES[currentIndex]).dynamic_region_present = value;
      saveAnnotations();
      renderForm();
    }}

    function zoomImage(src) {{
      document.getElementById('zoomImage').src = src;
      document.getElementById('zoomDialog').showModal();
    }}

    function mergedRows() {{
      saveCurrentForm();
      return SAMPLES.map(sample => {{
        const row = {{}};
        CSV_FIELDS.forEach(field => row[field] = sample[field] || '');
        Object.assign(row, annotationFor(sample));
        return row;
      }});
    }}

    function csvEscape(value) {{
      const text = String(value ?? '');
      if (/[",\\n\\r]/.test(text)) return '"' + text.replaceAll('"', '""') + '"';
      return text;
    }}

    function toCsv(rows) {{
      const lines = [CSV_FIELDS.join(',')];
      rows.forEach(row => lines.push(CSV_FIELDS.map(field => csvEscape(row[field])).join(',')));
      return lines.join('\\n') + '\\n';
    }}

    function download(filename, text, type) {{
      const blob = new Blob([text], {{ type }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }}

    function parseCsv(text) {{
      const rows = [];
      let row = [];
      let value = '';
      let quoted = false;
      for (let i = 0; i < text.length; i++) {{
        const ch = text[i];
        const next = text[i + 1];
        if (quoted) {{
          if (ch === '"' && next === '"') {{ value += '"'; i++; }}
          else if (ch === '"') quoted = false;
          else value += ch;
        }} else {{
          if (ch === '"') quoted = true;
          else if (ch === ',') {{ row.push(value); value = ''; }}
          else if (ch === '\\n') {{ row.push(value); rows.push(row); row = []; value = ''; }}
          else if (ch !== '\\r') value += ch;
        }}
      }}
      if (value || row.length) {{ row.push(value); rows.push(row); }}
      const headers = rows.shift() || [];
      return rows.filter(r => r.some(v => v.trim())).map(r => {{
        const obj = {{}};
        headers.forEach((h, i) => obj[h] = r[i] || '');
        return obj;
      }});
    }}

    function importCsv(text) {{
      const imported = parseCsv(text);
      const byId = new Map(imported.map(row => [row.packet_id, row]));
      SAMPLES.forEach(sample => {{
        const row = byId.get(sample.packet_id);
        if (!row) return;
        const a = annotationFor(sample);
        LABEL_FIELDS.forEach(field => a[field] = (row[field] || '').trim());
      }});
      saveAnnotations();
      render();
      alert(`Imported labels for ${{imported.length}} CSV rows.`);
    }}

    function escapeHtml(text) {{
      return String(text).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}

    document.getElementById('prevBtn').addEventListener('click', () => go(-1));
    document.getElementById('nextBtn').addEventListener('click', () => go(1));
    document.getElementById('saveBtn').addEventListener('click', () => {{ saveCurrentForm(); render(); }});
    document.getElementById('markTimeBtn').addEventListener('click', () => {{
      document.getElementById('reviewed_at_utc').value = new Date().toISOString();
      saveCurrentForm();
      render();
    }});
    document.getElementById('downloadCsvBtn').addEventListener('click', () => download('independent_dynamic_label_review_filled_p243.csv', toCsv(mergedRows()), 'text/csv'));
    document.getElementById('downloadJsonBtn').addEventListener('click', () => download('independent_dynamic_label_review_filled_p243.json', JSON.stringify(mergedRows(), null, 2), 'application/json'));
    document.getElementById('copyCsvBtn').addEventListener('click', async () => {{
      await navigator.clipboard.writeText(toCsv(mergedRows()));
      alert('CSV copied to clipboard.');
    }});
    document.getElementById('clearBtn').addEventListener('click', () => {{
      if (confirm('Clear all locally saved P243 labels in this browser?')) {{
        annotations = {{}};
        localStorage.removeItem(STORAGE_KEY);
        render();
      }}
    }});
    document.getElementById('importBtn').addEventListener('click', () => importCsv(document.getElementById('importText').value));
    document.getElementById('fileImportBtn').addEventListener('click', () => document.getElementById('fileInput').click());
    document.getElementById('fileInput').addEventListener('change', event => {{
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => importCsv(String(reader.result || ''));
      reader.readAsText(file);
    }});
    document.getElementById('reviewer_id').addEventListener('input', saveCurrentForm);
    document.getElementById('reviewed_at_utc').addEventListener('input', saveCurrentForm);
    document.getElementById('reviewer_notes').addEventListener('input', saveCurrentForm);
    document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {{
      currentView = tab.dataset.view;
      document.querySelectorAll('.tab').forEach(t => t.classList.toggle('selected', t === tab));
      renderViewer();
    }}));
    document.addEventListener('keydown', event => {{
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') go(-1);
      if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') go(1);
      if (event.key === '1') setPresent('yes');
      if (event.key === '2') setPresent('no');
      if (event.key === '3') setPresent('uncertain');
      if (event.key.toLowerCase() === 's') {{ saveCurrentForm(); render(); }}
    }});

    renderChoices();
    render();
  </script>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_doc(path: Path) -> None:
    text = f"""# P243 Interactive Independent Dynamic-Label Annotation Web Tool

## Purpose

`{rel(OUTPUT_HTML)}` is a local, single-file HTML/JavaScript annotation tool for the 18-sample P239/P242 independent dynamic-label packet. It is designed for direct reviewer use: inspect the images, click labels, save progress in the browser, and export a filled CSV or JSON.

## How To Use

1. Open `{rel(OUTPUT_HTML)}` locally in a browser from the repository checkout.
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
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=INPUT_CSV)
    parser.add_argument("--output-html", type=Path, default=OUTPUT_HTML)
    parser.add_argument("--doc-md", type=Path, default=DOC_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_csv(args.input_csv)
    validate_rows(rows)
    write_html(args.output_html, rows)
    write_doc(args.doc_md)
    print(f"Built P243 interactive annotation web tool for {len(rows)} samples at {rel(args.output_html)}")


if __name__ == "__main__":
    main()
