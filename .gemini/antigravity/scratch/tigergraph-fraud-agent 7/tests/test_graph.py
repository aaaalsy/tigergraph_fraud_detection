"""
Unit Tests for TigerGraph Connector & Graph Algorithms
"""

import unittest
from src.graph.tigergraph_connector import TigerGraphConnector

class TestTigerGraphConnector(unittest.TestCase):
    def setUp(self):
        self.connector = TigerGraphConnector(mode="embedded")
        
        # Seed test nodes
        self.connector.add_vertex("Customer", "CUST_TEST", {"full_name": "Alice Tester"})
        self.connector.add_vertex("Account", "ACC_TEST_1", {"balance": 500.0, "credit_limit": 5000.0, "status": "ACTIVE"})
        self.connector.add_vertex("Account", "ACC_TEST_2", {"balance": 200.0, "credit_limit": 5000.0, "status": "ACTIVE"})
        self.connector.add_vertex("Device", "DEV_TEST", {"device_fingerprint": "FP_TEST_123", "is_proxy_or_vpn": True})
        self.connector.add_vertex("Transaction", "TXN_TEST_1", {"amount": 2500.0, "risk_score": 0.85, "distance_from_home": 1500.0})
        
        # Seed test edges
        self.connector.add_edge("Customer", "CUST_TEST", "OWNS_ACCOUNT", "Account", "ACC_TEST_1")
        self.connector.add_edge("Transaction", "TXN_TEST_1", "DEBITED_FROM", "Account", "ACC_TEST_1")
        self.connector.add_edge("Transaction", "TXN_TEST_1", "ORIGINATED_FROM_DEVICE", "Device", "DEV_TEST")
        self.connector.add_edge("Account", "ACC_TEST_1", "TRANSFERRED_TO", "Account", "ACC_TEST_2", {"amount": 2000.0, "timestamp": "2026-06-01"})

    def test_vertex_retrieval(self):
        cust = self.connector.get_vertex("Customer", "CUST_TEST")
        self.assertIsNotNone(cust)
        self.assertEqual(cust["full_name"], "Alice Tester")

    def test_fund_flow_trace(self):
        flow = self.connector.trace_fund_flow("ACC_TEST_1", max_depth=2)
        self.assertEqual(len(flow["transfer_paths"]), 1)
        self.assertEqual(flow["total_volume_diverted"], 2000.0)
        self.assertIn("ACC_TEST_2", flow["implicated_accounts"])

    def test_ato_subgraph_detection(self):
        ato = self.connector.account_takeover_subgraph("TXN_TEST_1")
        self.assertTrue(ato["new_device_detected"])
        self.assertTrue(ato["proxy_or_tor_ip"])
        self.assertEqual(ato["distance_from_home_km"], 1500.0)
        self.assertTrue(ato["is_ato_suspicious"])

    def test_subgraph_extraction(self):
        sub = self.connector.fetch_case_subgraph("TXN_TEST_1", hops=2)
        self.assertGreater(sub["total_nodes"], 2)
        self.assertGreater(sub["total_edges"], 1)

if __name__ == "__main__":
    unittest.main()
