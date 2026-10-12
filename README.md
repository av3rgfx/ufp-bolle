# UFP bolle — prima versione locale

Programma funzionante per **preparare e verificare ricezioni**, confermare i dati esatti e **simulare** le due fasi `Nuovo DDT` e `Libero → Sospendi`, con ripresa dopo interruzione. Python 3.11 o successivo, sola libreria standard, nessun servizio esterno.

**ARS@Logistica non è collegato.** Non esistono credenziali, URL di produzione, selettori browser o un'opzione per attivare scritture reali. I test provano la logica locale, non la compatibilità con ARS. Il palmare rimane **NON VERIFICATO**.

Per riprendere il lavoro, leggere [stato, decisioni e prompt della prossima sessione](docs/prossima-sessione.md). L'utente ritiene che non esista un ambiente di prova e proverà a chiedere: l'assenza non è ancora accertata. È possibile preparare una prova limitata con una **nuova bolla reale**, dopo la verifica dell'accesso e degli esiti e con autorizzazione esplicita sul caso concreto prima delle scritture. Non è stata autorizzata alcuna operazione reale.

## Avvio in pochi passaggi

Aprire un terminale nella cartella del repository. Verificare `python --version`; su Windows, se necessario, usare `py -3` al posto di `python`. Non occorrono `pip install` o connessione a Internet.

L'esempio è **interamente sintetico**, ispirato alla conversione Pessinacciai: 0,072 TO ricevute, 72 KG da registrare, 100 KG residui iniziali, 28 KG dopo il caricamento. I codici `SIM-*` non sono identificativi ARS. La dichiarazione di controllo fisico dell'esempio è una finzione esplicita per il test.

```sh
python -m ufp_bolle sim-init --orders examples/orders.json --db state/demo/simulatore.sqlite
python -m ufp_bolle plan --receipt examples/receipt.json --sim-db state/demo/simulatore.sqlite --out state/demo/piano.json
```

Leggere il riepilogo: fornitore, bolla, ordine/riga, codici, quantità della bolla, quantità fisica, conversione, quantità da registrare, residuo e ubicazione. Poi sostituire `INCOLLA_IMPRONTA` con l'intera impronta di 64 caratteri mostrata, senza modificare il piano:

```sh
python -m ufp_bolle confirm --plan state/demo/piano.json --digest INCOLLA_IMPRONTA --operator OPERATORE-DEMO --state state/demo/registro.sqlite
python -m ufp_bolle run --plan state/demo/piano.json --state state/demo/registro.sqlite --sim-db state/demo/simulatore.sqlite --stage initial
python -m ufp_bolle run --plan state/demo/piano.json --state state/demo/registro.sqlite --sim-db state/demo/simulatore.sqlite --stage libero
python -m ufp_bolle status --state state/demo/registro.sqlite --digest INCOLLA_IMPRONTA
```

Risultato atteso: `initial` e `libero` in stato `VERIFIED`, identificativi `SIM-DDT-*` e `SIM-LIST-*`, stato lista `LIBERO_SUSPENDED`; palmare `NON_VERIFICATO`. `status` mostra lo **storico locale**, non una nuova lettura degli esiti. Ripetere `run` rilegge il simulatore e non aggiunge documenti già verificati.

`sim-init` rifiuta di reimpostare un simulatore già popolato. Per una nuova prova usare una cartella diversa. Non cancellare un registro per risolvere un'anomalia.

## Preparare un proprio caso

1. Dopo il controllo fisico, compilare una copia di `examples/receipt.json` in `private/` o `state/`. Non ricavare conferme dai segni a penna né dalle quantità ordinate.
2. Preparare uno snapshot ordini nel formato di `examples/orders.json`. Oggi è un file fornito manualmente o dal simulatore: **non è un export ARS verificato**. Non inventare ID mancanti per far passare il controllo.
3. Usare `plan --receipt private/ricezione.json --orders private/ordini.json --out state/piano-v1.json`. Questo prepara dati senza caricarli.
4. Risolvere tutte le anomalie. Il documento intero resta bloccato se anche una riga è ambigua. Correggere il file sorgente, produrre `piano-v2.json`, rileggere e confermare la nuova impronta. La v1 richiede la riconferma dell'intero piano, anche per una sola riga modificata.

Il [formato dei dati](docs/formato-dati.md) indica obblighi e limiti. Non si correggono codici per somiglianza, non si ripartiscono quantità tra ordini e non si deducono conversioni. Il controllo umano e la conferma digitata sono dichiarazioni dell'operatore, non un sistema di autenticazione o firma digitale.

## Provare un'interruzione e riprendere

Creare una **nuova** cartella di simulazione seguendo i primi comandi e confermare il piano. Eseguire la prima fase con guasto dopo il possibile salvataggio:

```sh
python -m ufp_bolle run --plan state/demo2/piano.json --state state/demo2/registro.sqlite --sim-db state/demo2/simulatore.sqlite --stage initial --fault after_save
```

L'uscita con codice `2` e stato locale `UNKNOWN` è attesa. Ripetere lo stesso comando **senza `--fault`**: il programma cerca il documento, ne confronta tutte le righe e recupera l'esito, senza ricrearlo. Per simulare un errore del secondo passaggio usare `--stage libero --fault after_save` dopo aver verificato `initial`.

| Situazione | Come riprendere |
| --- | --- |
| `before_save`, `after_save`, `after_intent` | Stesso piano e stessi database, `run` sulla fase interrotta senza guasto. Una lettura completa deve provare l'esito o l'assenza. |
| `readback_unknown` | Nessun nuovo tentativo finché l'esito non è leggibile. Solo nel simulatore: `sim-control --db PERCORSO --health normal`, poi `run` per riconciliare. Non equivale a una verifica manuale del gestionale. |
| Sessione scaduta o schermata inattesa | Arresto. Nel simulatore si imposta con `sim-control --health session_expired` / `unexpected_screen`; ripristinare `normal`, poi riconciliare. Sul reale occorrerà ripristinare l'accesso e verificare contesto ed esiti. |
| Ordine/residuo cambiato | Nessuna scrittura. Rileggere gli ordini, verificare la consegna, generare e confermare un nuovo piano. |
| Documento già presente ma diverso, parziale o con stato inatteso | Riconciliazione manuale. La v1 non completa automaticamente documenti parzialmente salvati e non presume un annullamento. |
| `Libero` fallito | Riprendere soltanto `libero`: il DDT viene riletto, senza ripetere `initial`. |
| Lock residuo dopo chiusura forzata | Verificare che non esista un altro processo UFP attivo; conservare i database e rimuovere **solo** il file `registro.sqlite.lock`. Al successivo `run` la riconciliazione resta obbligatoria. |

## Test e limiti

```sh
python -m unittest discover -s tests -v
```

I [risultati dei test](docs/test-locali.md) documentano casi, ambiente e limiti. Esecuzione locale verificata su Linux/Python 3.12; Windows non ancora provato. Un operatore e un processo alla volta. I database separati e il lock proteggono il lavoro locale; le transazioni SQLite del simulatore **non sono garanzie offerte da ARS**.

Per la futura integrazione vanno verificati accesso autorizzato, disponibilità dell'ambiente di prova, capacità native effettive, identificativi/esiti leggibili, regole UFP di testata e unità, risultato del palmare. La mancanza di un ambiente di prova non impedisce preparazione e verifiche in sola lettura; una prova in produzione richiede un caso limitato e autorizzato. [La procedura di prova reale](docs/prova-reale.md) definisce il prospetto da compilare e autorizzare **prima** di qualsiasi modifica reale; oggi non contiene un arrivo reale pronto da autorizzare.

## Dati e documentazione

Piani e database contengono dati aziendali necessari alla ripresa: conservarli in una cartella privata sulla postazione autorizzata, con backup e accessi controllati. Il programma non invia dati in rete e non scrive log con righe o credenziali; il riepilogo a terminale contiene i dati che l'operatore deve controllare. I file creati hanno permessi privati su sistemi POSIX; su Windows verificare le ACL della cartella. Non è implementata cifratura a riposo. `state/`, `private/`, database e media sono esclusi da Git.

- [Architettura e confini del simulatore](docs/architettura.md)
- [Passaggio alla prossima sessione e prompt pronto](docs/prossima-sessione.md)
- [Materiali letti, link Drive e limiti dei video](docs/materiali.md)
- [Fonti ufficiali e scelta tecnica, inclusi CLI-Anything e Jev](docs/fonti-e-scelta.md)
- [Formato dati](docs/formato-dati.md) e [prova reale](docs/prova-reale.md)

Nessuna misura di risparmio di tempo è stata effettuata.
