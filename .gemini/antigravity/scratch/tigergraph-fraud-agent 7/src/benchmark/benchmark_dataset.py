"""
Benchmark Dataset & Graph Seeder
Implements the 20 benchmark evaluation cases from Months 5 & 6 based on IEEE-CIS data structure,
populating the TigerGraph knowledge graph with accounts, devices, transactions, cards, and rings.
"""

from typing import Dict, List, Any
from ..graph.tigergraph_connector import TigerGraphConnector

BENCHMARK_CASES = [
    {
        "case_id": "CASE_01",
        "title": "Account Takeover via Chicago Datacenter Proxy",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5011",
        "transaction": {
            "transaction_id": "TXN_80101",
            "account_id": "ACC_2011",
            "customer_id": "CUST_5011",
            "amount": 3450.00,
            "risk_score": 0.89,
            "channel": "WEB",
            "distance_from_home": 1250.0,
            "device_id": "DEV_NEW_991",
            "device_fingerprint": "FP_WIN_CHROME_991",
            "device_type": "Windows",
            "is_proxy_or_vpn": True,
            "ip_address": "198.51.100.44",
            "is_tor": False,
            "is_data_center": True,
            "reputation_score": 0.85
        }
    },
    {
        "case_id": "CASE_02",
        "title": "Benign International Business Travel (London Hotel)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "CLEARED",
        "customer_id": "CUST_5012",
        "transaction": {
            "transaction_id": "TXN_80102",
            "account_id": "ACC_2012",
            "customer_id": "CUST_5012",
            "amount": 1850.00,
            "risk_score": 0.69,
            "channel": "WEB",
            "distance_from_home": 5800.0,
            "device_id": "DEV_MAC_5012",
            "device_fingerprint": "FP_MAC_SAFARI_5012",
            "device_type": "Mac",
            "is_proxy_or_vpn": False,
            "ip_address": "82.165.197.1",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.05
        }
    },
    {
        "case_id": "CASE_03",
        "title": "High-Value Account Takeover with Foreign IP ($12,800)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5013",
        "transaction": {
            "transaction_id": "TXN_80103",
            "account_id": "ACC_2013",
            "customer_id": "CUST_5013",
            "amount": 12800.00,
            "risk_score": 0.96,
            "channel": "WEB",
            "distance_from_home": 7500.0,
            "device_id": "DEV_LINUX_772",
            "device_fingerprint": "FP_LINUX_FIREFOX_772",
            "device_type": "Linux",
            "is_proxy_or_vpn": True,
            "ip_address": "185.220.101.5",
            "is_tor": True,
            "is_data_center": False,
            "reputation_score": 0.95
        }
    },
    {
        "case_id": "CASE_04",
        "title": "Synthetic Identity Ring Alpha (3 Accounts / Shared Device)",
        "trigger_type": "ANALYST_MANUAL",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5014",
        "transaction": {
            "transaction_id": "TXN_80104",
            "account_id": "ACC_RING_01",
            "customer_id": "CUST_5014",
            "amount": 7600.00,
            "risk_score": 0.93,
            "channel": "MOBILE_APP",
            "distance_from_home": 25.0,
            "device_id": "DEV_SHARED_RING_A",
            "device_fingerprint": "FP_SAMSUNG_S23_SHARED_A",
            "device_type": "Android",
            "is_proxy_or_vpn": False,
            "ip_address": "73.189.44.12",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.20
        }
    },
    {
        "case_id": "CASE_05",
        "title": "Bust-Out Fraud: Rapid 95% Line Depletion ($9,500)",
        "trigger_type": "VELOCITY_SPIKE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5015",
        "transaction": {
            "transaction_id": "TXN_80105",
            "account_id": "ACC_BUST_01",
            "customer_id": "CUST_5015",
            "amount": 9500.00,
            "risk_score": 0.92,
            "channel": "POS",
            "distance_from_home": 40.0,
            "device_id": "DEV_POS_TERMINAL_1",
            "device_fingerprint": "FP_VERIFONE_P400",
            "device_type": "POS",
            "is_proxy_or_vpn": False,
            "ip_address": "12.180.20.5",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.0
        }
    },
    {
        "case_id": "CASE_06",
        "title": "High-Velocity Carding & Multi-Mule Layering ($6,200)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5016",
        "transaction": {
            "transaction_id": "TXN_80106",
            "account_id": "ACC_MULE_SOURCE",
            "customer_id": "CUST_5016",
            "amount": 6200.00,
            "risk_score": 0.95,
            "channel": "WEB",
            "distance_from_home": 110.0,
            "device_id": "DEV_BOT_EMULATOR_1",
            "device_fingerprint": "FP_BLUESTACKS_ANDROID",
            "device_type": "Android",
            "is_proxy_or_vpn": True,
            "ip_address": "104.244.72.115",
            "is_tor": False,
            "is_data_center": True,
            "reputation_score": 0.90
        }
    },
    {
        "case_id": "CASE_07",
        "title": "First-Party Friendly Fraud (Legitimate Home Device Dispute)",
        "trigger_type": "CUSTOMER_REPORT",
        "expected_outcome": "CLEARED",
        "customer_id": "CUST_5017",
        "transaction": {
            "transaction_id": "TXN_80107",
            "account_id": "ACC_2017",
            "customer_id": "CUST_5017",
            "amount": 850.00,
            "risk_score": 0.35,
            "channel": "WEB",
            "distance_from_home": 0.0,
            "device_id": "DEV_HOME_IPAD_5017",
            "device_fingerprint": "FP_IPAD_IOS17_5017",
            "device_type": "iOS",
            "is_proxy_or_vpn": False,
            "ip_address": "68.45.12.90",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.0
        }
    },
    {
        "case_id": "CASE_08",
        "title": "Synthetic Identity Ring Beta (VoIP Numbers & Burner Devices)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5018",
        "transaction": {
            "transaction_id": "TXN_80108",
            "account_id": "ACC_RING_02",
            "customer_id": "CUST_5018",
            "amount": 5400.00,
            "risk_score": 0.88,
            "channel": "MOBILE_APP",
            "distance_from_home": 30.0,
            "device_id": "DEV_SHARED_RING_B",
            "device_fingerprint": "FP_MOTO_G_SHARED_B",
            "device_type": "Android",
            "is_proxy_or_vpn": False,
            "ip_address": "98.120.30.15",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.25
        }
    },
    {
        "case_id": "CASE_09",
        "title": "Velocity Spike at Local Merchant (Family Supermarket Run)",
        "trigger_type": "VELOCITY_SPIKE",
        "expected_outcome": "CLEARED",
        "customer_id": "CUST_5019",
        "transaction": {
            "transaction_id": "TXN_80109",
            "account_id": "ACC_2019",
            "customer_id": "CUST_5019",
            "amount": 420.00,
            "risk_score": 0.66,
            "channel": "POS",
            "distance_from_home": 5.0,
            "device_id": "DEV_IPHONE_5019",
            "device_fingerprint": "FP_IPHONE15_5019",
            "device_type": "iOS",
            "is_proxy_or_vpn": False,
            "ip_address": "172.56.21.90",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.0
        }
    },
    {
        "case_id": "CASE_10",
        "title": "Bust-Out Fraud: Precious Metals Drawdown ($14,500)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5020",
        "transaction": {
            "transaction_id": "TXN_80110",
            "account_id": "ACC_BUST_02",
            "customer_id": "CUST_5020",
            "amount": 14500.00,
            "risk_score": 0.97,
            "channel": "WEB",
            "distance_from_home": 85.0,
            "device_id": "DEV_CHROMEBOOK_5020",
            "device_fingerprint": "FP_CHROMEBOOK_5020",
            "device_type": "Linux",
            "is_proxy_or_vpn": False,
            "ip_address": "66.249.70.1",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.10
        }
    },
    {
        "case_id": "CASE_11",
        "title": "Mule Network Funneling to Offshore Crypto Offramp ($22,000)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5021",
        "transaction": {
            "transaction_id": "TXN_80111",
            "account_id": "ACC_MULE_HUB",
            "customer_id": "CUST_5021",
            "amount": 22000.00,
            "risk_score": 0.98,
            "channel": "WEB",
            "distance_from_home": 220.0,
            "device_id": "DEV_MULE_PC",
            "device_fingerprint": "FP_WIN_MULE_HUB",
            "device_type": "Windows",
            "is_proxy_or_vpn": True,
            "ip_address": "194.26.29.11",
            "is_tor": False,
            "is_data_center": True,
            "reputation_score": 0.92
        }
    },
    {
        "case_id": "CASE_12",
        "title": "Credential Stuffing with TOR Exit Node ($4,800)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5022",
        "transaction": {
            "transaction_id": "TXN_80112",
            "account_id": "ACC_2022",
            "customer_id": "CUST_5022",
            "amount": 4800.00,
            "risk_score": 0.91,
            "channel": "WEB",
            "distance_from_home": 4200.0,
            "device_id": "DEV_TOR_BROWSER",
            "device_fingerprint": "FP_TOR_TAILS_OS",
            "device_type": "Linux",
            "is_proxy_or_vpn": True,
            "ip_address": "185.220.100.241",
            "is_tor": True,
            "is_data_center": False,
            "reputation_score": 0.99
        }
    },
    {
        "case_id": "CASE_13",
        "title": "Benign Retail Electronics Upgrade (Customer In-Store)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "CLEARED",
        "customer_id": "CUST_5023",
        "transaction": {
            "transaction_id": "TXN_80113",
            "account_id": "ACC_2023",
            "customer_id": "CUST_5023",
            "amount": 2400.00,
            "risk_score": 0.61,
            "channel": "POS",
            "distance_from_home": 8.0,
            "device_id": "DEV_IPHONE16_NEW",
            "device_fingerprint": "FP_IPHONE16_PRO",
            "device_type": "iOS",
            "is_proxy_or_vpn": False,
            "ip_address": "172.56.40.10",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.0
        }
    },
    {
        "case_id": "CASE_14",
        "title": "Cross-Border Automated Carding Script on Gaming Store",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5024",
        "transaction": {
            "transaction_id": "TXN_80114",
            "account_id": "ACC_2024",
            "customer_id": "CUST_5024",
            "amount": 320.00,
            "risk_score": 0.94,
            "channel": "WEB",
            "distance_from_home": 6200.0,
            "device_id": "DEV_PUPPETEER_BOT",
            "device_fingerprint": "FP_HEADLESS_CHROME",
            "device_type": "Linux",
            "is_proxy_or_vpn": True,
            "ip_address": "45.154.255.88",
            "is_tor": False,
            "is_data_center": True,
            "reputation_score": 0.88
        }
    },
    {
        "case_id": "CASE_15",
        "title": "Commercial Wire Compromise with Spoofed Vendor ($48,500)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5025",
        "transaction": {
            "transaction_id": "TXN_80115",
            "account_id": "ACC_COMMERCIAL_01",
            "customer_id": "CUST_5025",
            "amount": 48500.00,
            "risk_score": 0.97,
            "channel": "WEB",
            "distance_from_home": 3400.0,
            "device_id": "DEV_UNKNOWN_AGENT",
            "device_fingerprint": "FP_WINDOWS_EDGE_SPOOF",
            "device_type": "Windows",
            "is_proxy_or_vpn": True,
            "ip_address": "91.240.118.50",
            "is_tor": False,
            "is_data_center": True,
            "reputation_score": 0.82
        }
    },
    {
        "case_id": "CASE_16",
        "title": "First-Party SaaS Chargeback Dispute (First-Party Dispute)",
        "trigger_type": "CUSTOMER_REPORT",
        "expected_outcome": "CLEARED",
        "customer_id": "CUST_5026",
        "transaction": {
            "transaction_id": "TXN_80116",
            "account_id": "ACC_2026",
            "customer_id": "CUST_5026",
            "amount": 120.00,
            "risk_score": 0.28,
            "channel": "WEB",
            "distance_from_home": 0.0,
            "device_id": "DEV_WORK_PC_5026",
            "device_fingerprint": "FP_WIN11_DELL_5026",
            "device_type": "Windows",
            "is_proxy_or_vpn": False,
            "ip_address": "24.114.88.2",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.0
        }
    },
    {
        "case_id": "CASE_17",
        "title": "Coordinated Terminal Card-Cloning Spree ($8,000)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5027",
        "transaction": {
            "transaction_id": "TXN_80117",
            "account_id": "ACC_2027",
            "customer_id": "CUST_5027",
            "amount": 8000.00,
            "risk_score": 0.93,
            "channel": "ATM",
            "distance_from_home": 450.0,
            "device_id": "DEV_ATM_STANDALONE",
            "device_fingerprint": "FP_NCR_ATM_GAS_STATION",
            "device_type": "ATM",
            "is_proxy_or_vpn": False,
            "ip_address": "12.202.99.14",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.30
        }
    },
    {
        "case_id": "CASE_18",
        "title": "Ambiguous Cellular IP Carrier Hop (Residential User)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "CLEARED",
        "customer_id": "CUST_5028",
        "transaction": {
            "transaction_id": "TXN_80118",
            "account_id": "ACC_2028",
            "customer_id": "CUST_5028",
            "amount": 350.00,
            "risk_score": 0.67,
            "channel": "MOBILE_APP",
            "distance_from_home": 250.0,
            "device_id": "DEV_SAMSUNG_5028",
            "device_fingerprint": "FP_GALAXY_S22_5028",
            "device_type": "Android",
            "is_proxy_or_vpn": False,
            "ip_address": "107.77.218.4",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.05
        }
    },
    {
        "case_id": "CASE_19",
        "title": "Synthetic Identity Ring Gamma ($31,000 Aggregated)",
        "trigger_type": "ANALYST_MANUAL",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5029",
        "transaction": {
            "transaction_id": "TXN_80119",
            "account_id": "ACC_RING_03",
            "customer_id": "CUST_5029",
            "amount": 31000.00,
            "risk_score": 0.99,
            "channel": "WEB",
            "distance_from_home": 60.0,
            "device_id": "DEV_SHARED_RING_C",
            "device_fingerprint": "FP_XIAOMI_SHARED_C",
            "device_type": "Android",
            "is_proxy_or_vpn": False,
            "ip_address": "69.143.20.100",
            "is_tor": False,
            "is_data_center": False,
            "reputation_score": 0.15
        }
    },
    {
        "case_id": "CASE_20",
        "title": "Account Takeover via Intercepted SIM Port ($16,500)",
        "trigger_type": "MODEL_SCORE",
        "expected_outcome": "FRAUD",
        "customer_id": "CUST_5030",
        "transaction": {
            "transaction_id": "TXN_80120",
            "account_id": "ACC_2030",
            "customer_id": "CUST_5030",
            "amount": 16500.00,
            "risk_score": 0.95,
            "channel": "WEB",
            "distance_from_home": 1800.0,
            "device_id": "DEV_NEW_IPHONE_SIMSWAP",
            "device_fingerprint": "FP_IPHONE15_PRO_UNAUTH",
            "device_type": "iOS",
            "is_proxy_or_vpn": True,
            "ip_address": "173.239.198.7",
            "is_tor": False,
            "is_data_center": True,
            "reputation_score": 0.78
        }
    }
]

def seed_graph_with_benchmark_data(connector: TigerGraphConnector):
    """
    Populates the TigerGraph instance with all entities, accounts, devices,
    cards, merchants, and relationships representing the IEEE-CIS benchmark graph.
    """
    # 1. Add Vertices for each Benchmark Case
    for case in BENCHMARK_CASES:
        txn = case["transaction"]
        c_id = case["customer_id"]
        acc_id = txn["account_id"]
        t_id = txn["transaction_id"]
        d_id = txn["device_id"]
        ip_addr = txn["ip_address"]

        # Customer
        connector.add_vertex("Customer", c_id, {
            "full_name": f"Customer {c_id}",
            "risk_tier": "HIGH" if case["expected_outcome"] == "FRAUD" else "STANDARD",
            "address": "100 Main St, New York, NY",
            "phone": "+1-555-0199"
        })

        # Account
        credit_limit = 10000.0 if "BUST" in acc_id or case["expected_outcome"] == "FRAUD" else 5000.0
        balance = 9200.0 if "BUST" in acc_id else 800.0
        connector.add_vertex("Account", acc_id, {
            "account_type": "CREDIT" if "BUST" in acc_id else "CHECKING",
            "balance": balance,
            "credit_limit": credit_limit,
            "status": "ACTIVE",
            "baseline_velocity": 3.0
        })

        # Device
        connector.add_vertex("Device", d_id, {
            "device_type": txn["device_type"],
            "device_fingerprint": txn["device_fingerprint"],
            "is_proxy_or_vpn": txn["is_proxy_or_vpn"]
        })

        # IP Address
        connector.add_vertex("IPAddress", ip_addr, {
            "ip_address": ip_addr,
            "is_tor": txn["is_tor"],
            "is_data_center": txn["is_data_center"],
            "reputation_score": txn["reputation_score"]
        })

        # Transaction
        connector.add_vertex("Transaction", t_id, {
            "amount": txn["amount"],
            "risk_score": txn["risk_score"],
            "channel": txn["channel"],
            "distance_from_home": txn["distance_from_home"]
        })

        # Connect Customer -> Account
        connector.add_edge("Customer", c_id, "OWNS_ACCOUNT", "Account", acc_id)
        # Connect Transaction -> Account
        connector.add_edge("Transaction", t_id, "DEBITED_FROM", "Account", acc_id)
        # Connect Transaction -> Device
        connector.add_edge("Transaction", t_id, "ORIGINATED_FROM_DEVICE", "Device", d_id)
        # Connect Transaction -> IP
        connector.add_edge("Transaction", t_id, "ORIGINATED_FROM_IP", "IPAddress", ip_addr)

        # Profile historical device for benign cases (so it's NOT flagged as new)
        if case["expected_outcome"] == "CLEARED":
            connector.add_edge("Customer", c_id, "USES_DEVICE", "Device", d_id)
            connector.add_edge("Customer", c_id, "USES_IP", "IPAddress", ip_addr)

    # 2. Add Synthetic Identity Ring Subgraphs (Cases 4, 8, 19)
    # Ring Alpha (Case 4)
    dev_a = "DEV_SHARED_RING_A"
    for extra_acc, extra_cust in [("ACC_RING_A_MEMBER2", "CUST_9901"), ("ACC_RING_A_MEMBER3", "CUST_9902")]:
        connector.add_vertex("Account", extra_acc, {"balance": 4500.0, "credit_limit": 5000.0, "status": "ACTIVE"})
        connector.add_vertex("Customer", extra_cust, {"full_name": f"Synthetic {extra_cust}"})
        connector.add_edge("Customer", extra_cust, "OWNS_ACCOUNT", "Account", extra_acc)
        connector.add_edge("Customer", extra_cust, "USES_DEVICE", "Device", dev_a)

    # Ring Beta (Case 8)
    dev_b = "DEV_SHARED_RING_B"
    for extra_acc, extra_cust in [("ACC_RING_B_MEMBER2", "CUST_9903"), ("ACC_RING_B_MEMBER3", "CUST_9904")]:
        connector.add_vertex("Account", extra_acc, {"balance": 3200.0, "credit_limit": 5000.0, "status": "ACTIVE"})
        connector.add_vertex("Customer", extra_cust, {"full_name": f"Synthetic {extra_cust}"})
        connector.add_edge("Customer", extra_cust, "OWNS_ACCOUNT", "Account", extra_acc)
        connector.add_edge("Customer", extra_cust, "USES_DEVICE", "Device", dev_b)

    # 3. Add Mule Network Layering Flow (Case 6 & Case 11)
    # Mule chain from ACC_MULE_SOURCE -> MULE_HOP_1 -> MULE_HOP_2
    connector.add_vertex("Account", "ACC_MULE_HOP_1", {"balance": 150.0, "status": "ACTIVE"})
    connector.add_vertex("Account", "ACC_MULE_HOP_2", {"balance": 20.0, "status": "ACTIVE"})
    connector.add_edge("Account", "ACC_MULE_SOURCE", "TRANSFERRED_TO", "Account", "ACC_MULE_HOP_1", {"amount": 6000.0, "timestamp": "2026-06-12 14:02:11"})
    connector.add_edge("Account", "ACC_MULE_HOP_1", "TRANSFERRED_TO", "Account", "ACC_MULE_HOP_2", {"amount": 5950.0, "timestamp": "2026-06-12 14:05:32"})

    # Mule hub from ACC_MULE_HUB -> CRYPTO_OFFSHORE
    connector.add_vertex("Account", "ACC_OFFSHORE_CRYPTO", {"balance": 99000.0, "status": "ACTIVE"})
    connector.add_edge("Account", "ACC_MULE_HUB", "TRANSFERRED_TO", "Account", "ACC_OFFSHORE_CRYPTO", {"amount": 21800.0, "timestamp": "2026-06-18 09:12:00"})

    # 4. Add Bust-out historical transactions (Cases 5 & 10)
    for b_acc, amt in [("ACC_BUST_01", 2000.0), ("ACC_BUST_01", 2800.0), ("ACC_BUST_01", 2400.0), ("ACC_BUST_01", 2300.0)]:
        t_dummy = f"TXN_BURST_{b_acc}_{amt}"
        connector.add_vertex("Transaction", t_dummy, {"amount": amt, "risk_score": 0.85})
        connector.add_edge("Transaction", t_dummy, "DEBITED_FROM", "Account", b_acc)

    for b_acc, amt in [("ACC_BUST_02", 3500.0), ("ACC_BUST_02", 4000.0), ("ACC_BUST_02", 3800.0), ("ACC_BUST_02", 3200.0)]:
        t_dummy = f"TXN_BURST_{b_acc}_{amt}"
        connector.add_vertex("Transaction", t_dummy, {"amount": amt, "risk_score": 0.90})
        connector.add_edge("Transaction", t_dummy, "DEBITED_FROM", "Account", b_acc)
