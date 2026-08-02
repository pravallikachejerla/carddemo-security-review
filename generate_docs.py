#!/usr/bin/env python3
"""
CardDemo Technical Documentation Renderer (Python-only)

Generates an HTML version of TECHNICAL_ANALYSIS_DOCUMENTATION.md
for easy viewing. Uses only Python + markdown (pip installed).

Run:
    pip install markdown
    python generate_docs.py
"""

import markdown
import os
from pathlib import Path

def main():
    md_path = Path("TECHNICAL_ANALYSIS_DOCUMENTATION.md")
    html_path = Path("documentation.html")
    
    if not md_path.exists():
        print("Error: TECHNICAL_ANALYSIS_DOCUMENTATION.md not found.")
        return 1
    
    print("Reading technical documentation...")
    content = md_path.read_text(encoding="utf-8")
    
    print("Converting Markdown to HTML...")
    html = markdown.markdown(
        content,
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "nl2br"
        ]
    )
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CardDemo Security, Performance & Bug Review — Technical Documentation</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 960px; margin: 40px auto; line-height: 1.6; }}
        h1, h2, h3 {{ color: #1a73e8; }}
        pre {{ background: #f5f5f5; padding: 12px; overflow-x: auto; border-radius: 4px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f0f0f0; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
    </style>
</head>
<body>
    {html}
    <hr>
    <p><small>Generated from TECHNICAL_ANALYSIS_DOCUMENTATION.md | 
    Repository: https://github.com/pravallikachejerla/carddemo-security-review</small></p>
</body>
</html>"""
    
    html_path.write_text(full_html, encoding="utf-8")
    print(f"\n✅ Documentation successfully rendered to: {html_path.absolute()}")
    print("\nOpen documentation.html in your browser to view the full analysis.")
    print("\nKey sections included:")
    print("  • Project Architecture")
    print("  • All 7 Injected Issues (I1-I7) with code locations, impact, fixes")
    print("  • Summary of real upstream issues (R1-R9)")
    print("  • Performance hotspots (O(n²) batch regression)")
    print("  • Critical bugs (balance corruption, fraud bypass, SQLi, backdoors)")
    print("  • Remediation roadmap")
    print("\nWorking on branch: genesis/fe2480d4-33d3-4741-aa71-3c4d87a2f52d-proj-repo-pravallikachejerla-carddemo-security-review")
    return 0

if __name__ == "__main__":
    exit(main())
