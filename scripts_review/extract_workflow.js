// extract_workflow.js — canonical extraction+verification workflow for ML / neural-network
// research papers (ANY domain: the model predicts some output and the paper reports it).
//
// Invoked from Claude Code with:
//   Workflow({ scriptPath: ".../extract_workflow.js", args: { workRoot, ids } })
// args.workRoot = absolute path to the work/ dir produced by preprocess.py
// args.ids      = array of pdf_id (the sub-folder names inside work/)
//
// One isolated extractor agent per PDF (text + tables + VISION on rendered result pages),
// then one ADVERSARIAL verifier agent per PDF. Returns { count, rows } where each row is
// the verified record. Writing the .xlsx is done OUTSIDE by write_excel.py (deterministic).

export const meta = {
  name: 'ml-litreview-extract',
  description: 'Extract + adversarially verify 35-field literature-review rows from ML/NN research PDFs (1 agent per PDF, vision on result figures)',
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
  required: ['pdf_name','paper_title','authors','year','publisher_venue','doi_link','application_domain','target_task','target_definition','data_modality','dataset','public_dataset','experimental_conditions','input_data_type','data_preparation','feature_extraction','model_category','nn_architecture','training_strategy','validation_strategy','baseline_models','metrics_reported','main_results','generalisation_tested','code_data_available','advantages','limitations','relevance','architecture_plain','input_representation','results_structured','results_source_page','extraction_confidence','uncertain_fields','notes'],
  properties: {
    pdf_name: { type: 'string' }, paper_title: { type: 'string' },
    authors: { type: 'string', description: 'FULL author list exactly as printed on the first page, comma-separated' },
    year: { type: 'string' },
    publisher_venue: { type: 'string', description: 'ONLY journal/conference name + publisher, e.g. "IEEE Transactions on Neural Networks, IEEE" or "NeurIPS". NO year, NO volume, NO issue, NO page numbers, NO DOI.' },
    doi_link: { type: 'string' },
    application_domain: { type: 'string', description: 'The field/problem the paper addresses, e.g. "Li-ion battery SOH", "medical image diagnosis", "electricity load forecasting", "credit-default prediction", "protein structure". Be specific.' },
    target_task: { type: 'string', description: 'What output is predicted and the ML task type (regression / classification / forecasting / segmentation / detection ...). Concise; put nuance in target_definition.' },
    target_definition: { type: 'string', description: 'Precise definition of the predicted quantity/label: units, thresholds, horizon, classes, how ground truth is defined.' },
    data_modality: { type: 'string', description: 'Nature of the data: time-series, tabular, images, text, audio, sensor signals, spectra, graph, multimodal, etc. (+ key specifics, e.g. sampling rate, image resolution).' },
    dataset: { type: 'string', description: 'Dataset(s) actually used for the experiments (not merely cited). Name + brief provenance (public benchmark vs self-collected).' },
    public_dataset: { type: 'string', description: 'Yes (+names of public datasets) / No (self-collected/proprietary) / Unclear. Only count datasets used for the actual work.' },
    experimental_conditions: { type: 'string', description: 'Experimental setup / protocol: how data was collected or split by condition, operating conditions, environment, acquisition protocol. Concise.' },
    input_data_type: { type: 'string', description: 'RAW measured/observed inputs fed to the model (the raw side of raw-vs-features), e.g. raw sensor channels, pixel arrays, raw token sequences, raw time-series.' },
    data_preparation: { type: 'string', description: 'Preprocessing actually described: normalization, denoising, decomposition, resampling, augmentation, windowing/sequence construction, feature selection, train/test split mechanics.' },
    feature_extraction: { type: 'string', description: 'ENGINEERED/derived features ONLY. For EACH feature give its FORMULA verbatim (read equation images if not in text) or a textual description if no formula, as a list "Feature: formula/description". If features are learned automatically (CNN/Transformer/autoencoder), say so and write "Engineered features: Not reported (none; learned automatically)" — do NOT fabricate formulas.' },
    model_category: { type: 'string', description: 'High level: Deep learning / classical ML / hybrid-fusion / physics-informed / optimisation-aided, with family names.' },
    nn_architecture: { type: 'string', description: 'Precise architecture and how blocks connect, e.g. CNN-LSTM, Transformer, U-Net, GNN, TCN-GRU-Attention. Note key hyperparameters if given.' },
    training_strategy: { type: 'string' },
    validation_strategy: { type: 'string', description: 'How validated: hold-out, k-fold, leave-one-X-out, cross-condition, cross-dataset. If the paper says "cross-validation" but does a single split, say so.' },
    baseline_models: { type: 'string' },
    metrics_reported: { type: 'string', description: 'Which metrics: RMSE, MAE, MAPE, MSE, R2, accuracy, precision, recall, F1, AUC, IoU, etc. Note if a common one is absent.' },
    main_results: { type: 'string', description: 'Concise narrative of the BEST results and headline claim; numbers must be the paper\'s; note abstract-vs-conclusion inconsistencies.' },
    generalisation_tested: { type: 'string' },
    code_data_available: { type: 'string', description: 'Code availability + data availability separately (public / on request / not reported).' },
    advantages: { type: 'string' }, limitations: { type: 'string' },
    relevance: { type: 'string', description: 'One line: how relevant and why (task + architecture + dataset angle).' },
    architecture_plain: { type: 'string', description: 'PLAIN-LANGUAGE 1-2 sentences a non-expert understands: what the model is and how data flows in (raw vs features -> blocks -> output).' },
    input_representation: { type: 'string', enum: ['Raw sequences','Engineered features','Hybrid','Unclear'] },
    results_structured: { type: 'string', description: 'Proposed model best results as a clean metric=value list, e.g. "RMSE=2.39%; MAE=2.07%; R2=0.99" or "Accuracy=0.94; F1=0.93". Prefer numbers read from result tables/figures; if only formulas, write "Only formulas found — Not reported".' },
    results_source_page: { type: 'string', description: 'Where each value came from: text/table/figure + page number(s).' },
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

const extractorPrompt = (id) => `You are a senior researcher and ML/deep-learning expert doing a rigorous literature review that will be PUBLISHED. The papers apply machine learning / neural networks / AI to PREDICT some output; they can come from ANY field (energy, medicine, finance, materials, NLP, vision, engineering...). Accuracy is legally critical: NEVER invent a value. If something is not explicitly in the paper, write exactly "Not reported".

Source of truth bundle: ${WORK}/${id}/
1. Read ${WORK}/${id}/text.txt (markers "[PAGE n/total]").
2. Read ${WORK}/${id}/tables.txt
3. Run: ls ${WORK}/${id}/page_*.png — then use the Read tool on EVERY PNG to VISUALLY read figures/result tables. Metric values often live only inside images; read them from there.

Fill the 35-field schema in ENGLISH. Rules:
- pdf_name = "${id}.pdf". Title/authors/year/venue/DOI from first-page text (PDF metadata may be empty).
- authors: FULL author list as printed on the first page, comma-separated.
- publisher_venue: ONLY journal/conference name + publisher. No year, volume, issue, pages or DOI.
- application_domain: be specific about the field and problem (e.g. "battery SOH", "diabetic-retinopathy screening", "short-term load forecasting").
- target_task: what is predicted + ML task type (regression/classification/forecasting/...). Put nuance in target_definition.
- data_modality: time-series / tabular / images / text / sensor signals / spectra / graph / multimodal (+ key specifics).
- input_data_type = RAW inputs ONLY; feature_extraction = ENGINEERED features ONLY, each WITH its formula (read equation images if needed) or a description; "Feature: formula/description". If features are learned automatically, say so — do not fabricate formulas. Keep raw vs engineered strictly separated.
- input_representation: one enum value.
- architecture_plain: 1-2 simple sentences (what the model is, how data flows in).
- results_structured: proposed model BEST metrics as "metric=value; ..."; prefer numbers read from tables/figures; if only formulas, write "Only formulas found — Not reported".
- results_source_page: cite table/figure + page for each value.
- extraction_confidence + uncertain_fields: list every field you are unsure about (especially image-derived) for human verification.
Concise, clean cells. Return ONLY the structured object.`

const verifierPrompt = (id, extracted) => `You are an ADVERSARIAL fact-checker for an ML literature review that will be PUBLISHED. Try to REFUTE the draft below, then return a corrected, trustworthy row. Default to "uncertain" if the paper does not clearly support a field. NEVER invent values.

Bundle: ${WORK}/${id}/  (re-read text.txt, tables.txt; run "ls ${WORK}/${id}/page_*.png" and Read each PNG).

DRAFT (JSON):
${JSON.stringify(extracted, null, 2)}

Re-verify especially: authors (full list), publisher_venue (must be ONLY venue+publisher — strip any year/volume/issue/pages/DOI), application_domain, target_task, data_modality, nn_architecture, input_data_type vs feature_extraction split (EACH engineered feature must include its formula or a textual description — add it from equation images if missing; do not fabricate formulas for auto-learned features), input_representation, dataset + public_dataset, metrics_reported, results_structured (every number must be traceable to a table/figure/page — if not traceable, set "Not reported" or mark uncertain), year/DOI. Correct any error. Fill field_verdicts, corrections_made, overall_confidence, final uncertain_fields. Return ONLY the structured object with the full corrected row in "row".`

const results = await pipeline(
  IDS,
  (id) => agent(extractorPrompt(id), { label: `extract:${id.slice(0,16)}`, phase: 'Extract', schema: ROW_SCHEMA }),
  (extracted, id) => agent(verifierPrompt(id, extracted), { label: `verify:${id.slice(0,16)}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' })
    .then(v => ({ pdf_id: id, ...v })),
)

const rows = results.filter(Boolean)
log(`Extraction done: ${rows.length}/${IDS.length} rows verified`)
return { count: rows.length, rows }
