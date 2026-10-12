"""Doppio locale di ARS: NON replica la UI o le transazioni reali.

I record SIM-* sono identificativi di questo simulatore, mai identificativi ARS.
Il database separato dal registro permette di simulare una risposta persa.
"""

import json
from decimal import Decimal, localcontext

from .planner import canonical, fingerprint
from .storage import connect


class StopOperation(Exception):
    """Nessuna ulteriore scrittura finché il problema non è risolto."""


class UncertainOutcome(StopOperation):
    """L'esito deve essere riletto, non dedotto dall'eccezione."""


def expected_effect(plan):
    rows = []
    for line in plan["lines"]:
        target = line["target"]
        rows.append({
            "receipt_line": line["receipt_line"],
            "row_id": target["row_id"],
            "order_type": target["order_type"],
            "order_number": target["order_number"],
            "order_line_id": target.get("order_line_id"),
            "supplier_code": target["supplier_code"],
            "internal_code": target["internal_code"],
            "warehouse": target["warehouse"],
            "location": target["location"],
            "quantity": line["registration_quantity"],
        })
    return {"document": plan["document"], "rows": rows}


class SimulatedArs:
    environment = "simulation"

    def __init__(self, path):
        self.path = path
        self.db = connect(path, "simulator-v1")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS orders (row_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY, stage TEXT NOT NULL, document_key TEXT NOT NULL,
                effect TEXT NOT NULL, state TEXT NOT NULL, parent_id TEXT,
                UNIQUE(stage, document_key));
            CREATE TABLE IF NOT EXISTS controls (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT OR IGNORE INTO controls VALUES ('health', 'normal');
        """)

    def close(self):
        self.db.close()

    def set_health(self, health):
        if health not in {"normal", "session_expired", "unexpected_screen", "unreadable"}:
            raise ValueError("Stato simulato non valido.")
        with self.db:
            self.db.execute("UPDATE controls SET value=? WHERE key='health'", (health,))

    def _check_health(self):
        health = self.db.execute("SELECT value FROM controls WHERE key='health'").fetchone()[0]
        messages = {
            "session_expired": "Sessione simulata scaduta: ripristinare l'accesso, poi riconciliare.",
            "unexpected_screen": "Schermata simulata inattesa: verificare il contesto prima della ripresa.",
            "unreadable": "Esito non leggibile: riconciliazione manuale necessaria; nessun nuovo caricamento.",
        }
        if health != "normal":
            raise StopOperation(messages.get(health, "Stato simulatore inatteso: interrompere."))

    def seed(self, orders):
        from .planner import validate_orders
        validate_orders(orders)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.db.execute("SELECT count(*) FROM orders").fetchone()[0] or self.db.execute("SELECT count(*) FROM artifacts").fetchone()[0]:
                raise ValueError("Simulatore già inizializzato: usare un altro percorso, senza cancellare il lavoro.")
            self.db.executemany("INSERT INTO orders VALUES (?, ?)", [(r["row_id"], canonical(r)) for r in orders])

    def orders(self):
        self._check_health()
        return [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM orders ORDER BY row_id")]

    def observe(self, plan, stage, parent_id=None):
        """Assenza autorevole solo nel simulatore. Rilettura completa dell'effetto."""
        self._check_health()
        desired = expected_effect(plan)
        rows = self.db.execute("SELECT * FROM artifacts WHERE stage=?", (stage,)).fetchall()
        matches = []
        for row in rows:
            actual = json.loads(row["effect"])
            doc = actual["document"]
            wanted = desired["document"]
            # Numero uguale nello stesso anno ma data diversa è una collisione da controllare.
            collision = all(doc[k] == wanted[k] for k in ("supplier_id", "number", "series", "warehouse")) and doc["date"][:4] == wanted["date"][:4]
            if row["document_key"] == plan["document_key"] or collision:
                matches.append(row)
        if not matches:
            return {"status": "absent", "evidence": "simulator_complete_search"}
        if len(matches) != 1:
            return {"status": "conflict", "reason": "Più documenti/liste candidati: riconciliare manualmente."}
        row = matches[0]
        expected_state = "DDT_VERIFIED" if stage == "initial" else "LIBERO_SUSPENDED"
        if (row["effect"] != canonical(desired) or row["state"] != expected_state
                or row["parent_id"] != parent_id):
            return {"status": "conflict", "reason": "Documento/lista presente con dati, collegamento o stato diversi: riconciliare manualmente."}
        return {"status": "verified", "id": row["id"], "state": row["state"],
                "effect_digest": fingerprint(desired), "evidence": "simulator_full_readback"}

    def _fresh_rows(self, plan):
        current = {r["row_id"]: r for r in self.orders()}
        for line in plan["lines"]:
            target = line["target"]
            if current.get(target["row_id"]) != target:
                raise StopOperation("Riga d'ordine o residuo cambiati: rileggere, preparare un nuovo piano e confermarlo.")

    def write(self, plan, stage, parent_id=None, fault=None):
        if stage not in {"initial", "libero"}:
            raise ValueError("Fase non valida.")
        if fault not in {None, "before_save", "after_save", "readback_unknown"}:
            raise ValueError("Guasto simulato non valido.")
        self._check_health()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            observation = self.observe(plan, stage, parent_id)
            if observation["status"] != "absent":
                raise StopOperation("Stato cambiato prima del salvataggio: rileggere senza ripetere l'operazione.")
            if stage == "initial":
                self._fresh_rows(plan)
            else:
                parent = self.observe(plan, "initial")
                if parent["status"] != "verified" or parent["id"] != parent_id:
                    raise StopOperation("DDT iniziale non riconciliato: Libero bloccato.")
            if fault == "before_save":
                raise UncertainOutcome("Interruzione simulata prima del salvataggio; rilettura obbligatoria alla ripresa.")
            prefix = "SIM-DDT" if stage == "initial" else "SIM-LIST"
            artifact_id = prefix + "-" + plan["document_key"]
            state = "DDT_VERIFIED" if stage == "initial" else "LIBERO_SUSPENDED"
            self.db.execute("INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?)",
                            (artifact_id, stage, plan["document_key"], canonical(expected_effect(plan)), state, parent_id))
            if stage == "initial":
                current = {r["row_id"]: r for r in self.orders()}
                with localcontext() as ctx:
                    ctx.prec = 60
                    for line in plan["lines"]:
                        row = current[line["target"]["row_id"]]
                        remainder = Decimal(row["remaining"]) - Decimal(line["registration_quantity"]["value"])
                        if remainder < 0:
                            raise StopOperation("Quantità cumulata superiore al residuo.")
                        row["remaining"] = format(remainder, "f")
                self.db.executemany("UPDATE orders SET payload=? WHERE row_id=?", [(canonical(r), r["row_id"]) for r in current.values()])
            if fault == "readback_unknown":
                self.db.execute("UPDATE controls SET value='unreadable' WHERE key='health'")
        if fault in {"after_save", "readback_unknown"}:
            raise UncertainOutcome("Risposta persa dopo un possibile salvataggio: esito incerto, rileggere prima di riprovare.")
        # Un ritorno normale non basta: sarà il chiamante a verificare tramite observe.
