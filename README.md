# ml-litreview-extractor

A Claude Code skill and multi-agent workflow for analysing and classifying research papers to support structured literature reviews. The workflow was developed and validated on a corpus of 100+ papers focused on neural-network-based estimation of lithium battery state of health (SOH), state of charge (SOC), and remaining useful life (RUL). It generates a spreadsheet that maps each paper against 35 machine-learning and application-oriented features, enabling faster comparison, synthesis, and gap identification.


## Key strenghts

- **Benchmarking:** glance comparison of networks architectures, data preparations and performance metrics 
- **Domain-agnostic:** scalable to different applied machine learning domains
- **Paywall:** running on local PDFs can bring to another level of detail your Zootero libraries and avoid basing literature reviews on only open access papers 



## How it works

```
PDFs ─▶ [1] preprocess.py  ─▶ work/<id>/{text.txt, tables.txt, page_*.png}
                                  │
                                  ▼
       [2] extract_workflow.js  (per PDF: extractor agent → adversarial verifier)
                                  │  → {count, rows} (schema-validated JSON)
                                  ▼
       [3] write_excel.py  ─▶ review_FILLED.xlsx  (35 columns; uncertain cells yellow)
```

Designed for **publication-grade accuracy**:


- **One agent per PDF + a second adversarial pass.** Isolation avoids
  cross-contamination between papers; the verifier *tries to refute* every
  critical field, catching plausible-but-wrong values a single read lets through.
- **Vision on result pages.** The preprocessor renders the result pages to PNG so
  the agents read metrics (RMSE, MAE, R², accuracy, F1, AUC…) from figures and
  image-tables, not just the text layer.
- **Uncertain cells are flagged** (highlighted yellow + listed in a
  `Fields to verify` column) so a human fact-check is fast and targeted.

Stages 1 and 3 are deterministic Python (no AI → no hallucination in prep or in
writing the spreadsheet). Stage 2 is the AI work, run as a schema-enforced
workflow so each agent returns a validated object, not free text.

## The 35 columns

Identity (PDF name, Paper title, Authors, Year, Publisher/venue, DOI), scope
(Application domain, Prediction target/task, Target definition), data (Data
modality, Dataset, Public dataset?, Experimental setup), inputs (raw inputs vs
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
  capability (the workflow runs in "ultracode" mode).

## Usage

1. Install as a Claude Code skill: copy this folder to
   `~/.claude/skills/ml-litreview-extractor/`.
2. Put your PDFs in a `pdfs/` directory and provide an `.xlsx` template (or let
   `write_excel.py` create the sheet).
3. Follow [`SKILL.md`](SKILL.md) (or paste [`PROMPT-ultracode.md`](PROMPT-ultracode.md)
   into a Claude Code session). The three stages run preprocess → workflow →
   write_excel and produce `review_FILLED.xlsx`.

## Note on the papers

This repository contains **only the tooling**. No PDFs are included: research
papers are copyrighted by their publishers (IEEE, Elsevier, Springer, Taylor &
Francis, Wiley, ACM, AIP…) and must not be redistributed. Bring your own
legally-obtained PDFs; processing happens locally on your machine.

