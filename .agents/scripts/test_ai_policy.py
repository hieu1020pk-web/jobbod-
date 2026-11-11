"""Smoke/negative tests for the declarative rules (stdlib unittest)."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ai_policy", Path(__file__).with_name("ai_policy.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
POLICY = json.loads((ROOT / "policies/company.policy.json").read_text())
SAMPLE = json.loads((ROOT / "examples/task.standard.example.json").read_text())


class TestPolicy(unittest.TestCase):
    def test_policy_json(self):
        self.assertEqual(m.validate_company(POLICY), [])

    def test_project_template_fails_closed(self):
        p = json.loads((ROOT / "project/project.policy.json").read_text())
        self.assertTrue(m.validate_project(p))

    def test_example_standard_passes(self):
        errors, tier, checks = m.validate_task(SAMPLE, POLICY)
        self.assertEqual(errors, [])
        self.assertEqual(tier, "STANDARD")
        self.assertIn("business_regression", checks)

    def test_fast_docs(self):
        t = copy.deepcopy(SAMPLE)
        t["risk_tier"] = "FAST"
        t["change_types"] = ["documentation"]
        t["required_checks"] = ["docs_check"]
        t["review"]["plan_review_reference"] = ""
        errors, tier, checks = m.validate_task(t, POLICY)
        self.assertEqual(errors, [])
        self.assertEqual((tier, checks), ("FAST", ["docs_check"]))

    def test_critical_signal_must_escalate(self):
        t = copy.deepcopy(SAMPLE)
        t["risk_signals"] = ["payment"]
        errors, tier, checks = m.validate_task(t, POLICY)
        self.assertEqual(tier, "CRITICAL")
        self.assertTrue(any("thấp hơn" in e for e in errors))
        self.assertIn("sast", checks)

    def test_critical_evidence_required(self):
        t = copy.deepcopy(SAMPLE)
        t["risk_tier"] = "CRITICAL"
        t["risk_signals"] = ["payment"]
        t["change_types"] = ["payment"]
        t["required_checks"] = ["build", "lint", "unit", "sast", "sca", "secrets_scan", "payment_negative", "idempotency_test", "security_review_check"]
        errors, tier, _ = m.validate_task(t, POLICY)
        self.assertEqual(tier, "CRITICAL")
        self.assertTrue(any("rollback_or_restore_plan" in e for e in errors))

    def test_outside_scope_and_governance_protected(self):
        files = ["src/sample/ok.cs", "tests/sample/test.cs", ".agents/rules/00-core.md", "src/other/bad.cs"]
        errors = m.validate_paths(files, SAMPLE, POLICY)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("Protected" in e for e in errors))

    def test_glob_traversal_rejected(self):
        t = copy.deepcopy(SAMPLE)
        t["scope"]["allowed_paths"] = ["**", "../etc/**"]
        errors, _, _ = m.validate_task(t, POLICY)
        self.assertTrue(any("quá rộng/không an toàn" in e for e in errors))

    def test_missing_gate_and_budget(self):
        t = copy.deepcopy(SAMPLE)
        t["required_checks"].remove("unit")
        errors, _, _ = m.validate_task(t, POLICY)
        self.assertTrue(any("unit" in e for e in errors))
        # Test with custom policy having explicit fix budget
        custom_policy = copy.deepcopy(POLICY)
        custom_policy["execution"]["maximum_code_fix_attempts_per_gate_failure"] = 2
        t["execution"]["fix_attempts_used"] = 5
        errors_budget, _, _ = m.validate_task(t, custom_policy)
        self.assertTrue(any("fix budget" in e for e in errors_budget))

    def test_critical_complete_manifest_passes_structural_validation(self):
        t = copy.deepcopy(SAMPLE)
        t["risk_tier"] = "CRITICAL"
        t["risk_signals"] = ["payment"]
        t["change_types"] = ["payment"]
        t["required_checks"] = ["build", "lint", "unit", "sast", "sca", "secrets_scan", "payment_negative", "idempotency_test", "security_review_check"]
        t["review"]["security_review_reference"] = "EXAMPLE-SECURITY-REVIEW"
        t["approval"]["human_change_approval_reference"] = "EXAMPLE-HUMAN-APPROVAL"
        t["release"]["rollback_or_restore_plan"] = "Example rollback strategy; not production approved"
        errors, tier, _ = m.validate_task(t, POLICY)
        self.assertEqual(tier, "CRITICAL")
        self.assertEqual(errors, [])

    def test_unknown_check_id_is_rejected(self):
        t = copy.deepcopy(SAMPLE)
        t["required_checks"].append("somthing_typo")
        errors, _, _ = m.validate_task(t, POLICY)
        self.assertTrue(any("unknown check ID" in e for e in errors))

    def test_unresolved_unknowns_blocks(self):
        t = copy.deepcopy(SAMPLE)
        t["risk_assessment"]["unresolved_unknowns"] = ["unknown data retention requirement"]
        errors, _, _ = m.validate_task(t, POLICY)
        self.assertTrue(any("unresolved_unknowns" in e for e in errors))

    def test_solo_dev_allowed_in_all_tiers_including_critical(self):
        t = copy.deepcopy(SAMPLE)
        t["owners"]["independent_reviewer"] = t["owners"]["executor"]
        errors, tier, _ = m.validate_task(t, POLICY)
        self.assertEqual(errors, [])
        # Now elevate to CRITICAL - same reviewer is completely allowed
        t["risk_tier"] = "CRITICAL"
        t["risk_signals"] = ["payment"]
        t["change_types"] = ["payment"]
        t["required_checks"] = ["build", "lint", "unit", "sast", "sca", "secrets_scan", "payment_negative", "idempotency_test", "security_review_check"]
        t["release"]["rollback_or_restore_plan"] = "ROLLBACK-1"
        errors, _, _ = m.validate_task(t, POLICY)
        self.assertEqual(errors, [])
    def test_lean_task_contract_string_ac_and_no_execution_block(self):
        t = copy.deepcopy(SAMPLE)
        t["acceptance_criteria"] = ["AC-01: Lean string criteria format"]
        del t["execution"]
        t["scope"]["out_of_scope"] = []
        errors, tier, _ = m.validate_task(t, POLICY)
        self.assertEqual(errors, [])

    def test_fast_new_change_types(self):
        for ct, check in [("config_tweak", "build"), ("test_update", "unit"), ("styling_asset", "lint")]:
            t = copy.deepcopy(SAMPLE)
            t["risk_tier"] = "FAST"
            t["change_types"] = [ct]
            t["required_checks"] = [check]
            errors, tier, checks = m.validate_task(t, POLICY)
            self.assertEqual(errors, [])
            self.assertEqual(tier, "FAST")
            self.assertIn(check, checks)



# Additional integration tests are appended as a separate test case to exercise real Git diff.
import os
import subprocess
import tempfile


class TestGitIntegration(unittest.TestCase):
    def _git(self, repo, *args):
        p = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
        return p.stdout.strip()

    def test_scope_with_real_git_history(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._git(repo, "init", "-q")
            self._git(repo, "config", "user.email", "example@example.invalid")
            self._git(repo, "config", "user.name", "Test")
            (repo / "src/sample").mkdir(parents=True)
            (repo / "src/sample/app.txt").write_text("base\n")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-qm", "init")
            base = self._git(repo, "rev-parse", "HEAD")
            (repo / "src/sample/app.txt").write_text("changed\n")
            self._git(repo, "commit", "-qam", "change")
            head = self._git(repo, "rev-parse", "HEAD")
            files = m.git_changed_files(repo, base, head)
            self.assertEqual(files, ["src/sample/app.txt"])
            self.assertEqual(m.validate_paths(files, SAMPLE, POLICY), [])
            (repo / ".agents/rules").mkdir(parents=True)
            (repo / ".agents/rules/core.md").write_text("changed company policy\n")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-qm", "governance")
            files = m.git_changed_files(repo, base, self._git(repo, "rev-parse", "HEAD"))
            self.assertTrue(any("Protected" in e for e in m.validate_paths(files, SAMPLE, POLICY)))


class TestCrossService(unittest.TestCase):
    def test_2_service_change_requires_integration(self):
        t = copy.deepcopy(SAMPLE)
        t["impacted_services"] = ["catalog", "inventory"]
        errors, tier, required = m.validate_task(t, POLICY)
        self.assertEqual(tier, "STANDARD")
        self.assertIn("cross_service_integration", required)
        self.assertTrue(any("cross_service_integration" in e for e in errors))

    def test_cross_service_with_gate_passes(self):
        t = copy.deepcopy(SAMPLE)
        t["impacted_services"] = ["catalog", "inventory"]
        t["required_checks"].append("cross_service_integration")
        errors, _, _ = m.validate_task(t, POLICY)
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
