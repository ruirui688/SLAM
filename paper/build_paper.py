#!/usr/bin/env python3
"""build_paper.py — Convert thick manuscript markdown to HTML and PDF."""

import markdown
import re, os, base64, sys, json
from pathlib import Path
from datetime import datetime

PAPER_DIR = Path(__file__).resolve().parent  # paper/
SLAM_DIR = PAPER_DIR.parent
EXPORT_DIR = PAPER_DIR / "export"
FIGURES_DIR = PAPER_DIR / "figures"
MANUSCRIPT_EN = PAPER_DIR / "manuscript_en_thick.md"
MANUSCRIPT_ZH = PAPER_DIR / "manuscript_zh_thick.md"
BUILD_LOG = EXPORT_DIR / "build_log.json"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def preprocess_markdown(text):
    """Pre-process markdown: handle figure references with file paths, math."""
    # Convert $$ ... $$ display math to have newlines for markdown parser
    text = re.sub(r'\$\$', '\n$$\n', text)
    
    # Figure filename → paper/figures/ file mapping (by basename)
    mapping = {
        'torwic_paper_result_overview.png': 1,
        'torwic_real_session_overlays.png': 2,
        'torwic_hallway_composite.png': 3,
        'torwic_dynamic_slam_backend_p134.png': 4,
        'torwic_dynamic_mask_coverage_p135.png': 5,
        'torwic_dynamic_mask_temporal_stress_p136.png': 6,
        'torwic_dynamic_mask_flow_stress_p137.png': 7,
        'torwic_dynamic_mask_first8_real_p138.png': 8,
        'torwic_dynamic_mask_first16_real_p139.png': 9,
        'torwic_dynamic_mask_first32_real_p140.png': 10,
    }
    
    def repl_fig(m):
        prefix = m.group(1)
        fname = m.group(2)
        fpath = FIGURES_DIR / fname
        if fpath.exists():
            rel = os.path.relpath(fpath, EXPORT_DIR)
            return f'{prefix}({rel})'
        return m.group(0)
    
    # Match: ![alt text](figures/filename.png)
    text = re.sub(r'(!\[[^\]]*\]\()figures/([^)]+\.png)\)', repl_fig, text)
    
    # Detect and wrap inline math \( ... \) — keep as-is for MathJax
    return text

def build_html(manuscript_path, lang='en'):
    """Build HTML from a markdown manuscript."""
    name = manuscript_path.stem
    print(f"  Processing {manuscript_path}...")
    
    with open(manuscript_path) as f:
        md_text = f.read()
    
    md_text = preprocess_markdown(md_text)
    
    # Markdown extensions
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.smarty',
    ]
    
    html_body = markdown.markdown(md_text, extensions=extensions)
    
    # KaTeX CSS for math rendering
    katex_css = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">'
    katex_js = '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>'
    katex_auto = '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body,{delimiters:[{left:\'$$\',right:\'$$\',display:true},{left:\'$\',right:\'$\',display:false},{left:\'\\\\(\',right:\'\\\\)\',display:false}]});"></script>'
    
    css = """
    body {
        font-family: 'Latin Modern Roman', 'Noto Serif CJK SC', Georgia, serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 2em 1em;
        line-height: 1.6;
        color: #222;
    }
    h1, h2, h3, h4 { font-family: 'Latin Modern Sans', 'Noto Sans CJK SC', Helvetica, sans-serif; }
    h1 { font-size: 1.5em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }
    h2 { font-size: 1.3em; border-bottom: 1px solid #999; padding-bottom: 0.2em; margin-top: 1.5em; }
    h3 { font-size: 1.15em; margin-top: 1.2em; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
    th { background: #f5f5f5; }
    img { max-width: 100%; height: auto; margin: 1em 0; }
    pre { background: #f5f5f5; padding: 10px; overflow-x: auto; font-size: 0.85em; }
    code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 3px solid #999; margin: 1em 0; padding: 0.5em 1em; color: #555; background: #fafafa; }
    .katex { font-size: 1.1em; }
    @media print { body { max-width: none; } }
    """
    
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="build_paper.py — markdown + weasyprint">
<title>{name}</title>
{katex_css}
<style>{css}</style>
</head>
<body>
{html_body}
{katex_js}
{katex_auto}
</body>
</html>"""
    
    out_path = EXPORT_DIR / f"{name}.html"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    size_kb = out_path.stat().st_size / 1024
    print(f"    → {out_path} ({size_kb:.1f} KB)")
    return out_path

def build_pdf(html_path):
    """Convert HTML to PDF using weasyprint."""
    from weasyprint import HTML
    out_path = html_path.with_suffix('.pdf')
    print(f"  Building PDF from {html_path.name}...")
    
    try:
        HTML(filename=str(html_path)).write_pdf(str(out_path))
        size_kb = out_path.stat().st_size / 1024
        print(f"    → {out_path} ({size_kb:.1f} KB)")
        return out_path, True
    except Exception as e:
        print(f"    ✗ PDF failed: {e}")
        return None, False

def main():
    build_report = {
        "timestamp": datetime.now().isoformat(),
        "toolchain": {
            "python": sys.version,
            "markdown": markdown.__version__,
        },
        "builds": {}
    }
    
    try:
        import weasyprint
        build_report["toolchain"]["weasyprint"] = weasyprint.__version__
    except:
        build_report["toolchain"]["weasyprint"] = "not available"
    
    results = []
    
    # Build English manuscript
    print("\n=== Building English Manuscript ===")
    html_en = build_html(MANUSCRIPT_EN, 'en')
    pdf_en, pdf_ok = build_pdf(html_en)
    results.append({
        "lang": "en",
        "html": str(html_en),
        "html_size_kb": round(html_en.stat().st_size / 1024, 1),
        "pdf": str(pdf_en) if pdf_ok else None,
        "pdf_size_kb": round(pdf_en.stat().st_size / 1024, 1) if pdf_ok else None,
        "pdf_ok": pdf_ok,
    })
    
    # Build Chinese manuscript
    print("\n=== Building Chinese Manuscript ===")
    html_zh = build_html(MANUSCRIPT_ZH, 'zh')
    pdf_zh, pdf_ok_zh = build_pdf(html_zh)
    results.append({
        "lang": "zh",
        "html": str(html_zh),
        "html_size_kb": round(html_zh.stat().st_size / 1024, 1),
        "pdf": str(pdf_zh) if pdf_ok_zh else None,
        "pdf_size_kb": round(pdf_zh.stat().st_size / 1024, 1) if pdf_ok_zh else None,
        "pdf_ok": pdf_ok_zh,
    })
    
    build_report["builds"] = results
    
    # Overall status
    all_pdf_ok = all(r["pdf_ok"] for r in results)
    build_report["status"] = "ok" if all_pdf_ok else "partial"
    
    with open(BUILD_LOG, 'w', encoding='utf-8') as f:
        json.dump(build_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Build Report: {BUILD_LOG} ===")
    print(f"Status: {build_report['status']}")
    for r in results:
        html_ok = '✅' if r['html'] else '❌'
        pdf_ok = '✅' if r['pdf_ok'] else '❌'
        print(f"  {r['lang']}: HTML {html_ok} ({r['html_size_kb']} KB) | PDF {pdf_ok} ({r.get('pdf_size_kb','—')} KB)")
    
    return build_report

if __name__ == '__main__':
    report = main()
    sys.exit(0 if report['status'] == 'ok' else 1)
