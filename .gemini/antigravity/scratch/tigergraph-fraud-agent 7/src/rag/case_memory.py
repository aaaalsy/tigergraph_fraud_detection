"""
Case Memory: Historical Investigation Memory & Outcome Retrieval
Stores and retrieves findings, analyst decisions, actions, and outcomes from prior closed cases
(from the initial 4 months) to guide new investigations through case-based reasoning.
"""

import math
from typing import Dict, List, Any, Optional

class CaseMemory:
    def __init__(self):
        self.memory: List[Dict[str, Any]] = []
        self._seed_historical_cases()

    def _seed_historical_cases(self):
        """Pre-populates memory with closed investigations from Months 1-4."""
        self.memory = [
            {
                "case_id": "HIST_CASE_001",
                "month": 1,
                "customer_id": "CUST_9021",
                "pattern": "ACCOUNT_TAKEOVER",
                "features": {"amount": 2850.0, "risk_score": 0.88, "distance_km": 1400.0, "new_device": True, "tor_proxy": True},
                "investigation_outcome": "CONFIRMED_FRAUD",
                "decision": "BLOCK_CARD_AND_FREEZE",
                "sar_filed": False, # < $5000 threshold
                "analyst_rationale": "Customer confirmed unprompted login attempt from Dallas IP while living in Seattle. Step-up auth failed. Card cancelled immediately."
            },
            {
                "case_id": "HIST_CASE_002",
                "month": 1,
                "customer_id": "CUST_4412",
                "pattern": "BENIGN_TRAVEL",
                "features": {"amount": 1200.0, "risk_score": 0.68, "distance_km": 3200.0, "new_device": False, "tor_proxy": False},
                "investigation_outcome": "CLEARED_LEGITIMATE",
                "decision": "ALLOW_TRANSACTION",
                "sar_filed": False,
                "analyst_rationale": "High distance jump triggered rule, but transaction was made on customer's verified MacBook. Customer confirmed business travel to London via SMS."
            },
            {
                "case_id": "HIST_CASE_003",
                "month": 2,
                "customer_id": "CUST_8830",
                "pattern": "SYNTHETIC_IDENTITY_RING",
                "features": {"amount": 8900.0, "risk_score": 0.94, "distance_km": 50.0, "new_device": False, "ring_size": 4},
                "investigation_outcome": "CONFIRMED_FRAUD",
                "decision": "FREEZE_RING_AND_FILE_SAR",
                "sar_filed": True, # > $5000 and ring detected
                "analyst_rationale": "Graph query uncovered 4 accounts created with overlapping SSN prefixes and sharing identical Android hardware ID. FinCEN SAR filed under $8,900 ring activity."
            },
            {
                "case_id": "HIST_CASE_004",
                "month": 2,
                "customer_id": "CUST_1102",
                "pattern": "BUST_OUT_FRAUD",
                "features": {"amount": 9400.0, "risk_score": 0.91, "utilization": 0.96, "velocity_burst": 6},
                "investigation_outcome": "CONFIRMED_FRAUD",
                "decision": "TERMINATE_ACCOUNT_AND_FILE_SAR",
                "sar_filed": True,
                "analyst_rationale": "Account opened 3 months prior. Suddenly maxed out 96% of line across 6 luxury electronics purchases in 24 hours. Check payment bounced. Recovered via collections."
            },
            {
                "case_id": "HIST_CASE_005",
                "month": 3,
                "customer_id": "CUST_7741",
                "pattern": "FRIENDLY_FRAUD",
                "features": {"amount": 650.0, "risk_score": 0.52, "distance_km": 0.0, "new_device": False, "tor_proxy": False},
                "investigation_outcome": "CLEARED_FIRST_PARTY",
                "decision": "DENY_CHARGEBACK",
                "sar_filed": False,
                "analyst_rationale": "Cardholder claimed non-recognition of gaming console purchase. Merchant provided digital delivery proof to cardholder's son's verified console ID. Dispute denied."
            },
            {
                "case_id": "HIST_CASE_006",
                "month": 3,
                "customer_id": "CUST_3309",
                "pattern": "CARDING_AND_MULE_FUNNELING",
                "features": {"amount": 7200.0, "risk_score": 0.96, "mule_hops": 3, "rapid_funnel": True},
                "investigation_outcome": "CONFIRMED_FRAUD",
                "decision": "FREEZE_OUTWARD_TRANSFERS_AND_SAR",
                "sar_filed": True,
                "analyst_rationale": "Series of $1.50 test charges on gift card portal followed by $7,200 wire split across 3 intermediary mule accounts. TigerGraph fund flow traced to overseas crypto offramp."
            },
            {
                "case_id": "HIST_CASE_007",
                "month": 4,
                "customer_id": "CUST_5521",
                "pattern": "BENIGN_EQUIPMENT_UPGRADE",
                "features": {"amount": 2100.0, "risk_score": 0.62, "distance_km": 15.0, "new_device": True, "tor_proxy": False},
                "investigation_outcome": "CLEARED_LEGITIMATE",
                "decision": "ALLOW_TRANSACTION",
                "sar_filed": False,
                "analyst_rationale": "New iPhone 15 device fingerprint detected at local Best Buy. Customer promptly satisfied biometrics via mobile banking push notification."
            },
            {
                "case_id": "HIST_CASE_008",
                "month": 4,
                "customer_id": "CUST_6634",
                "pattern": "ACCOUNT_TAKEOVER",
                "features": {"amount": 14500.0, "risk_score": 0.97, "distance_km": 6000.0, "new_device": True, "tor_proxy": True},
                "investigation_outcome": "CONFIRMED_FRAUD",
                "decision": "FREEZE_ACCOUNT_AND_FILE_SAR",
                "sar_filed": True,
                "analyst_rationale": "High-value wire originated from Lagos, Nigeria IP following password reset. Legitimate account holder reached via alternate phone verified breach. Full wire recall initiated."
            }
        ]

    def find_similar_cases(self, current_features: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Calculates similarity between incoming case signals and historical case memory.
        Uses normalized Euclidean / cosine weighted distance on key risk vectors.
        """
        scored_cases = []
        curr_amt = float(current_features.get("amount", 1000.0))
        curr_score = float(current_features.get("risk_score", 0.5))
        curr_new_dev = bool(current_features.get("new_device", False))
        curr_dist = float(current_features.get("distance_km", 0.0))

        for item in self.memory:
            hist_feat = item["features"]
            hist_amt = float(hist_feat.get("amount", 1000.0))
            hist_score = float(hist_feat.get("risk_score", 0.5))
            hist_new_dev = bool(hist_feat.get("new_device", False))
            hist_dist = float(hist_feat.get("distance_km", 0.0))

            # Feature differences
            amt_diff = abs(curr_amt - hist_amt) / max(curr_amt, hist_amt, 1.0)
            score_diff = abs(curr_score - hist_score)
            dev_diff = 0.0 if curr_new_dev == hist_new_dev else 0.4
            dist_diff = min(abs(curr_dist - hist_dist) / 2000.0, 1.0)

            # Weighted composite distance (lower is closer)
            distance = (0.25 * amt_diff) + (0.35 * score_diff) + (0.20 * dev_diff) + (0.20 * dist_diff)
            similarity = max(0.0, min(1.0, 1.0 - distance))

            scored_cases.append({
                "case_id": item["case_id"],
                "pattern": item["pattern"],
                "outcome": item["investigation_outcome"],
                "prior_decision": item["decision"],
                "sar_filed": item["sar_filed"],
                "analyst_rationale": item["analyst_rationale"],
                "similarity_score": round(similarity, 3)
            })

        # Sort by highest similarity
        scored_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_cases[:top_k]

    def store_resolved_case(self, case_record: Dict[str, Any]):
        """Dynamically appends a newly resolved case to memory."""
        self.memory.append({
            "case_id": case_record.get("case_id"),
            "month": 6,
            "customer_id": case_record.get("customer_id", "UNKNOWN"),
            "pattern": case_record.get("detected_pattern", "UNKNOWN"),
            "features": {
                "amount": float(case_record.get("amount", 0.0)),
                "risk_score": float(case_record.get("risk_score", 0.0)),
                "distance_km": float(case_record.get("distance_km", 0.0)),
                "new_device": bool(case_record.get("new_device", False))
            },
            "investigation_outcome": case_record.get("status", "CLOSED_RESOLVED"),
            "decision": case_record.get("post_nba_action", "ACTION_TAKEN"),
            "sar_filed": bool(case_record.get("sar_required", False)),
            "analyst_rationale": case_record.get("decision_rationale", "")
        })
