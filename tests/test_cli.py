"""Prova della CLI pubblica tramite processi separati, con file temporanei."""

import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from ufp_bolle.storage import read_json, single_operator


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.sim = self.folder / "sim.sqlite"
        self.state = self.folder / "state.sqlite"
        self.plan = self.folder / "plan.json"

    def cli(self, *args, code=0):
        result = subprocess.run([sys.executable, "-m", "ufp_bolle", *map(str, args)],
                                cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def prepare(self):
        self.cli("sim-init", "--orders", ROOT / "examples/orders.json", "--db", self.sim)
        result = self.cli("plan", "--receipt", ROOT / "examples/receipt.json", "--sim-db", self.sim, "--out", self.plan)
        self.assertIn("72 KG", result.stdout)
        plan = read_json(self.plan)
        self.cli("confirm", "--plan", self.plan, "--state", self.state,
                 "--digest", plan["digest"], "--operator", "TEST")
        return plan

    def run_phase(self, stage, *args, code=0):
        return self.cli("run", "--plan", self.plan, "--state", self.state,
                        "--sim-db", self.sim, "--stage", stage, *args, code=code)

    def test_cli_persistent_recovery_after_lost_response_and_separate_libero(self):
        plan = self.prepare()
        self.run_phase("initial", "--fault", "after_save", code=2)
        self.run_phase("initial")
        self.run_phase("libero", "--fault", "after_save", code=2)
        self.run_phase("libero")
        result = self.cli("status", "--state", self.state, "--digest", plan["digest"])
        status = json.loads(result.stdout)
        self.assertEqual(status["initial"]["status"], "VERIFIED")
        self.assertEqual(status["libero"]["status"], "VERIFIED")
        self.assertEqual(status["palmare"], "NON_VERIFICATO")
        with sqlite3.connect(self.sim) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM artifacts").fetchone()[0], 2)
            row = json.loads(db.execute("SELECT payload FROM orders").fetchone()[0])
            self.assertEqual(row["remaining"], "28")

    def test_cli_refuses_plan_overwrite_and_seed_reset(self):
        self.prepare()
        before = self.plan.read_bytes()
        self.cli("plan", "--receipt", ROOT / "examples/receipt.json", "--orders", ROOT / "examples/orders.json", "--out", self.plan, code=2)
        self.assertEqual(before, self.plan.read_bytes())
        self.cli("sim-init", "--orders", ROOT / "examples/orders.json", "--db", self.sim, code=2)

    def test_cli_blocked_plan_is_reviewable_but_not_confirmable(self):
        receipt = read_json(ROOT / "examples/receipt.json")
        receipt["lines"][0]["supplier_code"] = "CODICE-DISCORDANTE"
        source = self.folder / "bad.json"
        source.write_text(json.dumps(receipt), encoding="utf-8")
        result = self.cli("plan", "--receipt", source, "--orders", ROOT / "examples/orders.json", "--out", self.plan, code=2)
        self.assertIn("CODE_MISMATCH", result.stdout)
        plan = read_json(self.plan)
        self.cli("confirm", "--plan", self.plan, "--state", self.state,
                 "--digest", plan["digest"], "--operator", "TEST", code=2)

    def test_cli_refuses_shared_database_roles_without_artifacts(self):
        self.prepare()
        self.cli("run", "--plan", self.plan, "--state", self.sim,
                 "--sim-db", self.sim, "--stage", "initial", code=2)
        with sqlite3.connect(self.sim) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM artifacts").fetchone()[0], 0)

    def test_second_process_lock_blocks_writes_and_preserves_state(self):
        self.prepare()
        with single_operator(self.state):
            result = self.run_phase("initial", code=2)
            self.assertIn("lock", result.stderr)
        self.run_phase("initial")

    def test_json_accepts_windows_bom_but_rejects_duplicate_keys(self):
        source = self.folder / "windows.json"
        source.write_text('{"value":"0.072"}', encoding="utf-8-sig")
        self.assertEqual(read_json(source), {"value": "0.072"})
        source.write_text('{"value":"0.072","value":"72"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            read_json(source)


if __name__ == "__main__":
    unittest.main()
