# Raiatea pilot: checklist di accettazione end-to-end

Questa checklist permette a un valutatore non tecnico di verificare il primo pilot locale completo.

## 1. Prerequisiti

- Python 3.12 o una versione Python 3 recente;
- un browser moderno;
- una copia del repository;
- porta locale `8000` libera.

Non servono account, API key, cloud o connessione internet durante l'uso del pilot già costruito.

## 2. Costruzione

Dalla radice del repository scegliere una destinazione che non esiste:

```bash
python prototype/pedagogical-module/build/build_pilot.py \
  --output /tmp/raiatea-pilot-acceptance
```

**Esito atteso:** il terminale stampa `/tmp/raiatea-pilot-acceptance` e la directory contiene `index.html`, i due moduli, `pilot-manifest.json` e `pilot-dashboard.js`.

Ripetendo lo stesso comando senza eliminare la directory, il builder deve rifiutare la sovrascrittura e lasciare intatti i file esistenti.

## 3. Avvio e arresto

Avviare:

```bash
python -m http.server 8000 \
  --bind 127.0.0.1 \
  --directory /tmp/raiatea-pilot-acceptance
```

Aprire:

```text
http://127.0.0.1:8000/index.html
```

Per arrestare il server premere `Ctrl+C` nel terminale.

## 4. Percorso da verificare

1. La pagina iniziale mostra due moduli, entrambi **Non iniziato**, e consiglia il primo.
2. La guida distingue dashboard, riepilogo del modulo ed export JSON del singolo modulo.
3. Premere **Inizia il percorso**.
4. Nel primo modulo, alla domanda “Questa figura mostra già tutti i calcoli dell'attention?”, scegliere **Sì**.
5. Compare **Recupero mirato**. Alla domanda di recupero scegliere **Si calcolano score, pesi e una somma pesata**.
6. Premere **Torna alla domanda originale**, poi scegliere **No**. Compare il feedback corretto.
7. Scorrere a **Riepilogo del percorso**: deve risultare un tentativo corretto dopo recupero, non un voto o un mastery score.
8. Usare il link di percorso per aprire **Query, Key e Value nella self-attention**. Nessun blocco impedisce la navigazione.
9. Alla prima domanda scegliere **Dallo stesso embedding con matrici diverse**.
10. Nel riepilogo del secondo modulo deve comparire almeno `1/3 verifiche completate`.
11. Prima del click non deve essere scaricato alcun file. Premere **Esporta evidenze JSON**.
12. Il browser scarica `query-key-value-evidence-v1.json`.
13. Il JSON indica formato `raiatea-learner-evidence`, versione `1`, modulo `query-key-value` e contiene solo osservazioni del modulo corrente.
14. Tornare all'**Indice del pilot**. Entrambi i moduli risultano **In corso** e il consiglio resta sul primo modulo, ancora incompleto.
15. Tutti i link restano disponibili e non vengono richiesti login o servizi esterni.

## 5. Controlli di privacy e non distruttività

Dopo l'export:

- il progresso dei moduli è ancora presente;
- la dashboard mostra gli stessi stati derivati;
- le preferenze di lettura non cambiano;
- eventuali altre chiavi del browser non vengono incluse nel file né modificate;
- non avvengono upload, analytics, telemetria o richieste verso domini esterni;
- il file riguarda un solo modulo e non è un portfolio completo del percorso.

## 6. Risoluzione dei problemi

- **Il browser non apre la pagina:** verificare che il terminale del server sia ancora attivo e usare esattamente l'indirizzo `127.0.0.1:8000`.
- **La porta è occupata:** sostituire `8000` con una porta libera sia nel comando sia nell'indirizzo.
- **La build rifiuta la destinazione:** scegliere una nuova directory oppure eliminare esplicitamente solo la precedente directory di prova.
- **Il download non compare:** controllare che il browser non blocchi i download locali e premere nuovamente il pulsante esplicito nel modulo.
- **Gli stati sembrano già avanzati:** cancellare i dati del sito locale dal browser oppure usare una nuova porta per una prova isolata.

## 7. Verbale pass/fail

```text
Data:
Valutatore:
Sistema operativo e browser:

[ ] Build completata
[ ] Rifiuto sovrascrittura verificato
[ ] Launcher e due moduli raggiungibili
[ ] Remediation completata
[ ] Dashboard aggiornata
[ ] Riepilogo verificato
[ ] Export v1 scaricato e controllato
[ ] Nessuna richiesta esterna osservata
[ ] Stato locale invariato dopo export

Esito finale: PASS / FAIL
Note:
```
