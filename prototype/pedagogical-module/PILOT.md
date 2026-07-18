# Raiatea pilot: avvio e prova

Questo pilot locale presenta un percorso in due moduli:

1. **Query, key e value**;
2. **Self-attention**.

Non richiede account, cloud, API key o connessione di rete durante l'uso.

## Requisiti

- Python 3.12 o una versione Python 3 recente;
- un browser moderno.

## Costruzione

Dalla radice del repository:

```bash
rm -rf /tmp/raiatea-pilot
python prototype/pedagogical-module/build/build_pilot.py \
  --output /tmp/raiatea-pilot
```

La directory contiene:

- `index.html`;
- `query-key-value.html`;
- `self-attention.html`;
- `pilot-manifest.json`.

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
2. **Inizia il percorso** apre `Query, key e value`.
3. I pulsanti degli step permettono di avanzare nel modulo.
4. Una risposta errata mostra il percorso di recupero previsto.
5. Il link **Self-attention →** apre il secondo modulo.
6. Il link **← Query, key e value** torna al primo modulo.
7. **Indice del pilot** riporta alla pagina iniziale.
8. Ricaricando un modulo, il progresso locale resta disponibile nel browser.
9. L'esportazione delle evidenze resta esplicita e locale.
10. Nessuna pagina richiede login, rete, dati personali o servizi esterni.

## Limiti di questo incremento

Il launcher collega due moduli e ne rende il percorso direttamente provabile. Non aggrega ancora i progressi in una dashboard comune e non decide automaticamente quando un modulo può essere considerato completato. Queste funzioni appartengono agli incrementi successivi della parent issue #58.
