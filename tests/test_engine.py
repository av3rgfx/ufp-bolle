"""End-to-end checks against a separate, persistent, local ARS simulator.

These checks establish local safety behavior; they do not exercise ARS itself.
Only synthetic example records are used, with a fresh pair of databases per test.
"""

import copy
import json
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ufp_bolle.engine import Ledger, run_stage
from ufp_bolle.planner import build_plan, fingerprint
from ufp_bolle.simulator import SimulatedArs, StopOperation


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.receipt = json.loads((EXAMPLES / "receipt.json").read_text())
        self.orders = json.loads((EXAMPLES / "orders.json").read_text())
        self.adapter = SimulatedArs(self.root / "ars.sqlite")
        self.adapter.seed(copy.deepcopy(self.orders))
        self.ledger = Ledger(self.root / "ledger.sqlite")
        self.addCleanup(lambda: self.adapter.close())
        self.addCleanup(lambda: self.ledger.close())
        self.plan = build_plan(self.receipt, self.adapter.orders())
        self.assertTrue(self.plan["ready"])

    def approve(self, plan=None):
        plan = self.plan if plan is None else plan
        self.ledger.approve(plan, "Operatore test", plan["digest"])

    def artifact_count(self, stage=None):
        if stage is None:
            return self.adapter.db.execute("SELECT count(*) FROM artifacts").fetchone()[0]
        return self.adapter.db.execute(
            "SELECT count(*) FROM artifacts WHERE stage=?", (stage,)
        ).fetchone()[0]

    def remaining(self):
        return {row["row_id"]: Decimal(row["remaining"])
                for row in self.adapter.orders()}

    def stage_status(self, stage="initial", plan=None):
        plan = self.plan if plan is None else plan
        return self.ledger.status(plan["digest"])[stage]["status"]

    def revised_receipt(self, *, number=None, quantity=None):
        receipt = copy.deepcopy(self.receipt)
        if number is not None:
            receipt["document"]["number"] = number
        if quantity is not None:
            for key in ("document_quantity", "received_quantity"):
                receipt["lines"][0][key]["value"] = quantity
        return receipt

    def test_ordinary_conversion_partial_delivery_and_separate_libero(self):
        self.approve()
        result = run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertEqual("verified", result["status"])
        self.assertEqual("DDT_VERIFIED", result["state"])
        self.assertEqual("simulator_full_readback", result["evidence"])
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())
        self.assertEqual("VERIFIED", self.stage_status())
        self.assertEqual("PENDING", self.stage_status("libero"))
        self.assertEqual(0, self.artifact_count("libero"))

        result = run_stage(self.ledger, self.adapter, self.plan, "libero")
        self.assertEqual("verified", result["status"])
        self.assertEqual("LIBERO_SUSPENDED", result["state"])
        self.assertEqual("VERIFIED", self.stage_status("libero"))
        self.assertEqual(2, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_later_document_can_receive_residual_without_duplicate_block(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        later = build_plan(
            self.revised_receipt(number="SIM-DDT-002", quantity="0.020"),
            self.adapter.orders(),
        )
        self.assertTrue(later["ready"])
        self.approve(later)
        run_stage(self.ledger, self.adapter, later, "initial")
        self.assertEqual(2, self.artifact_count("initial"))
        self.assertEqual({"SIM-ROW-001": Decimal("8")}, self.remaining())

    def test_physical_shortfall_registers_received_quantity_only(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["lines"][0]["received_quantity"]["value"] = "0.050"
        receipt["lines"][0]["difference_reason"] = "Controllo fisico: ricevuti 50 kg dei 72 kg in bolla"
        plan = build_plan(receipt, self.adapter.orders())
        self.approve(plan)
        run_stage(self.ledger, self.adapter, plan, "initial")
        self.assertEqual({"SIM-ROW-001": Decimal("50")}, self.remaining())
        effect = json.loads(self.adapter.db.execute(
            "SELECT effect FROM artifacts WHERE stage='initial'"
        ).fetchone()[0])
        self.assertEqual({"value": "50", "unit": "KG"}, effect["rows"][0]["quantity"])
        self.assertEqual("0.072", plan["source_receipt"]["lines"][0]["document_quantity"]["value"])

    def test_repeated_article_on_different_orders_keeps_exact_targets(self):
        self.adapter.close()
        self.adapter = SimulatedArs(self.root / "multiple-orders.sqlite")
        other_order = copy.deepcopy(self.orders[0])
        other_order.update(row_id="SIM-ROW-002", order_number="SIM-ORD-002",
                           order_line_id="SIM-RIGA-002", remaining="200")
        self.adapter.seed(self.orders + [other_order])
        receipt = copy.deepcopy(self.receipt)
        other_line = copy.deepcopy(receipt["lines"][0])
        other_line.update(receipt_line="2", order_number="SIM-ORD-002",
                          order_line_id="SIM-RIGA-002")
        other_line["document_quantity"]["value"] = "0.010"
        other_line["received_quantity"]["value"] = "0.010"
        receipt["lines"].append(other_line)
        plan = build_plan(receipt, self.adapter.orders())
        self.approve(plan)
        run_stage(self.ledger, self.adapter, plan, "initial")
        self.assertEqual({"SIM-ROW-001": Decimal("28"), "SIM-ROW-002": Decimal("190")}, self.remaining())
        effect = json.loads(self.adapter.db.execute(
            "SELECT effect FROM artifacts WHERE stage='initial'"
        ).fetchone()[0])
        self.assertEqual(["SIM-ORD-001", "SIM-ORD-002"],
                         [row["order_number"] for row in effect["rows"]])

    def test_repeated_success_rechecks_server_and_does_not_write_again(self):
        self.approve()
        first = run_stage(self.ledger, self.adapter, self.plan, "initial")
        with patch.object(self.adapter, "observe", wraps=self.adapter.observe) as observe:
            with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
                second = run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertTrue(observe.called, "A local VERIFIED record alone must not prove remote state")
        write.assert_not_called()
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(1, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_existing_document_detected_even_after_local_ledger_loss(self):
        self.approve()
        first = run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.ledger.close()
        (self.root / "ledger.sqlite").unlink()
        self.ledger = Ledger(self.root / "ledger.sqlite")
        self.approve()
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            second = run_stage(self.ledger, self.adapter, self.plan, "initial")
        write.assert_not_called()
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(1, self.artifact_count())
        self.assertEqual("VERIFIED", self.stage_status())

    def test_existing_document_with_changed_contents_requires_reconciliation(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        changed = build_plan(self.revised_receipt(quantity="0.010"), self.adapter.orders())
        self.approve(changed)
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, changed, "initial")
        self.assertEqual(1, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_same_document_number_with_changed_date_is_not_silently_duplicated(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        receipt = self.revised_receipt(quantity="0.010")
        receipt["document"]["date"] = "2026-10-13"
        changed = build_plan(receipt, self.adapter.orders())
        self.approve(changed)
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, changed, "initial")
        self.assertEqual(1, self.artifact_count())

    def test_interruption_before_save_requires_readback_then_can_resume(self):
        self.approve()
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial", fault="before_save")
        self.assertEqual("UNKNOWN", self.stage_status())
        self.assertEqual(0, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("100")}, self.remaining())
        result = run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertEqual("verified", result["status"])
        self.assertEqual(1, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_interruption_after_save_recovers_persisted_result_without_rewriting(self):
        self.approve()
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial", fault="after_save")
        self.assertEqual("UNKNOWN", self.stage_status())
        self.assertEqual(1, self.artifact_count())
        self.ledger.close()
        self.adapter.close()
        self.ledger = Ledger(self.root / "ledger.sqlite")
        self.adapter = SimulatedArs(self.root / "ars.sqlite")
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            result = run_stage(self.ledger, self.adapter, self.plan, "initial")
        write.assert_not_called()
        self.assertEqual("verified", result["status"])
        self.assertEqual("VERIFIED", self.stage_status())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_interruption_after_durable_intent_does_not_imply_saved(self):
        self.approve()
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial", fault="after_intent")
        self.assertEqual("INTENT", self.stage_status())
        self.assertEqual(0, self.artifact_count())
        result = run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertEqual("verified", result["status"])
        self.assertEqual(1, self.artifact_count())

    def test_unreadable_outcome_blocks_retry_until_remote_evidence_returns(self):
        self.approve()
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial", fault="readback_unknown")
        self.assertEqual("UNKNOWN", self.stage_status())
        self.assertEqual(1, self.artifact_count())
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            with self.assertRaises(StopOperation):
                run_stage(self.ledger, self.adapter, self.plan, "initial")
        write.assert_not_called()
        self.assertEqual("UNKNOWN", self.stage_status())
        self.adapter.set_health("normal")
        result = run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertEqual("verified", result["status"])
        self.assertEqual(1, self.artifact_count())

    def test_libero_failure_before_save_resumes_without_repeating_initial(self):
        self.approve()
        initial = run_stage(self.ledger, self.adapter, self.plan, "initial")
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "libero", fault="before_save")
        self.assertEqual("VERIFIED", self.stage_status())
        self.assertEqual("UNKNOWN", self.stage_status("libero"))
        self.assertEqual(1, self.artifact_count("initial"))
        self.assertEqual(0, self.artifact_count("libero"))
        result = run_stage(self.ledger, self.adapter, self.plan, "libero")
        self.assertEqual("verified", result["status"])
        self.assertEqual(initial["id"], self.ledger.status(self.plan["digest"])["initial"]["artifact_id"])
        self.assertEqual(1, self.artifact_count("initial"))
        self.assertEqual(1, self.artifact_count("libero"))
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_libero_failure_after_save_recovers_without_repeating_either_stage(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "libero", fault="after_save")
        self.assertEqual("VERIFIED", self.stage_status())
        self.assertEqual("UNKNOWN", self.stage_status("libero"))
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            result = run_stage(self.ledger, self.adapter, self.plan, "libero")
        write.assert_not_called()
        self.assertEqual("LIBERO_SUSPENDED", result["state"])
        self.assertEqual(2, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_libero_cannot_implicitly_create_initial_document(self):
        self.approve()
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "libero")
        self.assertEqual(0, self.artifact_count())

    def test_stale_residual_stops_instead_of_using_previously_approved_snapshot(self):
        self.approve()
        concurrent = build_plan(
            self.revised_receipt(number="SIM-OTHER-RECEIPT", quantity="0.010"),
            self.adapter.orders(),
        )
        self.approve(concurrent)
        run_stage(self.ledger, self.adapter, concurrent, "initial")
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertEqual(1, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("90")}, self.remaining())

    def test_expired_session_or_unexpected_screen_blocks_new_writes(self):
        self.approve()
        for health in ("session_expired", "unexpected_screen"):
            with self.subTest(health=health):
                self.adapter.set_health(health)
                with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
                    with self.assertRaises(StopOperation):
                        run_stage(self.ledger, self.adapter, self.plan, "initial")
                write.assert_not_called()
                self.assertEqual(0, self.artifact_count())
        self.adapter.set_health("normal")
        self.assertEqual("verified", run_stage(self.ledger, self.adapter, self.plan, "initial")["status"])

    def test_local_verified_state_does_not_bypass_failed_remote_read(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.adapter.set_health("session_expired")
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial")
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "libero")
        self.assertEqual(1, self.artifact_count())

    def test_uncertain_save_with_suspended_document_requires_manual_reconciliation(self):
        self.approve()
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "initial", fault="after_save")
        # External state change in the simulator: a document exists, but its
        # final state is not the state required by the approved operation.
        with self.adapter.db:
            self.adapter.db.execute(
                "UPDATE artifacts SET state='DDT_SUSPENDED' WHERE stage='initial'"
            )
        self.assertEqual("UNKNOWN", self.stage_status())
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            with self.assertRaisesRegex(StopOperation, "riconciliare"):
                run_stage(self.ledger, self.adapter, self.plan, "initial")
            with self.assertRaises(StopOperation):
                run_stage(self.ledger, self.adapter, self.plan, "libero")
        write.assert_not_called()
        self.assertEqual("UNKNOWN", self.stage_status())
        self.assertEqual(1, self.artifact_count("initial"))
        self.assertEqual(0, self.artifact_count("libero"))
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_uncertain_libero_with_wrong_parent_is_not_recreated_or_verified(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        with self.assertRaises(StopOperation):
            run_stage(self.ledger, self.adapter, self.plan, "libero", fault="after_save")
        # Correct rows and quantities do not suffice: the parent DDT must match.
        with self.adapter.db:
            self.adapter.db.execute(
                "UPDATE artifacts SET parent_id=? WHERE stage='libero'",
                ("SIM-DDT-OTHER-DOCUMENT",),
            )
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            with self.assertRaisesRegex(StopOperation, "riconciliare"):
                run_stage(self.ledger, self.adapter, self.plan, "libero")
        write.assert_not_called()
        self.assertEqual("VERIFIED", self.stage_status())
        self.assertEqual("UNKNOWN", self.stage_status("libero"))
        self.assertEqual(1, self.artifact_count("initial"))
        self.assertEqual(1, self.artifact_count("libero"))
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_previously_verified_document_removed_remotely_is_not_recreated(self):
        self.approve()
        run_stage(self.ledger, self.adapter, self.plan, "initial")
        # Deletion is an explicit test-only external mutation, not an undo API.
        with self.adapter.db:
            self.adapter.db.execute("DELETE FROM artifacts WHERE stage='initial'")
        self.assertEqual("VERIFIED", self.stage_status())
        with patch.object(self.adapter, "write", wraps=self.adapter.write) as write:
            with self.assertRaisesRegex(StopOperation, "senza ricrearlo"):
                run_stage(self.ledger, self.adapter, self.plan, "initial")
            with self.assertRaises(StopOperation):
                run_stage(self.ledger, self.adapter, self.plan, "libero")
        write.assert_not_called()
        self.assertEqual(0, self.artifact_count())
        self.assertEqual({"SIM-ROW-001": Decimal("28")}, self.remaining())

    def test_run_requires_explicit_confirmation_of_this_exact_plan(self):
        with self.assertRaises((ValueError, StopOperation)):
            run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.approve()
        revised = build_plan(self.revised_receipt(quantity="0.050"), self.adapter.orders())
        with self.assertRaises((ValueError, StopOperation)):
            run_stage(self.ledger, self.adapter, revised, "initial")
        self.assertEqual(0, self.artifact_count())
        self.approve(revised)
        run_stage(self.ledger, self.adapter, revised, "initial")
        self.assertEqual({"SIM-ROW-001": Decimal("50")}, self.remaining())

    def test_confirmation_rejects_wrong_digest(self):
        with self.assertRaises((ValueError, StopOperation)):
            self.ledger.approve(self.plan, "Operatore test", "0" * 64)
        with self.assertRaises((ValueError, StopOperation)):
            run_stage(self.ledger, self.adapter, self.plan, "initial")
        self.assertEqual(0, self.artifact_count())

    def test_tampered_plan_and_resigned_derived_quantity_are_rejected(self):
        self.approve()
        tampered = copy.deepcopy(self.plan)
        tampered["lines"][0]["registration_quantity"]["value"] = "99"
        with self.assertRaises((ValueError, StopOperation)):
            run_stage(self.ledger, self.adapter, tampered, "initial")
        tampered["digest"] = fingerprint({key: value for key, value in tampered.items() if key != "digest"})
        with self.assertRaises((ValueError, StopOperation)):
            self.approve(tampered)
        self.assertEqual(0, self.artifact_count())

    def test_discordant_code_plan_cannot_be_confirmed_or_executed(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["lines"][0]["supplier_code"] = "SIM-DISCORDANT"
        blocked = build_plan(receipt, self.adapter.orders())
        self.assertFalse(blocked["ready"])
        with self.assertRaises((ValueError, StopOperation)):
            self.approve(blocked)
        with self.assertRaises((ValueError, StopOperation)):
            run_stage(self.ledger, self.adapter, blocked, "initial")
        self.assertEqual(0, self.artifact_count())

    def test_real_adapter_is_rejected_before_any_access(self):
        class RealAdapter:
            environment = "real"

            def observe(self, *args, **kwargs):
                raise AssertionError("A real adapter must not be contacted by this version")

            def write(self, *args, **kwargs):
                raise AssertionError("A real adapter must not receive writes")

        self.approve()
        with self.assertRaises((ValueError, StopOperation)):
            run_stage(self.ledger, RealAdapter(), self.plan, "initial")
        self.assertEqual(0, self.artifact_count())


if __name__ == "__main__":
    unittest.main()
