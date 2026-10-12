# Ripresa del progetto nella prossima sessione

Passaggio di consegne del **12 ottobre 2026**. Repository: <https://github.com/av3rgfx/ufp-bolle>.
Obiettivo successivo: qualificare la postazione e il collegamento autorizzato ad ARS, poi sviluppare soltanto l'integrazione sostenuta dalle verifiche. Non ripetere un'analisi generale e non interpretare questo documento come autorizzazione a scrivere nel gestionale.

## Stato consegnato

Il commit **`018e3f3`** appartiene allo storico locale precedente alla pubblicazione e non è un riferimento necessario o garantito sul remoto. Il repository GitHub è pubblico: la consegna usa una storia pubblicabile senza i dettagli aziendali dello storico locale. Per codice, documentazione di chiusura, PR e branch aggiornato consultare Git e GitHub; non presumere che la PR sia stata unita né che `main` contenga già il lavoro. All'avvio controllare branch, stato locale e stato della PR, preservando eventuali modifiche dell'utente.

| Ambito | Stato effettivo |
| --- | --- |
| Implementato e verificato localmente | CLI Python 3.11+, sola libreria standard; schema JSON, abbinamento esatto alle righe, controllo dei residui, conversioni esplicite con `Decimal`, riepilogo e conferma SHA-256, registro persistente, fasi iniziale e `Libero` separate, ripresa e blocco degli esiti incerti. |
| Simulato | Ordini, DDT, liste, identificativi `SIM-*`, salvataggi atomici, lettura completa degli esiti, sessioni, schermate e guasti. Le garanzie del simulatore non sono garanzie ARS. |
| Non implementato | Connettore reale, accesso browser, importazione/API ARS, selettori verificati e comandi di produzione. L'esecutore accetta esclusivamente `SimulatedArs`. |
| Verificato sul gestionale reale | **Nessuna operazione del programma.** Compatibilità ARS, salvataggi e stato del palmare non verificati. |
| Test locali registrati | **63/63 superati:** 31 planner, 26 engine, 6 CLI; Linux/Python 3.12.14. Windows non ancora provato. Dettagli in [test-locali.md](test-locali.md). |

La versione serve un operatore alla volta e richiede tutte le righe da registrare della bolla. Consente consegne parziali rispetto agli ordini; non suddivide la stessa bolla in caricamenti indipendenti. Una sola anomalia blocca il documento intero. Ogni modifica richiede nuovo piano e riconferma completa. Il comando `status` mostra lo storico locale, non rilegge il gestionale.

## Decisioni e risposte ancora mancanti

L'utente **non crede esista un ambiente di prova** e proverà a chiedere: la sua assenza non è stata accertata. È stata prospettata una prova limitata con una **nuova bolla reale**, anche in produzione se non esiste un ambiente separato, dopo aver qualificato accesso, lettura degli esiti e connettore. Questo orientamento non autorizza ancora alcuna modifica reale. Le interruzioni artificiali si provano nel simulatore, mai in produzione.

La domanda finale della sessione precedente — «Il PC del magazzino è Windows e puoi installare/eseguire Python, direttamente o tramite assistenza?» — **non ha ancora ricevuto risposta**. Chrome su Windows è un riscontro storico dello studio, non conferma della postazione destinata all'esecuzione.

Le sole risposte necessarie per avanzare sono:

1. **Postazione e accesso:** sistema operativo attuale, possibilità di eseguire Python, rete e modalità di accesso autorizzata, permessi dell'operatore e dell'eventuale automazione. Definire cartella privata, backup e accessi ai dati. Non chiedere password in chat.
2. **Percorso nativo:** disponibilità effettiva di importazione o integrazione documentata per questa installazione, compresi riferimenti alle righe, residui, esiti e secondo passaggio. `Importa documento` nello studio riguarda ordini interni: non dimostra un'importazione CSV. Non sono state inviate richieste all'assistenza.
3. **Regole operative:** campi obbligatori di testata, numero completo/serie, magazzino/ubicazione, colli, vettore e UM; conferma dell'operatore sui dati strutturati. `Coppia`/`NR` resta da chiarire; TO/KG richiede una regola esplicita applicabile al caso.
4. **Esiti e palmare:** riferimenti stabili realmente leggibili, momento dei salvataggi anche intermedi, ricerca completa dei documenti/liste e significato di `Sospendi`. Chiarire quale risultato vedere sul dispositivo e quale azione registri il movimento definitivo.

Chiedere ciò che condiziona il passo in corso; procedere con le normali scelte tecniche motivate e con il lavoro locale indipendente dalle risposte.

## Materiali da riusare senza inventare verifiche

Sono stati letti lo studio e cinque fotografie; i riscontri e i collegamenti originali sono in [materiali.md](materiali.md). I video non sono stati riprodotti nuovamente: il tentativo sul più piccolo è stato bloccato dal limite di trasferimento di **32 MiB**, e il tentativo con l'URL temporaneo ha restituito **HTTP 403**. Le osservazioni sui video restano attribuite allo studio. Il palmare non è provato dai materiali.

Il DOCX originale era un allegato temporaneo della sessione, non un file del repository. Il suo percorso `/tmp/codex-remote-attachments/...` potrebbe non esistere nella prossima sessione. Usare prima i riscontri documentati; se una nuova verifica dell'originale è necessaria e l'allegato non è disponibile, chiederne il caricamento senza dichiarare di averlo riletto. Fotografie, video, dati aziendali e credenziali restano fuori da Git.

Le fonti ufficiali, CLI-Anything e Jev sono conservate in [fonti-e-scelta.md](fonti-e-scelta.md). Non è emersa una loro necessità per la v1. Nessun risparmio di tempo è stato misurato.

## Prossimi passi nell'ordine

1. **Riprendere il codice giusto:** leggere [README](../README.md), questo documento, [architettura.md](architettura.md), [formato-dati.md](formato-dati.md) e [prova-reale.md](prova-reale.md); controllare Git/PR. Avvio e simulazione sono nel README; comando di verifica: `python -m unittest discover -s tests -v`.
2. **Qualificare la postazione:** ottenere le risposte necessarie su PC, Python, accesso e permessi. Fare una simulazione sulla postazione concordata. L'ambiente separato rimane una verifica da fare, non un requisito che blocca ogni attività preparatoria.
3. **Verificare il percorso nativo:** consultare la documentazione applicabile o il riscontro dell'assistenza prima di scegliere il connettore. Non presumere API, tracciati o moduli presenti. Non inviare messaggi all'assistenza per conto dell'utente senza istruzione.
4. **Ispezionare in sola lettura:** con accesso autorizzato controllare ordini, righe, residui, DDT, liste e paginazione, senza aprire creazioni o azionare comandi dai possibili effetti ignoti. Registrare le evidenze necessarie alla ripresa. Identificare gli eventuali salvataggi intermedi prima di automatizzarli.
5. **Sviluppare l'adattatore minimo:** preferire una funzione nativa adeguata; altrimenti valutare Playwright locale con elementi identificabili, controlli di sessione/pagina e lettura completa degli esiti. Nessun selettore inventato, ID sintetico usato come reale o dipendenza da coordinate. L'adattatore reale richiede un percorso distinto e verificato; non basta togliere il blocco del simulatore. Se identità o esiti non sono affidabili, mantenere la preparazione automatica e il caricamento manuale.
6. **Preparare il caso concreto:** nuova bolla completa di un fornitore, idealmente 1–3 righe, articoli noti, abbinamenti univoci e stessa UM. L'operatore controlla fisicamente la merce. Rileggere stato iniziale, residui e documenti/lista preesistenti; compilare la scheda di [prova-reale.md](prova-reale.md) con dati e identificativi reali, riepilogo congelato, quantità e unità, residui attesi e criteri di successo. Non riusare le bolle storiche già lavorate.
7. **Attendere l'autorizzazione sul caso esatto:** presentare modifiche e controlli prima di qualsiasi scrittura. La conferma SHA-256 locale non sostituisce questa autorizzazione. Separare caricamento iniziale e `Libero`; entrambi possono essere autorizzati insieme solo se il riepilogo ne espone concretamente tutte le operazioni.
8. **Verificare e consegnare:** dopo ogni fase rileggere risultato, stato, righe, quantità, UM, collegamenti e assenza di duplicati. Controllare il palmare effettivo o mantenerlo `NON_VERIFICATO`. Aggiornare documentazione e test in base alle prove eseguite; lasciare la PR aperta per la revisione finché non viene richiesto il merge.

In caso di interruzione conservare piano e registro, interrompere le scritture e rileggere l'esito prima di ripetere. Un timeout non dimostra un mancato salvataggio. Esito incerto, documento parziale o discordante richiedono riconciliazione manuale; non è previsto un annullamento automatico. Un errore in `Libero` non deve ricreare il DDT. Le procedure dettagliate sono nel README e nella scheda di prova.

## Prompt da copiare nella prossima sessione

```text
Riprendi il progetto https://github.com/av3rgfx/ufp-bolle dalla PR di consegna della sessione precedente. Verifica prima branch, stato Git e stato della PR; non presumere che sia già unita. Leggi README.md e docs/prossima-sessione.md, poi i documenti pertinenti. Preserva le modifiche locali.

Esiste una prima versione Python locale con pianificazione, conferma dei dati esatti, registro persistente e simulazione separata di Nuovo DDT e Libero → Sospendi. Sono registrati 63 test superati. ARS@Logistica non è collegato, Windows non è stato provato e il palmare non è verificato. Non presentare la simulazione come compatibilità reale.

Non credo esista un ambiente di prova; proverò a chiedere. Possiamo preparare una prova limitata con una nuova bolla reale anche senza tale ambiente, ma questo NON autorizza scritture. Prima di modificare ARS presentami il caso concreto, le operazioni esatte, il riepilogo congelato e i controlli, poi attendi la mia autorizzazione. Non provocare guasti in produzione.

Il prossimo passo è qualificare la postazione: sistema operativo, possibilità di eseguire Python, rete, accesso autorizzato e permessi sono ancora da chiarire. Fammi domande mirate e continua il lavoro locale indipendente dalle risposte. Non chiedere password in chat.

Verifica prima funzioni native o integrazioni documentate applicabili; altrimenti sviluppa il minimo collegamento browser sostenuto da ispezione autorizzata in sola lettura, identificativi affidabili e rilettura completa degli esiti. Non inventare API o selettori. Mantieni distinti DDT e Libero; prima di una ripetizione verifica il risultato sul gestionale, fermandoti per riconciliazione se incerto.

Parti dai materiali già documentati senza rifare un'analisi generale. Studio e cinque foto sono stati letti; i video non sono stati riprodotti nuovamente per limiti di trasferimento. Se serve il DOCX originale e non è accessibile, chiedimi di allegarlo.

Mantieni il controllo fisico umano. Prepara successivamente una nuova bolla completa di 1–3 righe secondo docs/prova-reale.md. Aggiorna documentazione e test e lascia la PR disponibile per la revisione.
```
