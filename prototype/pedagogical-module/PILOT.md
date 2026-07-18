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

L'uso della remediation non impedisce il completamento locale. La dashboard suggerisce il primo modulo non ancora completato, ma tutti i link restano sempre disponibili.

La dashboard legge soltanto le chiavi `raiatea-progress:<module-id>` dei moduli del percorso. Non enumera altre chiavi, non modifica o cancella progressi e non invia dati.

## Riepilogo del modulo ed export JSON

Dashboard, riepilogo ed export hanno significati diversi:

1. la **dashboard** aiuta a orientarsi tra i moduli;
2. il **Riepilogo del percorso** dentro un modulo mostra tentativi, risposte corrette, uso della remediation e attività di recupero osservate in quel modulo;
3. **Esporta evidenze JSON** scarica, solo dopo un click esplicito, il documento learner-evidence v1 del modulo corrente.

Questi dati non sono un voto, un mastery score, una diagnosi o una certificazione.

Per provare l'export:

1. aprire un modulo;
2. svolgere almeno una verifica, anche usando il recupero;
3. scorrere fino a **Riepilogo del percorso**;
4. leggere il riepilogo e premere **Esporta evidenze JSON**;
5. verificare che il browser scarichi `<module-id>-evidence-v1.json`.

Il file contiene soltanto identità e contesto consentiti del modulo, posizione corrente e osservazioni per step. Non include altri moduli, chiavi estranee di `localStorage`, preferenze di lettura, identità del discente, timestamp, analytics o telemetria. L'export non modifica il progresso né lo stato della dashboard. Non esiste ancora un portfolio o bundle unico dell'intero percorso.

## Arresto

Tornare nel terminale del server e premere `Ctrl+C`.

## Checklist di prova

1. La pagina iniziale mostra i due moduli nell'ordine previsto.
2. Senza progressi entrambi risultano **Non iniziato**.
3. La guida statica distingue dashboard, riepilogo ed export del singolo modulo.
4. **Inizia il percorso** apre il modulo di orientamento sulla self-attention.
5. Dopo un tentativo e il ritorno all'indice, il primo modulo risulta **In corso**.
6. Una risposta errata mostra il percorso di recupero previsto e il riepilogo registra l'uso della remediation.
7. Quando tutte le attività sono verificate, compare **Completato localmente** e il consiglio passa al modulo successivo.
8. Nel modulo, **Riepilogo del percorso** mostra solo osservazioni e non un voto.
9. Nessun file viene scaricato prima di premere **Esporta evidenze JSON**.
10. Il click produce `<module-id>-evidence-v1.json` per il solo modulo aperto.
11. Dopo l'export, progresso, dashboard, preferenze e chiavi estranee restano invariati.
12. Tutti i moduli restano apribili e nessuna pagina richiede login, rete o servizi esterni.

## Limiti di questo incremento

Il pilot non crea un nuovo documento multi-modulo, non esporta learner-evidence v2 dal browser, non assegna voti o mastery score e non esegue backup, upload, firma o cifratura automatica.
