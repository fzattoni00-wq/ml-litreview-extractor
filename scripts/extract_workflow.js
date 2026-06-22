// extract_workflow.js — canonical extraction+verification workflow for ALL PDFs.
// Invoked from Claude Code with:  Workflow({ scriptPath: ".../extract_workflow.js", args: { workRoot, ids } })
// args.workRoot = absolute path to the work/ dir produced by preprocess.py
// args.ids      = array of pdf_id (the sub-folder names inside work/)
//
// One isolated extractor agent per PDF (text + tables + VISION on rendered result pages),
// then one ADVERSARIAL verifier agent per PDF. Returns { count, rows } where each row is
// the verified record. Writing the .xlsx is done OUTSIDE by write_excel.py (deterministic).

export const meta = {
  name: 'battery-lit-review-extract',
  description: 'Extract + adversarially verify 34-field review rows from battery-ML PDFs (1 agent per PDF)',
  phases: [
    { title: 'Extract', detail: 'one expert agent per PDF: text + tables + vision on figures' },
    { title: 'Verify', detail: 'one adversarial agent per PDF: refute/correct each critical field' },
  ],
}

let _A = args
if (typeof _A === 'string') { try { _A = JSON.parse(_A) } catch (e) { _A = {} } }
_A = _A || {}
const WORK = _A.workRoot
const IDS = _A.ids
if (!WORK || !Array.isArray(IDS) || IDS.length === 0) {
  throw new Error('args must be { workRoot: string, ids: string[] }; got: ' + JSON.stringify(args))
}

const ROW_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['pdf_name','paper_title','authors','year','publisher_venue','doi_link','target_task','target_definition','battery_chemistry','cell_module_pack_level','dataset','public_dataset','experimental_conditions','input_data_type','data_preparation','feature_extraction','model_category','nn_architecture','training_strategy','validation_strategy','baseline_models','metrics_reported','main_results','generalisation_tested','code_data_available','advantages','limitations','relevance','architecture_plain','input_representation','results_structured','results_source_page','extraction_confidence','uncertain_fields','notes'],
  properties: {
    pdf_name: { type: 'string' }, paper_title: { type: 'string' },
    authors: { type: 'string', description: 'FULL author list exactly as printed on the first page, comma-separated' },
    year: { type: 'string' },
    publisher_venue: { type: 'string', description: 'ONLY journal/venue name + publisher, e.g. "Journal of Energy Storage, Elsevier". NO year, NO volume, NO issue, NO page numbers, NO DOI.' },
    doi_link: { type: 'string' },
    target_task: { type: 'string', enum: ['SOH / capacity estimation','RUL / lifetime prediction','Both (SOH + RUL)','Other / Not reported'] },
    target_definition: { type: 'string', description: 'how the target is defined (EOL threshold etc.) + any task nuance; put explanations HERE, not in target_task' },
    battery_chemistry: { type: 'string' }, cell_module_pack_level: { type: 'string' },
    dataset: { type: 'string' }, public_dataset: { type: 'string' },
    experimental_conditions: { type: 'string' },
    input_data_type: { type: 'string', description: 'RAW measured signals ONLY: voltage, current, temperature, capacity, time, cycle index' },
    data_preparation: { type: 'string' },
    feature_extraction: { type: 'string', description: 'ENGINEERED/derived features ONLY. For EACH feature give its FORMULA verbatim (read equation images if not in text) or a textual description if no formula, as a list "Feature: formula/description". E.g. "CCCT: time from CC-charge start to CV onset; IC peak: dQ/dV max; ..."' },
    model_category: { type: 'string' }, nn_architecture: { type: 'string' },
    training_strategy: { type: 'string' }, validation_strategy: { type: 'string' },
    baseline_models: { type: 'string' }, metrics_reported: { type: 'string' },
    main_results: { type: 'string' }, generalisation_tested: { type: 'string' },
    code_data_available: { type: 'string' }, advantages: { type: 'string' },
    limitations: { type: 'string' }, relevance: { type: 'string' },
    architecture_plain: { type: 'string', description: 'PLAIN-LANGUAGE 1-2 sentences: what the net is and how data flows in' },
    input_representation: { type: 'string', enum: ['Raw sequences','Engineered features','Hybrid','Unclear'] },
    results_structured: { type: 'string', description: 'proposed model best results as metric=value list; Not reported if absent' },
    results_source_page: { type: 'string', description: 'text/table/figure + page for each value' },
    extraction_confidence: { type: 'string', enum: ['High','Medium','Low'] },
    uncertain_fields: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['row','field_verdicts','overall_confidence','corrections_made','uncertain_fields'],
  properties: {
    row: ROW_SCHEMA,
    field_verdicts: { type: 'string' },
    overall_confidence: { type: 'string', enum: ['High','Medium','Low'] },
    corrections_made: { type: 'string' },
    uncertain_fields: { type: 'array', items: { type: 'string' } },
  },
}

const extractorPrompt = (id) => `You are a senior expert in battery degradation modelling, machine learning, electrochemistry and power electronics, doing a rigorous literature review that will be PUBLISHED. Accuracy is legally critical: NEVER invent a value. If something is not explicitly in the paper, write exactly "Not reported".

Source of truth bundle: ${WORK}/${id}/
1. Read ${WORK}/${id}/text.txt (markers "[PAGE n/total]").
2. Read ${WORK}/${id}/tables.txt
3. Run: ls ${WORK}/${id}/page_*.png — then use the Read tool on EVERY PNG to VISUALLY read figures/result tables. Metric values often live only inside images; read them from there.

Fill the 34-field schema in ENGLISH. Rules:
- pdf_name = "${id}.pdf". Title/authors/year/venue/DOI from first-page text (PDF metadata may be empty).
- authors: the FULL author list exactly as printed on the first page, comma-separated.
- publisher_venue: ONLY journal/venue name + publisher (e.g. "Journal of Energy Storage, Elsevier"). Do NOT include year, volume, issue, page numbers or DOI.
- target_task: MUST be exactly one of "SOH / capacity estimation", "RUL / lifetime prediction", "Both (SOH + RUL)", "Other / Not reported". Put ALL explanation/nuance in target_definition, never in target_task.
- input_data_type = RAW measured signals ONLY. feature_extraction = ENGINEERED features ONLY, and for EACH feature give its FORMULA verbatim (read equation images if not in the text layer) or a textual description if no formula, formatted as "Feature: formula/description". Keep raw vs engineered strictly separated.
- input_representation: one enum value.
- architecture_plain: 1-2 simple sentences (how the net is built, how data flows in).
- results_structured: proposed model BEST metrics as "RMSE=...; MAE=...; R2=..."; prefer numbers read from tables/figures; if only formulas, write "Only formulas found — Not reported".
- results_source_page: cite table/figure + page for each value.
- extraction_confidence + uncertain_fields: list every field you are unsure about (especially image-derived) for human verification.
Concise, clean cells. Return ONLY the structured object.`

const verifierPrompt = (id, extracted) => `You are an ADVERSARIAL fact-checker for a battery-ML literature review that will be PUBLISHED. Try to REFUTE the draft below, then return a corrected, trustworthy row. Default to "uncertain" if the paper does not clearly support a field. NEVER invent values.

Bundle: ${WORK}/${id}/  (re-read text.txt, tables.txt; run "ls ${WORK}/${id}/page_*.png" and Read each PNG).

DRAFT (JSON):
${JSON.stringify(extracted, null, 2)}

Re-verify especially: authors (full list), publisher_venue (must be ONLY journal+publisher — strip any year/volume/issue/pages/DOI), target_task, nn_architecture, input_data_type vs feature_extraction split (EACH engineered feature must include its formula or a textual description — add it from equation images if missing), input_representation, dataset + public_dataset, metrics_reported, results_structured (every number must be traceable to a table/figure/page — if not traceable, set "Not reported" or mark uncertain), year/DOI. Correct any error. Fill field_verdicts, corrections_made, overall_confidence, final uncertain_fields. Return ONLY the structured object with the full corrected row in "row".`

const results = await pipeline(
  IDS,
  (id) => agent(extractorPrompt(id), { label: `extract:${id.slice(0,16)}`, phase: 'Extract', schema: ROW_SCHEMA }),
  (extracted, id) => agent(verifierPrompt(id, extracted), { label: `verify:${id.slice(0,16)}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' })
    .then(v => ({ pdf_id: id, ...v })),
)

const rows = results.filter(Boolean)
log(`Extraction done: ${rows.length}/${IDS.length} rows verified`)
return { count: rows.length, rows }
