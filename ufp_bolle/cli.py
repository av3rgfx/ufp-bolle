"""Interfaccia locale, presidiata e senza credenziali o accesso di rete."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .engine import Ledger, run_stage
from .planner import build_plan, validate_plan
from .simulator import SimulatedArs, StopOperation
from .storage import read_json, write_json


def summary(plan):
    doc = plan["document"]
    out = ["SOLO PREPARAZIONE / SIMULAZIONE LOCALE — nessuna scrittura ARS",
           f"Fornitore: {doc['supplier_name']} [{doc['supplier_id']}]",
           f"Bolla: {doc['number']} | data {doc['date']} | serie {doc['series']!r} | magazzino {doc['warehouse']}"]
    check = plan["source_receipt"]["physical_check"]
    out.append(f"Controllo fisico dichiarato: {check['operator']} — {check['checked_at']}")
    planned = {line["receipt_line"]: line for line in plan["lines"]}
    for line in plan["source_receipt"]["lines"]:
        key = line["receipt_line"]
        dq, rq = line["document_quantity"], line["received_quantity"]
        out += [f"\nRiga ricezione {key}: ordine {line['order_type']} / {line['order_number']} / riga {line.get('order_line_id') or '(da risolvere univocamente)'}",
                f"  Codice fornitore {line['supplier_code']} → interno {line['internal_code']}",
                f"  Bolla {dq['value']} {dq['unit']} | fisico {rq['value']} {rq['unit']}",
                f"  Ubicazione {line['location']}"]
        if "difference_reason" in line:
            out.append(f"  Differenza motivata: {line['difference_reason']}")
        if "conversion" in line:
            conv = line["conversion"]
            out.append(f"  Conversione: {conv['from']} → {conv['to']} × {conv['factor']} | {conv['reference']}")
        if key in planned:
            match = planned[key]
            qty, target = match["registration_quantity"], match["target"]
            out.append(f"  Da registrare: {qty['value']} {qty['unit']} | residuo iniziale {target['remaining']} {target['unit']}")
            out.append(f"  Abbinamento snapshot: {target['row_id']} | riga ordine {target.get('order_line_id') or '(non disponibile)'}")
        for anomaly in plan["anomalies"]:
            if anomaly["receipt_line"] == key:
                out.append(f"  BLOCCO [{anomaly['code']}]: {anomaly['message']}")
    out += ["", "Piano pronto per la simulazione." if plan["ready"] else "Piano BLOCCATO: correggere i dati e produrre una nuova revisione.",
            f"Impronta dei dati esatti: {plan['digest']}",
            "Fasi distinte: initial = caricamento DDT; libero = lista sospesa collegata al DDT.",
            "Palmare: NON VERIFICATO. Identificativi e stati del simulatore non provano quelli ARS."]
    return "\n".join(out)


def existing_sim(path):
    if not Path(path).is_file():
        raise ValueError("Simulatore inesistente: usare prima sim-init con un database separato.")
    return SimulatedArs(path)


def parser():
    result = argparse.ArgumentParser(description="UFP bolle: preparazione e simulazione locale. ARS reale non collegato.")
    commands = result.add_subparsers(dest="command", required=True)
    init = commands.add_parser("sim-init", help="Crea un simulatore nuovo da ordini sintetici")
    init.add_argument("--orders", required=True)
    init.add_argument("--db", required=True)
    plan = commands.add_parser("plan", help="Valida, abbina e mostra il riepilogo senza caricamenti")
    plan.add_argument("--receipt", required=True)
    source = plan.add_mutually_exclusive_group(required=True)
    source.add_argument("--orders", help="Snapshot JSON locale")
    source.add_argument("--sim-db", help="Snapshot corrente dal simulatore")
    plan.add_argument("--out", required=True, help="Nuovo file piano; non sovrascrive un piano esistente")
    show = commands.add_parser("show", help="Mostra i dati esatti di un piano")
    show.add_argument("--plan", required=True)
    confirm = commands.add_parser("confirm", help="Conferma l'impronta dopo la verifica umana del riepilogo")
    confirm.add_argument("--plan", required=True)
    confirm.add_argument("--digest", required=True, help="Copiare l'intera impronta del riepilogo verificato")
    confirm.add_argument("--operator", required=True)
    confirm.add_argument("--state", required=True)
    run = commands.add_parser("run", help="Esegue o riconcilia una sola fase nel simulatore")
    run.add_argument("--plan", required=True)
    run.add_argument("--state", required=True)
    run.add_argument("--sim-db", required=True)
    run.add_argument("--stage", choices=["initial", "libero"], required=True)
    run.add_argument("--fault", choices=["before_save", "after_save", "after_intent", "readback_unknown"])
    status = commands.add_parser("status", help="Legge lo storico locale, senza attestare lo stato attuale ARS")
    status.add_argument("--state", required=True)
    status.add_argument("--digest", required=True)
    control = commands.add_parser("sim-control", help="Cambia soltanto lo stato del simulatore per provare i blocchi")
    control.add_argument("--db", required=True)
    control.add_argument("--health", choices=["normal", "session_expired", "unexpected_screen", "unreadable"], required=True)
    return result


def execute(args):
    if args.command == "sim-init":
        sim = SimulatedArs(args.db)
        try:
            sim.seed(read_json(args.orders))
        finally:
            sim.close()
        print("Simulatore inizializzato. Nessun collegamento al gestionale reale.")
    elif args.command == "plan":
        if args.orders:
            orders = read_json(args.orders)
        else:
            sim = existing_sim(args.sim_db)
            try:
                orders = sim.orders()
            finally:
                sim.close()
        plan = build_plan(read_json(args.receipt), orders)
        write_json(args.out, plan)
        print(summary(plan))
        return 0 if plan["ready"] else 2
    elif args.command in {"show", "confirm", "run"}:
        plan = read_json(args.plan)
        validate_plan(plan)
        if args.command == "show":
            print(summary(plan))
            return 0 if plan["ready"] else 2
        ledger = Ledger(args.state)
        try:
            if args.command == "confirm":
                print(summary(plan))
                ledger.approve(plan, args.operator, args.digest)
                print("Conferma registrata per questa impronta. Vale solo per la simulazione locale.")
            else:
                sim = existing_sim(args.sim_db)
                try:
                    observation = run_stage(ledger, sim, plan, args.stage, args.fault)
                finally:
                    sim.close()
                print(json.dumps({"environment": "simulation", "stage": args.stage, **observation,
                                  "palmare": "NON_VERIFICATO"}, ensure_ascii=False, indent=2))
        finally:
            ledger.close()
    elif args.command == "status":
        ledger = Ledger(args.state)
        try:
            print(json.dumps(ledger.status(args.digest), ensure_ascii=False, indent=2))
        finally:
            ledger.close()
    elif args.command == "sim-control":
        sim = existing_sim(args.db)
        try:
            sim.set_health(args.health)
        finally:
            sim.close()
        print("Stato del simulatore aggiornato. La ripresa rileggerà gli esiti.")
    return 0


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return execute(args)
    except (ValueError, StopOperation) as exc:
        print(f"ARRESTO: {exc}", file=sys.stderr)
        return 2
    except (OSError, sqlite3.Error):
        print("ARRESTO: impossibile leggere/scrivere i file locali. Controllare percorsi, permessi, lock e spazio; non eliminare il registro per riprovare.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
