# Materiali, provenienza e verifiche

Verifica di questa sessione: **12 ottobre 2026**. Il rapporto fornito è
`Studio_fattibilita_UFP.docx` (studio datato 5 ottobre 2026). È stato letto
tramite estrazione locale del testo del DOCX; non è stato modificato né
caricato nel repository. Le fotografie sono state scaricate tramite il
connettore Google Drive, convertite localmente da HEIC a JPEG e osservate.
Non è stato usato OCR e non sono state inviate a un servizio esterno di
riconoscimento. Originali e derivati di lavoro restano fuori dal repository.

Questo repository è pubblico. La versione pubblicata conserva i riferimenti
richiesti dall'utente e le evidenze necessarie al progetto, senza trascrivere
numeri di DDT, ordini, codici articolo o altri identificativi aziendali estratti
dalle foto. I dettagli vanno ricontrollati nelle fonti originali tramite un
accesso autorizzato. Gli esempi eseguibili contengono soltanto dati sintetici.

## Collegamenti conservati

- Cartella valida fornita dall'utente e riportata nello studio:
  <https://drive.google.com/drive/folders/1oNqODNp_cwIcac_tjdyc2gk4I2u6ZzQ4?usp=sharing>.
- Secondo riferimento ricevuto, conservato **senza correggerlo**:

  ```text
  https://
  drive.google.com/drive/folders/
  10NqODNp_cwIcac_tjdyc2g-
  k4|2u6ZzQ4?usp=sharing
  ```

  Questo testo contiene interruzioni e un identificativo diverso, incluso
  `|`: non è stato assunto equivalente al primo né usato come fonte.
- Repository richiesto: <https://github.com/av3rgfx/ufp-bolle>.
- Strumenti indicati: <https://github.com/HKUDS/CLI-Anything> e
  <https://typesafe.ai>.

## Legenda

- **Osservato in questa sessione**: letto nel file originale o nei suoi
  metadati, con limite dichiarato.
- **Riscontro dello studio**: osservazione descritta nel DOCX, non
  necessariamente ripetuta in questa sessione.
- **Conclusione dello studio**: raccomandazione, non capacità dimostrata
  del gestionale.
- **Ipotesi tecnica**: scelta del prototipo o simulazione, non informazione
  attribuita ad ARS@Logistica.
- **Da verificare**: informazione assente o insufficiente per l'uso reale.

## Riscontri ripetuti sui documenti originali

La cartella è accessibile: il connettore ha elencato **10 HEIC e 5 MP4**.
Sono state rilette le cinque foto pertinenti ai rischi della prima versione:

| Fonte | Osservato in questa sessione | Conseguenza e limite |
| --- | --- | --- |
| IMG_2375, Häfele | Pagina 1/1; una riga, codice e riferimenti di ordine leggibili, unità **Coppia**. Numero/data DDT e riferimenti sono stati confrontati con lo studio, ma non trascritti qui. | Caso documentale semplice. Il riferimento fornitore/posizione non prova l'ID della riga interna. Codice interno, residuo e UM `NR` sono riscontri dello studio sui video, non della foto. Nessun fattore Coppia → NR è autorizzato dalla sola foto. |
| IMG_2372, Pessinacciai | Tre nastri di dimensioni diverse; quantità in **TO**. La quantità 0,072 TO ha ispirato l'esempio sintetico. Il codice comune è etichettato **HS Code**. | Non usare il codice doganale come codice articolo. La conversione metrica ×1000 è deterministica; associazione alle righe interne e adozione operativa richiedono ancora verifica. La foto non conferma quantità fisicamente arrivate. |
| IMG_2368, FAC | Pagina 1/1. Lo stesso codice compare due volte con uguale quantità e UM, in gruppi con riferimenti d'ordine diversi. | Due righe non vanno fuse o eliminate perché articolo e quantità coincidono. La foto non fornisce identificativi interni stabili e non dimostra l'associazione alle righe del gestionale. |
| IMG_2377, Friulsider p. 2 | Pagina **2 di 5**. Letti codice e quantità della riga interessata dalla discordanza citata nel rapporto. | La discordanza con il codice interno è descritta nello studio sul video V2, non visibile nella sola foto. Non stabilire equivalenze per somiglianza. |
| IMG_2378, Friulsider p. 3 | Stesso DDT, pagina **3 di 5**, con rinvio a pagina 4. Letti codice e quantità della riga citata nel rapporto. | La foto prova la riga documentale; la sua assenza dall'ordine e la successiva correzione sono riscontri dello studio. Non è disponibile una prova della completezza del DDT. |

I segni a penna sono visibili, ma il loro significato operativo non è stato
concordato: **non valgono come conferma della ricezione fisica**.

## Video: disponibilità e limite della verifica attuale

I metadati dei cinque file sono stati riletti; durate e sequenze nella tabella
seguente provengono dallo studio. **Nessun video è stato riprodotto nuovamente
in questa sessione**.

| Sigla dello studio | File | Durata riportata | Dimensione dai metadati |
| --- | --- | --- | ---: |
| V1 | `record_2026-10-05_12-24-47.mp4` | 04:25 | 268.164.990 byte |
| V2 | `record_2026-10-05_14-55-42.mp4` | 15:20 | 932.395.325 byte |
| V3 | `record_2026-10-05_15-21-12.mp4` | 06:59 | 423.939.022 byte |
| V4 | `record_2026-10-05_15-34-25.mp4` | 05:52 | 355.912.635 byte |
| V5 | `record_2026-10-05_15-37-37.mp4` | 01:30 | 89.827.993 byte |

È stato tentato il download di V5 dalla cartella originale,
il file più piccolo e pertinente al secondo passaggio. Il connettore ha
restituito il riferimento al file completo; il trasferimento nel workspace
ha fallito perché il tool ammette al massimo **32 MiB**. Il tentativo di usare
l'URL temporaneo restituito dal connettore ha ricevuto **HTTP 403**. Non sono
stati salvati URL temporanei o credenziali nel repository. Non sono stati
ripetuti download degli altri video, tutti superiori al medesimo limite.

Restano quindi impossibili in questa sessione la nuova verifica fotogramma
per fotogramma di etichette, campi, quantità nelle schermate, timestamp,
sospensioni e risultati visuali descritti nel rapporto. La disponibilità dei
metadati non equivale alla lettura del contenuto.

## Riscontri dello studio adottati come base, senza elevarli a nuove prove

- **ARS@Logistica 4.6**, Chrome su Windows e indirizzo di rete privata.
  Etichette: `Ingresso Merci > Nuovo DDT` e `Logistica Interna > Libero`.
- V2, circa 00:25–01:25: l'importazione riguarda ordini già presenti;
  per Häfele sono riportati ordine/codice interni, quantità in NR,
  magazzino e ubicazione. L'equivalenza è riferita a quell'articolo, non a una
  regola generale sui prefissi.
- V1, circa 03:15–03:35: Pessinacciai mostra quantità in KG. La foto
  riletta concorda con la parte documentale del rapporto.
- V2–V4: più ordini nella stessa bolla e ripresa del DDT sospeso;
  anomalia Friulsider, chiamata all'ufficio e successiva correzione
  dichiarata. L'intervento dell'ufficio non è ripreso.
- V5, circa 00:42–00:49: selezione articoli, conferma del prelievo,
  riepilogo, `Sospendi`, nuova riga nelle liste sospese. Questo non è una
  prova della successiva disponibilità sul palmare.
- V3, circa 02:45: errore di ubicazione non valida nonostante il testo presente.
  Il testo presente nel campo non dimostra che il gestionale lo abbia
  acquisito correttamente.

**Conclusione dello studio:** automazione assistita plausibile, condizionata
alla lettura affidabile di righe/stati/esiti; precedenza a funzione nativa o
integrazione ufficiale adeguata, poi eventuale automazione locale di Chrome.
CLI-Anything e Jev non risolvono da soli accesso, identità delle righe o
ripresa. Queste sono conclusioni progettuali, non una verifica di
compatibilità o affidabilità di un prodotto.

## Verifiche ancora necessarie

1. Ambiente effettivo di esecuzione, rete/accesso autorizzato, permessi e
   ambiente di prova; non sono disponibili qui una sessione o credenziali
   del gestionale.
2. Funzioni native/file/API della specifica installazione, documentazione
   ufficiale, modalità di lettura di ordini, righe, residui e documenti
   esistenti. `Importa documento` nei video non prova un'importazione da CSV.
3. Identificativi realmente esposti e stabili, momento delle scritture
   server, stati intermedi, controlli contro duplicati e dati concorrenti;
   nessuna garanzia di transazione o annullamento automatico è dimostrata.
4. Conferma fisica dell'operatore, regole UFP per UM, colli, vettore e
   numero DDT completo con eventuali suffissi. Per Häfele chiarire
   `Coppia`/`NR`; per Pessinacciai approvare la conversione nel contesto
   corretto. Non trasformare i valori storici nelle regole di un nuovo arrivo.
5. Risultato di `Sospendi` e comportamento del palmare: visibilità,
   assegnazione, quantità e momento dell'eventuale movimento definitivo.
   Il rapporto dichiara che il palmare non compare nei materiali.
6. Pagine 4–5 Friulsider, abbinamento del video FAC e bolla OTLAV: limiti
   già segnalati dallo studio e non risolti da questa rilettura mirata.

La simulazione usa casi ispirati a queste evidenze e identificativi
esplicitamente dimostrativi. Gli esempi storici non autorizzano a reinserire
i DDT già lavorati. Test locali riusciti verificano la logica del programma,
**non la compatibilità con ARS@Logistica né lo stato del palmare**.
