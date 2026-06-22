# Gold example + real pitfalls

This is the standard to match. The worked row below comes from the **battery
domain** (the corpus the pipeline was first validated on), but it illustrates the
**general method** — the same discipline applies to any field (medicine, finance,
vision, NLP…). The pitfalls after it are real mistakes the adversarial verifier
caught during validation; hunt for these patterns in every domain.

## Gold-standard row (worked example — battery SOH domain)

Paper: *TCN-GRU-Attention SOH prediction* (`025040_1_5.0243760.pdf`)

- **Authors**: Yong Liu, Sangyu Lai, Yunqiang Mai, Wencan Zhang, Hancheng He
- **Year**: 2025
- **Publisher / venue**: `AIP Advances, AIP Publishing`  ← venue + publisher only
- **DOI / link**: https://doi.org/10.1063/5.0243760
- **Application domain**: Li-ion battery State-of-Health (SOH) estimation
- **Prediction target / task**: SOH / capacity estimation (regression; SOH trajectory cycle-by-cycle)
- **Target definition**: SOH = (C / C_initial) × 100%; predicted from 100% down to 50% (experiment stops at SOH=50%). No RUL/EOL prediction.
- **Data modality**: Time-series of charging signals (voltage + 3-point temperature), 5 s sampling.
- **Dataset / Public dataset?**: Self-built lab dataset (Neware tester, 25 °C chamber); 1C/2C/3C, set #1 train / #2 test → `No (self-collected)`.
- **Experimental setup**: CCCV charge (1C CC→4.2 V, CV→0.05C), CC discharge at 1C/2C/3C→2.5 V, 25 °C, 30-min rests, stop at SOH=50%.
- **Input variables (raw)**: charging voltage + 3-point surface temperature. Current & capacity are visualized but are not the described model inputs → noted.
- **Feature extraction** (engineered only, with formulas): none hand-crafted; features learned by the TCN. Equations are network ops, not features → `Engineered features: Not reported (none; learned automatically)`.
- **Model / NN architecture**: TCN-GRU-Attention (multi-channel dilated-causal TCN → GRU → self-attention).
- **Architecture (plain-language)**: Raw charging voltage and three temperatures are fed as channels into a temporal CNN that learns time patterns of degradation; a GRU models the sequence and a self-attention layer weights the key time steps to output SOH.
- **Input representation**: `Raw sequences`
- **Metrics reported**: ME, MAE, MSE, RMSE (%). No R².
- **Results (structured)**: `RMSE=2.39%; MAE=2.07%; MSE=0.06%; ME=1.48% (1C, best); R2=Not reported` (2C: RMSE=3.43%; 3C: RMSE=3.16%).
- **Results source + page**: Table III, p.12 (confirmed in rendered page_12.png) + text p.10.
- **Extraction confidence**: High. **Fields to verify**: data_modality/raw inputs (current/capacity input vs analysis-only).

What makes it gold: clean `Publisher`; full `Authors`; specific `Application
domain`; raw vs features strictly separated with an honest "learned
automatically" note instead of fabricated formulas; every number traced to a
table/figure/page, one of them confirmed *from the image*; genuine uncertainties
flagged, not hidden.

## Real pitfalls the verifier must hunt for (general)

These happened on real papers. Default to skepticism in any domain.

1. **Unsupported specifics.** Asserting a detail (a hardware/format/setting) the
   paper only *hints* at. State "inferred" and flag, or `Not reported`.
2. **Wrong attribute by association.** Inferring a property from a dataset name
   (e.g. guessing battery chemistry, patient population, or sensor type from the
   benchmark). Do not guess → `Not reported` unless the paper states it.
3. **Misread image-table.** A value read from the wrong cell of a figure/table.
   Re-read the enlarged image crop before trusting a number read from an image.
4. **Stray units/percent.** Adding or dropping a unit/`%` that the paper did not
   use. Copy units exactly as printed.
5. **Fabricated features.** When a model learns features automatically (CNN/
   Transformer/autoencoder/end-to-end), there are no hand-crafted formulas.
   Inventing feature formulas is a serious error → say "learned automatically".
6. **"Cross-validation" that isn't.** Papers often call a single train/test split
   "cross-validation". Report what was actually done.
7. **Datasets from related work.** Only count datasets used for the actual
   experiments, not ones cited in the literature review.
8. **Untraceable metric.** If a number cannot be tied to a specific table/figure/
   page, it is not a fact → `Not reported` or flag as uncertain.
9. **Abstract vs conclusion mismatch.** Headline numbers sometimes differ between
   abstract and conclusion. Note the inconsistency rather than picking one
   silently.

## What the verifier returns
A corrected `row`, per-field `field_verdicts` (confirmed/corrected/uncertain +
reason), `corrections_made`, an `overall_confidence`, and the final
`uncertain_fields` list (these become the yellow cells). Bias toward marking
uncertain over asserting — the human fact-check is the safety net for publication.
