# Raiatea pilot: avvio e prova

Questo README operativo descrive il primo pilot locale in due moduli:

1. **Il ruolo della self-attention nel modello GPT**;
2. **Query, Key e Value nella self-attention**.

L'ordine segue il percorso pedagogico canonico. Il pilot non richiede account, cloud, API key o connessione di rete durante l'uso.

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
- `pilot-manifest.json`;
- `pilot-dashboard.js`.

Il builder non sovrascrive una destinazione esistente.

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

## Dashboard del percorso

La pagina iniziale mostra per ogni modulo:

- **Non iniziato** quando non esiste uno stato locale valido o tutti i valori osservabili sono ancora vuoti;
- **In corso** quando esiste almeno un tentativo o un'altra attività osservabile;
- **Completato localmente** quando ogni step risulta `correct: true` oppure `activityCompleted: true`.

L'uso della remediation non impedisce il completamento locale. La dashboard suggerisce il primo modulo non ancora completato, ma tutti i link restano sempre disponibili: non esistono blocchi o sblocchi automatici.

La dashboard legge soltanto le chiavi `raiatea-progress:<module-id>` dei moduli del percorso. Non enumera altre chiavi, non modifica o cancella progressi, non invia dati e non mostra contenuti grezzi dello storage. Uno stato malformato viene trattato come non iniziato.

## Arresto

Tornare nel terminale del server e premere `Ctrl+C`.

## Checklist di prova

1. La pagina iniziale mostra i due moduli nell'ordine previsto.
2. Senza progressi entrambi risultano **Non iniziato**.
3. **Inizia il percorso** apre il modulo di orientamento sulla self-attention.
4. Dopo un tentativo e il ritorno all'indice, il primo modulo risulta **In corso**.
5. Una risposta errata mostra il percorso di recupero previsto.
6. Il link **Query, Key e Value nella self-attention →** apre il secondo modulo.
7. **Indice del pilot** riporta alla dashboard aggiornata.
8. Quando tutte le attività di un modulo sono verificate, compare **Completato localmente** e il consiglio passa al modulo successivo.
9. Tutti i moduli restano apribili indipendentemente dallo stato.
10. L'esportazione delle evidenze resta esplicita e locale.
11. Nessuna pagina richiede login, rete, dati personali o servizi esterni.

## Limiti di questo incremento

La dashboard aggrega soltanto stati derivati per la navigazione. Non crea un nuovo documento di evidenze multi-modulo, non assegna voti o mastery score e non modifica il formato di progresso dei moduli.
