"""
Unit Tests for Benchmark Answer Files
Verifies that all 20 answer files strictly comply with the hackathon submission format.
"""

import os
import json
import unittest

class TestBenchmarkDeliverables(unittest.TestCase):
    def setUp(self):
        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "output", "cases")

    def test_all_20_case_answers_exist(self):
        for i in range(1, 21):
            filename = f"case_{i:02d}_answer.json"
            path = os.path.join(self.output_dir, filename)
            self.assertTrue(os.path.exists(path), f"Missing required deliverable: {filename}")

    def test_case_answer_schema_compliance(self):
        for i in range(1, 21):
            filename = f"case_{i:02d}_answer.json"
            path = os.path.join(self.output_dir, filename)
            with open(path, "r") as f:
                data = json.load(f)

            # 1. Internal investigation record, evidence, findings, decisions
            self.assertIn("case_summary", data)
            self.assertIn("investigation_record", data)
            self.assertIn("graph_findings", data["investigation_record"])
            self.assertIn("policy_rules_evaluated", data["investigation_record"])
            self.assertIn("case_memory_precedents", data["investigation_record"])

            # 2. Case written to graph
            self.assertIn("graph_persistence", data)
            self.assertTrue(data["graph_persistence"]["written_to_tigergraph"])

            # 3. Next best action before & after additional evidence
            self.assertIn("next_best_action", data)
            self.assertIn("before_additional_evidence", data["next_best_action"])
            self.assertIn("after_additional_evidence", data["next_best_action"])
            self.assertIn("required_approval_route", data["next_best_action"]["before_additional_evidence"])
            self.assertIn("required_approval_route", data["next_best_action"]["after_additional_evidence"])

            # 4. Suspicious activity report when required by policy
            self.assertIn("suspicious_activity_report", data)
            amt = data["case_summary"]["amount"]
            if amt >= 5000.0 and "FRAUD" in data["case_summary"]["status"]:
                self.assertIsInstance(data["suspicious_activity_report"], dict, f"SAR required for {filename}")
                self.assertIn("fincen_narrative", data["suspicious_activity_report"])

if __name__ == "__main__":
    unittest.main()
