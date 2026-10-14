# Scheda per la futura prova reale

**Stato: non pronta per l'esecuzione. Nessuna autorizzazione richiesta ora.** Mancano nuova bolla controllata, accesso concordato, identificativi reali, regole UFP e connettore verificato. La CLI consegnata opera soltanto in simulazione; `confirm` conferma il piano locale e non autorizza una scrittura nel gestionale. Questa scheda serve a rendere concreta e verificabile la successiva richiesta di autorizzazione.

**Aggiornamento di fine sessione, 12 ottobre 2026:** l'utente non ritiene disponibile un ambiente di prova e si informerà presso l'assistenza. Non è un'assenza accertata e non si attende questa risposta per preparare dati o qualificare l'accesso in sola lettura. È stato discusso un percorso con una nuova bolla reale, limitata e presidiata, dopo i controlli di questa scheda. La domanda dell'utente sulla possibilità di usare bolle reali **non autorizza ancora alcuna scrittura**. Guasti artificiali, prove distruttive e duplicazioni volontarie restano esclusi dalla produzione; i test di errore continuano nel simulatore o in un eventuale ambiente separato. Stato e domande da riprendere: [prossima-sessione.md](prossima-sessione.md).

## Condizioni da risolvere prima delle scritture

Prima verificare con IT/assistenza una funzione nativa o un'importazione/integrazione documentata che copra ricezione parziale, collegamento alle righe d'ordine, lettura degli esiti e ripresa di DDT e `Libero`. Se non è disponibile o adeguata, qualificare l'accesso browser autorizzato in sola lettura: identificazione stabile di campi/righe, paginazione completa, sessione, messaggi, ricerca documenti/liste e momento dei salvataggi. Nessun selettore o identificativo va ricavato per supposizione dai video.

L'ispezione deve usare una modalità effettivamente priva di scritture: non aprire creazioni o premere comandi di cui non sia noto l'effetto. Un pulsante per aggiungere una riga può già scrivere sul server. Se gli esiti non sono leggibili in modo affidabile, limitare il prodotto alla preparazione e lasciare il caricamento all'operatore.

Vanno inoltre chiariti sistema operativo/postazione, rete e modalità autorizzata di accesso, permessi, ambiente di prova, conservazione locale dei dati, modo di confermare il controllo fisico, regole dei campi di testata e significato del passaggio sul palmare. Le domande all'operatore sono pendenti nella conversazione; nessun valore storico costituisce una risposta. Credenziali e URL privati si configurano localmente con IT, senza inserirli in documentazione, codice o log. Non sono state inviate richieste all'assistenza.

## Caso limitato da compilare

Scegliere **una nuova bolla completa di un solo fornitore, 1–3 righe e un solo operatore**, con articoli noti e abbinamenti univoci. Il caso può seguire la forma Pessinacciai, che ha ispirato l'esempio locale, ma numero, quantità, ordini e residui devono provenire dal nuovo arrivo. Non riusare i DDT già lavorati dei video. Preferire stessa UM; TO/KG è ammesso solo con regola esplicita verificata. Non usare `Coppia`/`NR` finché non è chiarita l'anagrafica.

| Campo della scheda | Valore da fornire e fonte |
| --- | --- |
| Ambiente, operatore e responsabile della riconciliazione | Da compilare; indicare prova separata oppure produzione autorizzata. |
| Fornitore | Denominazione e identificativo letto dal gestionale. |
| Bolla | Numero completo, suffissi/serie, data, tutte le pagine; riferimento locale alla fonte. |
| Destinazione | Magazzino e ubicazione selezionabili e verificati nel gestionale. |
| Testata e trasporto | Causale/alfa, colli, Vettore, date e altri campi obbligatori: elenco e regole da verificare con UFP. Non copiare alla cieca i valori storici dai video. |
| Controllo fisico | Operatore, istante, articoli/quantità/UM realmente controllati e motivi delle differenze. |
| Piano congelato | Percorso della revisione JSON e SHA-256 completo; stato ordini e istante della lettura. |
| Esito iniziale atteso | DDT pertinente, righe esatte, quantità/UM, residui e stato reale concordato. |
| Esito `Libero` atteso | Una sola lista pertinente collegata a quel DDT, stato dopo `Sospendi` e destinazione operativa concordati. |
| Palmare | Dispositivo/operatore, vista attesa, identificativo o collegamento verificabile con DDT/lista, momento del controllo. |

Compilare una riga della tabella per ciascuna riga ricevuta; nessun segnaposto può restare nella richiesta di autorizzazione:

| Riga bolla e fonte | Ordine: tipo/numero/riga e identificativo reale | Codice fornitore / interno | Quantità bolla / UM | Quantità fisica / UM | Conversione e fonte | Da registrare / UM | Residuo prima → dopo | Magazzino/ubicazione |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Da compilare | Da leggere da ARS | Da verificare esattamente | Da bolla | Da operatore | Nessuna oppure regola approvata | Calcolata | Letto → calcolato | Da verificare |

## Controlli prima e autorizzazioni

1. Riconciliare l'intera bolla e il controllo fisico con il piano. Selezionare soltanto le righe arrivate. Controllare separatamente righe ripetute, codici, quantità, UM, magazzino, ubicazione e somma rispetto ai residui. Nessuna anomalia aperta.
2. Cercare nel gestionale DDT e liste preesistenti in tutti gli stati pertinenti, inclusi sospesi e documenti su altre pagine. Usare fornitore, numero completo, serie, data/anno e magazzino; una collisione stesso numero/anno con data diversa richiede chiarimento. Confrontare righe e identificativi effettivi, non il nome di un file o il solo codice articolo.
3. Registrare lo stato iniziale e l'evidenza della ricerca completa, senza credenziali. Confrontare subito prima dell'azione gli ordini e i residui attuali con quelli approvati. Ogni modifica invalida il piano: nuova revisione, nuovo riepilogo e nuova autorizzazione.
4. Presentare all'utente la scheda completata, piano/impronta, modifiche esatte e criteri di successo. **Attendere autorizzazione esplicita per il caricamento iniziale** nell'ambiente nominato. L'autorizzazione riguarda quel caso e quei dati.
5. Dopo il caricamento, verificare il DDT effettivo e le operazioni previste in `Libero`. Se la seconda fase era compresa nell'autorizzazione esplicita sul riepilogo completo e i dati non sono cambiati, proseguire entro quel perimetro; altrimenti presentare le operazioni concrete e attenderne l'autorizzazione. Le due fasi restano tecnicamente distinte: non richiedere di nuovo un'autorizzazione già valida e non estenderla a modifiche non presentate.

Non bastano un piano JSON valido o una conferma fisica dichiarata: l'operatore deve aver controllato la merce e letto il riepilogo. Gli identificativi mancanti non si sostituiscono con `SIM-*`. Anche eventuali passaggi manuali che modificano il gestionale rientrano nel perimetro da presentare e autorizzare.

## Esecuzione e risultati da provare

| Fase | Operazione limitata | Evidenze e criteri di successo |
| --- | --- | --- |
| Iniziale | Creare/riprendere il DDT autorizzato e registrare soltanto le righe congelate. | Rilettura del DDT completo, su **tutte le pagine**, con ID e stato reali; testata corretta; tutti e soli gli ordini/righe, codici, quantità e UM approvati; residui diminuiti solo delle quantità ricevute; nessun duplicato. |
| `Libero` | Sul DDT già verificato, creare/riprendere la lista pertinente e arrivare al passaggio autorizzato `Sospendi`. | Rilettura della lista completa, ID/stato reali e collegamento al DDT; stessi articoli/quantità/UM previsti; nessuna seconda lista. Non riscrivere il DDT se questa fase fallisce. |
| Palmare | Controllare effettivamente sul dispositivo il risultato operativo concordato. | Identificativo o riferimento riconciliabile alla stessa lista/DDT, righe/quantità attese, operatore e istante del controllo. Annotare `NON VERIFICATO` finché manca questo riscontro. L'eventuale azione sul palmare che registra movimenti richiede a sua volta un perimetro autorizzato. |

Il ritorno alla home, l'assenza di un errore e un clic riuscito non sono prove. Anche una lista sospesa visibile nel browser non dimostra la disponibilità sul palmare. Conservare le evidenze soltanto nella sede aziendale autorizzata; non allegare bolle, schermate aziendali o sessioni a repository e servizi esterni.

## Arresto e ripresa controllata

- **Timeout, risposta persa o processo interrotto:** interrompere le scritture e conservare piano, registro e identificativi disponibili. Rileggere nel gestionale documento, righe, residui e liste prima di ripetere qualsiasi azione. Non cancellare lo storico per ripartire.
- **Esito esattamente presente:** adottare l'identificativo reale verificato e riprendere dalla fase ancora mancante. Se il DDT è completo e manca soltanto `Libero`, non creare un altro DDT.
- **Documento parziale o sospeso:** identificare le righe già salvate e riconciliare con il piano. La simulazione atomica non autorizza a reinviare l'intero documento. Se l'adattatore non supporta quel punto di ripresa, prosegue soltanto l'operatore autorizzato con procedura concordata.
- **Esito assente:** ripetere soltanto dopo una ricerca completa e attendibile e dopo aver confermato dati/residui invariati e validità dell'autorizzazione. Un elenco vuoto per filtro, sessione scaduta o paginazione incompleta non prova assenza.
- **Esito incerto, duplicati, identificativo cambiato, sessione scaduta, schermata inattesa o dati discordanti:** arresto; riconciliazione manuale con il responsabile. Ripristinare l'accesso non basta: occorre rileggere lo stato prima della ripresa.

Non si presume annullamento automatico. Correzioni, storni o cancellazioni sono operazioni distinte da presentare con effetti e controlli prima di chiederne l'autorizzazione. Provare guasti e ripartenze in un ambiente separato; non provocare duplicazioni o errori in produzione. La prova si chiude con esito per ciascun criterio, anomalie residue e riscontro palmare separato. Eventuali tempi vanno misurati includendo preparazione e controllo; nessun risparmio è promesso.
