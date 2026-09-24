"""
FinCEN Suspicious Activity Report (SAR) Generator
Generates regulatory-grade SAR narratives adhering to 31 CFR § 1020.320 guidelines
when suspicious activity exceeds monetary thresholds or involves organized fraud rings.
"""

from typing import Dict, Any, List
from datetime import datetime

class SARGenerator:
    def __init__(self, institution_name: str = "Apex National Bank"):
        self.institution_name = institution_name

    def generate_sar(self, case_record: Dict[str, Any], ground_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs a complete FinCEN SAR filing record.
        """
        sar_id = f"SAR-{datetime.now().strftime('%Y%m')}-{case_record.get('case_id', '000')}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        txn_summary = ground_context.get("transaction_summary", {})
        graph_ev = ground_context.get("graph_evidence", {})
        typology = ground_context.get("matched_typology", {})
        
        amount = float(txn_summary.get("amount", 0.0))
        account_id = txn_summary.get("account_id", "UNKNOWN")
        customer_id = case_record.get("customer_id", "UNKNOWN")
        pattern_name = typology.get("details", {}).get("name", "Uncategorized Suspicious Activity")
        
        # Build regulatory narrative
        narrative_parts = [
            f"SUSPICIOUS ACTIVITY REPORT (FINCEN FORM 111 / 31 CFR § 1020.320)",
            f"Filing Institution: {self.institution_name} | Date: {date_str} | Tracking: {sar_id}",
            f"================================================================================",
            f"1. SUBJECT & ACCOUNT IDENTIFICATION:",
            f"   Primary Account: {account_id}",
            f"   Customer Reference: {customer_id}",
            f"   Total Suspicious Amount Identified: ${amount:,.2f} USD",
            f"",
            f"2. SUSPICIOUS PATTERN / TYPOLOGY DETECTED:",
            f"   Typology: {pattern_name}",
            f"   Confidence Assessment: {typology.get('confidence', 0.0)*100:.1f}%",
            f"",
            f"3. DETAILED INVESTIGATION & GRAPH EVIDENCE FINDINGS:",
        ]
        
        for indicator in typology.get("detected_indicators", []):
            narrative_parts.append(f"   - {indicator}")
            
        # Fund flow if available
        fund_flow = graph_ev.get("fund_flow", {})
        if fund_flow.get("transfer_paths"):
            narrative_parts.append(f"   - Graph Layering Traced: Diverted funds routed across {len(fund_flow['implicated_accounts'])} mule accounts.")
            for p in fund_flow["transfer_paths"][:3]:
                narrative_parts.append(f"     * Path: {p['source']} -> {p['target']} (${p['amount']})")

        # Device ring if available
        dev_ring = graph_ev.get("device_ring", {})
        if dev_ring.get("ring_size", 0) > 0:
            narrative_parts.append(f"   - Hardware Fingerprint Sharing: Linked to {dev_ring['ring_size']} other distinct banking accounts.")

        narrative_parts.extend([
            f"",
            f"4. ACTIONS TAKEN & GOVERNANCE:",
            f"   Pre-Evidence Recommendation: {case_record.get('pre_nba_action')}",
            f"   Post-Evidence Final Action: {case_record.get('post_nba_action')}",
            f"   Approval Authority: BSA/AML Compliance Officer (Tier-3)",
            f"   Law Enforcement Referral: Recommended for federal task force review.",
            f"================================================================================"
        ])
        
        narrative = "\n".join(narrative_parts)

        return {
            "sar_id": sar_id,
            "filing_date": date_str,
            "filing_status": "READY_FOR_SUBMISSION",
            "institution": self.institution_name,
            "account_id": account_id,
            "customer_id": customer_id,
            "suspicious_amount": amount,
            "primary_typology": pattern_name,
            "fincen_narrative": narrative,
            "requires_tier3_signoff": True
        }
