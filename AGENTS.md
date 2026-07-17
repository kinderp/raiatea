# AGENTS.md

Questo file indica il bootstrap minimo per agenti AI e contributori automatici che lavorano su Raiatea.

Prima di modificare codice, schema, documentazione o workflow:

1. leggere [`docs/it/00-regole-operative.md`](docs/it/00-regole-operative.md);
2. leggere soltanto i documenti `genesis/` pertinenti al task corrente;
3. aprire issue, pull request, codice e test collegati;
4. distinguere stato corrente, roadmap futura, ipotesi e decisioni consolidate;
5. non introdurre cambiamenti architetturali importanti senza accordo esplicito del maintainer.

Regole minime:

- procedere per micro-step coerenti, verificabili e reversibili;
- usare branch e pull request per modifiche non banali;
- mantenere una sola PR di lavoro aperta per filone sequenziale;
- richiedere due round consecutivi di review senza nuovi finding bloccanti prima del merge di una PR non banale;
- correggere le GitHub Actions rosse prima di dichiarare stabile un incremento;
- aggiornare schema, validatore, esempio, test e documentazione quando cambia un contratto dichiarativo;
- preservare provenienza e separare fonte, traduzione, adattamento, derivazione, inferenza e ipotesi;
- non chiamare competenza o mastery semplici interazioni osservate;
- comunicare in chat apertura e chiusura di issue e PR;
- produrre il report giornaliero in `docs/daily-reports/` e aggiornare il relativo indice.

In caso di conflitto, prevalgono nell'ordine:

1. richiesta esplicita corrente del maintainer;
2. `docs/it/00-regole-operative.md`;
3. ADR e contratti stabili del componente;
4. roadmap della milestone corrente;
5. documentazione generale;
6. note storiche e idee future.
