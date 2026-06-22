---
name: ml-litreview-extractor
description: >-
  Turn a folder of research papers that apply Machine Learning / neural networks
  / AI to PREDICT some output into a clean, publication-grade literature-review
  matrix in Excel (one row per paper, 35 columns). Domain-agnostic: works for ANY
  field — energy, batteries, medicine, finance, materials, NLP, computer vision,
  engineering, climate, genomics, etc. Use this skill WHENEVER the user wants to
  review, screen, classify, tabulate, summarise, or compare a folder/ZIP of ML /
  deep-learning / neural-network research PDFs, build or extend a "review matrix"/
  literature-review spreadsheet, or pull out architecture, datasets, experimental
  setup, metrics/results, advantages or limitations from predictive-modelling
  papers — even if they don't name this skill. Its edge over commercial review
  tools: it runs on the PDFs the user ALREADY downloaded, including paywalled ones
  (IEEE, Elsevier, Springer, Taylor & Francis, Wiley, ACM…). It uses a
  1-agent-per-PDF extractor + adversarial verifier workflow with VISION on result
  figures, never invents data, and flags uncertain cells for human verification
  (the output is meant for publication, so accuracy is treated as legally critical).
---

# ML Literature Review Extractor

Turn a pile of ML / neural-network research papers into a clean, publishable
**review matrix**: one row per PDF, 35 columns, every value traceable, nothing
invented. **Domain-agnostic** — the paper just has to use a model to predict some
output; the field (batteries, medicine, finance, vision, NLP…) is captured in an
`Application domain` column rather than hard-coded.

This pipeline was built and **validated on real papers** (human-approved).
Follow it exactly; the quality comes from the discipline, not from improvisation.

## Why it exists (the edge)

Commercial review assistants (Elicit, SciSpace, Scholarcy…) work off open-access
metadata and can't read papers behind a paywall. Researchers, however, usually
**already have the PDFs** they need (downloaded through their institution from
IEEE Xplore, ScienceDirect/Elsevier, SpringerLink, Taylor & Francis, Wiley, ACM).
This skill runs **on those local PDFs**, so it covers exactly the literature a
real review depends on, and it goes deeper: it reads the figures and result
tables as images. Bring legally-obtained PDFs; the tool does the rest.

## Why it is built this way (read this first)

The output feeds a **published** literature review, so accuracy is critical:

1. **One isolated agent per PDF + a second adversarial verifier.** The extractor
   reads the paper and fills the row; the verifier then *tries to refute* every
   critical field against the same source. Isolation per paper means no
   cross-contamination between documents; the second pass catches plausible-but-
   wrong values a single read lets through.
2. **Vision on the result pages.** Metric values (RMSE, MAE, R², accuracy, F1,
   AUC…) very often live *inside figures and image-tables*, not the text layer.
   The preprocessor renders the result pages to PNG and the agents **read the
   images**. Skipping this is the single biggest source of error.

Golden rule overriding everything: **never invent**. If a value is not explicitly
in the paper, write `Not reported`. A number that cannot be traced to a specific
table/figure/page is not recorded as fact.

## The 3-stage pipeline

```
PDFs ──▶ [1] preprocess.py ──▶ work/<id>/{text.txt, tables.txt, page_*.png}
                                   │
                                   ▼
        [2] extract_workflow.js  (per PDF: extractor agent → adversarial verifier agent)
                                   │  returns {count, rows} (schema-validated JSON)
                                   ▼
        [3] write_excel.py ──▶ output/...FILLED.xlsx  (35 cols, uncertain cells yellow)
```

Stages 1 and 3 are **deterministic Python, no AI** (no hallucination in prep or in
writing the spreadsheet). Stage 2 is the AI work, structured as a schema-enforced
workflow so each agent returns a validated object, not free text.

All three scripts are bundled in `scripts/`. Do not rewrite them inline; call
them. The authoritative column definitions, a worked gold example, and the list of
real mistakes to avoid live in `references/` — read them before judging or
correcting any extraction.

## How to run it

Set a project dir with `pdfs/` (all PDFs), an `.xlsx` template, and an `output/`
dir. Then:

**Step 1 — preprocess (deterministic).**
```bash
python3 scripts/preprocess.py pdfs work --max-render 6 --dpi-zoom 2.0
python3 -c "import json; ids=[d['pdf_id'] for d in json.load(open('work/_index.json')) if 'pdf_id' in d]; json.dump(ids, open('work/_ids.json','w')); print(len(ids),'bundles')"
```

**Step 2 — extract + verify (workflow, 1 agent per PDF).** From the agent
session (NOT bash), invoke the bundled workflow, passing the work dir and id list:
```
Workflow({ scriptPath: "<skill>/scripts/extract_workflow.js",
           args: { workRoot: "<abs>/work", ids: <contents of work/_ids.json> } })
```
When it finishes, write its output to `output/verified_rows.json`. IMPORTANT: the
result is large and arrives **truncated** in the agent context — do not copy it
from context. Read the task output file the completion notification points to
(`/private/tmp/.../tasks/<task-id>.output`), `json.load` it, take `["result"]`
(`{count, rows}`), and save that.

**Step 3 — write the Excel (deterministic).**
```bash
python3 scripts/write_excel.py output/verified_rows.json <template.xlsx> output/review_FILLED.xlsx
```

**Verify:** rows == number of PDFs, columns == 35. Yellow cells are what a human
must check first.

### Scaling notes
- The workflow caps concurrency itself (~16 agents in parallel); pass all ids at
  once, they queue and drain. Budget roughly ~190k tokens and ~9 min per 6 PDFs.
- Rendering PNGs uses disk. On a tight disk, lower `--max-render` or delete
  `work/<id>/page_*.png` after Step 2.
- Published papers are copyrighted: process them locally, never redistribute them.
- Never modify the original template; always write to `output/`.

## The 35 columns (summary — full definitions in references)

Identity: `PDF name`, `Paper title`, `Authors` (full list), `Year`,
`Publisher / venue` (venue + publisher ONLY — no year/volume/pages/DOI),
`DOI / link`.
Scope: `Application domain` (field/problem), `Prediction target / task`,
`Target definition`.
Data: `Data modality` (time-series/tabular/images/text/…), `Dataset`,
`Public dataset?` (+names), `Experimental setup`.
Inputs: `Input variables (raw)` = **raw inputs only**; `Data preparation`;
`Feature extraction` = **engineered features only, each with its formula or a text
description**.
Model: `Model category`, `Model / NN architecture`, `Training strategy`,
`Validation strategy`, `Baseline models`.
Results: `Metrics reported`, `Main results`, `Generalisation tested?`,
`Code/data available?`.
Synthesis: `Advantages`, `Limitations`, `Relevance to my review`, `Notes`.
Analytical add-ons: `Architecture (plain-language)`, `Input representation`
(Raw sequences / Engineered features / Hybrid / Unclear),
`Results (structured)` (metric=value), `Results source + page`,
`Extraction confidence`, `Fields to verify (manual)`.

→ Read `references/column-schema.md` for the precise rule per column.
→ Read `references/gold-and-pitfalls.md` for a fully-worked validated row and the
   real extraction mistakes the verifier must hunt for.

## Non-negotiables (the spirit of the skill)
- Never invent. Absent → `Not reported`. Untraceable number → not a fact.
- Read the images on result pages; metrics hide there.
- Keep raw inputs and engineered features strictly separate.
- Every engineered feature gets a formula or a textual description; never fabricate
  formulas for features the model learns automatically.
- English in every cell. Concise, clean — no raw multi-paragraph dumps.
- Flag anything uncertain; the human fact-check is the last line of defence.
