# Column schema — precise extraction rule per column (35 columns)

The order below is the exact column order written to the Excel. Cells are in
**English**, concise, no raw multi-paragraph dumps. Absent information = the
literal string `Not reported`. Never infer a value the paper does not support;
when in doubt, state the uncertainty and add the column to `Fields to verify`.

| # | Column | Rule |
|---|--------|------|
| 1 | PDF name | The source filename, e.g. `1-s2.0-S....-main.pdf`. Identity key. |
| 2 | Paper title | Exact title from the first page text (PDF metadata is often empty — do not trust it). |
| 3 | Authors | FULL author list exactly as printed on the first page, comma-separated. Not "et al." |
| 4 | Year | Publication year only (4 digits). |
| 5 | Publisher / venue | ONLY journal/venue name + publisher, e.g. `Journal of Energy Storage, Elsevier`. NO year, NO volume, NO issue, NO page numbers, NO DOI (those have their own columns). |
| 6 | DOI / link | The DOI (prefer `https://doi.org/...`). |
| 7 | Target task | Controlled vocabulary — exactly one of: `SOH / capacity estimation`, `RUL / lifetime prediction`, `Both (SOH + RUL)`, `Other / Not reported`. No explanation here. |
| 8 | Target definition | How the target is defined: e.g. SOH = C/C_initial×100%; EOL/RUL threshold (80%, 70%…); what exactly is predicted. Put task nuance here, not in column 7. |
| 9 | Battery chemistry | Chemistry (LFP, NMC, NCA, LCO, LMO, LTO, Li-ion generic) + form factor when stated (18650, 21700, cylindrical, pouch, prismatic, coin). If form factor is only *inferred*, say so and flag it — do not assert 18650/cylindrical unless the paper says it. |
| 10 | Cell / module / pack level | Cell / module / pack (or combination). |
| 11 | Dataset | Dataset(s) actually used for the experiments (not ones merely cited in related work). Name + brief provenance (public benchmark vs self-built lab platform, cells/batches used). |
| 12 | Public dataset? | `Yes` (+ names: NASA PCoE, CALCE, Oxford, MIT-Stanford/Severson, HUST, XJTU, Sandia, Tongji, MATR, Mendeley, Zenodo, Battery Archive, HNEI, Kaggle…) / `No (self-built)` / `Unclear`. Only count datasets used for the actual work. |
| 13 | Experimental conditions | Cycling protocol: charge/discharge mode (CC, CV, CCCV), C-rate(s), temperature(s), number of cycles, rest periods, sampling, EOL criterion. Concise. |
| 14 | Input data type | RAW measured signals ONLY: voltage, current, temperature, capacity, time, cycle index. This is the raw side of the raw-vs-features split. If the paper visualizes a signal but does not feed it to the model, say so. |
| 15 | Data preparation | Preprocessing actually described: normalization, denoising, decomposition (VMD/EMD/CEEMDAN), sliding-window/sequence construction, feature selection, train/test split mechanics. If none described → `Not reported`. |
| 16 | Feature extraction | ENGINEERED/derived features ONLY, and for EACH feature its **formula verbatim** (read equation images if not in the text) or a textual description if no formula. Format as a list `Feature: formula/description`. Examples: CCCT, CVCT, IC/dQdV peaks, DV/dVdQ, internal resistance, EIS features, statistical/entropy/wavelet features, health indicators. If the model learns features automatically from raw sequences (e.g. CNN/TCN/autoencoder feature learning), state that explicitly and put `Engineered features: Not reported (none; learned automatically)` — do NOT fabricate formulas. |
| 17 | Model category | High level: Deep learning / Machine learning / Hybrid-fusion / Optimisation-aided / Physics-informed, with the family names in parentheses. |
| 18 | NN architecture | Precise architecture and how blocks connect, e.g. `CNN-LSTM`, `TCN-GRU-Attention`, `SSA-CNN-BiLSTM`, `Transformer`, `CAE-DNN`, `KAN-HDBLSTM-AM`. Note key hyperparameters if given. |
| 19 | Training strategy | Optimizer, loss, learning rate, epochs, batch size, hardware/software if stated, transfer learning, optimisation algorithm (BO/PSO/SSA…). |
| 20 | Validation strategy | How it was validated: hold-out, k-fold, leave-one-battery-out, cross-condition, cross-dataset. If the paper says "cross-validation" but actually does a single split, say so honestly. |
| 21 | Baseline models | Models compared against, with key config if given. |
| 22 | Metrics reported | Which metrics: RMSE, MAE, MAPE, MSE, R², relative error, precision, recall, F1, accuracy. List exactly what the paper reports (and note if a common one like R² is absent). |
| 23 | Main results | Concise narrative of the BEST results and the headline claim. Numbers must be the paper's. Note internal inconsistencies if the abstract and conclusion disagree. |
| 24 | Generalisation tested? | Yes/partial/no + how (multi-dataset, cross-condition, cross-chemistry, cross-temperature). Be precise about the limits. |
| 25 | Code/data available? | Code availability + data availability separately (public / on request / not reported). |
| 26 | Advantages | The approach's genuine strengths as argued/evidenced in the paper. |
| 27 | Limitations | Stated + clearly-evident limitations (single dataset, one chemistry, no R², no UQ, no code, deployment complexity, early-cycle underfitting…). |
| 28 | Relevance to my review | One line: how relevant and why (task + architecture + dataset angle). |
| 29 | Notes | Anything important not captured above (e.g. typo in the paper, page coverage). |
| 30 | Architecture (plain-language) | 1–2 simple sentences a non-expert understands: what the network is and how data flows in (raw vs features → blocks → output). |
| 31 | Input representation | Controlled: `Raw sequences` / `Engineered features` / `Hybrid` / `Unclear`. The clean classifier of the raw-vs-features question. |
| 32 | Results (structured) | The PROPOSED model's BEST metrics as a clean list, e.g. `RMSE=2.39%; MAE=2.07%; R2=0.99`. Prefer numbers read from result tables/figures. If only formulas (no values) are present → `Only formulas found — Not reported`. |
| 33 | Results source + page | Where each value came from: text / table / figure + page number(s), e.g. `RMSE from Table 4, p.8; MAE from Fig.10, p.11`. This is the traceability column. |
| 34 | Extraction confidence | `High` / `Medium` / `Low`, set by the verifier. |
| 35 | Fields to verify (manual) | Semicolon list of the field names the verifier was not fully sure about (especially image-derived values). These cells are highlighted yellow in the Excel. |
