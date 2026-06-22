#!/usr/bin/env python3
"""
preprocess.py — Deterministic, NO-AI pre-processing for the battery ML literature review.

For each input PDF it produces, under <out_dir>/<pdf_id>/:
  - text.txt        full text layer, page-delimited with [PAGE n] markers
  - tables.txt      tables extracted with pdfplumber from candidate result pages
  - manifest.json   metadata + which pages were rendered and why
  - page_<n>.png    rendered images of: page 1 (title/abstract) + candidate result pages

"Candidate result pages" = pages whose text mentions ML metrics / result tables /
figures, i.e. exactly the pages a human checks to read the numbers. These PNGs are
what the vision agent reads to capture metric values trapped inside figures/images.

Usage:
  python preprocess.py <input_dir_or_pdf> <out_dir> [--max-render N] [--dpi-zoom Z]

Deterministic: no network, no AI. Safe to re-run (idempotent per pdf_id).
"""
import sys, os, re, json, argparse, hashlib

import fitz  # PyMuPDF
try:
    import pdfplumber
    HAS_PLUMBER = True
except Exception:
    HAS_PLUMBER = False

# Metric / result signals that mark a page worth rendering for the vision agent.
METRIC_PAT = re.compile(
    r"\b(RMSE|MAE|MAPE|MSE|R\s?2|R\^?2|R²|F1|F-?score|precision|recall|"
    r"relative error|mean (absolute|square)|determination coefficient|accuracy)\b",
    re.IGNORECASE,
)
RESULT_HDR_PAT = re.compile(
    r"\b(results?|experiment|evaluation|comparison|conclusion|discussion|"
    r"performance|prediction (results?|error))\b",
    re.IGNORECASE,
)
TABLEFIG_PAT = re.compile(r"\b(table|fig(\.|ure)?)\s*\.?\s*\d", re.IGNORECASE)
NUM_PAT = re.compile(r"\d+\.\d+")


def pdf_id(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:120]


def score_page(text):
    """Higher score => more likely to contain result values worth rendering."""
    if not text:
        return 0
    s = 0
    s += 4 * len(METRIC_PAT.findall(text))
    s += 2 * len(TABLEFIG_PAT.findall(text))
    s += 1 if RESULT_HDR_PAT.search(text) else 0
    s += min(len(NUM_PAT.findall(text)), 20) * 0.2  # numeric density, capped
    return s


def process_pdf(path, out_root, max_render=6, dpi_zoom=2.0):
    pid = pdf_id(path)
    out_dir = os.path.join(out_root, pid)
    os.makedirs(out_dir, exist_ok=True)

    doc = fitz.open(path)
    n = len(doc)
    pages_text = []
    scores = []
    for i in range(n):
        t = doc[i].get_text("text")
        pages_text.append(t)
        scores.append(score_page(t))

    # full text dump
    with open(os.path.join(out_dir, "text.txt"), "w", encoding="utf-8") as f:
        for i, t in enumerate(pages_text, start=1):
            f.write(f"\n===== [PAGE {i}/{n}] =====\n")
            f.write(t)

    # choose pages to render: page 1 always + top-scoring result pages (deduped, in order)
    ranked = sorted(range(n), key=lambda i: scores[i], reverse=True)
    chosen = []
    if n > 0:
        chosen.append(0)  # title/abstract
    for i in ranked:
        if scores[i] <= 0:
            break
        if i not in chosen:
            chosen.append(i)
        if len(chosen) >= max_render:
            break
    chosen = sorted(set(chosen))

    rendered = []
    mat = fitz.Matrix(dpi_zoom, dpi_zoom)
    for i in chosen:
        pix = doc[i].get_pixmap(matrix=mat)
        fn = f"page_{i+1}.png"
        pix.save(os.path.join(out_dir, fn))
        rendered.append({"page": i + 1, "score": round(scores[i], 2), "file": fn})

    # table extraction (candidate pages only, cheap & focused)
    tables_txt = []
    if HAS_PLUMBER:
        try:
            with pdfplumber.open(path) as pl:
                for i in chosen:
                    if i >= len(pl.pages):
                        continue
                    for tbl in (pl.pages[i].extract_tables() or []):
                        rows = ["\t".join("" if c is None else str(c) for c in row) for row in tbl]
                        if rows:
                            tables_txt.append(f"--- TABLE on page {i+1} ---\n" + "\n".join(rows))
        except Exception as e:
            tables_txt.append(f"[pdfplumber error: {e}]")
    with open(os.path.join(out_dir, "tables.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(tables_txt) if tables_txt else "[no tables extracted on candidate pages]")

    meta = doc.metadata or {}
    total_chars = sum(len(t) for t in pages_text)
    manifest = {
        "pdf_id": pid,
        "source_pdf": os.path.basename(path),
        "n_pages": n,
        "total_text_chars": total_chars,
        "is_text_native": total_chars > 200 * max(n, 1),  # heuristic: real text layer
        "meta_title": (meta.get("title") or "").strip(),
        "rendered_pages": rendered,
        "tables_found": len(tables_txt),
        "first_page_text_preview": pages_text[0][:600] if pages_text else "",
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    doc.close()
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", help="input dir of PDFs or single PDF")
    ap.add_argument("out", help="output work dir")
    ap.add_argument("--max-render", type=int, default=6)
    ap.add_argument("--dpi-zoom", type=float, default=2.0)
    args = ap.parse_args()

    if os.path.isdir(args.inp):
        pdfs = sorted(
            os.path.join(args.inp, f)
            for f in os.listdir(args.inp)
            if f.lower().endswith(".pdf")
        )
    else:
        pdfs = [args.inp]

    os.makedirs(args.out, exist_ok=True)
    index = []
    for p in pdfs:
        try:
            m = process_pdf(p, args.out, args.max_render, args.dpi_zoom)
            index.append(m)
            print(f"OK  {m['pdf_id']}  pages={m['n_pages']} rendered={len(m['rendered_pages'])} "
                  f"tables={m['tables_found']} native={m['is_text_native']}")
        except Exception as e:
            print(f"ERR {os.path.basename(p)}: {e}")
            index.append({"source_pdf": os.path.basename(p), "error": str(e)})
    with open(os.path.join(args.out, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\nTotal: {len(pdfs)} PDFs -> {args.out}")


if __name__ == "__main__":
    main()
