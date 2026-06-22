# Column schema — precise extraction rule per column (35 columns)

Domain-agnostic: works for any paper that uses ML / neural networks / AI to
predict an output (energy, medicine, finance, materials, NLP, vision, …). The
order below is the exact column order written to the Excel. Cells are in
**English**, concise, no raw multi-paragraph dumps. Absent information = the
literal string `Not reported`. Never infer a value the paper does not support;
when in doubt, state the uncertainty and add the column to `Fields to verify`.

| # | Column | Rule |
|---|--------|------|
| 1 | PDF name | The source filename. Identity key. |
| 2 | Paper title | Exact title from the first page text (PDF metadata is often empty — do not trust it). |
| 3 | Authors | FULL author list exactly as printed on the first page, comma-separated. Not "et al." |
| 4 | Year | Publication year only (4 digits). |
| 5 | Publisher / venue | ONLY journal/conference name + publisher, e.g. `IEEE Transactions on Neural Networks, IEEE` or `NeurIPS`. NO year, NO volume, NO issue, NO page numbers, NO DOI (those have their own columns). |
| 6 | DOI / link | The DOI (prefer `https://doi.org/...`). |
| 7 | Application domain | The field/problem the paper addresses, specifically: e.g. `Li-ion battery SOH`, `diabetic-retinopathy screening`, `short-term electricity load forecasting`, `credit-default prediction`, `protein secondary structure`. This is what makes the matrix domain-agnostic. |
| 8 | Prediction target / task | What output is predicted + the ML task type (regression / classification / forecasting / segmentation / detection / ranking …). Concise; no long prose. |
| 9 | Target definition | Precise definition of the predicted quantity/label: units, thresholds, forecast horizon, class set, how ground truth is defined. |
| 10 | Data modality | Nature of the data: time-series, tabular, images, text, audio, sensor signals, spectra, graph, multimodal… + key specifics (sampling rate, image resolution, sequence length). |
| 11 | Dataset | Dataset(s) actually used for the experiments (not ones merely cited in related work). Name + brief provenance (public benchmark vs self-collected). |
| 12 | Public dataset? | `Yes` (+ names) / `No (self-collected/proprietary)` / `Unclear`. Only count datasets used for the actual work. |
| 13 | Experimental setup | The protocol: how data was acquired or split by condition, operating conditions, environment, acquisition/measurement protocol. Concise. (For a battery paper this is the cycling protocol; for imaging, the acquisition/labelling protocol; etc.) |
| 14 | Input variables (raw) | RAW measured/observed inputs fed to the model — the raw side of the raw-vs-features split. E.g. raw sensor channels, pixel arrays, raw token sequences, raw time-series. If a signal is shown but not fed to the model, say so. |
| 15 | Data preparation | Preprocessing actually described: normalization, denoising, decomposition, resampling, augmentation, sliding-window/sequence construction, feature selection, train/test split mechanics. If none → `Not reported`. |
| 16 | Feature extraction | ENGINEERED/derived features ONLY, and for EACH feature its **formula verbatim** (read equation images if not in the text) or a textual description if no formula. Format `Feature: formula/description`. If the model learns features automatically (CNN/Transformer/autoencoder/end-to-end), state that explicitly and write `Engineered features: Not reported (none; learned automatically)` — do NOT fabricate formulas. |
| 17 | Model category | High level: Deep learning / classical ML / hybrid-fusion / physics-informed / optimisation-aided, with the family names in parentheses. |
| 18 | Model / NN architecture | Precise architecture and how blocks connect, e.g. `CNN-LSTM`, `Transformer`, `U-Net`, `GNN`, `TCN-GRU-Attention`, `XGBoost`. Note key hyperparameters if given. |
| 19 | Training strategy | Optimizer, loss, learning rate, epochs, batch size, hardware/software if stated, transfer learning, optimisation algorithm (BO/PSO/GA…). |
| 20 | Validation strategy | How validated: hold-out, k-fold, leave-one-X-out, cross-condition, cross-dataset, temporal split. If the paper says "cross-validation" but actually does a single split, say so honestly. |
| 21 | Baseline models | Models compared against, with key config if given. |
| 22 | Metrics reported | Which metrics the paper reports: RMSE, MAE, MAPE, MSE, R², relative error, accuracy, precision, recall, F1, AUC, IoU, Dice… (and note if a common one is absent). |
| 23 | Main results | Concise narrative of the BEST results and the headline claim. Numbers must be the paper's. Note internal inconsistencies if the abstract and conclusion disagree. |
| 24 | Generalisation tested? | Yes/partial/no + how (multi-dataset, cross-condition, cross-domain, external test set). Be precise about the limits. |
| 25 | Code/data available? | Code availability + data availability separately (public / on request / not reported). |
| 26 | Advantages | The approach's genuine strengths as argued/evidenced in the paper. |
| 27 | Limitations | Stated + clearly-evident limitations (single dataset, narrow conditions, missing metric, no uncertainty quantification, no code, deployment complexity…). |
| 28 | Relevance to my review | One line: how relevant and why (task + architecture + dataset angle). |
| 29 | Notes | Anything important not captured above (e.g. typo in the paper, page coverage). |
| 30 | Architecture (plain-language) | 1–2 simple sentences a non-expert understands: what the model is and how data flows in (raw vs features → blocks → output). |
| 31 | Input representation | Controlled: `Raw sequences` / `Engineered features` / `Hybrid` / `Unclear`. The clean classifier of the raw-vs-features question. |
| 32 | Results (structured) | The PROPOSED model's BEST metrics as a clean list, e.g. `RMSE=2.39%; MAE=2.07%; R2=0.99` or `Accuracy=0.94; F1=0.93; AUC=0.97`. Prefer numbers read from result tables/figures. If only formulas (no values) → `Only formulas found — Not reported`. |
| 33 | Results source + page | Where each value came from: text / table / figure + page number(s), e.g. `RMSE from Table 4, p.8; F1 from Fig.10, p.11`. This is the traceability column. |
| 34 | Extraction confidence | `High` / `Medium` / `Low`, set by the verifier. |
| 35 | Fields to verify (manual) | Semicolon list of the field names the verifier was not fully sure about (especially image-derived values). These cells are highlighted yellow in the Excel. |
