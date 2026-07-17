# Regole operative di Raiatea

Questo documento è la costituzione pratica del progetto. Deve restare stabile, leggibile e più breve dei manuali specialistici. Le procedure dettagliate, i contratti tecnici e le decisioni architetturali vivono nei documenti collegati.

Serve come memoria di lavoro per maintainer, contributori e agenti AI: prima di continuare una sessione interrotta o iniziare un task non banale, leggere questo file e i documenti strettamente pertinenti al lavoro corrente.

## 1. Obiettivo del metodo

Raiatea deve produrre non soltanto software funzionante, ma anche conoscenza durevole, verificabile, aggiornabile e didatticamente utile.

Ogni incremento significativo deve quindi lasciare almeno una delle seguenti prove:

- comportamento osservabile;
- test eseguibile;
- esempio riproducibile;
- contratto dati o API;
- decisione documentata;
- provenienza ricostruibile;
- misura o benchmark, quando rilevante;
- spiegazione comprensibile a studenti e nuovi contributori.

Criterio di costruzione:

> Non implementare in Raiatea ciò che un modello generalista può già fornire con accuratezza, durata, riproducibilità, aggiornabilità, portabilità e governance equivalenti, ma con costo minore.

Raiatea è giustificata quando il risultato deve diventare una mappa persistente che possa essere verificata, revisionata, collegata, condivisa e mantenuta viva nel tempo.

## 2. Fonti di verità

```text
GitHub Discussion  -> ragionamento ancora aperto
ADR                -> decisione architetturale specifica
Documentazione     -> spiegazione consolidata corrente
Issue              -> lavoro da svolgere
Pull request       -> modifica concreta e verificabile
Test               -> evidenza eseguibile del comportamento
Benchmark          -> evidenza misurata del costo
Provenienza        -> origine e trasformazioni del contenuto
Git                -> storia cronologica
```

Una Discussion non è un contratto. Quando una scelta viene presa, deve entrare nell'ADR o nei documenti stabili interessati.

La documentazione non sostituisce i test; i test non sostituiscono la spiegazione; la cronologia Git non sostituisce una decisione architetturale esplicita.

## 3. Bootstrap di una sessione

Prima di modificare codice, schema o contratti:

1. leggere `AGENTS.md` nella root;
2. leggere questo file;
3. leggere i documenti `genesis/` pertinenti alla milestone corrente;
4. leggere la documentazione del componente interessato;
5. aprire il codice e i test reali;
6. controllare issue, pull request e stato della CI collegati al task;
7. distinguere chiaramente contratto corrente, roadmap futura e note storiche.

Non leggere indiscriminatamente tutta la documentazione: un contesto troppo ampio può mescolare visione futura, decisioni correnti e ipotesi non ancora approvate.

## 4. Scheda obbligatoria del task

Prima di un passo non banale, chiarire almeno:

| Domanda | Perché serve |
| --- | --- |
| Quale risultato utente o didattico cambia? | Evita refactor senza valore osservabile. |
| Quale componente possiede la regola? | Evita logica nel modulo sbagliato. |
| Quale contratto può cambiare? | Protegge compatibilità e sostituibilità. |
| Quali fonti o dati sono coinvolti? | Determina provenienza, privacy e qualità. |
| Quale dipendenza esterna è coinvolta? | Identifica adapter, lock-in e rischio supply-chain. |
| Tocca un percorso critico? | Determina benchmark e review prestazionale. |
| Quali test o esempi servono? | Rende il passo verificabile. |
| Quali documenti vanno aggiornati? | Mantiene il progetto studiabile. |
| È scope corrente o roadmap? | Impedisce espansione incontrollata. |
| Quale evidenza dimostrerà che il passo è concluso? | Evita definizioni di done vaghe. |

Se l'interpretazione del task è ambigua e può cambiare architettura, dati, sicurezza o prodotto, fermarsi e chiedere una decisione. Per dettagli locali e reversibili, scegliere l'opzione più semplice e documentare l'assunzione.

## 5. Micro-step e vertical slice

Un micro-step è un comportamento coerente, reviewabile e reversibile. Non è necessariamente un singolo file e non deve essere frammentato artificialmente.

Un buon micro-step:

- produce un risultato osservabile;
- include i test adeguati;
- aggiorna schema, validatore, esempio e documentazione quando il contratto cambia;
- può essere revisionato senza comprendere un'intera milestone;
- può essere annullato senza compromettere modifiche indipendenti.

Esempio valido:

```text
Aggiungere una micro-attività di recupero dichiarativa, validarla, renderizzarla,
registrarne l'esito come evidenza osservata e coprirla con test positivi e negativi.
```

Esempio troppo grande:

```text
Costruire ingestion, knowledge graph, tutor, editor, federazione e marketplace.
```

Esempio troppo frammentato:

```text
PR 1 campo vuoto; PR 2 parser; PR 3 bottone senza comportamento; PR 4 primo test.
```

## 6. Principi di ragionamento e modifica

- Pensare prima di modificare: dichiarare assunzioni, dubbi e trade-off quando il passo non è banale.
- Non nascondere confusione: se una richiesta ammette interpretazioni materialmente diverse, esplicitarle.
- Semplicità prima: implementare il minimo necessario, senza astrazioni speculative.
- Modifiche chirurgiche: toccare solo i file necessari al passo corrente.
- Ogni riga modificata deve essere collegabile a una richiesta, un test, un bug o un aggiornamento documentale necessario.
- Non anticipare grandi refactor se il comportamento corrente non è protetto da test.
- Separare sempre comportamento osservabile, struttura interna e roadmap futura.
- Non dichiarare completato, corretto o supportato ciò che non è dimostrato da evidenza verificabile.
- Non introdurre nuove dipendenze senza motivazione, impatto, alternativa e piano di aggiornamento.
- Preferire contratti dichiarativi e dati strutturati a logica duplicata nei template o nei moduli specifici.

## 7. Provenienza, affermazioni e conoscenza

Raiatea deve distinguere esplicitamente:

```text
fonte originale
traduzione
selezione
adattamento
rielaborazione
valore derivato
inferenza
ipotesi
```

Regole:

- non inventare fonti, pagine, citazioni, risultati o misure;
- non presentare un'inferenza come contenuto originale della fonte;
- conservare la provenienza a livello sufficientemente granulare per ricostruire il passaggio;
- quando il contenuto viene tradotto, sintetizzato o trasformato, registrare la trasformazione;
- i valori calcolati devono indicare dati di partenza e procedimento;
- le ipotesi devono restare distinguibili dalle conclusioni supportate;
- se una fonte non è disponibile o non è verificabile, dichiararlo.

## 8. Evidenze di apprendimento

Le interazioni dell'utente sono evidenze osservate, non prove automatiche di competenza.

Non usare termini come `mastery`, `competenza acquisita` o punteggi assoluti senza un modello di valutazione documentato e validato.

È lecito registrare:

- tentativi;
- risposta corretta o errata;
- uso di recupero;
- completamento di una micro-attività;
- progressione nel modulo;
- risultato di una verifica esplicita.

Le raccomandazioni devono essere spiegabili, deterministiche quando possibile e separate dai dati grezzi osservati.

## 9. Commenti nel codice

I commenti devono spiegare ciò che il codice da solo non rende evidente.

Commentare soprattutto:

- motivazione di una scelta non ovvia;
- invarianti e precondizioni;
- ownership, lifetime e responsabilità;
- vincoli di sicurezza o prestazione;
- workaround temporanei con causa e criterio di rimozione;
- differenza tra comportamento corrente e roadmap futura;
- provenienza o trasformazioni quando non sono espresse dai tipi.

Evitare:

- commenti che ripetono letteralmente l'istruzione;
- cronache di modifiche già conservate da Git;
- TODO vaghi senza contesto;
- spiegazioni lunghe che appartengono alla documentazione;
- commenti che descrivono un comportamento non più vero.

Regola pratica:

```text
Il codice spiega cosa accade.
Il commento spiega perché, quali vincoli valgono e cosa non deve cambiare.
La documentazione spiega il sistema nel suo insieme.
```

I commenti nel codice restano sintetici e, salvo diversa convenzione del componente, in inglese. La documentazione didattica e operativa può essere in italiano.

## 10. Documentazione obbligatoria

Una modifica non banale deve aggiornare almeno uno tra:

- documento architetturale;
- contratto dati o API;
- ADR;
- schema;
- esempio completo;
- strategia di test;
- diagramma o mappa del flusso;
- guida per contributori;
- report benchmark;
- threat model;
- registro milestone o report giornaliero.

Se una spiegazione importante nasce in chat, in una review o durante il debugging, non deve restare soltanto lì.

La documentazione deve distinguere:

- stato supportato oggi;
- comportamento sperimentale;
- debito noto;
- idea futura;
- decisione rimandata.

## 11. GitHub: milestone, issue e pull request

Usare come struttura di coordinamento:

```text
Milestone
    |
    v
Issue madre
    |
    +--> Discussion, quando il ragionamento è ancora aperto
    +--> Issue figlie per micro-step, bug, test o debiti
    +--> Pull request per modifiche concrete
    +--> Documentazione stabile per la decisione consolidata
```

Regole operative:

- una sola pull request di lavoro aperta per agente o filone sequenziale, salvo lavori realmente indipendenti;
- non lavorare direttamente su `main` per modifiche non banali;
- ogni PR deve avere uno scope coerente e una prova verificabile;
- collegare la PR alla issue con `Closes #...` quando il merge deve chiuderla;
- aggiornare la issue madre con stato e tracciabilità dei micro-step;
- comunicare in chat apertura e chiusura di issue e PR;
- non chiudere una issue senza evidenza verificabile e documentazione aggiornata;
- applicare label utili ad area e tipo, evitando label decorative;
- mantenere checklist sintetica e tabella di tracciabilità coerenti, quando entrambe esistono.

## 12. Review

Una PR non banale richiede due round consecutivi di review senza nuovi finding bloccanti prima del merge.

Un round è concluso quando:

1. vengono letti diff, test e documenti interessati;
2. i finding sono classificati per severità;
3. i finding validi vengono corretti o motivatamente respinti;
4. la CI è verde;
5. non restano thread irrisolti rilevanti.

Se dopo un round vengono introdotte modifiche sostanziali, il conteggio dei round consecutivi riparte.

Non approvare una PR soltanto perché i test passano. Verificare anche:

- correttezza del contratto;
- semplicità;
- compatibilità;
- sicurezza e privacy;
- provenienza;
- chiarezza didattica;
- assenza di scope creep;
- aggiornamento della documentazione.

## 13. CI e gestione delle Action rosse

- Una Action in corso non blocca automaticamente il micro-step successivo.
- Al termine del lavoro successivo, controllare lo stato della CI precedente.
- Se una Action è rossa, analizzare il log prima di proseguire con nuovi incrementi sostanziali.
- Correggere la causa, aggiungere o migliorare il test che avrebbe dovuto intercettarla e rieseguire la CI.
- Non limitarsi a rilanciare una Action fallita senza capire se il problema è deterministico, intermittente o infrastrutturale.
- Se il problema è infrastrutturale e non dipende dalla modifica, documentarlo chiaramente.
- Non dichiarare stabile una modifica con CI rossa.

## 14. Test e verifiche

Scegliere la prova in base al contratto:

- unit test: regole pure e validatori;
- contract test: compatibilità tra produttori e consumatori;
- integration test: build, storage, filesystem, rete e dipendenze;
- browser test: interazioni, persistenza e accessibilità;
- snapshot o golden test: output dichiarativi stabili;
- property test: invarianti su grafi, trasformazioni e layout;
- performance test: latenza, memoria e dimensione degli artefatti;
- security test: input ostili, isolamento e confini di fiducia;
- audit manuale: qualità pedagogica, leggibilità e provenienza.

Un test funzionale non dimostra prestazioni; un benchmark non dimostra correttezza; una validazione strutturale non dimostra qualità didattica.

## 15. Definition of Done

Una slice è conclusa quando, per quanto applicabile:

- il risultato utente o didattico è osservabile;
- il contratto è chiaro;
- schema e validatore sono coerenti;
- esiste almeno un esempio reale;
- i test positivi e negativi corretti passano;
- la CI è verde;
- provenienza e trasformazioni sono tracciate;
- privacy e sicurezza sono state considerate;
- documentazione e tracciabilità GitHub sono aggiornate;
- non restano finding bloccanti;
- sono stati completati due round consecutivi di review per una PR non banale;
- il lavoro rimandato è esplicitato e non nascosto come comportamento supportato.

Per modifiche al modulo pedagogico dichiarativo, la Definition of Done include normalmente:

```text
schema
→ validatore
→ renderer o builder
→ esempio reale
→ test positivi e negativi
→ documentazione
→ Action verde
```

## 16. Report giornalieri

A fine giornata creare:

```text
docs/daily-reports/YYYY-MM-DD.md
```

Il report deve contenere:

- obiettivi della giornata;
- attività svolte;
- file modificati;
- commit principali;
- issue e PR aperte o chiuse;
- decisioni tecniche;
- problemi incontrati e soluzioni;
- stato finale delle GitHub Actions;
- lavoro incompleto;
- prossimi passi.

Aggiornare anche:

```text
docs/daily-reports/README.md
```

aggiungendo il collegamento cronologico senza duplicati.

## 17. Regola finale

Quando una modifica rende il sistema più difficile da capire, verificare o spiegare, il costo deve essere giustificato da un beneficio concreto e misurabile.

In assenza di tale beneficio, preferire la soluzione più semplice, più esplicita e più facilmente reversibile.
