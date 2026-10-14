# Architettura della prima versione

La versione attuale prepara dati controllati e fa funzionare il flusso **in un simulatore locale**. Non contiene un connettore ARS, una sessione browser o un comando di produzione. Il blocco nell'esecutore accetta esclusivamente `SimulatedArs`: aggiungere un URL o cambiare un flag non abilita scritture reali.

La scelta è Python con libreria standard: CLI, JSON, `Decimal`, SHA-256 e SQLite. Un solo operatore e due fasi esplicite bastano al caso iniziale; nessun OCR, AI o servizio cloud è necessario. Motivazioni e fonti: [fonti-e-scelta.md](fonti-e-scelta.md). Provenienza dei casi e limiti dei materiali: [materiali.md](materiali.md).

## Componenti e confini

| Componente | Responsabilità | Cosa non dimostra |
| --- | --- | --- |
| `planner.py` | Validazione delle sorgenti JSON, abbinamenti esatti, conversioni e residui, piano completo e impronta. Nessun accesso al gestionale. | Che lo snapshot sia quello attuale di ARS o che il controllo fisico sia avvenuto. |
| `cli.py` | Riepilogo leggibile, conferma dell'impronta, avvio separato delle fasi, stato e guasti simulati. | Che la conferma locale autorizzi una scrittura reale. |
| `engine.py` | Conferme e stato durevole; lettura dell'esito prima di ogni scrittura/ripresa e dopo il tentativo. | Compatibilità con stati intermedi o transazioni ARS. |
| `simulator.py` | Ordini, DDT e liste fittizi, residui, ricerca completa e risposte perse. | UI, identificativi, vincoli o atomicità del gestionale reale. |
| `storage.py` | JSON non sovrascritti, SQLite con ruoli separati, permessi locali e lock per registro. | Protezione contro altri operatori o applicazioni che agiscono sul server. |

Il registro SQLite contiene conferme, piano esatto, fase, identificativo dell'artefatto simulato, evidenza e storico degli stati. Il database del simulatore contiene invece ordini e documenti. I ruoli impediscono di usare lo stesso database per entrambi. Questa separazione permette di perdere una risposta dopo un salvataggio e poi ritrovare il documento senza affidarsi al registro.

## Dati, abbinamenti e conferma

- La chiave documento combina **fornitore, numero completo, data, serie e magazzino**. Non si eliminano zeri, suffissi o segni. Il simulatore blocca anche la collisione stesso fornitore/numero/serie/magazzino nello stesso anno con data diversa.
- Ogni ricezione conserva riferimento di riga, tipo/numero ordine, riga d'ordine se disponibile, entrambi i codici, ubicazione e tre quantità: documentale, fisicamente confermata e da registrare. La terza è calcolata, non dedotta dalla quantità ordinata.
- Il confronto usa valori esatti di fornitore, magazzino, ordine, ubicazione, codici fornitore/interno ed eventuale riga d'ordine. Senza riga esplicita è ammesso solo un candidato univoco. Non si sceglie il primo risultato e non si ripartiscono automaticamente quantità fra ordini.
- Lo snapshot richiede `row_id` stabile; gli esempi usano valori `SIM-*`. **Non è stato accertato quale identificativo equivalente esponga ARS.** Se non sarà disponibile un riferimento verificabile alla riga, l'adattatore reale non potrà abilitare il caricamento di quel caso.
- Righe ripetute restano distinte. Se più righe della bolla puntano alla stessa riga d'ordine, la somma da registrare deve stare nel residuo. Una consegna successiva usa una nuova bolla e uno snapshot aggiornato del residuo; non è un duplicato della precedente soltanto perché ripete l'articolo.
- Le quantità sono stringhe decimali e i calcoli usano `Decimal`, senza arrotondamenti impliciti. Bolla e controllo fisico devono usare la stessa UM nella v1; una differenza di quantità richiede un motivo. Sono ammesse conversioni esplicite **TO → KG ×1000** e **KG → TO ×0.001**, con riferimento alla regola verificata. Altre equivalenze, incluso `Coppia`/`NR`, restano bloccate.

La v1 richiede tutte le righe da registrare della bolla e `complete_document: true`. Una consegna parziale rispetto all'ordine è ammessa; dividere in più caricamenti indipendenti la stessa bolla non è supportato. Qualsiasi anomalia blocca l'intero documento: le righe sane restano nel riepilogo, ma non vengono caricate separatamente. È una scelta prudente per evitare un secondo problema di ripresa all'interno del DDT.

Il piano include le sorgenti complete e i risultati; SHA-256 lega la conferma a quei dati esatti. All'uso il piano viene anche ricostruito dalle sorgenti: cambiare un risultato e ricalcolare soltanto l'impronta non basta. Qualsiasi revisione richiede un nuovo piano e una nuova conferma dell'intero riepilogo. La conferma registra operatore e istante; non è una firma digitale né una prova indipendente dell'identità o del controllo fisico.

## Due fasi e ripresa

Per ogni piano il registro mantiene `initial` e `libero` separati. Gli stati locali sono `PENDING`, `INTENT`, `UNKNOWN`, `VERIFIED`; non sono nomi attribuiti ad ARS.

1. Verificare piano e conferma. Per `libero`, rileggere prima il DDT iniziale e conservarne l'identificativo effettivamente restituito dal simulatore.
2. Cercare nel simulatore il documento/lista pertinente. Se esiste con dati, collegamento e stato esatti, registrare la verifica e terminare senza riscrivere. Conflitto o esito illeggibile arrestano il flusso. Un documento prima verificato e poi assente non viene ricreato automaticamente.
3. Se la ricerca completa prova l'assenza, registrare `INTENT` prima del tentativo. Il simulatore ripete il controllo dentro la propria transazione; per `initial` confronta anche righe e residui attuali con quelli approvati.
4. Scrivere nel simulatore e rileggere l'effetto completo. Solo la corrispondenza porta a `VERIFIED`. Errori durante il tentativo portano a `UNKNOWN`; un arresto dopo l'intento può lasciare `INTENT`. Entrambi richiedono rilettura alla ripresa.

Un errore in `libero` non richiama il caricamento iniziale. La ripresa verifica il DDT già presente e cerca la lista: crea soltanto ciò che risulta assente. Il comando `status` mostra il registro locale e non compie questa riconciliazione; `run` la esegue esclusivamente nel simulatore. Il palmare resta sempre `NON_VERIFICATO`.

Nel simulatore il DDT e l'aggiornamento dei residui sono atomici e il vincolo documento/fase è univoco. Queste sono **proprietà del modello di prova**, non garanzie di ARS: i video non chiariscono se ogni riga provochi già un salvataggio. Un adattatore reale richiederà eventuali stati/identificativi intermedi e letture complete prima di poter usare la stessa strategia di ripresa. L'assenza deve essere provata dal sistema; un registro locale vuoto, una schermata incompleta o un timeout non bastano.

## Dati locali e limiti operativi

I file contengono dati aziendali e non sono cifrati dal programma: conservarli in una cartella privata della postazione autorizzata, con backup e permessi IT appropriati. Sono richiesti permessi restrittivi nei sistemi che li supportano; su Windows vanno verificati anche gli ACL della cartella. Non inserire credenziali nei JSON. Il programma non richiede password, non invia telemetria e non effettua richieste di rete; il riepilogo a terminale contiene necessariamente i dati da controllare.

Il lock protegge un registro locale; registri distinti non coordinano operatori distinti. L'uso resta limitato a un operatore. Dopo un arresto verificare che il processo sia terminato prima di eliminare un eventuale `.lock` residuo; conservare piano e database. Non cancellare il registro per aggirare un'anomalia. La [procedura della futura prova reale](prova-reale.md) definisce le ulteriori condizioni: oggi non è stata eseguita alcuna operazione sul gestionale.
