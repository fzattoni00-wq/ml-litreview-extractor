# PROMPT — run the review over all your PDFs (ultracode, 1 agent per file)

> Paste the block below into a Claude Code session started with skip-permission.
> The word `ultracode` enables the multi-agent workflow. One agent per PDF.
> Replace `<PROJECT>` with your project directory.

---

ultracode.

You are doing a **publication-grade literature review** of research papers that
apply Machine Learning / neural networks / AI to predict an output (ANY field).
The output is meant for publication: the absolute rule is **never invent a value**
(absent = "Not reported"; a number not traceable to a specific table/figure/page
is not a fact).

Use the skill **ml-litreview-extractor** (in ~/.claude/skills/): read its SKILL.md
and the files in references/ and follow that pattern EXACTLY (extractor +
adversarial verifier, 1 agent per PDF, VISION reading of the result figures). Use
its 35 columns, not a schema of your own.

Project: <PROJECT>
- pdfs/ → the PDFs to analyse (put your legally-obtained PDFs here)
- model_template.xlsx → optional column template (do NOT modify it)
- output/ → the final Excel goes here

Run the 3 stages of the skill (scripts in ~/.claude/skills/ml-litreview-extractor/scripts/):

1) PRE-PROCESSING (deterministic):
   cd <PROJECT>
   python3 ~/.claude/skills/ml-litreview-extractor/scripts/preprocess.py pdfs work --max-render 6 --dpi-zoom 2.0
   python3 -c "import json; ids=[d['pdf_id'] for d in json.load(open('work/_index.json')) if 'pdf_id' in d]; json.dump(ids, open('work/_ids.json','w')); print(len(ids),'bundles')"

2) EXTRACT + VERIFY (workflow, 1 agent per PDF). Read the ids from work/_ids.json and invoke the bundled workflow:
   Workflow({ scriptPath: "/Users/<you>/.claude/skills/ml-litreview-extractor/scripts/extract_workflow.js",
              args: { workRoot: "<PROJECT>/work", ids: <array from work/_ids.json> } })
   When the workflow finishes, the result in context is TRUNCATED. Read the task output file from the completion notification (/private/tmp/.../tasks/<task-id>.output), json.load it, take ["result"] ({count, rows}), and save it to output/verified_rows.json.

3) WRITE EXCEL (deterministic):
   python3 ~/.claude/skills/ml-litreview-extractor/scripts/write_excel.py output/verified_rows.json model_template.xlsx output/review_FILLED.xlsx
   cp output/review_FILLED.xlsx ~/Downloads/review_FILLED.xlsx

FINAL CHECK (report the numbers): rows == number of PDFs, columns == 35, how many yellow cells (to verify by hand), and the path of the Excel files.

CONSTRAINTS (non-negotiable): never invent (Not reported); read the result-page images for metrics; keep raw inputs vs engineered features separate; each engineered feature with formula or description; Publisher = venue + publisher only; full Authors; cells in English. Do NOT modify the template or the PDFs. No git/push/credentials. Papers are copyrighted: process locally, never redistribute.
