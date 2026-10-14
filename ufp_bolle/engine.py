"""Due fasi indipendenti, con intento durevole e riconciliazione obbligatoria."""

import json
from datetime import datetime, timezone

from .planner import canonical, validate_plan
from .simulator import SimulatedArs, StopOperation, UncertainOutcome
from .storage import connect, single_operator


def now():
    return datetime.now(timezone.utc).isoformat()


class Ledger:
    def __init__(self, path):
        self.path = path
        self.db = connect(path, "ledger-v1")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS approvals (
                digest TEXT PRIMARY KEY, plan TEXT NOT NULL, operator TEXT NOT NULL, approved_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS phases (
                digest TEXT NOT NULL, stage TEXT NOT NULL, status TEXT NOT NULL,
                artifact_id TEXT, evidence TEXT, updated_at TEXT NOT NULL,
                PRIMARY KEY(digest, stage));
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, digest TEXT NOT NULL, stage TEXT NOT NULL,
                status TEXT NOT NULL, at TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def approve(self, plan, operator, digest):
        validate_plan(plan)
        if not plan["ready"]:
            raise ValueError("Anomalie da risolvere prima della conferma.")
        if digest != plan["digest"]:
            raise ValueError("Impronta diversa dal riepilogo: verificare nuovamente i dati.")
        if not isinstance(operator, str) or not operator.strip() or len(operator) > 120 or any(ord(c) < 32 for c in operator):
            raise ValueError("Identificativo operatore obbligatorio, senza caratteri di controllo.")
        with single_operator(self.path), self.db:
            self.db.execute("INSERT OR IGNORE INTO approvals VALUES (?, ?, ?, ?)",
                            (digest, canonical(plan), operator, now()))
            for stage in ("initial", "libero"):
                self.db.execute("INSERT OR IGNORE INTO phases VALUES (?, ?, 'PENDING', NULL, NULL, ?)",
                                (digest, stage, now()))

    def require_approval(self, plan):
        validate_plan(plan)
        row = self.db.execute("SELECT plan FROM approvals WHERE digest=?", (plan["digest"],)).fetchone()
        if not plan["ready"] or row is None or row[0] != canonical(plan):
            raise StopOperation("Dati non confermati: leggere il riepilogo e confermare questa precisa impronta.")

    def phase(self, digest, stage):
        row = self.db.execute("SELECT status, artifact_id, evidence, updated_at FROM phases WHERE digest=? AND stage=?", (digest, stage)).fetchone()
        if row is None:
            raise StopOperation("Piano non confermato nel registro.")
        result = dict(row)
        result["evidence"] = json.loads(result["evidence"]) if result["evidence"] else None
        return result

    def record(self, digest, stage, status, evidence=None):
        with self.db:
            self.db.execute("UPDATE phases SET status=?, artifact_id=?, evidence=?, updated_at=? WHERE digest=? AND stage=?",
                            (status, evidence.get("id") if evidence else None,
                             canonical(evidence) if evidence else None, now(), digest, stage))
            self.db.execute("INSERT INTO events (digest, stage, status, at) VALUES (?, ?, ?, ?)",
                            (digest, stage, status, now()))

    def status(self, digest):
        row = self.db.execute("SELECT operator, approved_at FROM approvals WHERE digest=?", (digest,)).fetchone()
        if row is None:
            raise ValueError("Impronta non presente nel registro.")
        return {"digest": digest, **dict(row), "environment": "simulation",
                "initial": self.phase(digest, "initial"), "libero": self.phase(digest, "libero"),
                "palmare": "NON_VERIFICATO"}


def _observe(ledger, adapter, plan, stage, parent_id=None):
    observation = adapter.observe(plan, stage, parent_id)
    previous = ledger.phase(plan["digest"], stage)
    if observation["status"] == "verified":
        if previous["status"] == "VERIFIED" and previous["artifact_id"] != observation["id"]:
            raise StopOperation("Identificativo remoto cambiato: riconciliare manualmente.")
        ledger.record(plan["digest"], stage, "VERIFIED", observation)
        return observation
    if observation["status"] == "conflict":
        raise StopOperation(observation["reason"])
    if observation["status"] != "absent":
        raise StopOperation("Esito incerto: riconciliazione manuale necessaria, nessun nuovo caricamento.")
    if previous["status"] == "VERIFIED":
        raise StopOperation("Il documento prima verificato non è più presente: riconciliare, senza ricrearlo.")
    return observation


def run_stage(ledger, adapter, plan, stage="initial", fault=None):
    # Blocco strutturale: nessun flag/URL può trasformare la simulazione in produzione.
    if type(adapter) is not SimulatedArs or adapter.environment != "simulation":
        raise StopOperation("Adattatore reale non implementato né autorizzato. Disponibile solo la simulazione locale.")
    if stage not in {"initial", "libero"}:
        raise ValueError("Fase non valida.")
    if fault not in {None, "before_save", "after_save", "after_intent", "readback_unknown"}:
        raise ValueError("Guasto simulato non valido.")
    ledger.require_approval(plan)
    with single_operator(ledger.path):
        parent_id = None
        if stage == "libero":
            parent = _observe(ledger, adapter, plan, "initial")
            if parent["status"] != "verified":
                raise StopOperation("Caricamento iniziale non verificato: eseguire o riconciliare initial prima di Libero.")
            parent_id = parent["id"]
        observation = _observe(ledger, adapter, plan, stage, parent_id)
        if observation["status"] == "verified":
            return observation
        # L'assenza viene dalla lettura completa del simulatore, mai dal registro locale.
        ledger.record(plan["digest"], stage, "INTENT")
        if fault == "after_intent":
            raise UncertainOutcome("Arresto simulato dopo l'intento durevole: prima di riprendere verrà riletto l'esito.")
        try:
            adapter.write(plan, stage, parent_id, fault)
            observation = adapter.observe(plan, stage, parent_id)
            if observation["status"] != "verified":
                raise UncertainOutcome("Salvataggio senza prova completa dell'esito: riconciliazione manuale necessaria.")
        except Exception:
            # Anche un errore locale dopo l'invio non dimostra un mancato salvataggio.
            ledger.record(plan["digest"], stage, "UNKNOWN")
            raise
        ledger.record(plan["digest"], stage, "VERIFIED", observation)
        return observation
