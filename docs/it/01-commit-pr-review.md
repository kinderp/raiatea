# Commit, issue, pull request, review e finding

Questo documento definisce il flusso operativo dettagliato usato da maintainer,
contributori e agenti AI. Integra le regole generali di
[`00-regole-operative.md`](00-regole-operative.md) e deve essere letto prima di
aprire issue, branch, commit o pull request.

## 1. Modello di coordinamento

Per ogni lavoro non banale usare questa catena:

```text
Milestone
    |
    v
Issue madre
    |
    +--> Issue figlia del micro-step
            |
            v
         Branch
            |
            v
        Draft PR
            |
            v
        Review round 1
            |
            v
        Fix finding
            |
            v
        Review round 2
            |
            v
          Merge
```

Una sola pull request di lavoro deve restare aperta per lo stesso filone
sequenziale. Una nuova PR si apre soltanto dopo il merge o la chiusura della
precedente, salvo attività realmente indipendenti e dichiarate.

## 2. Issue madre

Una milestone o un lavoro che supera un singolo micro-step deve avere una issue
madre.

La issue madre deve contenere almeno:

- obiettivo misurabile;
- contesto e motivazione;
- documento roadmap principale, quando esiste;
- scope incluso;
- scope esplicitamente escluso;
- criteri di completamento;
- checklist sintetica;
- tabella di tracciabilità;
- rischi, dipendenze e decisioni aperte;
- collegamenti a issue figlie, PR, Discussion, ADR e documenti.

Forma minima della tracciabilità:

```text
| Micro-step | Stato | Issue | PR | Commit | Note |
| --- | --- | --- | --- | --- | --- |
| ... | Todo / In progress / Done | #... | #... | abc1234 | ... |
```

Checklist e tabella devono restare coerenti nello stesso aggiornamento.

## 3. Issue figlie

Ogni micro-step non banale della issue madre deve avere una issue figlia.

La issue figlia deve:

- descrivere un comportamento coerente, reviewabile e reversibile;
- linkare la issue madre;
- indicare input, output e prova attesa;
- elencare file o componenti probabilmente coinvolti;
- dichiarare Definition of Done locale;
- linkare la PR quando viene aperta;
- essere chiusa dal merge tramite `Closes #<numero>` quando appropriato.

Bug, debiti, test mancanti e documentazione scoperti durante il lavoro non devono
essere nascosti in una PR più grande. Se sono fuori scope, creare una issue
figlia o una issue separata e collegarla dal finding.

## 4. Branch

Non lavorare direttamente su `main` per modifiche non banali.

Il branch deve partire da `main` aggiornato e avere un nome descrittivo:

```text
feature/<tema-breve>
fix/<tema-breve>
docs/<tema-breve>
test/<tema-breve>
refactor/<tema-breve>
```

Evitare nomi generici come `work`, `changes`, `update` o `test`.

Prima di aprire il branch verificare che non esista già una PR aperta sullo
stesso filone sequenziale.

## 5. Commit

### 5.1 Principi

Ogni commit deve essere:

- atomico;
- coerente con il micro-step;
- comprensibile senza leggere tutta la chat;
- compilabile o almeno esplicitamente preparatorio;
- associabile a test, documentazione, bug o decisione precisa.

Non accumulare in un singolo commit modifiche indipendenti. Non creare commit
artificialmente microscopici che non producono uno stato leggibile.

### 5.2 Messaggio

Usare un soggetto imperativo, breve e specifico:

```text
Add step-level provenance validation
Fix declarative layout compilation in CI
Document consecutive review rounds
```

Evitare:

```text
Update files
Changes
Fix stuff
WIP
```

Quando utile, il body deve spiegare:

- perché il cambiamento è necessario;
- quale contratto modifica;
- quali alternative sono state escluse;
- quali test lo verificano;
- quale lavoro resta fuori scope.

### 5.3 Riferimento del commit

In issue, PR, report e commenti usare sempre lo SHA abbreviato cliccabile alla
pagina GitHub del commit.

Formato:

```markdown
[`abc1234`](https://github.com/kinderp/raiatea/commit/abc1234...)
```

Lo SHA mostrato deve essere tagliato normalmente a 7 caratteri. Il link deve
puntare alla pagina GitHub del commit completo, non a una ricerca testuale e non
alla sola branch.

Esempio:

```markdown
Risolto in [`5e5691a`](https://github.com/kinderp/raiatea/commit/5e5691ae804a47dee0718911b8bf49ce8c7c121e).
```

## 6. Apertura della pull request

La PR deve essere aperta presto come draft quando il micro-step ha già uno scope
chiaro. Non aspettare che tutto sia perfetto per rendere visibile il lavoro.

Il body deve contenere almeno:

```text
## Summary
## Linked issue
## Scope
## Out of scope
## Validation
## Documentation
## Risks and review focus
## Finding log
```

La PR deve:

- linkare la issue figlia;
- usare `Closes #...` se il merge deve chiuderla;
- linkare la issue madre;
- indicare test eseguiti e loro esito;
- indicare Action in corso, verde o rossa;
- dichiarare modifiche di schema, API, provenienza, privacy o sicurezza;
- segnalare eventuali commit preparatori;
- restare draft finché non è pronta per il primo round completo.

Quando una PR viene aperta, chiusa, convertita da draft o mergiata, inviare un
feedback in chat con numero, titolo, stato e link.

## 7. Review automatica: due round consecutivi

Una PR non banale può essere mergiata solo dopo **due round consecutivi di
review senza nuovi finding bloccanti**.

### 7.1 Round 1

Il primo round deve controllare almeno:

- correttezza funzionale;
- coerenza con issue e scope;
- contratti e compatibilità;
- semplicità e assenza di astrazioni speculative;
- test positivi e negativi;
- gestione errori;
- sicurezza e privacy;
- provenienza;
- qualità pedagogica;
- documentazione;
- CI.

Ogni finding deve essere registrato nel punto corretto della PR.

### 7.2 Correzione

Dopo ogni finding valido:

1. correggere il codice o la documentazione;
2. aggiungere o aggiornare il test quando possibile;
3. creare un commit dedicato o chiaramente riconoscibile;
4. rispondere nel thread del finding;
5. linkare il commit con SHA abbreviato cliccabile;
6. spiegare cosa è cambiato e perché il finding è risolto;
7. lasciare il thread aperto finché il reviewer non verifica.

Esempio di risposta:

```markdown
Risolto in [`abc1234`](https://github.com/kinderp/raiatea/commit/<sha-completo>).

Il validatore ora esclude il contenuto dei blocchi `<script>` prima di analizzare
i link statici. Ho aggiunto un test che mantiene il rifiuto di `#missing` nel
markup reale senza trattare i template literal JavaScript come link HTML.
```

Non rispondere soltanto con `fixed`, `done` o un emoji.

### 7.3 Round 2

Il secondo round deve essere una nuova lettura reale del diff aggiornato, non una
conferma formale.

Deve verificare:

- che tutti i finding del round precedente siano realmente risolti;
- che i fix non abbiano introdotto regressioni;
- che test e documentazione siano coerenti con il codice finale;
- che non emergano nuovi finding bloccanti;
- che la CI sia verde;
- che tutti i thread rilevanti siano risolti.

Se il round 2 produce un nuovo finding bloccante, il conteggio si azzera. Dopo il
fix servono nuovamente due round consecutivi puliti.

Modifiche puramente meccaniche richieste dalla review possono essere verificate
nel round successivo senza azzerare automaticamente il conteggio; modifiche
sostanziali a comportamento, contratto, architettura o test lo azzerano sempre.

## 8. Classificazione dei finding

Usare una classificazione esplicita:

- `blocking`: impedisce merge;
- `major`: errore importante, contratto incoerente o rischio serio;
- `minor`: problema locale da correggere prima del merge salvo motivazione;
- `nit`: suggerimento stilistico non bloccante;
- `question`: richiesta di chiarimento;
- `out-of-scope`: problema valido ma da spostare in issue separata.

Ogni finding deve contenere:

- titolo sintetico;
- severità;
- file e linea o sezione;
- descrizione del problema;
- impatto concreto;
- proposta o criterio di correzione;
- eventuale issue separata se fuori scope.

Esempio:

```text
[major] Il validatore accetta correctIndex fuori range

File: prototype/.../validate_module.py
Impatto: il modulo può essere pubblicato con una risposta corretta inesistente.
Criterio: rifiutare indici negativi o >= len(answers) e aggiungere test negativo.
```

## 9. Finding log nella PR

Il body o un commento stabile della PR deve mantenere un finding log:

```text
| ID | Severità | Stato | Descrizione | Fix commit | Thread |
| --- | --- | --- | --- | --- | --- |
| F1 | major | Resolved | correctIndex fuori range | abc1234 | link |
```

Stati ammessi:

- `Open`;
- `Accepted`;
- `Fix in progress`;
- `Resolved`;
- `Rejected with rationale`;
- `Moved to issue #...`.

Un finding non deve essere segnato `Resolved` finché:

- il fix è presente nel branch;
- il test pertinente passa;
- la risposta nel thread contiene spiegazione e link al commit;
- il reviewer ha verificato o il round successivo lo ha confermato.

## 10. Reiezione motivata di un finding

Un finding può essere respinto, ma mai ignorato.

La risposta deve spiegare:

- quale assunzione del finding non vale;
- quale contratto o documento supporta la decisione;
- quale test o comportamento osservabile la dimostra;
- perché la modifica proposta sarebbe peggiore o fuori scope.

Se resta disaccordo su architettura, prodotto, sicurezza o dati, fermarsi e
chiedere una decisione al maintainer.

## 11. CI durante la review

- Una Action in corso non impedisce di preparare il micro-step successivo.
- Prima del merge, tutte le Action richieste devono essere verdi.
- Una Action rossa richiede analisi del log e fix della causa.
- Il fix della CI deve essere commentato nella PR con SHA abbreviato cliccabile e
  spiegazione della causa.
- Non rilanciare semplicemente un job rosso senza distinguere errore reale,
  flakiness e problema infrastrutturale.
- Se il problema è infrastrutturale, documentare evidenza e decisione.

## 12. Merge

Prima del merge verificare:

- issue figlia collegata;
- scope completo e nessun lavoro occulto;
- due round consecutivi puliti;
- finding log chiuso;
- thread rilevanti risolti;
- CI verde;
- documentazione aggiornata;
- issue madre e traceability aggiornate;
- report giornaliero aggiornabile con PR e commit.

Dopo il merge:

1. verificare la chiusura automatica della issue figlia;
2. chiuderla manualmente solo se i criteri sono realmente soddisfatti;
3. aggiornare la issue madre;
4. riallineare `main`;
5. eliminare o archiviare il branch quando appropriato;
6. aprire la nuova issue figlia e la nuova PR soltanto per il micro-step
   successivo;
7. inviare feedback in chat con numero PR, merge commit, issue chiuse e stato CI.

## 13. Chiusura delle issue

Una issue si chiude soltanto quando:

- il comportamento richiesto è presente;
- i test pertinenti passano;
- la documentazione necessaria è aggiornata;
- la PR è mergiata;
- la traceability è aggiornata;
- il lavoro rimandato è stato trasformato in issue esplicite.

Il commento finale deve riassumere:

- risultato ottenuto;
- PR mergiata;
- commit principale con SHA abbreviato cliccabile;
- test eseguiti;
- eventuali issue successive.

## 14. Automazione e feedback in chat

Quando un agente opera autonomamente deve comunicare subito:

- apertura di issue madre;
- apertura di issue figlia;
- apertura di draft PR;
- passaggio della PR a ready for review;
- completamento di ciascun round;
- finding bloccanti scoperti;
- fix dei finding;
- Action rossa e relativo fix;
- merge o chiusura della PR;
- chiusura di issue.

Il feedback deve essere breve ma contenere numero, titolo, stato, link e prossimo
passo.

## 15. Regola finale

La velocità non sostituisce la tracciabilità. Un micro-step è davvero concluso
solo quando codice, test, documentazione, issue, PR, finding e commit raccontano
la stessa storia verificabile.