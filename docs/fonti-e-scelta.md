# Fonti e scelta del percorso minimo

Verifica della documentazione pubblica: **12 ottobre 2026**. Studio letto: `Studio_fattibilita_UFP.docx`, documento allegato dall'utente; le sue fonti erano state consultate il 5 ottobre 2026. Le capacità pubblicizzate dal produttore non certificano disponibilità, licenze o comportamento dell'installazione UFP 4.6.

## Quali informazioni sostengono la scelta

| Livello di evidenza | Informazione | Conseguenza per la prima versione |
| --- | --- | --- |
| Riferito dall'utente | Il magazziniere controlla materialmente la merce. L'automazione parte soltanto da dati confermati. | Nessuna foto, quantità ordinata o suggerimento automatico sostituisce la conferma fisica. |
| Osservato nello studio sui materiali originali; non nuova verifica del gestionale | Chrome su Windows, ARS@Logistica 4.6, `Ingresso Merci > Nuovo DDT`, importazione di ordini già presenti, selezione di righe e quantità; poi `Logistica Interna > Libero`, conclusione con `Sospendi`. | Due fasi separate con verifica degli esiti e ripresa indipendente. `Importa documento` non è prova di importazione CSV/API. |
| Osservato nello studio | Più ordini e causali possono concorrere a un DDT; codici ripetuti; discordanza Friulsider e ripresa dopo intervento dell'ufficio. | Identificazione della riga d'ordine, residui e blocco delle discordanti; nessuna correzione per somiglianza. |
| Osservato nello studio | Pessinacciai: quantità in TO nella bolla e KG nel gestionale. Häfele: `Coppia` nella bolla e `NR` a video. | Conversioni esplicite. La relazione tonnellata metrica/chilogrammo è aritmetica; `Coppia`/`NR` richiede la regola dell'anagrafica UFP. |
| Conclusione dello studio | Automazione assistita plausibile, ma subordinata alla capacità di leggere righe, identificativi, documenti e liste già creati. | Si sviluppa il motore locale; il collegamento reale resta da qualificare. |
| Ipotesi tecnica adottata per la prima versione | Un operatore, dati strutturati controllati, logica deterministica, stato locale e adattatore separato. | Si può verificare la logica con un simulatore senza inventare API, selettori o garanzie transazionali. |
| Verifica ancora necessaria | Accesso autorizzato, ambiente di prova, identificativi stabili, momenti di salvataggio, equivalenze anagrafiche e risultato sul palmare. | Nessuna compatibilità con ARS né disponibilità sul palmare viene dichiarata sulla base della simulazione. |

Il rapporto indica come incompleti le pagine 4–5 di Friulsider, l'abbinamento della registrazione FAC e la bolla OTLAV. Questi limiti impediscono le rispettive riconciliazioni complete; non devono essere colmati inventando dati. I DDT storici dei video sono esempi, non candidati da caricare nuovamente.

## Prima verifica: funzioni native e integrazioni

La [pagina ufficiale ARS@Logistica di Altaquota](https://www.aquota.net/prodotti/ars-logistica/) descrive un prodotto web mobile, ricevimento merci, movimentazioni interne e integrazione con la linea Ad Hoc Zucchetti. La [presentazione ufficiale](https://www.aquota.net/landing/ars-logistica-software-gestione-magazzino/) mostra selezione di ordini e di righe d'ordine per il DDT fornitore. È coerente con l'importazione **interna** riportata nello studio; non espone un contratto per importare ricezioni da un file preparato dall'operatore.

La [pagina ufficiale Ad Hoc Revolution](https://www.aquota.net/prodotti/ad-hoc-revolution/) menziona importazione automatica di archivi, movimenti e documenti. È una pista concreta da verificare con l'assistenza: non sappiamo se UFP utilizzi quel gestionale, con quali moduli, né se questa funzione conservi i riferimenti alle righe d'ordine e produca/riprenda la lista `Libero`.

Sono state consultate queste pagine e ricerche circoscritte al sito ufficiale con i termini ARS@Logistica, API, importazione, file, manuale, tracciato e 4.6. **Non è stato trovato un tracciato o contratto API pubblico applicabile al flusso UFP descritto. Questo non dimostra che tale integrazione non esista.** Non sono stati contattati fornitori o inviati documenti aziendali.

Prima di scegliere l'adattatore reale, IT/assistenza devono chiarire:

1. Gestionale sottostante, versione/moduli e possibilità nativa di ricevere quantità confermate da file o integrazione documentata.
2. Riferimenti disponibili per ordine, causale, singola riga, DDT e lista; gestione dei residui, importazione parziale e lettura dei documenti preesistenti.
3. Creazione e ripresa separate di DDT e `Libero`; possibilità di leggere stato e righe completi dopo un'interruzione; eventuali vincoli contro duplicati.
4. Ambiente di prova e modalità autorizzata di accesso dalla postazione UFP; consenso all'eventuale automazione browser.

La richiesta resta una lista di verifiche, non una comunicazione già inviata. Un'integrazione nativa documentata che soddisfi questi punti ha priorità rispetto al browser.

## Strumenti considerati

| Strumento e fonte ufficiale | Capacità documentata oggi | Decisione circoscritta a UFP |
| --- | --- | --- |
| [CLI-Anything, HKUDS](https://github.com/HKUDS/CLI-Anything) | Pipeline di generazione CLI basata sull'analisi dei sorgenti; possibili rifiniture. Il repository include anche adattatori su API e browser, tra cui DOMShell/accessibility tree e un esempio Playwright. La roadmap menziona ancora confezionamento di API per software chiusi. | Nessun connettore ARS identificato nel README consultato e nessuna compatibilità provata. Senza sorgenti o interfaccia ARS documentata aggiunge uno strato senza risolvere l'incertezza attuale. Non necessario nella prima versione. |
| [Jev / TypeSafe](https://typesafe.ai), [modelli](https://docs.typesafe.ai/models), [ruolo rispetto agli agenti](https://docs.typesafe.ai/introduction/coding-agents) | Jev riceve testo/dati testuali strutturati e produce decisioni tipizzate. La documentazione corrente presenta Jev 1.13; non accetta direttamente immagini, audio o video e non è un agente che chiama strumenti o guida il browser. | Il problema richiede codici esatti, quantità e controlli di stato. Nessuna necessità di decisioni probabilistiche o invio dei dati a un'API esterna. Escluso dalla prima versione. |
| [Limiti Jev 1.13](https://docs.typesafe.ai/model-jaggedness/jev-1.13) | La documentazione sconsiglia di ricostruire numeri esatti dagli score, la cui calibrazione numerica è debole. | Le conversioni e i residui si calcolano deterministicamente; l'operatore decide le discordanti. |
| [Playwright Python: locators](https://playwright.dev/python/docs/locators) e [auto-waiting](https://playwright.dev/python/docs/actionability) | Ricerca degli elementi per ruolo, etichetta o identificatore concordato, controlli prima delle azioni e attese automatiche. | Candidato minimo **se** manca una soluzione nativa adeguata e il DOM reale permette letture/azioni stabili. Nessun selettore ARS verificato. Un clic riuscito o l'auto-waiting non provano il salvataggio del DDT. |

I prezzi e le stime economiche dello studio non sono necessari alla scelta attuale e non vengono trattati come preventivi o benefici misurati. Nessuno di questi strumenti è stato installato o collegato al gestionale per questa verifica delle fonti.

## Architettura minima motivata

Il nucleo locale riceve una lista controllata dall'operatore e uno stato degli ordini fornito esplicitamente. Mantiene separate quantità della bolla, quantità fisica e quantità da registrare; calcola conversioni autorizzate; produce abbinamenti e anomalie comprensibili. La conferma è legata ai dati esatti, non a un semplice flag riutilizzabile dopo modifiche. Il registro di lavoro distingue tentativo ed esito verificato per ciascuna delle due fasi.

Il simulatore fornisce l'ambiente su cui esercitare questa logica, incluse interruzioni e letture degli esiti. Gli identificativi dei suoi ordini e documenti sono dati di simulazione: la loro presenza non dimostra che ARS esponga gli stessi campi. Il registro locale non prova l'assenza di documenti nel gestionale.

L'adattatore reale resta separato fino alla verifica dell'interfaccia disponibile. Se servirà Playwright, si useranno elementi identificabili, controlli espliciti su sessione e schermata, rilettura del documento completo e arresto in presenza di ambiguità. Nessuna dipendenza da coordinate o immagini è giustificata dai materiali attuali. Non si introduce un'interfaccia complessa, OCR, AI o servizio cloud per questa prima versione.

## Riferimenti originali conservati

- Repository richiesto: <https://github.com/av3rgfx/ufp-bolle>.
- Studio: allegato dell'utente `Studio_fattibilita_UFP.docx`.
- Cartella indicata nel corpo della richiesta e nello studio: <https://drive.google.com/drive/folders/1oNqODNp_cwIcac_tjdyc2gk4I2u6ZzQ4?usp=sharing>.
- CLI-Anything: <https://github.com/HKUDS/CLI-Anything>.
- Jev/TypeSafe: <https://typesafe.ai>.

L'ultimo collegamento dell'utente è stato fornito anche nella seguente forma spezzata e discordante; viene conservato senza interpretare `0` come `o`, `|` come `I` o rimuovere arbitrariamente il trattino:

```text
https://
drive.google.com/drive/folders/
10NqODNp_cwIcac_tjdyc2g-
k4|2u6ZzQ4?usp=sharing
```

Per cercare i materiali si usa il primo URL completo, corroborato dallo studio. L'esito effettivo dell'accesso ai file originali va documentato separatamente dalla verifica delle fonti pubbliche qui svolta.
