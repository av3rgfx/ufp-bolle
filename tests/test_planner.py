"""Business-rule tests against synthetic data only; no ARS compatibility claim."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from ufp_bolle.planner import build_plan, canonical, fingerprint, validate_orders, validate_plan


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def fixture():
    receipt = json.loads((EXAMPLES / "receipt.json").read_text(encoding="utf-8"))
    orders = json.loads((EXAMPLES / "orders.json").read_text(encoding="utf-8"))
    return receipt, orders


def ordinary_fixture(quantity="10", remaining="10"):
    receipt, orders = fixture()
    line = receipt["lines"][0]
    line["document_quantity"] = {"value": quantity, "unit": "NR"}
    line["received_quantity"] = {"value": quantity, "unit": "NR"}
    line["registration_unit"] = "NR"
    del line["conversion"]
    orders[0].update(unit="NR", remaining=remaining)
    return receipt, orders


def codes(plan):
    return {item["code"] for item in plan["anomalies"]}


class PlannerTest(unittest.TestCase):
    def test_ordinary_full_delivery(self):
        receipt, orders = ordinary_fixture()
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertEqual(plan["anomalies"], [])
        self.assertEqual(plan["lines"][0]["target"], orders[0])
        self.assertEqual(plan["lines"][0]["registration_quantity"], {"value": "10", "unit": "NR"})
        self.assertIsNone(validate_plan(plan))

    def test_partial_delivery_does_not_replace_with_document_quantity(self):
        receipt, orders = ordinary_fixture("10", "20")
        receipt["lines"][0]["received_quantity"]["value"] = "4"
        receipt["lines"][0]["difference_reason"] = "Confermati fisicamente 4 pezzi; 6 mancanti"
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertEqual(plan["lines"][0]["registration_quantity"]["value"], "4")
        self.assertEqual(plan["lines"][0]["document_quantity"]["value"], "10")
        self.assertEqual(plan["lines"][0]["target"]["remaining"], "20")

    def test_difference_without_reason_blocks(self):
        receipt, orders = ordinary_fixture()
        receipt["lines"][0]["received_quantity"]["value"] = "4"
        plan = build_plan(receipt, orders)
        self.assertFalse(plan["ready"])
        self.assertIn("DIFFERENCE_REASON_REQUIRED", codes(plan))

    def test_exact_metric_conversion_and_three_distinct_quantities(self):
        receipt, orders = fixture()
        receipt["lines"][0]["received_quantity"]["value"] = "0.070"
        receipt["lines"][0]["difference_reason"] = "Peso confermato inferiore alla bolla"
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        line = plan["lines"][0]
        self.assertEqual(line["document_quantity"], {"value": "0.072", "unit": "TO"})
        self.assertEqual(line["received_quantity"], {"value": "0.070", "unit": "TO"})
        self.assertEqual(line["registration_quantity"], {"value": "70", "unit": "KG"})

    def test_reverse_conversion_is_exact(self):
        receipt, orders = fixture()
        line = receipt["lines"][0]
        line["document_quantity"] = {"value": "72", "unit": "KG"}
        line["received_quantity"] = {"value": "72", "unit": "KG"}
        line["registration_unit"] = "TO"
        line["conversion"].update({"from": "KG", "to": "TO", "factor": "0.001"})
        orders[0].update(unit="TO", remaining="0.100")
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertEqual(plan["lines"][0]["registration_quantity"], {"value": "0.072", "unit": "TO"})

    def test_same_article_on_different_orders_matches_by_order(self):
        receipt, orders = ordinary_fixture()
        second_order = deepcopy(orders[0])
        second_order.update(row_id="SIM-ROW-002", order_number="SIM-ORD-002", remaining="20")
        orders.append(second_order)
        second_line = deepcopy(receipt["lines"][0])
        second_line.update(receipt_line="2", order_number="SIM-ORD-002")
        receipt["lines"].append(second_line)
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertEqual([line["target"]["row_id"] for line in plan["lines"]],
                         ["SIM-ROW-001", "SIM-ROW-002"])

    def test_same_article_on_same_order_requires_unambiguous_line(self):
        receipt, orders = ordinary_fixture()
        second_order = deepcopy(orders[0])
        second_order.update(row_id="SIM-ROW-002", order_line_id="SIM-RIGA-002")
        orders.append(second_order)
        receipt["lines"][0]["order_line_id"] = None
        plan = build_plan(receipt, orders)
        self.assertFalse(plan["ready"])
        self.assertIn("AMBIGUOUS_ORDER_LINE", codes(plan))
        receipt["lines"][0]["order_line_id"] = "SIM-RIGA-002"
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertEqual(plan["lines"][0]["target"]["row_id"], "SIM-ROW-002")

    def test_optional_line_id_not_fabricated_when_absent(self):
        receipt, orders = ordinary_fixture()
        del receipt["lines"][0]["order_line_id"]
        del orders[0]["order_line_id"]
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertNotIn("order_line_id", plan["lines"][0]["target"])

    def test_discordant_code_never_corrected(self):
        receipt, orders = ordinary_fixture()
        receipt["lines"][0]["supplier_code"] = "SIM-FORN-00I"
        plan = build_plan(receipt, orders)
        self.assertFalse(plan["ready"])
        self.assertEqual(plan["lines"], [])
        self.assertIn("CODE_MISMATCH", codes(plan))
        self.assertEqual(plan["source_receipt"]["lines"][0]["supplier_code"], "SIM-FORN-00I")

    def test_match_requires_supplier_warehouse_location_type_and_order(self):
        for scope, field in (("document", "supplier_id"), ("document", "warehouse"),
                             ("line", "location"), ("line", "order_type"),
                             ("line", "order_number")):
            with self.subTest(field=field):
                receipt, orders = ordinary_fixture()
                obj = receipt["document"] if scope == "document" else receipt["lines"][0]
                obj[field] = "UNMATCHED"
                plan = build_plan(receipt, orders)
                self.assertFalse(plan["ready"])
                self.assertIn("ORDER_NOT_FOUND", codes(plan))

    def test_registration_unit_must_match_order(self):
        receipt, orders = ordinary_fixture()
        orders[0]["unit"] = "PZ"
        self.assertIn("ORDER_UNIT_MISMATCH", codes(build_plan(receipt, orders)))

    def test_document_and_physical_units_must_match(self):
        receipt, orders = fixture()
        receipt["lines"][0]["document_quantity"]["unit"] = "KG"
        self.assertIn("DOCUMENT_RECEIVED_UNIT_MISMATCH", codes(build_plan(receipt, orders)))

    def test_conversion_required_and_wrong_factor_blocked(self):
        receipt, orders = fixture()
        receipt["lines"][0]["conversion"]["factor"] = "100"
        self.assertIn("INVALID_CONVERSION", codes(build_plan(receipt, orders)))
        del receipt["lines"][0]["conversion"]
        self.assertIn("CONVERSION_REQUIRED", codes(build_plan(receipt, orders)))

    def test_conversion_pair_is_not_guessed(self):
        receipt, orders = ordinary_fixture()
        line = receipt["lines"][0]
        line["document_quantity"]["unit"] = "COPPIA"
        line["received_quantity"]["unit"] = "COPPIA"
        line["conversion"] = {"from": "COPPIA", "to": "NR", "factor": "2", "reference": "Ipotesi"}
        plan = build_plan(receipt, orders)
        self.assertFalse(plan["ready"])
        self.assertIn("UNSUPPORTED_CONVERSION", codes(plan))

    def test_identity_conversion_cannot_change_quantity(self):
        receipt, orders = ordinary_fixture()
        receipt["lines"][0]["conversion"] = {
            "from": "NR", "to": "NR", "factor": "2", "reference": "Errata"}
        self.assertIn("INVALID_CONVERSION", codes(build_plan(receipt, orders)))

    def test_conversion_never_rounds_precision_overflow(self):
        receipt, orders = ordinary_fixture("0.000001", "10")
        line = receipt["lines"][0]
        line["document_quantity"]["unit"] = line["received_quantity"]["unit"] = "KG"
        line["registration_unit"] = "TO"
        line["conversion"] = {"from": "KG", "to": "TO", "factor": "0.001", "reference": "Metrica"}
        orders[0]["unit"] = "TO"
        plan = build_plan(receipt, orders)
        self.assertFalse(plan["ready"])
        self.assertIn("REGISTRATION_QUANTITY_OUT_OF_RANGE", codes(plan))

    def test_multiple_receipt_lines_same_target_preserved_with_cumulative_check(self):
        receipt, orders = ordinary_fixture("6", "12")
        second = deepcopy(receipt["lines"][0])
        second["receipt_line"] = "2"
        receipt["lines"].append(second)
        plan = build_plan(receipt, orders)
        self.assertTrue(plan["ready"])
        self.assertEqual(len(plan["lines"]), 2)
        orders[0]["remaining"] = "11"
        plan = build_plan(receipt, orders)
        self.assertFalse(plan["ready"])
        self.assertEqual(plan["lines"], [])
        self.assertEqual([item["receipt_line"] for item in plan["anomalies"]], ["1", "2"])
        self.assertEqual(codes(plan), {"QUANTITY_EXCEEDS_REMAINING"})

    def test_zero_remaining_blocks_new_receipt(self):
        receipt, orders = ordinary_fixture("1", "0")
        self.assertIn("QUANTITY_EXCEEDS_REMAINING", codes(build_plan(receipt, orders)))

    def test_all_or_nothing_when_one_line_is_unmatched(self):
        receipt, orders = ordinary_fixture()
        second = deepcopy(receipt["lines"][0])
        second.update(receipt_line="2", order_number="MISSING")
        receipt["lines"].append(second)
        plan = build_plan(receipt, orders)
        self.assertEqual(len(plan["lines"]), 1)
        self.assertFalse(plan["ready"])
        validate_plan(plan)

    def test_source_data_and_physical_confirmation_are_bound_to_digest(self):
        receipt, orders = ordinary_fixture()
        first = build_plan(receipt, orders)
        receipt["physical_check"]["operator"] = "SIM-ALTRO"
        second = build_plan(receipt, orders)
        self.assertNotEqual(first["digest"], second["digest"])
        self.assertEqual(first["document_key"], second["document_key"])
        orders[0]["remaining"] = "11"
        third = build_plan(receipt, orders)
        self.assertNotEqual(second["digest"], third["digest"])
        self.assertEqual(first["source_orders"][0]["remaining"], "10")

    def test_document_identity_distinguishes_partial_delivery_bills(self):
        receipt, orders = ordinary_fixture()
        first = build_plan(receipt, orders)
        receipt["document"]["number"] = "SIM-DDT-002"
        second = build_plan(receipt, orders)
        self.assertNotEqual(first["document_key"], second["document_key"])
        receipt["document"]["number"] = "SIM-DDT-001"
        receipt["document"]["supplier_name"] = "Etichetta cambiata"
        third = build_plan(receipt, orders)
        self.assertEqual(first["document_key"], third["document_key"])
        self.assertNotEqual(first["digest"], third["digest"])

    def test_modified_plan_fails_even_when_attacker_recomputes_digest(self):
        receipt, orders = ordinary_fixture()
        plan = build_plan(receipt, orders)
        plan["lines"][0]["registration_quantity"]["value"] = "11"
        with self.assertRaises(ValueError):
            validate_plan(plan)
        plan["digest"] = fingerprint({key: value for key, value in plan.items() if key != "digest"})
        with self.assertRaisesRegex(ValueError, "coerente"):
            validate_plan(plan)

    def test_digest_is_order_independent_for_json_object_keys(self):
        self.assertEqual(canonical({"b": 2, "a": 1}), '{"a":1,"b":2}')
        self.assertEqual(fingerprint({"a": 1, "b": 2}), fingerprint({"b": 2, "a": 1}))
        for value in (float("nan"), float("inf"), object()):
            with self.assertRaises(ValueError):
                canonical(value)

    def test_malformed_quantities_rejected(self):
        for value in (True, False, None, 1, 0.1, "NaN", "Infinity", "1e3", "-1", "0",
                      "1,2", "01", "1000000000000", "0.0000001", " 1"):
            with self.subTest(value=value):
                receipt, orders = ordinary_fixture()
                receipt["lines"][0]["received_quantity"]["value"] = value
                with self.assertRaises(ValueError):
                    build_plan(receipt, orders)

    def test_bad_dates_timezone_completeness_and_missing_operator_rejected(self):
        for field, value in (("date", "2026-02-30"), ("date", "20261012"),
                             ("checked_at", "2026-10-12T09:00:00"),
                             ("checked_at", "2026-10-12"), ("operator", ""),
                             ("complete_document", False), ("complete_document", 1),
                             ("schema_version", True)):
            with self.subTest(field=field, value=value):
                receipt, orders = ordinary_fixture()
                if field == "date":
                    receipt["document"][field] = value
                elif field in ("operator", "checked_at"):
                    receipt["physical_check"][field] = value
                else:
                    receipt[field] = value
                with self.assertRaises(ValueError):
                    build_plan(receipt, orders)

    def test_duplicate_receipt_line_or_snapshot_row_ids_rejected(self):
        receipt, orders = ordinary_fixture()
        receipt["lines"].append(deepcopy(receipt["lines"][0]))
        with self.assertRaisesRegex(ValueError, "receipt_line duplicata"):
            build_plan(receipt, orders)
        receipt, orders = ordinary_fixture()
        orders.append(deepcopy(orders[0]))
        with self.assertRaisesRegex(ValueError, "row_id duplicato"):
            validate_orders(orders)

    def test_invalid_snapshot_residual_or_required_fields_rejected(self):
        for field, value in (("remaining", "-1"), ("remaining", 10),
                             ("remaining", "0.0000001"), ("row_id", None),
                             ("warehouse", ""), ("order_line_id", True)):
            with self.subTest(field=field, value=value):
                _, orders = ordinary_fixture()
                orders[0][field] = value
                with self.assertRaises(ValueError):
                    validate_orders(orders)

    def test_empty_orders_report_unmatched_but_empty_receipt_is_invalid(self):
        receipt, _ = ordinary_fixture()
        plan = build_plan(receipt, [])
        self.assertFalse(plan["ready"])
        self.assertIn("ORDER_NOT_FOUND", codes(plan))
        receipt["lines"] = []
        with self.assertRaises(ValueError):
            build_plan(receipt, [])

    def test_unsupported_fields_rejected_at_every_schema_level(self):
        # No silently ignored operational fields may imply unsupported effects.
        paths = [(), ("document",), ("physical_check",), ("lines", 0),
                 ("lines", 0, "document_quantity"), ("lines", 0, "received_quantity"),
                 ("lines", 0, "conversion")]
        for path in paths:
            with self.subTest(path=path):
                receipt, orders = fixture()
                target = receipt
                for key in path:
                    target = target[key]
                target["vettore"] = "SIM-Trasporto"
                with self.assertRaisesRegex(ValueError, "campi non supportati: vettore"):
                    build_plan(receipt, orders)
        receipt, orders = fixture()
        orders[0]["automatic_save"] = True
        with self.assertRaisesRegex(ValueError, "campi non supportati: automatic_save"):
            validate_orders(orders)

    def test_empty_series_is_explicit_and_participates_in_identity(self):
        receipt, orders = fixture()
        original = build_plan(receipt, orders)
        receipt["document"]["series"] = ""
        no_series = build_plan(receipt, orders)
        self.assertTrue(no_series["ready"])
        self.assertEqual(no_series["document"]["series"], "")
        self.assertNotEqual(original["document_key"], no_series["document_key"])
        del receipt["document"]["series"]
        with self.assertRaises(ValueError):
            build_plan(receipt, orders)

    def test_unbounded_text_is_rejected_before_planning(self):
        receipt, orders = fixture()
        receipt["physical_check"]["operator"] = "X" * 1001
        with self.assertRaisesRegex(ValueError, "massimo 1000 caratteri"):
            build_plan(receipt, orders)


if __name__ == "__main__":
    unittest.main()
