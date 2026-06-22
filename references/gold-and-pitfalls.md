# Gold example + real pitfalls

This is the standard to match. The row below is a real, human-approved
extraction. The pitfalls after it are real mistakes the adversarial verifier
caught during validation — hunt for these patterns specifically.

## Gold-standard row (paper: TCN-GRU-Attention SOH, 025040_1_5.0243760.pdf)

- **Authors**: Yong Liu, Sangyu Lai, Yunqiang Mai, Wencan Zhang, Hancheng He
- **Year**: 2025
- **Publisher / venue**: `AIP Advances, AIP Publishing`  ← journal + publisher only
- **DOI / link**: https://doi.org/10.1063/5.0243760
- **Target task**: `SOH / capacity estimation`  ← controlled value, no prose
- **Target definition**: SOH = (C / C_initial) × 100%; trajectory predicted cycle-by-cycle from 100% down to 50% (experiment stops at SOH=50%). No RUL/EOL prediction.
- **Battery chemistry**: Li-ion, NMC cathode Li(NiCoMn)O2 / graphite anode; 3.15 Ah, 3.7 V nominal, 4.2/2.5 V cut-offs (Table II). Form factor NOT explicitly stated → flagged.
- **Dataset / Public dataset?**: Self-built lab dataset (Neware tester, 25 °C chamber); 1C/2C/3C, set #1 train / #2 test. → `No (self-built)`.
- **Experimental conditions**: CCCV charge (1C CC→4.2 V, CV→0.05C), CC discharge at 1C/2C/3C→2.5 V, 25 °C, 30-min rests, 5 s sampling, stop at SOH=50%.
- **Input data type** (raw only): charging voltage + 3-point surface temperature (positive/middle/negative pole). Current & capacity are visualized but are not the described model inputs → noted.
- **Feature extraction** (engineered only, with formulas): none hand-crafted; features learned by the TCN. Equations are network ops, not features: causal conv `h_t=f(x_t*W+b)` (Eq.2), dilated conv (Eq.3), residual `o_t=h_t+x_t` (Eq.4). → `Engineered features: Not reported (none; learned automatically)`.
- **NN architecture**: TCN-GRU-Attention (multi-channel dilated-causal TCN, k=2, expansion 2^i, ReLU+Dropout+residual → GRU → self-attention).
- **Architecture (plain-language)**: Raw charging voltage and three temperatures are fed as channels into a temporal CNN that learns time patterns of degradation; a GRU models the sequence and a self-attention layer weights the key time steps to output SOH.
- **Input representation**: `Raw sequences`
- **Metrics reported**: ME, MAE, MSE, RMSE (%). No R².
- **Results (structured)**: `RMSE=2.39%; MAE=2.07%; MSE=0.06%; ME=1.48% (1C, best); R2=Not reported` (2C: RMSE=3.43%, MAE=2.64%; 3C: RMSE=3.16%, MAE=2.14%).
- **Results source + page**: Table III, p.12 (confirmed in rendered page_12.png) + text p.10.
- **Extraction confidence**: High. **Fields to verify**: battery_chemistry (form factor inferred); input_data_type (current/capacity input vs analysis-only).

What makes it gold: controlled `Target task`; clean `Publisher`; full `Authors`;
raw vs features strictly separated with the honest "learned automatically" note
instead of fabricated formulas; every number traced to a table/figure/page, one
of them confirmed *from the image*; genuine uncertainties flagged, not hidden.

## Real pitfalls the verifier must hunt for

These all happened on real papers in this corpus. Default to skepticism.

1. **Unsupported form factor.** Draft asserted `18650`/`cylindrical` from thermal
   conductivity hints. The paper never said it. → Remove; state "inferred" and flag.
2. **Wrong chemistry by association.** Draft wrote "NASA cells are commonly
   LCO/NMC". NASA PCoE uses A123 cells = **LFP** in several batches. Do not guess
   chemistry from the dataset name → `Not reported` unless the paper states it.
3. **Misread image-table.** "B0007 EOL = None" was wrong — "None" sat in the
   *Reference* column of the table, not the EOL column. Re-read the enlarged image
   crop before trusting a cell read from a figure.
4. **Stray unit/percent.** A draft added a `%` to an MAE that was reported without
   one. Copy units exactly as printed.
5. **Fabricated features.** When a model learns features automatically (CNN/TCN/
   autoencoder), there are no hand-crafted formulas. Writing invented feature
   formulas is a serious error → say "learned automatically; none engineered".
6. **"Cross-validation" that isn't.** Papers often call a single train/test split
   "cross-validation". Report what was actually done.
7. **Datasets from related work.** Only count datasets used for the actual
   experiments, not ones cited in the literature review.
8. **Untraceable metric.** If a number cannot be tied to a specific table/figure/
   page, it is not a fact → `Not reported` or flag as uncertain.
9. **Abstract vs conclusion mismatch.** Reduction percentages sometimes differ
   between abstract and conclusion. Note the inconsistency rather than picking one
   silently.

## What the verifier returns
A corrected `row`, per-field `field_verdicts` (confirmed/corrected/uncertain +
reason), `corrections_made`, an `overall_confidence`, and the final
`uncertain_fields` list (these become the yellow cells). Bias toward marking
uncertain over asserting — the human fact-check is the safety net for publication.
