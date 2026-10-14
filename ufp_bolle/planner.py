"""Deterministic receipt planning. This module never talks to a management system.

Order snapshots and stable ``row_id`` values are supplied by an adapter. The
included adapter uses simulated identifiers; real ARS identifiers are unverified.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, localcontext
import hashlib
import json
import re
from typing import Any


_NUMBER = re.compile(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,6})?\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_CONVERSIONS = {("TO", "KG"): Decimal("1000"), ("KG", "TO"): Decimal("0.001")}
_RECEIPT_FIELDS = {"schema_version", "document", "complete_document", "physical_check", "lines"}
_DOCUMENT_FIELDS = {"supplier_id", "supplier_name", "number", "date", "series", "warehouse"}
_CHECK_FIELDS = {"operator", "checked_at"}
_LINE_FIELDS = {"receipt_line", "order_type", "order_number", "order_line_id",
                "supplier_code", "internal_code", "document_quantity", "received_quantity",
                "registration_unit", "conversion", "difference_reason", "location"}
_QUANTITY_FIELDS = {"value", "unit"}
_CONVERSION_FIELDS = {"from", "to", "factor", "reference"}
_ORDER_FIELDS = {"row_id", "supplier_id", "order_type", "order_number", "order_line_id",
                 "supplier_code", "internal_code", "unit", "remaining", "warehouse", "location"}


def canonical(value: Any) -> str:
    """Return stable JSON, rejecting non-JSON data and nonfinite numbers."""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("I dati devono essere serializzabili come JSON finito") from exc


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _clone(value: Any) -> Any:
    return json.loads(canonical(value))


def _object(value: Any, where: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{where}: oggetto obbligatorio")
    return value


def _known_fields(value: dict, allowed: set[str], where: str) -> None:
    unknown = value.keys() - allowed
    if unknown:
        names = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"{where}: campi non supportati: {names}")


def _text(value: Any, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{where}: testo non vuoto obbligatorio")
    if value != value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError(f"{where}: spazi esterni e caratteri di controllo non ammessi")
    if len(value) > 1000:
        raise ValueError(f"{where}: massimo 1000 caratteri")
    return value


def _decimal(value: Any, where: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not _NUMBER.fullmatch(value):
        raise ValueError(f"{where}: usare una stringa decimale senza esponente, "
                         "massimo 12 cifre intere e 6 decimali")
    result = Decimal(value)
    if positive and result <= 0:
        raise ValueError(f"{where}: la quantità deve essere maggiore di zero")
    return result


def _decimal_text(value: Decimal) -> str:
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def _quantity(value: Any, where: str) -> tuple[Decimal, str]:
    quantity = _object(value, where)
    _known_fields(quantity, _QUANTITY_FIELDS, where)
    return (_decimal(quantity.get("value"), f"{where}.value", positive=True),
            _text(quantity.get("unit"), f"{where}.unit"))


def _optional_line_id(row: dict, where: str) -> None:
    if row.get("order_line_id") is not None:
        _text(row["order_line_id"], f"{where}.order_line_id")


def _validate_receipt(receipt: Any) -> None:
    receipt = _object(receipt, "receipt")
    _known_fields(receipt, _RECEIPT_FIELDS, "receipt")
    if type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1:
        raise ValueError("receipt.schema_version deve essere 1")
    if receipt.get("complete_document") is not True:
        raise ValueError("complete_document deve essere true: includere tutte le righe "
                         "da registrare per questa bolla")
    document = _object(receipt.get("document"), "document")
    _known_fields(document, _DOCUMENT_FIELDS, "document")
    for field in ("supplier_id", "supplier_name", "number", "date", "warehouse"):
        _text(document.get(field), f"document.{field}")
    # An absent document series is explicitly represented by the empty string;
    # the key is still required and participates in the document identity hash.
    _text(document.get("series"), "document.series", allow_empty=True)
    try:
        if not _DATE.fullmatch(document["date"]):
            raise ValueError
        date.fromisoformat(document["date"])
    except ValueError as exc:
        raise ValueError("document.date deve essere una data reale YYYY-MM-DD") from exc
    check = _object(receipt.get("physical_check"), "physical_check")
    _known_fields(check, _CHECK_FIELDS, "physical_check")
    _text(check.get("operator"), "physical_check.operator")
    timestamp = _text(check.get("checked_at"), "physical_check.checked_at")
    try:
        if "T" not in timestamp:
            raise ValueError
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
    except ValueError as exc:
        raise ValueError("physical_check.checked_at richiede ISO8601 con fuso orario") from exc
    rows = receipt.get("lines")
    if not isinstance(rows, list) or not rows:
        raise ValueError("receipt.lines deve contenere almeno una riga ricevuta; "
                         "escludere le righe con quantità ricevuta zero")
    seen: set[str] = set()
    for index, line in enumerate(rows):
        where = f"lines[{index}]"
        line = _object(line, where)
        _known_fields(line, _LINE_FIELDS, where)
        for field in ("receipt_line", "order_type", "order_number", "supplier_code",
                      "internal_code", "registration_unit", "location"):
            _text(line.get(field), f"{where}.{field}")
        if line["receipt_line"] in seen:
            raise ValueError(f"receipt_line duplicata: {line['receipt_line']}")
        seen.add(line["receipt_line"])
        _optional_line_id(line, where)
        _quantity(line.get("document_quantity"), f"{where}.document_quantity")
        _quantity(line.get("received_quantity"), f"{where}.received_quantity")
        if "difference_reason" in line:
            _text(line["difference_reason"], f"{where}.difference_reason")
        if "conversion" in line:
            conversion = _object(line["conversion"], f"{where}.conversion")
            _known_fields(conversion, _CONVERSION_FIELDS, f"{where}.conversion")
            for field in ("from", "to", "reference"):
                _text(conversion.get(field), f"{where}.conversion.{field}")
            _decimal(conversion.get("factor"), f"{where}.conversion.factor", positive=True)


def validate_orders(orders: Any) -> None:
    """Validate a complete adapter snapshot, without changing or normalizing it."""
    if not isinstance(orders, list):
        raise ValueError("orders deve essere una lista di righe d'ordine")
    seen: set[str] = set()
    for index, row in enumerate(orders):
        where = f"orders[{index}]"
        row = _object(row, where)
        _known_fields(row, _ORDER_FIELDS, where)
        for field in ("row_id", "supplier_id", "order_type", "order_number",
                      "supplier_code", "internal_code", "unit", "warehouse", "location"):
            _text(row.get(field), f"{where}.{field}")
        _optional_line_id(row, where)
        _decimal(row.get("remaining"), f"{where}.remaining")
        if row["row_id"] in seen:
            raise ValueError(f"row_id duplicato nello snapshot ordini: {row['row_id']}")
        seen.add(row["row_id"])


def build_plan(receipt: dict, orders: list[dict]) -> dict:
    """Validate confirmed input and plan exact order matches without any writes.

    Invalid structures and unsupported fields raise ValueError. Document ``series``
    is required but can be empty when the document has no series; order_line_id is
    optional. Business anomalies are returned per line;
    any anomaly blocks the entire document. No fuzzy matching or implicit unit
    conversion is performed. The digest binds both full sources and all results.
    """
    _validate_receipt(receipt)
    validate_orders(orders)
    receipt, orders = _clone(receipt), _clone(orders)
    document = receipt["document"]
    identity = {key: document[key] for key in
                ("supplier_id", "number", "date", "series", "warehouse")}
    anomalies: list[dict] = []
    lines: list[dict] = []

    def anomaly(line: dict, code: str, message: str) -> None:
        anomalies.append({"receipt_line": line["receipt_line"],
                          "code": code, "message": message})

    with localcontext() as context:
        context.prec = 60  # Products of bounded input decimals remain exact.
        for line in receipt["lines"]:
            before = len(anomalies)
            document_value, document_unit = _quantity(line["document_quantity"], "document_quantity")
            received_value, received_unit = _quantity(line["received_quantity"], "received_quantity")
            if document_unit != received_unit:
                anomaly(line, "DOCUMENT_RECEIVED_UNIT_MISMATCH",
                        "Quantità in bolla e confermata devono usare la stessa unità nella v1")
            elif document_value != received_value and not line.get("difference_reason"):
                anomaly(line, "DIFFERENCE_REASON_REQUIRED",
                        "Quantità in bolla e quantità fisica diverse: indicare il motivo verificato")

            base = [row for row in orders if
                    row["supplier_id"] == document["supplier_id"] and
                    row["warehouse"] == document["warehouse"] and
                    row["order_type"] == line["order_type"] and
                    row["order_number"] == line["order_number"] and
                    row["location"] == line["location"] and
                    (line.get("order_line_id") is None or
                     row.get("order_line_id") == line["order_line_id"])]
            candidates = [row for row in base if
                          row["supplier_code"] == line["supplier_code"] and
                          row["internal_code"] == line["internal_code"]]
            if not candidates:
                if base:
                    anomaly(line, "CODE_MISMATCH",
                            "Codici fornitore/interno discordanti dalle righe dell'ordine: verificare in ufficio")
                else:
                    anomaly(line, "ORDER_NOT_FOUND",
                            "Nessuna riga coincide con fornitore, magazzino, ordine, riga e ubicazione indicati")
                continue
            if len(candidates) != 1:
                anomaly(line, "AMBIGUOUS_ORDER_LINE",
                        "Più righe d'ordine coincidono: occorre identificare la riga esatta, senza ripartizioni automatiche")
                continue
            target = candidates[0]
            registration_unit = line["registration_unit"]
            if target["unit"] != registration_unit:
                anomaly(line, "ORDER_UNIT_MISMATCH",
                        "Unità da registrare diversa dall'unità della riga d'ordine")

            conversion = line.get("conversion")
            factor = Decimal("1")
            if received_unit == registration_unit:
                if conversion is not None and (
                    conversion["from"] != received_unit or
                    conversion["to"] != registration_unit or
                    Decimal(conversion["factor"]) != 1
                ):
                    anomaly(line, "INVALID_CONVERSION", "Conversione identità incoerente: il fattore deve essere 1")
            elif conversion is None:
                anomaly(line, "CONVERSION_REQUIRED",
                        "Unità fisica e unità da registrare diverse: serve una conversione esplicita verificata")
            else:
                allowed = _CONVERSIONS.get((received_unit, registration_unit))
                if allowed is None:
                    anomaly(line, "UNSUPPORTED_CONVERSION",
                            "Conversione non supportata nella v1: verificare una regola deterministica prima di procedere")
                elif (conversion["from"] != received_unit or
                      conversion["to"] != registration_unit or
                      Decimal(conversion["factor"]) != allowed):
                    anomaly(line, "INVALID_CONVERSION",
                            "Conversione incoerente: ammessi solo TO→KG ×1000 e KG→TO ×0.001")
                else:
                    factor = allowed
            registered = received_value * factor
            registered_text = _decimal_text(registered)
            if not _NUMBER.fullmatch(registered_text):
                anomaly(line, "REGISTRATION_QUANTITY_OUT_OF_RANGE",
                        "Quantità convertita fuori limite (12 cifre intere e 6 decimali); nessun arrotondamento applicato")
            if len(anomalies) == before:
                planned = _clone(line)
                planned["target"] = _clone(target)
                planned["registration_quantity"] = {"value": registered_text, "unit": registration_unit}
                lines.append(planned)

        grouped: dict[str, list[dict]] = defaultdict(list)
        for line in lines:
            grouped[line["target"]["row_id"]].append(line)
        rejected: set[str] = set()
        for row_id, group in grouped.items():
            total = sum((Decimal(line["registration_quantity"]["value"]) for line in group), Decimal("0"))
            remaining = Decimal(group[0]["target"]["remaining"])
            if total > remaining:
                rejected.add(row_id)
                for line in group:
                    anomaly(line, "QUANTITY_EXCEEDS_REMAINING",
                            f"Totale da registrare {_decimal_text(total)} superiore al residuo "
                            f"{_decimal_text(remaining)} {line['target']['unit']}; verificare tutte le righe abbinate")
        lines = [line for line in lines if line["target"]["row_id"] not in rejected]

    plan = {"version": 1, "document": _clone(document),
            "document_key": fingerprint(identity), "lines": lines,
            "anomalies": anomalies, "ready": not anomalies and bool(lines),
            "source_receipt": receipt, "source_orders": orders}
    plan["digest"] = fingerprint(plan)
    return plan


def validate_plan(plan: dict) -> None:
    """Reject tampering, stale derived fields and digest-only re-signing.

    This validates consistency, not real-system state or operator identity.
    Confirmation and fresh remote checks are the executor's responsibility.
    """
    _object(plan, "plan")
    if not isinstance(plan.get("digest"), str):
        raise ValueError("Piano privo di digest")
    unsigned = {key: value for key, value in plan.items() if key != "digest"}
    if fingerprint(unsigned) != plan["digest"]:
        raise ValueError("Digest del piano non valido: generare un nuovo piano e confermarlo")
    expected = build_plan(plan.get("source_receipt"), plan.get("source_orders"))
    if canonical(plan) != canonical(expected):
        raise ValueError("Piano non coerente con i dati sorgente: ricrearlo e riconfermarlo")
