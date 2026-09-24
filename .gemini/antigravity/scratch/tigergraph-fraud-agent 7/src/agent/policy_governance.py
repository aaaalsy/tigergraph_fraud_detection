"""
Policy Governance & Approval Matrix
Enforces organizational controls, permission levels, and human-in-the-loop gates
for recommended fraud actions.
"""

from typing import Dict, Any, Tuple
from ..rag.knowledge_base import BANK_FRAUD_POLICY_V42

class PolicyGovernance:
    def __init__(self):
        self.matrix = BANK_FRAUD_POLICY_V42["governance_matrix"]

    def evaluate_action_governance(self, action: str) -> Dict[str, Any]:
        """
        Determines the permission level, approval requirement, and execution state
        for any recommended action.
        """
        clean_action = action.upper().replace(" ", "_")

        # Check Tier 1 (Autonomous)
        for act in self.matrix["TIER_1_AUTO"]["allowed_actions"]:
            if act in clean_action or clean_action in act:
                return {
                    "action": action,
                    "tier": "TIER_1_AUTO",
                    "approval_required": "None (Agent Autonomous Execution)",
                    "execution_status": "EXECUTED_AUTOMATICALLY",
                    "requires_human_approval": False,
                    "authority_role": "AI_AGENT"
                }

        # Check Tier 2 (Analyst Approval)
        for act in self.matrix["TIER_2_ANALYST"]["allowed_actions"]:
            if act in clean_action or clean_action in act:
                return {
                    "action": action,
                    "tier": "TIER_2_ANALYST",
                    "approval_required": "Tier-2 Fraud Analyst Sign-Off",
                    "execution_status": "PENDING_ANALYST_APPROVAL",
                    "requires_human_approval": True,
                    "authority_role": "FRAUD_ANALYST"
                }

        # Check Tier 3 (Senior Compliance Approval)
        for act in self.matrix["TIER_3_SENIOR_COMPLIANCE"]["allowed_actions"]:
            if act in clean_action or clean_action in act:
                return {
                    "action": action,
                    "tier": "TIER_3_SENIOR_COMPLIANCE",
                    "approval_required": "BSA/AML Compliance Officer Approval",
                    "execution_status": "PENDING_COMPLIANCE_SIGN_OFF",
                    "requires_human_approval": True,
                    "authority_role": "BSA_COMPLIANCE_OFFICER"
                }

        # Default fallback
        return {
            "action": action,
            "tier": "TIER_2_ANALYST",
            "approval_required": "Tier-2 Fraud Analyst Sign-Off",
            "execution_status": "PENDING_ANALYST_APPROVAL",
            "requires_human_approval": True,
            "authority_role": "FRAUD_ANALYST"
        }
