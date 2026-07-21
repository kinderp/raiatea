# Audit di Project Genesis e matrice di tracciabilità

> Stato: bozza di audit per la revisione del maintainer
>
> Issue madre: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Issue figlia: [#99](https://github.com/kinderp/raiatea/issues/99)
>
> Data di osservazione: 21 luglio 2026
>
> Ambito: documentazione Genesis, prototipo pedagogico e tracciabilità GitHub

## 1. Scopo

Questo documento non sostituisce le note di Project Genesis e non consolida
ancora decisioni architetturali. Serve a rendere supervisionabile il passaggio
da una conversazione fondativa molto ricca e da ventuno note esplorative a una
Inception coerente, navigabile e verificabile.

L'audit risponde a quattro domande:

1. quali idee fondative sono già conservate nel repository;
2. quali idee sono assenti, disperse o formulate in modo non canonico;
3. qual è lo stato reale dello sviluppo rispetto alla documentazione;
4. quali decisioni richiedono una scelta esplicita del maintainer.

## 2. Metodo e limiti

Sono stati esaminati:

- `AGENTS.md` e le regole operative in `docs/it/`;
- `COMPASS.md` e il `README.md` principale;
- `genesis/README.md` e i documenti da `genesis/00-*.md` a
  `genesis/20-*.md`;
- i placeholder nelle cartelle `vision/`, `manifesto/`, `architecture/`,
  `ontology/`, `adr/`, `research/`, `branding/`, `journal/` e `philosophy/`;
- la documentazione e i contratti del prototipo in
  `prototype/pedagogical-module/`;
- i report giornalieri più recenti;
- branch, issue, pull request e Actions visibili su GitHub alla data di
  osservazione.

La conversazione fondativa fornita dal maintainer è stata trattata come fonte
di requisiti e intenzioni, non come prova fattuale. I riferimenti storici,
culturali, sanitari o scientifici emersi nella conversazione dovranno essere
verificati con fonti autorevoli prima di diventare affermazioni pubbliche.

### 2.1 Legenda delle fonti Genesis

Le tabelle usano la forma breve `genesis/NN`. Ogni numero rimanda a una delle
note esplorative preservate:

- [`genesis/00`](../00-understanding.md): comprensione, realtà e conoscenza;
- [`genesis/01`](../01-public-reality.md): ricostruzione della realtà pubblica;
- [`genesis/02`](../02-public-figures.md): persone pubbliche e posizioni;
- [`genesis/03`](../03-evidence-integrity-and-contribution.md): integrità
  dell'evidenza e contributi;
- [`genesis/04`](../04-continuous-knowledge-ingestion.md): acquisizione
  continua delle fonti;
- [`genesis/05`](../05-dynamic-systems-and-stochastic-processes.md): sistemi
  dinamici e processi stocastici;
- [`genesis/06`](../06-federated-knowledge-network.md): rete federata della
  conoscenza;
- [`genesis/07`](../07-participatory-computation-governance-and-continuous-briefing.md):
  calcolo partecipativo, governance e briefing continui;
- [`genesis/08`](../08-independence-business-model-and-failure-analysis.md):
  indipendenza, modello economico e failure analysis;
- [`genesis/09`](../09-constitution.md): costituzione del progetto;
- [`genesis/10`](../10-immediate-value-thesis.md): tesi del valore immediato;
- [`genesis/11`](../11-derived-knowledge-sharing.md): condivisione della
  conoscenza derivata;
- [`genesis/12`](../12-source-citation-and-user-knowledge-profile.md): citazione
  delle fonti e profilo di conoscenza;
- [`genesis/13`](../13-personalized-source-recommendations-and-revenue-firewall.md):
  raccomandazioni e revenue firewall;
- [`genesis/14`](../14-microlicensing-and-generated-alternatives.md):
  microlicensing e alternative generate;
- [`genesis/15`](../15-paid-continuous-expedition-updates.md): aggiornamenti
  continui delle Expedition;
- [`genesis/16`](../16-public-interest-access-and-civic-briefings.md): livello
  di interesse pubblico;
- [`genesis/17`](../17-emergency-open-access.md): accesso aperto in emergenza;
- [`genesis/18`](../18-why-raiatea-not-just-an-llm.md): differenza rispetto a
  un LLM generalista;
- [`genesis/19`](../19-private-corpus-adaptive-exercises.md): esercizi adattivi
  da corpus privati;
- [`genesis/20`](../20-pedagogical-visual-standard.md): standard visuale
  pedagogico.

## 3. Risultato sintetico

Le idee principali non sono andate perdute: la maggior parte è presente nei
documenti Genesis. Il problema è la loro forma attuale.

- Le note sono ampie, profonde e spesso già coerenti tra loro.
- Tutte rimangono documenti esplorativi in stato di bozza.
- Non esiste ancora una separazione canonica tra principio, decisione,
  ipotesi, roadmap e ricerca differita.
- `genesis/README.md` annuncia otto artefatti di Inception che non sono mai
  stati creati.
- Le cartelle destinate a Vision, Manifesto, architettura, ontologia e ADR
  contengono soltanto placeholder.
- Il `README.md` principale descrive Raiatea come precedente
  all'implementazione, mentre esiste già un prototipo pedagogico articolato e
  un processo di pilot supervisionato molto avanzato.
- Il codice ha maturato contratti, validazione, packaging e procedure di
  valutazione più velocemente del modello di prodotto e del linguaggio
  ubiquitario.

La conclusione non è quindi "ricostruire tutto", ma:

1. preservare le note Genesis come memoria progettuale;
2. estrarne artefatti canonici più brevi e stabili;
3. collegare esplicitamente ogni decisione alle note di origine;
4. riallineare la descrizione del progetto con il vertical slice realmente
   implementato;
5. sottoporre al maintainer le poche decisioni che cambiano davvero la
   direzione.

## 4. Tassonomia di stato proposta

La documentazione usa oggi quasi esclusivamente la parola `draft`. Non basta
per distinguere il peso delle diverse affermazioni. Si propone, senza renderla
ancora vincolante, la seguente tassonomia.

| Stato | Significato | Esempio |
| --- | --- | --- |
| `principle` | Vincolo valoriale che orienta tutte le scelte | Nessuna affermazione importante senza provenienza |
| `current-contract` | Comportamento implementato e protetto da test | Evidenze locali osservate, non dichiarazioni di competenza |
| `provisional-decision` | Scelta corrente, reversibile dopo nuova evidenza | HTML autosufficiente come formato del pilot |
| `working-hypothesis` | Tesi da verificare con utenti o esperimenti | Una figura procedurale migliora il trasferimento concettuale |
| `planned` | Incremento approvato ma non ancora implementato | Gate riproducibile della release candidate del pilot |
| `deferred-research` | Idea valida da studiare, fuori dallo scope attuale | Federazione, calcolo distribuito e governance partecipativa |
| `historical-note` | Ragionamento conservato per tracciabilità | Prime metafore di Knowledge OS e Memory Graph |
| `rejected` | Opzione valutata e scartata con motivazione | Copia editoriale pagina per pagina del libro sorgente |

Questa classificazione dovrebbe comparire nel front matter dei futuri
documenti canonici e, progressivamente, nelle note che vengono revisionate.

## 5. Mappa delle idee fondative

### 5.1 Studio, libri e AI Research Notebook

| Idea | Presenza attuale | Lacuna | Destinazione canonica proposta |
| --- | --- | --- | --- |
| Usare libri, paper, codice e video come fonti, non come testo da ricopiare | `genesis/04`, `10`, `11`, `12`, `19`, `20` | Nessun use case end-to-end canonico | Vision, Use Case Model |
| Originale inglese sempre verificabile, traduzione e rielaborazione separate | `genesis/03`, `11`, `12`, `20`; contratti del prototipo | Manca una policy editoriale bilingue sintetica | Manifesto, glossario, ADR editoriale futuro |
| La rielaborazione deve aggiungere valore pedagogico misurabile | `genesis/10`, `19`, `20` | Ipotesi di prodotto non ancora collegata ai risultati del pilot | Vision, Risk List, Inception Review |
| AI Research Notebook come primo prodotto verticale | `genesis/08`, `10` | Nome e confini oscillano tra notebook, workspace e Study Pack | Product Map, decisione D1 |
| Percorso personale con prerequisiti, dubbi, esperimenti e idee di ricerca | `genesis/10`, `19`; parzialmente nel prototipo | Manca il modello canonico di Expedition e profilo dell'apprendente | Use Case Model, glossario |

### 5.2 Grafo temporale, provenienza e comprensione

| Idea | Presenza attuale | Lacuna | Destinazione canonica proposta |
| --- | --- | --- | --- |
| Distinguere grafo delle fonti e conoscenza canonica rielaborata | `genesis/03`, `05`, `11`, `12` | Nessun modello di dominio consolidato | System Context, glossario, futura ontologia |
| Ogni claim deve conservare fonte, tempo, contesto e incertezza | `genesis/01`, `02`, `03`, `05` | `Claim`, `Evidence`, `Observation`, `Position` e `Hypothesis` non hanno ancora un contratto unico | Glossario e futuro Domain Model |
| Non sovrascrivere il passato; ricostruire cambiamenti di posizione | `genesis/01`, `02`, `05` | Manca la scelta tra modello temporale semplice e bitemporale | Risk List e futura ADR |
| Il grafo è una vista della memoria, non necessariamente il centro del sistema | metafore distribuite in `genesis/05`, `06`, `07` | Terminologia instabile: Knowledge Graph, Memory Graph, World Model, Process Model | Decisione D2 e glossario |
| Separare fonte, interpretazione, derivazione e inferenza | `genesis/03`, `05`, `09`, regole operative | Presente come principio, non ancora uniforme nei dati di lungo periodo | Manifesto, glossario, contratti futuri |

### 5.3 Field Intelligence e attualità

| Idea | Presenza attuale | Lacuna | Destinazione canonica proposta |
| --- | --- | --- | --- |
| Mappa di un campo: persone, paper, scuole, controversie e percorso di lettura | `genesis/01`, `02`, `04`, `05`, `07`, `10` | Field Intelligence Map non e definita come prodotto o use case canonico | Product Map, Use Case Model |
| Misurare influenza scientifica, industriale, open source e discorsiva separatamente | `genesis/02`, `05` | Nessun trust/influence model approvato; rischio di falsa precisione | Risk List, ricerca differita |
| Conservare claim pubblici e cambiamenti di posizione senza trasformarli in fatti | `genesis/01`, `02`, `03`, `05` | Mancano policy di attribuzione, contestualizzazione e rettifica | Manifesto, Risk List |
| Timeline di paper, eventi, release, repository e dibattito | `genesis/01`, `04`, `05`, `07` | Manca il primo scenario verticale verificabile | Use Case Model |
| Forecast probabilistici con criteri di risoluzione e calibrazione | `genesis/01`, `05`, `07` | Nessun contratto di forecasting; idea prematura per il prodotto corrente | `deferred-research`, Risk List |

### 5.4 Fonti continue e Knowledge Sensors

| Fonte o capacità | Presenza attuale | Stato reale |
| --- | --- | --- |
| Libri, scansioni, OCR, EPUB e PDF | `genesis/04`, `11`, `12`, `19` | Visione; il prototipo usa contenuti strutturati preparati, non una pipeline generale di ingestion |
| Paper, documentazione e repository GitHub | `genesis/04`, `10`, `12` | Visione e fonti previste; nessun provider generale implementato |
| YouTube, trascrizioni esistenti e speech-to-text | `genesis/04` | Idea catturata ad alto livello; mancano policy e adapter |
| News, RSS, Hacker News, Reddit, podcast e newsletter | `genesis/04`, `07` | Ricerca differita |
| X e LinkedIn | `genesis/04`, `07` | Necessita di verifica aggiornata su API, costi, diritti e conservazione |
| Monitoraggio continuo e change detection | `genesis/04`, `07`, `15` | Visione; non implementato nel pilot |
| Rights-aware ingestion e conservazione selettiva | `genesis/04`, `11`, `12`, `14` | Principio forte; manca un Rights Policy Model canonico |

### 5.5 Prodotti e convergenza

La conversazione ha esplorato Raiatea come possibile nucleo comune per AI
Research Notebook, Learning Lab, Second Brain, Reality Observatory, Field
Intelligence Maps e Forecast Lab, con Alfred come ispirazione event-driven.

Le note `genesis/07`, `08` e `10` conservano buona parte di questa direzione,
ma non esiste ancora una Product Map che distingua:

- prodotto disponibile oggi;
- primo prodotto da validare;
- capability condivisa futura;
- applicazione o vista possibile;
- progetto esterno correlato;
- ricerca di lungo periodo.

Senza questa distinzione, la metafora del "Knowledge OS" rischia di far
apparire come un'unica piattaforma già decisa ciò che è ancora un insieme di
ipotesi convergenti.

### 5.6 Federazione, governance ed economia

Le idee di federazione, Knowledge Bundle, contributi distribuiti, useful work,
governance partecipativa, fondazione, revenue firewall, microlicensing,
aggiornamenti continui a pagamento, livello pubblico gratuito ed emergency
open access sono ampiamente conservate in `genesis/06`-`17`.

Sono una riserva progettuale importante, ma non appartengono al contratto del
prototipo corrente. Dovrebbero essere classificate prevalentemente come
`deferred-research`, salvo i principi già applicabili oggi:

- sovranità dei dati;
- provenienza e verificabilita;
- separazione tra accesso privato e pubblicazione;
- indipendenza dai provider;
- firewall tra missione e incentivi commerciali.

### 5.7 Identita, nome e immaginario di Raiatea

La conversazione fondativa contiene un filone identitario non ancora
formalizzato:

- omaggio al viaggio di Bernard Moitessier e alla barca Joshua;
- conoscenza come navigazione continua, non come gara verso una risposta;
- scelta del nome Raiatea;
- costellazioni polinesiane come possibile metafora del collegamento tra
  conoscenze;
- balena come possibile mascotte;
- preferenza per un marchio semplice, non riconducibile alla grafica generica
  dei prodotti AI;
- necessita di rispetto culturale e verifica delle fonti polinesiane.

Nel repository esistono soltanto placeholder in `branding/` e `manifesto/`.
Questo filone è quindi realmente mancante. Prima di pubblicarlo dovranno essere
verificati riferimenti storici, citazioni, nomi culturali e possibilità di uso
del marchio.

## 6. Stato reale dello sviluppo

### 6.1 Vertical slice implementato

Il codice disponibile non è un Knowledge Core generale. È un vertical slice
locale e supervisionabile della tesi pedagogica di Raiatea.

Risultano implementati, con livelli diversi di maturita:

- moduli pedagogici dichiarativi generati come HTML autosufficiente;
- Focus UI con tema, preferenze di lettura e animazioni controllabili;
- figure semantiche e procedurali step-by-step;
- concetti collegabili, glossario e recuperi mirati;
- micro-attività deterministiche dopo una risposta errata;
- persistenza locale di tentativi ed evidenze osservate;
- provenienza a livello di modulo e di passaggio;
- almeno due moduli di dominio: self-attention e Query/Key/Value;
- validazione di schema, renderer, layout dichiarativi e riferimenti interni;
- test Python e test browser;
- esportazione e migrazione delle evidenze locali;
- archivi riproducibili per valutatori, checksum e helper POSIX/Windows;
- intake multi-record, aggregazione, synthesis kit e runbook del pilot
  supervisionato.

Non risultano invece implementati:

- ingestion generale di libri, paper, YouTube o social;
- grafo temporale canonico;
- identity resolution di persone e organizzazioni;
- Claim/Position/Trend/Forecast engine;
- federazione tra nodi;
- laboratorio containerizzato per l'esecuzione di codice;
- adattamento generativo mediante LLM;
- prodotti Reality Observatory o Forecast Lab.

### 6.2 Stato GitHub osservato

Al 21 luglio 2026:

- `main` locale e `origin/main` coincidono sul commit `13aff47`;
- la PR [#95](https://github.com/kinderp/raiatea/pull/95), relativa al log
  locale degli incidenti del pilot, è aperta, mergeable e con check Linux,
  browser, artifact e Windows verdi;
- la issue madre [#93](https://github.com/kinderp/raiatea/issues/93) guida il
  pilot supervisionato;
- le issue [#96](https://github.com/kinderp/raiatea/issues/96) e
  [#97](https://github.com/kinderp/raiatea/issues/97) coprono rispettivamente
  release-candidate gate e accettazione post-pilot;
- le issue [#33](https://github.com/kinderp/raiatea/issues/33) e
  [#34](https://github.com/kinderp/raiatea/issues/34) restano differite;
- prima di questo audit non risultavano milestone GitHub aperte; la
  consolidazione Genesis ha ora la milestone dedicata
  [Project Genesis consolidation v1](https://github.com/kinderp/raiatea/milestone/1).

Il filone documentale di questo audit e indipendente dalla PR #95 e non deve
ritardare o alterare il pilot senza una scelta esplicita.

### 6.3 Stato delle verifiche locali

Le Actions più recenti del prodotto su `main` e i check finali della PR #95
sono verdi con Python 3.12.

La suite completa, eseguita nell'ambiente locale disponibile con Python
3.10.12, non può importare `build_module.py`: una f-string usa la grammatica
resa valida da Python 3.12. Questo fa emergere un'ambiguità di contratto:

- le workflow di build e test usano Python 3.12;
- il pilot indica Python 3.12 o una versione Python 3 recente;
- gli helper di lancio dichiarano Python 3.10+ per servire gli artefatti già
  costruiti;
- la documentazione non distingue con sufficiente evidenza runtime di build e
  runtime del pacchetto di valutazione.

Non è stata modificata l'implementazione durante questo audit. Il punto va
registrato come finding documentale/di compatibilità e risolto in un micro-step
separato.

## 7. Disallineamenti e rischi documentali

### 7.1 README non aggiornato allo stato del prodotto

Il `README.md` principale descrive Project Genesis come precedente
all'implementazione. La frase protegge correttamente da dichiarazioni premature,
ma oggi nasconde un vertical slice reale e un pilot pronto alla supervisione.

Correzione proposta: descrivere Raiatea come progetto ancora in Genesis sul
piano della piattaforma complessiva, ma in Elaboration/validation sul primo
vertical slice pedagogico.

### 7.2 Indice Genesis non corrispondente ai file

`genesis/README.md` prevede:

1. Why Raiatea;
2. Manifesto;
3. Vision;
4. System Context;
5. Product Map;
6. Use Case Model;
7. Risk List;
8. Glossary;
9. Inception Review.

Questi artefatti non esistono. I numeri `00`-`20` sono invece occupati da note
tematiche. La soluzione proposta e creare `genesis/inception/` per gli
artefatti canonici e mantenere intatti i percorsi delle note storiche.

### 7.3 Assenza di un linguaggio ubiquitario

Termini come Knowledge OS, Knowledge Core, Memory Graph, World Model, Process
Model, Expedition, Study Pack, Research Brief e AI Research Notebook sono
spesso compatibili, ma non ancora gerarchizzati. Questa ambiguità è creativa
nella fase esplorativa e rischiosa quando entra in schema, API e roadmap.

### 7.4 Stato uniforme `draft`

Una costituzione, un principio di provenienza, un'ipotesi commerciale e una
possibile architettura federata non possono avere lo stesso peso operativo.
Serve la tassonomia proposta nella sezione 4.

### 7.5 Mastery ed evidenze osservate

`genesis/19` usa anche il termine `MasteryEvidence`, mentre le regole operative
e il prototipo adottano la formulazione più prudente "evidenze osservate". Il
glossario canonico dovrà riservare `competenza` o `mastery` a un modello
validato e non a semplici interazioni locali.

### 7.6 Rafforzamento tecnico prima della prova di valore

Il prototipo ha investito molto in packaging, migrazioni, intake e tracciati di
valutazione. Questo lavoro rende il pilot riproducibile, ma non dimostra ancora
la tesi principale: che Raiatea migliori comprensione, trasferimento e ripresa
dello studio rispetto alle alternative.

Il rischio non richiede di eliminare l'hardening. Richiede di chiudere il ciclo
#93 -> #95 -> #96 -> #97 e usare i risultati del pilot prima di ampliare
ulteriormente l'infrastruttura.

### 7.7 Diritti, fonti esterne e policy variabili

Le idee su libri protetti, YouTube, X e LinkedIn dipendono da licenze, termini
di servizio, API e giurisdizioni variabili. Genesis contiene principi corretti,
ma nessuna implementazione deve assumere accesso o conservazione consentiti
senza una verifica aggiornata e una policy esplicita.

## 8. Architettura documentale proposta

Le note esistenti restano dove sono durante la prima consolidazione. I documenti
canonici vengono aggiunti in una sottocartella separata:

```text
genesis/
├── README.md
├── 00-...md                  # note esplorative preservate
├── ...
├── 20-...md
└── inception/
    ├── README.md
    ├── 00-genesis-audit-and-traceability.md
    ├── 01-why-raiatea.md
    ├── 02-manifesto.md
    ├── 03-vision.md
    ├── 04-system-context.md
    ├── 05-product-map.md
    ├── 06-use-case-model.md
    ├── 07-risk-list.md
    ├── 08-glossary.md
    └── 09-inception-review.md
```

Ogni documento canonico dovrebbe includere:

- stato e data di revisione;
- decisioni che contiene;
- domande ancora aperte;
- note Genesis di provenienza;
- capability correnti e future chiaramente separate;
- criteri che possono falsificare le ipotesi di prodotto.

Le ADR rimangono in `adr/` e vengono create solo per decisioni tecniche
effettivamente prese. Genesis non deve diventare un deposito di ADR preventive.

## 9. Decisioni da sottoporre al maintainer

### D1. Nome e confine del primo prodotto

Opzioni emerse:

- **AI Research Notebook**: forte identità, ma può sembrare un corpus editoriale;
- **Private AI Research & Learning Workspace**: descrive meglio il prodotto da
  validare, ma e meno memorabile;
- **Study Pack / Living Knowledge Book**: ottimi output o formati, non
  necessariamente il prodotto complessivo.

Proposta iniziale: usare **AI Research Notebook** come esperienza verticale
visibile e **Private Research & Learning Workspace** come categoria di
prodotto. La decisione resta aperta.

### D2. Nome del nucleo di lungo periodo

`Knowledge OS` e `Memory Graph` sono metafore potenti ma troppo impegnative per
un contratto architetturale corrente. `Temporal Provenance Knowledge Core` e
più preciso, ma presuppone comunque un core non ancora implementato.

Proposta iniziale: chiamare **Raiatea** il progetto e usare **knowledge core**
solo come descrizione provvisoria di una capability futura, fino al System
Context.

### D3. Relazione con Alfred e Learning Lab

La convergenza concettuale è reale, ma non dimostra ancora che debbano
condividere un unico runtime, repository o modello di dominio.

Proposta iniziale: descriverli come progetti correlati e possibili consumatori
o integratori, evitando di dichiararli sottoprodotti di Raiatea prima di use
case e confini verificati.

### D4. Priorita tra pilot e nuova infrastruttura

Proposta iniziale: completare il pilot supervisionato e l'accettazione
post-pilot prima di estendere il codice verso ingestion, graph core o AI
generation. La consolidazione documentale può procedere in parallelo perché non
modifica il prodotto.

### D5. Stato di federazione, governance e forecasting

Proposta iniziale: classificarli come `deferred-research`, mantenendo nei
documenti canonici soltanto i vincoli che devono rendere possibile una futura
evoluzione senza imporla oggi.

### D6. Manifesto e riferimenti culturali

Proposta iniziale: conservare la metafora della navigazione e il principio che
la conoscenza sia un viaggio verificabile. Citazioni, Moitessier, Raiatea,
costellazioni e balena richiedono invece una ricerca culturale dedicata prima
di entrare nel Manifesto o nel branding pubblico.

## 10. Sequenza raccomandata

1. Revisionare questo audit con il maintainer.
2. Approvare o correggere la tassonomia di stato.
3. Risolvere le decisioni D1-D6, oppure marcarle esplicitamente come aperte.
4. Scrivere Why Raiatea, Manifesto e Vision in forma breve e canonica.
5. Costruire System Context e Product Map prima del Domain Model.
6. Derivare attori e casi d'uso architetturalmente significativi.
7. Ordinare i rischi per impatto e incertezza, includendo la prova di valore
   pedagogica.
8. Completare l'Inception Review e aggiornare README e indici.
9. Solo dopo decidere quali nuove capability software entrano in Elaboration.

## 11. Criterio di successo della consolidazione

La consolidazione sarà riuscita se un nuovo collaboratore potrà rispondere,
senza leggere ventuno saggi e l'intera conversazione, a queste domande:

- quale problema risolve Raiatea oggi;
- quale primo utente e quale primo prodotto stiamo validando;
- cosa è già implementato e cosa non lo è;
- quali principi non sono negoziabili;
- quali ipotesi potrebbero essere smentite;
- quali prodotti futuri condividono davvero capability comuni;
- come ogni affermazione importante risale alle sue fonti;
- quale decisione deve essere presa dopo e da chi.

Le note Genesis continueranno a offrire profondita, storia e alternative. Gli
artefatti di Inception offriranno invece orientamento e contratto progettuale.
