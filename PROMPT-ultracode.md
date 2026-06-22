# PROMPT FINALE — run ultracode su tutti i 117 PDF (1 agente per file)

> Incolla TUTTO il blocco qui sotto nella sessione Claude Code già aperta
> (lanciata con skip-permission). La parola `ultracode` abilita il workflow
> multi-agente. Tempo atteso ~45-75 min. Output finale anche in ~/Downloads.

---

ultracode.

Sei in un task di **literature review pubblicabile** su paper di Machine Learning per batterie al litio (RUL — Remaining Useful Life, e SOH — State of Health). L'output è destinato a pubblicazione: un errore può avere conseguenze legali, quindi la regola assoluta è **non inventare mai un dato** (assente = "Not reported"; numero non tracciabile a tabella/figura/pagina = non è un fatto).

Usa la skill **battery-lit-review-extractor** (in ~/.claude/skills/): leggi il suo SKILL.md e i file in references/ e segui ESATTAMENTE quel pattern (estrattore + verificatore avversariale, 1 agente per PDF, lettura VISION delle figure dei risultati). Non improvvisare uno schema tuo: usa le 35 colonne e le regole della skill.

Progetto: /Users/francescozattoni/Sviluppo/battery-lit-review
- pdfs/ → 117 PDF da analizzare (già scompattati; se vuota, scompatta da ~/Downloads/wetransfer_ml_main-zip_2026-06-19_0919/ML_main.zip e ML_backup.zip)
- model_template.xlsx → modello colonne (NON modificarlo)
- output/ → qui va l'Excel finale

Esegui i 3 stadi della skill (gli script sono in ~/.claude/skills/battery-lit-review-extractor/scripts/):

1) PRE-PROCESSING (deterministico):
   cd /Users/francescozattoni/Sviluppo/battery-lit-review
   python3 ~/.claude/skills/battery-lit-review-extractor/scripts/preprocess.py pdfs work --max-render 6 --dpi-zoom 2.0
   python3 -c "import json; ids=[d['pdf_id'] for d in json.load(open('work/_index.json')) if 'pdf_id' in d]; json.dump(ids, open('work/_ids.json','w')); print(len(ids),'bundles')"

2) ESTRAZIONE + VERIFICA (workflow, 1 agente per PDF). Leggi gli id da work/_ids.json e invoca il workflow bundlato:
   Workflow({ scriptPath: "/Users/francescozattoni/.claude/skills/battery-lit-review-extractor/scripts/extract_workflow.js",
              args: { workRoot: "/Users/francescozattoni/Sviluppo/battery-lit-review/work", ids: <array da work/_ids.json> } })
   Quando il workflow termina: il risultato in contesto è TRONCATO. Leggi il file output del task indicato dalla notifica di completamento (/private/tmp/.../tasks/<task-id>.output), fai json.load, prendi ["result"] (cioè {count, rows}) e salvalo in output/verified_rows.json.

3) SCRITTURA EXCEL (deterministico):
   python3 ~/.claude/skills/battery-lit-review-extractor/scripts/write_excel.py output/verified_rows.json model_template.xlsx output/battery_ml_review_FILLED.xlsx
   cp output/battery_ml_review_FILLED.xlsx ~/Downloads/battery_ml_review_FILLED.xlsx

VERIFICA FINALE (obbligatoria, riportami i numeri):
   python3 - <<'PY'
   import openpyxl, json
   ws = openpyxl.load_workbook("output/battery_ml_review_FILLED.xlsx")["Review_Matrix"]
   ids = json.load(open("work/_ids.json"))
   print("Righe dati:", ws.max_row-1, "| Colonne:", ws.max_column, "| PDF attesi:", len(ids), "| match righe:", ws.max_row-1==len(ids))
   PY
Atteso: righe == 117, colonne == 35.

VINCOLI (non derogabili): mai inventare (Not reported); leggere le immagini delle pagine-risultati per le metriche; raw signals e feature engineered separati; ogni feature engineered con formula o descrizione; Publisher = solo rivista + editore; Authors = lista completa; lingua celle in inglese; celle incerte in giallo + colonna "Fields to verify". NON modificare model_template.xlsx né i PDF. Nessun git, nessun push, nessuna credenziale. I PDF sono paper pubblici: nessun dato personale.

Quando hai finito, dimmi: righe/colonne della verifica finale, quante celle gialle (da verificare a mano), e il path dei due file Excel (output/ e ~/Downloads/).
