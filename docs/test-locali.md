# Verifica della prima versione

Esecuzione del **12 ottobre 2026**, workspace Linux, Python **3.12.14**, sola libreria standard. Comando eseguito dalla radice del repository:

```sh
python -m unittest discover -s tests -v
```

**Risultato: 63 test eseguiti, 63 superati, 0 errori/fallimenti** (2,523 secondi nell'esecuzione registrata). Il tempo è quello della suite sintetica, non una misura del lavoro in magazzino.

| Gruppo | Test | Verifiche principali |
| --- | ---: | --- |
| [`test_planner.py`](../tests/test_planner.py) | 31 | Quantità e unità, schema dei dati, abbinamenti esatti, ambiguità, residui cumulati, conversioni, impronta e modifiche del piano. |
| [`test_engine.py`](../tests/test_engine.py) | 26 | Persistenza, duplicati, evidenze rilette dal simulatore, esiti incerti, dati cambiati, separazione DDT/Libero, blocco dell'adattatore reale. |
| [`test_cli.py`](../tests/test_cli.py) | 6 | CLI invocata in processi separati, ripresa persistente, riepiloghi bloccati, protezione dei file/database, lock, JSON con BOM Windows e chiavi duplicate. |

## Casi richiesti e risultati

| Caso | Prova effettivamente eseguita | Risultato |
| --- | --- | --- |
| Caricamento ordinario | Quantità completa correttamente abbinata; lettura documento dopo il salvataggio. | Superato. |
| Consegna parziale | Conversione 0,072 TO → 72 KG su residuo 100 KG; successiva bolla sul residuo; quantità fisica inferiore alla bolla con motivo. | Superato: residuo 28 KG nel primo caso; registrata soltanto la quantità ricevuta. |
| Articolo ripetuto su ordini diversi | Stessi codici, ordini diversi; righe ripetute sullo stesso ordine con/senza ID. | Superato: bersagli distinti, ambiguità bloccate; controllo della somma sul medesimo residuo. |
| Codice discordante | Codice fornitore diverso da quello dello snapshot. | Superato: nessuna correzione, piano non confermabile. |
| Conversione di unità | TO/KG esplicita e inversa; fattore errato, conversione assente, Coppia/NR e precisione non rappresentabile. | Superato: nessuna conversione implicita o arrotondamento. |
| Documento già elaborato | Ripetizione dopo successo, anche con nuovo registro locale; stessa bolla con dati/data diversi. | Superato: lettura del simulatore, nessun duplicato; conflitti bloccati. |
| Interruzione prima di salvare | Guasto `before_save` e arresto `after_intent`. | Superato: nessun salvataggio dedotto dal registro; ripresa dopo prova dell'assenza. |
| Interruzione dopo possibile salvataggio | Guasto `after_save` e `readback_unknown`. | Superato: recupero del documento presente; esito illeggibile blocca ulteriori scritture. |
| Fallimento Libero | Guasto prima e dopo il salvataggio della lista. | Superato: un solo DDT e una sola lista dopo la ripresa; il caricamento iniziale non si ripete. |
| Stato reale simulato diverso dallo storico | DDT sospeso, documento rimosso dopo verifica, lista con collegamento errato. | Superato: riconciliazione richiesta, nessuna ricreazione automatica. |
| Sessione, pagina o dati cambiati | Sessione scaduta, schermata inattesa, residuo differente dal piano. | Superato: scritture bloccate. |
| Conferma riferita ai dati esatti | Impronta errata, piano modificato, derivati alterati anche con hash ricalcolato, piano non approvato. | Superato: esecuzione rifiutata. |

La prova CLI utilizza due database temporanei separati e processi distinti per ogni comando. Dopo risposte perse in entrambe le fasi verifica **esattamente due artefatti** (un DDT e una lista), residuo 28 KG e stato palmare `NON_VERIFICATO`. Gli identificativi sono sintetici.

Una revisione indipendente del codice non ha rilevato problemi bloccanti riproducibili su duplicati, conferme e ripresa. Ha rilevato il rifiuto dei JSON con BOM prodotti da alcuni strumenti Windows: corretto usando lettura `utf-8-sig` e coperto dalla suite. Il controllo whitespace viene eseguito anche sui file aggiunti prima della consegna.

## Confini della verifica

- **Implementato e testato:** logica locale, conferma, riepilogo, registro, simulazione e ripresa descritti sopra.
- **Simulato:** salvataggi, identificativi, unicità lato sistema, transazioni, lettura completa degli esiti, sessione e schermate. I guasti sono iniettati; non sono state provocate interruzioni nel gestionale.
- **Non verificato su ARS:** connessione, DOM/selettori, importazioni/API, permessi, campi obbligatori, transazioni e salvataggi intermedi, identificativi realmente disponibili, comportamento operativo degli stati.
- **Non verificato:** uso su Windows, controllo fisico reale, correttezza anagrafica delle equivalenze, disponibilità sul palmare, tempi/risparmi del processo.

La gestione automatica di un DDT salvato solo in parte è fuori dal perimetro della v1: il caso viene fermato per riconciliazione. Il simulatore usa una transazione per la fase iniziale; questa semplificazione non va trasferita al gestionale senza prova. Per la futura integrazione seguire la [scheda della prova reale](prova-reale.md).
