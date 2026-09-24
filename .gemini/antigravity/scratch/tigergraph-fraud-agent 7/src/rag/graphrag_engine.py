"""
GraphRAG Engine: Knowledge Graph + Policy & Typology Grounding
Combines graph structural evidence (TigerGraph subgraphs, device rings, fund flows)
with formal fraud policies, regulatory guidelines, and case memory to produce
grounded, high-signal context for agent decisioning.
"""

from typing import Dict, List, Any
from .knowledge_base import BANK_FRAUD_POLICY_V42, KNOWN_FRAUD_PATTERNS
from .case_memory import CaseMemory
from ..graph.tigergraph_connector import TigerGraphConnector

class GraphRAGEngine:
    def __init__(self, connector: TigerGraphConnector, case_memory: CaseMemory):
        self.connector = connector
        self.case_memory = case_memory

    def ground_investigation(self, transaction_data: Dict[str, Any], trigger_type: str) -> Dict[str, Any]:
        """
        Gathers connected graph evidence, matches fraud typologies, looks up
        relevant policy rules, and retrieves similar historical cases.
        """
        txn_id = transaction_data.get("transaction_id", "")
        account_id = transaction_data.get("account_id", "")
        amount = float(transaction_data.get("amount", 0.0))
        model_risk_score = float(transaction_data.get("risk_score", 0.0))
        channel = transaction_data.get("channel", "WEB")

        # 1. TigerGraph Graph Queries (Multi-hop structural signals)
        ato_signals = self.connector.account_takeover_subgraph(txn_id)
        device_ring = self.connector.detect_shared_device_ring(account_id)
        fund_flow = self.connector.trace_fund_flow(account_id)
        bust_out = self.connector.detect_bust_out(account_id)
        subgraph = self.connector.fetch_case_subgraph(txn_id, hops=2)

        # 2. Fraud Typology Pattern Matching
        matched_typology = None
        matched_confidence = 0.0
        pattern_indicators_found = []

        if device_ring.get("ring_size", 0) >= 2:
            matched_typology = "SYNTHETIC_IDENTITY_RING"
            matched_confidence = 0.90
            pattern_indicators_found.append(f"Connected to {device_ring['ring_size']} other accounts via shared device hardware ID")

        elif bust_out.get("is_bust_out_risk"):
            matched_typology = "BUST_OUT_FRAUD"
            matched_confidence = 0.88
            pattern_indicators_found.append(f"Credit line utilization at {bust_out['credit_utilization']*100:.1f}% with velocity surge ratio {bust_out['velocity_ratio']}x")

        elif fund_flow.get("total_volume_diverted", 0.0) >= 3000.0 or len(fund_flow.get("transfer_paths", [])) >= 2:
            matched_typology = "CARDING_AND_MULE_FUNNELING"
            matched_confidence = 0.92
            pattern_indicators_found.append(f"Immediate outbound layering detected to {len(fund_flow.get('implicated_accounts', []))} intermediary accounts (${fund_flow['total_volume_diverted']})")

        elif ato_signals.get("is_ato_suspicious") or (ato_signals.get("new_device_detected") and model_risk_score >= 0.70):
            matched_typology = "ACCOUNT_TAKEOVER"
            matched_confidence = 0.86
            pattern_indicators_found.append(f"Unprofiled device login coupled with distance jump of {ato_signals['distance_from_home_km']:.0f} km and proxy IP flag")

        elif model_risk_score < 0.40 and not ato_signals.get("new_device_detected"):
            matched_typology = "BENIGN_BASELINE"
            matched_confidence = 0.95
            pattern_indicators_found.append("Transaction matches verified baseline device, home geo-location, and standard velocity")

        else:
            matched_typology = "AMBIGUOUS_UNCERTAIN"
            matched_confidence = 0.50
            pattern_indicators_found.append("Signals are mixed: elevated model score without definitive ring or proxy indicators")

        # 3. Policy & Regulatory Retrieval
        policy_hits = []
        sar_mandatory = False

        if model_risk_score >= BANK_FRAUD_POLICY_V42["thresholds"]["auto_hold_score"]:
            policy_hits.append("Policy Rule §4.2.1: Model score >= 0.82 warrants immediate transaction soft-hold.")

        if model_risk_score >= BANK_FRAUD_POLICY_V42["thresholds"]["step_up_auth_score"] and matched_typology != "BENIGN_BASELINE":
            policy_hits.append("Policy Rule §4.2.3: Elevated risk requires controlled step-up authentication prior to release.")

        if amount >= BANK_FRAUD_POLICY_V42["thresholds"]["sar_mandatory_amount"] and matched_typology not in ["BENIGN_BASELINE", "AMBIGUOUS_UNCERTAIN"]:
            sar_mandatory = True
            policy_hits.append(f"FinCEN 31 CFR § 1020.320: Mandatory SAR filing triggered (Amount ${amount:.2f} >= $5,000 threshold with identified suspect/modus operandi).")

        # 4. Case Memory Retrieval (Historic similarity)
        case_features = {
            "amount": amount,
            "risk_score": model_risk_score,
            "new_device": ato_signals.get("new_device_detected", False),
            "distance_km": ato_signals.get("distance_from_home_km", 0.0)
        }
        similar_past_cases = self.case_memory.find_similar_cases(case_features, top_k=2)

        # 5. Assemble Grounded Context Package
        grounded_context = {
            "transaction_summary": {
                "id": txn_id,
                "account_id": account_id,
                "amount": amount,
                "model_risk_score": model_risk_score,
                "channel": channel,
                "trigger_type": trigger_type
            },
            "graph_evidence": {
                "ato_analysis": ato_signals,
                "device_ring": device_ring,
                "fund_flow": fund_flow,
                "bust_out_analysis": bust_out,
                "subgraph_summary": f"{subgraph['total_nodes']} nodes, {subgraph['total_edges']} edges in 2-hop neighborhood"
            },
            "matched_typology": {
                "pattern_id": matched_typology,
                "details": KNOWN_FRAUD_PATTERNS.get(matched_typology, {}),
                "confidence": matched_confidence,
                "detected_indicators": pattern_indicators_found
            },
            "policy_citations": policy_hits,
            "sar_mandatory": sar_mandatory,
            "case_memory_insights": similar_past_cases
        }

        return grounded_context
