# AGENTS.md

Questo file indica il bootstrap minimo per agenti AI e contributori automatici che lavorano su Raiatea.

Prima di modificare codice, schema, documentazione o workflow:

1. leggere [`docs/it/00-regole-operative.md`](docs/it/00-regole-operative.md);
2. leggere [`docs/it/01-commit-pr-review.md`](docs/it/01-commit-pr-review.md);
3. leggere soltanto i documenti `genesis/` pertinenti al task corrente;
4. aprire issue, pull request, codice e test collegati;
5. distinguere stato corrente, roadmap futura, ipotesi e decisioni consolidate;
6. non introdurre cambiamenti architetturali importanti senza accordo esplicito del maintainer.

Regole minime:

- procedere per micro-step coerenti, verificabili e reversibili;
- usare la catena `milestone -> issue madre -> issue figlia -> branch -> draft PR -> review -> merge` per lavori non banali;
- usare branch e pull request per modifiche non banali;
- mantenere una sola PR di lavoro aperta per filone sequenziale;
- aprire presto la PR come draft e collegarla a issue madre e issue figlia;
- usare commit atomici con soggetto imperativo e specifico;
- citare commit in issue, PR, finding e report con SHA di 7 caratteri cliccabile alla pagina GitHub del commit completo;
- registrare ogni finding nel thread pertinente e nel finding log della PR;
- rispondere ai finding con spiegazione, test e link al commit di fix; non usare risposte come `fixed` o `done` senza contesto;
- richiedere due round consecutivi di review senza nuovi finding bloccanti prima del merge di una PR non banale;
- azzerare il conteggio dei round dopo modifiche sostanziali o nuovi finding bloccanti;
- correggere le GitHub Actions rosse, commentare causa e fix nella PR e non mergiare finché le Action richieste non sono verdi;
- aggiornare schema, validatore, esempio, test e documentazione quando cambia un contratto dichiarativo;
- preservare provenienza e separare fonte, traduzione, adattamento, derivazione, inferenza e ipotesi;
- non chiamare competenza o mastery semplici interazioni osservate;
- comunicare in chat apertura e chiusura di issue e PR, round di review, finding bloccanti, fix, Action rosse e merge;
- produrre il report giornaliero in `docs/daily-reports/` e aggiornare il relativo indice.

In caso di conflitto, prevalgono nell'ordine:

1. richiesta esplicita corrente del maintainer;
2. `docs/it/00-regole-operative.md`;
3. `docs/it/01-commit-pr-review.md`;
4. ADR e contratti stabili del componente;
5. roadmap della milestone corrente;
6. documentazione generale;
7. note storiche e idee future.
