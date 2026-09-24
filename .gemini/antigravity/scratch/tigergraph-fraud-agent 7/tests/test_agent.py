"""
Unit Tests for Autonomous AI Fraud Investigation Agent
"""

import unittest
from src.graph.tigergraph_connector import TigerGraphConnector
from src.agent.investigation_agent import InvestigationAgent
from src.agent.policy_governance import PolicyGovernance
from src.benchmark.benchmark_dataset import seed_graph_with_benchmark_data

class TestInvestigationAgent(unittest.TestCase):
    def setUp(self):
        self.connector = TigerGraphConnector(mode="embedded")
        seed_graph_with_benchmark_data(self.connector)
        self.agent = InvestigationAgent(self.connector)
        self.governance = PolicyGovernance()

    def test_policy_governance_routing(self):
        # Tier 1 Autonomous
        gov1 = self.governance.evaluate_action_governance("TEMPORARY_24H_HOLD")
        self.assertEqual(gov1["tier"], "TIER_1_AUTO")
        self.assertFalse(gov1["requires_human_approval"])

        # Tier 2 Analyst Sign-off
        gov2 = self.governance.evaluate_action_governance("BLOCK_CARD")
        self.assertEqual(gov2["tier"], "TIER_2_ANALYST")
        self.assertTrue(gov2["requires_human_approval"])

        # Tier 3 Senior Compliance
        gov3 = self.governance.evaluate_action_governance("FILE_SAR_REPORT")
        self.assertEqual(gov3["tier"], "TIER_3_SENIOR_COMPLIANCE")
        self.assertTrue(gov3["requires_human_approval"])

    def test_investigation_flow_with_repudiation(self):
        case_input = {
            "case_id": "TEST_CASE_ATO",
            "trigger_type": "MODEL_SCORE",
            "customer_id": "CUST_5011",
            "transaction": {
                "transaction_id": "TXN_80101",
                "account_id": "ACC_2011",
                "customer_id": "CUST_5011",
                "amount": 3450.00,
                "risk_score": 0.89,
                "channel": "WEB",
                "distance_from_home": 1250.0
            }
        }
        answer = self.agent.run_investigation(case_input, simulated_evidence_response={
            "step_up_result": "FAILED_OR_EXPIRED",
            "customer_confirmation": "CONFIRMED_FRAUD"
        })

        self.assertEqual(answer["case_summary"]["status"], "CLOSED_FRAUD")
        self.assertIn("BLOCK_CARD", answer["next_best_action"]["after_additional_evidence"]["recommended_action"])
        self.assertTrue(answer["graph_persistence"]["written_to_tigergraph"])

    def test_investigation_flow_with_validation(self):
        case_input = {
            "case_id": "TEST_CASE_BENIGN",
            "trigger_type": "MODEL_SCORE",
            "customer_id": "CUST_5011",
            "transaction": {
                "transaction_id": "TXN_80101",
                "account_id": "ACC_2011",
                "customer_id": "CUST_5011",
                "amount": 1200.00,
                "risk_score": 0.65,
                "channel": "WEB",
                "distance_from_home": 1250.0
            }
        }
        answer = self.agent.run_investigation(case_input, simulated_evidence_response={
            "step_up_result": "PASSED",
            "customer_confirmation": "LEGITIMATE_PURCHASE"
        })

        self.assertEqual(answer["case_summary"]["status"], "CLOSED_CLEARED")
        self.assertIn("ALLOW_TRANSACTION", answer["next_best_action"]["after_additional_evidence"]["recommended_action"])

if __name__ == "__main__":
    unittest.main()
