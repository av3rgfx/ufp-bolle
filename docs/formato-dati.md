# Formato dati v1

JSON UTF-8; vedi gli esempi completi in [`examples/`](../examples). Le quantità sono **stringhe decimali** con punto, senza separatori delle migliaia, segno o esponente; massimo 12 cifre intere e 6 decimali. `"0.072"` è valido; `0.072`, `"0,072"`, `"NaN"` non lo sono. Codici e identificativi rimangono testo, preservando zeri iniziali e suffissi. Nessuna normalizzazione automatica.

## Ricezione

| Campo | Obbligo e significato |
| --- | --- |
| `schema_version` | Intero `1`. |
| `document.supplier_id`, `supplier_name` | Identità fornitore e nome leggibile; la validità dell'ID reale resta da verificare nell'adattatore. |
| `document.number`, `date` | Numero completo della bolla, senza rimuovere suffissi; data ISO `YYYY-MM-DD`. |
| `document.series`, `warehouse` | Serie dichiarata (stringa vuota solo se il documento non ha serie) e magazzino. Nessun valore UFP preimpostato. |
| `complete_document` | `true`: documento controllato completo e tutte le righe ricevute da registrare incluse. Non usarlo con pagine mancanti. Non prova da solo la completezza: è dichiarato dall'operatore. |
| `physical_check.operator`, `checked_at` | Chi ha controllato materialmente e quando, timestamp ISO con fuso, per esempio `2026-10-12T09:00:00+02:00`. |
| `lines` | Almeno una riga ricevuta; omettere righe con arrivo zero. La v1 non gestisce resi/quantità negative. |
| `lines[].receipt_line` | Riferimento univoco della riga di ricezione, per esempio pagina/posizione; non ID dell'ordine. |
| `order_type`, `order_number` | Causale/tipo e numero dell'ordine **interno verificato**, non un riferimento fornitore assunto equivalente. |
| `order_line_id` | Facoltativo/null se non esposto. Se manca, il confronto esatto deve comunque individuare una sola riga. Nessuna scelta del primo candidato. |
| `supplier_code`, `internal_code` | Entrambi obbligatori per il perimetro v1; devono coincidere con la coppia nello snapshot ordine. Nessuna regola inventata su prefissi/punti. Un articolo senza codice fornitore affidabile richiede una futura regola validata, non un valore fittizio. |
| `document_quantity` | `{ "value": "…", "unit": "…" }`, quantità positiva riportata sulla bolla. |
| `received_quantity` | Stessa struttura, quantità positiva fisicamente confermata. Nella v1 deve avere la stessa unità della quantità bolla; non viene ricavata da questa. |
| `difference_reason` | Obbligatorio se quantità bolla e fisica differiscono; testo della motivazione controllata. |
| `registration_unit` | Unità prevista dalla riga d'ordine. La quantità da registrare viene calcolata, non editata nel piano. |
| `conversion` | Necessaria quando unità fisica e da registrare differiscono: `from`, `to`, `factor` come stringa decimale, `reference` della regola verificata. |
| `location` | Ubicazione di ricezione dichiarata e confrontata esattamente con lo snapshot. La semantica ARS resta da verificare. |

La conversione supportata è soltanto tonnellata metrica `TO` → `KG` con fattore `"1000"` e inversa con `"0.001"`; nessun arrotondamento. L'operatore deve verificare che le unità abbiano questo significato nel caso concreto. `Coppia` → `NR` non è supportata: la foto Häfele non basta a stabilirne la regola. Quantità e fattore entrano nell'impronta da confermare.

Colli, Vettore, date di trasporto e altri campi specifici ARS **non sono implementati**: occorre determinarne obbligatorietà e significato prima dell'adattatore reale. Non aggiungerli al JSON come se venissero gestiti. I campi sconosciuti vengono rifiutati.

## Snapshot ordini

Array di righe con `row_id`, `supplier_id`, `order_type`, `order_number`, eventuale `order_line_id`, `supplier_code`, `internal_code`, `unit`, `remaining`, `warehouse`, `location`. Tutti i campi sono stringhe; `order_line_id` può essere assente/null. `remaining` è un decimale non negativo. `row_id` deve essere unico nello snapshot, ma la sua esistenza nel simulatore non prova un ID stabile in ARS.

Una riga è abbinata per fornitore, magazzino, tipo/numero ordine, eventuale riga, coppia di codici e ubicazione; unità e residuo sono verificati separatamente. Due righe candidate restano ambigue anche se una ha residuo più comodo. Più righe della bolla che puntano allo stesso ordine/riga restano distinte e la loro somma non può superare il residuo. Stesso articolo su ordini diversi non viene deduplicato.

## Piano e conferma

`plan` conserva i due input, i risultati deterministici, le anomalie, `document_key` e `digest` SHA-256. `show` verifica l'integrità ricalcolando il piano e presenta i dati. `confirm` lega operatore e istante a **quella esatta impronta**. `run` richiede il file coerente e la corrispondente conferma persistita.

Non modificare a mano i risultati del piano: correggere la ricezione o rileggere gli ordini e generare un nuovo file. Qualsiasi modifica dell'input, incluse le quantità fisiche e i dati di controllo, cambia l'impronta e richiede una nuova conferma. La validazione del file non autentica l'operatore e non dimostra lo stato corrente del gestionale.

L'identità documento usa fornitore, numero completo, data, serie e magazzino. Una bolla successiva sullo stesso ordine è ammessa entro il residuo aggiornato; lo stesso DDT con contenuti diversi o salvataggio parziale va riconciliato. La v1 non aggiunge automaticamente righe a un DDT già esistente.
