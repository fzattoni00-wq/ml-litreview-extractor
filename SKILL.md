---
name: battery-lit-review-extractor
description: >-
  Extract a structured literature-review row from each battery / lithium-ion
  Machine-Learning PDF (RUL — Remaining Useful Life, or SOH — State of Health
  estimation) and write them into an Excel review matrix (one row per paper, 35
  columns). Use this skill WHENEVER the user wants to review, classify, screen,
  tabulate, or compare a folder/ZIP of battery-ML papers, build or extend a
  "review matrix"/"battery_ml_review" spreadsheet, or asks to pull architecture,
  datasets, experimental conditions, metrics/results, advantages or limitations
  out of battery degradation / SOH / RUL / EV-battery / BMS neural-network
  papers — even if they don't name this skill. It runs a 1-agent-per-PDF
  extractor + adversarial verifier workflow with VISION on result figures, never
  invents data, and flags uncertain cells for human verification (the output is
  meant for publication, so accuracy is treated as legally critical).
---

# Battery ML Literature Review Extractor

Turn a pile of battery-ML papers into a clean, publishable **review matrix**:
one row per PDF, 35 columns, every number traceable, nothing invented.

This skill encodes a pipeline that was built and **validated on real papers**
(human-approved). Follow it exactly; the quality comes from the discipline, not
from improvisation.

## Why it is built this way (read this first)

The output feeds a **published** literature review. A wrong value (a metric, a
dataset name, an architecture) can have real consequences. Two design choices
exist purely to protect against that:

1. **One isolated agent per PDF + a second adversarial verifier.** The extractor
   reads the paper and fills the row; the verifier then *tries to refute* every
   critical field against the same source. Isolation per paper means no
   cross-contamination between documents; the second pass catches the plausible-
   but-wrong values a single read lets through.
2. **Vision on the result pages.** In these papers the actual metric values
   (RMSE, MAE, R²…) very often live *inside figures and image-tables*, not in the
   text layer. The preprocessor renders the result pages to PNG and the agents
   **read the images**. Skipping this is the single biggest source of error.

The golden rule that overrides everything: **never invent**. If a value is not
explicitly in the paper, write exactly `Not reported`. If a number cannot be
traced to a specific table/figure/page, it does not go in as fact.

## The 3-stage pipeline

```
PDFs ──▶ [1] preprocess.py ──▶ work/<id>/{text.txt, tables.txt, page_*.png}
                                   │
                                   ▼
        [2] extract_workflow.js  (per PDF: extractor agent → adversarial verifier agent)
                                   │  returns {count, rows} (verified JSON)
                                   ▼
        [3] write_excel.py ──▶ output/...FILLED.xlsx  (35 cols, uncertain cells yellow)
```

Stages 1 and 3 are **deterministic Python, no AI** (no hallucination risk in
prep or in writing the spreadsheet). Stage 2 is the AI work, structured as a
schema-enforced workflow so each agent returns a validated object, not free text.

All three scripts are bundled in `scripts/`. Do not rewrite them inline; call
them. The authoritative column definitions, the gold-standard example, and the
list of real mistakes to avoid live in `references/` — read them before judging
or correcting any extraction.

## How to run it

Set a project dir with `pdfs/` (all PDFs), the model `.xlsx` template, and an
`output/` dir. Then:

**Step 1 — preprocess (deterministic).**
```bash
python3 scripts/preprocess.py pdfs work --max-render 6 --dpi-zoom 2.0
python3 -c "import json; ids=[d['pdf_id'] for d in json.load(open('work/_index.json')) if 'pdf_id' in d]; json.dump(ids, open('work/_ids.json','w')); print(len(ids),'bundles')"
```

**Step 2 — extract + verify (workflow, 1 agent per PDF).** From the agent
session (NOT bash), invoke the bundled workflow, passing the work dir and the id
list:
```
Workflow({ scriptPath: "<skill>/scripts/extract_workflow.js",
           args: { workRoot: "<abs>/work", ids: <contents of work/_ids.json> } })
```
When it finishes, write its output to `output/verified_rows.json`. IMPORTANT: the
workflow result is large and arrives **truncated** in the agent context. Do not
copy it from context — read the task output file the completion notification
points to (`/private/tmp/.../tasks/<task-id>.output`), `json.load` it, take the
`["result"]` object (`{count, rows}`), and save that to `output/verified_rows.json`.

**Step 3 — write the Excel (deterministic).**
```bash
python3 scripts/write_excel.py output/verified_rows.json <template.xlsx> output/battery_ml_review_FILLED.xlsx
```

**Verify:** rows == number of PDFs, columns == 35. Yellow cells are what a human
must check first.

### Scaling notes
- The workflow caps concurrency itself (~16 agents in parallel); pass all ids at
  once, they queue and drain. Budget roughly ~190k tokens and ~9 min per 6 PDFs.
- Rendering PNGs uses disk. On a tight disk, lower `--max-render` or delete
  `work/<id>/page_*.png` after Step 2.
- These papers are public (Elsevier/AIP/IEEE…): no personal data, no GDPR issue.
- Never modify the original template; always write to `output/`.

## The 35 columns (summary — full definitions in references)

Identity: `PDF name`, `Paper title`, **`Authors`** (full list), `Year`,
`Publisher / venue` (journal + publisher ONLY — no year/volume/pages/DOI),
`DOI / link`.
Task: `Target task` (controlled: SOH / RUL / Both / Other), `Target definition`.
Battery: `Battery chemistry` (+form factor), `Cell / module / pack level`.
Data: `Dataset`, `Public dataset?` (+names), `Experimental conditions` (CC/CV,
C-rate, temperature, cycles, EOL).
Inputs: `Input data type` = **raw signals only**; `Data preparation`;
`Feature extraction` = **engineered features only, each with its formula or a
text description**.
Model: `Model category`, `NN architecture`, `Training strategy`,
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
- Keep raw signals and engineered features strictly separate.
- Every engineered feature gets a formula or a textual description.
- English in every cell. Concise, clean — no raw multi-paragraph dumps.
- Flag anything uncertain; the human fact-check is the last line of defence.
