# battery-lit-review-extractor

A Claude Code skill + workflow that turns a folder of **battery machine-learning
papers** (RUL — Remaining Useful Life, or SOH — State of Health estimation) into
a clean, **publication-grade review matrix**: one row per PDF, 35 columns, every
value traceable, nothing invented.

It runs **one isolated agent per PDF** (extractor) followed by an **adversarial
verifier** agent, and reads **figures/result tables as images** (vision) because
in these papers the actual metric values often live inside images, not the text
layer.

## Why it is built this way

The output is meant for a published literature review, so accuracy is treated as
critical:

- **Never invent.** If a value is not explicitly in the paper, the cell reads
  `Not reported`. A number that cannot be traced to a specific table/figure/page
  is not recorded as fact.
- **One agent per PDF + a second adversarial pass.** Isolation avoids
  cross-contamination between papers; the verifier tries to *refute* every
  critical field, catching plausible-but-wrong values a single read lets through.
- **Vision on result pages.** The preprocessor renders the result pages to PNG so
  the agents read the metrics from figures and image-tables.
- **Uncertain cells are flagged** (highlighted yellow + listed in a
  `Fields to verify` column) so a human fact-check is fast and targeted.

## Pipeline (3 stages)

```
PDFs ─▶ [1] preprocess.py  ─▶ work/<id>/{text.txt, tables.txt, page_*.png}
                                  │
                                  ▼
       [2] extract_workflow.js  (per PDF: extractor agent → adversarial verifier)
                                  │  → {count, rows} (schema-validated JSON)
                                  ▼
       [3] write_excel.py  ─▶ review_FILLED.xlsx  (35 columns; uncertain cells yellow)
```

Stages 1 and 3 are deterministic Python (no AI → no hallucination in prep or in
writing the spreadsheet). Stage 2 is the AI work, structured as a schema-enforced
workflow so each agent returns a validated object, not free text.

## The 35 columns

Identity (PDF name, Paper title, Authors, Year, Publisher/venue, DOI), task
(Target task + definition), battery (chemistry + form factor, cell/module/pack),
data (Dataset, Public dataset?, Experimental conditions), inputs (raw signals vs
engineered features — each feature with its formula or description), model
(category, NN architecture, training/validation strategy, baselines), results
(metrics, main results, generalisation, code/data availability), synthesis
(advantages, limitations, relevance, notes), plus analytical add-ons
(plain-language architecture, input representation, structured results, results
source+page, extraction confidence, fields to verify).

Full per-column rules: [`references/column-schema.md`](references/column-schema.md).
Gold example + the real extraction mistakes to avoid:
[`references/gold-and-pitfalls.md`](references/gold-and-pitfalls.md).

## Requirements

- Python 3 with `pymupdf`, `pdfplumber`, `openpyxl`
  (`pip install pymupdf pdfplumber openpyxl`)
- [Claude Code](https://claude.com/claude-code) with the multi-agent **Workflow**
  capability (the workflow is launched in "ultracode" mode).

## Usage

1. Install as a Claude Code skill: copy this folder to
   `~/.claude/skills/battery-lit-review-extractor/`.
2. Put your PDFs in a `pdfs/` directory and provide an `.xlsx` template.
3. Follow [`SKILL.md`](SKILL.md) (or paste [`PROMPT-ultracode.md`](PROMPT-ultracode.md)
   into a Claude Code session). The three stages run preprocess → workflow →
   write_excel and produce `review_FILLED.xlsx`.

## Note on the papers

This repository contains **only the tooling**. The source PDFs are **not
included**: research papers are copyrighted by their publishers (Elsevier, IEEE,
AIP, …) and must not be redistributed. Bring your own legally-obtained PDFs.

## License

MIT — see [LICENSE](LICENSE).
