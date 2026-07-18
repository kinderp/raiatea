# Raiatea pilot: avvio e prova

Questo README operativo descrive il primo pilot locale in due moduli:

1. **Il ruolo della self-attention nel modello GPT**;
2. **Query, Key e Value nella self-attention**.

L'ordine segue il percorso pedagogico canonico: prima si colloca la self-attention nel flusso del modello, poi si distinguono query, key e value. Il pilot non richiede account, cloud, API key o connessione di rete durante l'uso.

## Requisiti

- Python 3.12 o una versione Python 3 recente;
- un browser moderno.

## Costruzione

Dalla radice del repository, scegliere una destinazione che non esiste ancora:

```bash
python prototype/pedagogical-module/build/build_pilot.py \
  --output /tmp/raiatea-pilot
```

La directory contiene:

- `index.html`;
- `self-attention.html`;
- `query-key-value.html`;
- `pilot-manifest.json`.

Il builder non sovrascrive una destinazione esistente. Per ricostruire il pilot, eliminare esplicitamente una precedente directory usa-e-getta oppure scegliere un nuovo percorso.

## Avvio

```bash
python -m http.server 8000 \
  --bind 127.0.0.1 \
  --directory /tmp/raiatea-pilot
```

Aprire nel browser:

```text
http://127.0.0.1:8000/index.html
```

## Arresto

Tornare nel terminale del server e premere `Ctrl+C`.

## Checklist di prova

1. La pagina iniziale mostra i due moduli nell'ordine previsto.
2. **Inizia il percorso** apre il modulo di orientamento sulla self-attention.
3. I pulsanti degli step permettono di avanzare nel modulo.
4. Una risposta errata mostra il percorso di recupero previsto.
5. Il link **Query, Key e Value nella self-attention →** apre il secondo modulo.
6. Il link **← Il ruolo della self-attention nel modello GPT** torna al primo modulo.
7. **Indice del pilot** riporta alla pagina iniziale.
8. Ricaricando un modulo, il progresso locale resta disponibile nel browser.
9. L'esportazione delle evidenze resta esplicita e locale.
10. Nessuna pagina richiede login, rete, dati personali o servizi esterni.

## Limiti di questo incremento

Il launcher collega due moduli e ne rende il percorso direttamente provabile. Non aggrega ancora i progressi in una dashboard comune e non decide automaticamente quando un modulo può essere considerato completato. Queste funzioni appartengono agli incrementi successivi della parent issue #58.
