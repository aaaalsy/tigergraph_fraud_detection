"""
Knowledge Base: Fraud Policies, Procedures, and Typologies
Grounds the GraphRAG engine with Bank Fraud Policy v4.2, regulatory standards,
and formal descriptions of the 5 known fraud typologies.
"""

BANK_FRAUD_POLICY_V42 = {
    "policy_name": "Apex National Bank Fraud Risk Management & Resolution Policy v4.2",
    "effective_date": "2026-01-01",
    "regulatory_frameworks": [
        "FinCEN 31 CFR § 1020.320 (Reports by banks of suspicious transactions)",
        "CFPB Regulation E (12 CFR Part 1005 - Electronic Fund Transfers)",
        "FFIEC Guidance on Authentication and Access to Financial Institution Services and Systems",
        "PCI-DSS v4.0 Requirement 10 (Log and Network Monitoring)"
    ],
    "thresholds": {
        "auto_hold_score": 0.82,  # Risk model score triggering immediate hold
        "step_up_auth_score": 0.65,  # Score triggering step-up authentication
        "sar_mandatory_amount": 5000.0,  # Any suspicious transaction >= $5,000 where suspect is identified
        "sar_unidentified_amount": 25000.0, # Suspicious transaction >= $25,000 where suspect is unknown
        "chargeback_time_limit_days": 60, # Reg E customer dispute window
        "high_velocity_count_threshold": 4, # Max allowed transactions in 1 hour without MFA
    },
    "governance_matrix": {
        "TIER_1_AUTO": {
            "allowed_actions": [
                "REQUEST_STEP_UP_AUTH",
                "SEND_CUSTOMER_VERIFICATION_SMS",
                "TEMPORARY_24H_HOLD",
                "FLAG_FOR_MONITORING"
            ],
            "approval_required": "None (Agent Autonomous Execution)"
        },
        "TIER_2_ANALYST": {
            "allowed_actions": [
                "BLOCK_CARD",
                "FREEZE_ACCOUNT",
                "DECLINE_TRANSACTION",
                "FORCE_PASSWORD_RESET",
                "CLOSE_FALSE_POSITIVE"
            ],
            "approval_required": "Tier-2 Fraud Analyst Sign-Off"
        },
        "TIER_3_SENIOR_COMPLIANCE": {
            "allowed_actions": [
                "FILE_SAR_REPORT",
                "PERMANENT_ACCOUNT_TERMINATION",
                "LAW_ENFORCEMENT_REFERRAL",
                "CROSS_INSTITUTION_ALERT"
            ],
            "approval_required": "BSA/AML Compliance Officer Approval"
        }
    }
}

KNOWN_FRAUD_PATTERNS = {
    "ACCOUNT_TAKEOVER": {
        "name": "Account Takeover (ATO) with Credential Stuffing & Device Switching",
        "description": "An unauthorized party compromises valid user credentials, accesses the account from a new unprofiled device or TOR/VPN proxy, and initiates immediate high-value funds transfers or card purchases.",
        "indicators": [
            "Transaction originates from a newly seen device fingerprint",
            "IP address is hosted in a commercial data center or TOR exit node",
            "Geolocation distance jump > 500 km within < 2 hours of prior legitimate session",
            "Password or contact info modified shortly before transaction"
        ],
        "primary_evidence_needed": "Out-of-band customer verification & step-up biometric/MFA response",
        "default_pre_nba": "TEMPORARY_24H_HOLD and REQUEST_STEP_UP_AUTH",
        "default_post_nba_confirmed": "BLOCK_CARD, FREEZE_ACCOUNT, and FILE_SAR_REPORT",
        "default_post_nba_cleared": "ALLOW_TRANSACTION and UPDATE_CUSTOMER_DEVICE_PROFILE"
    },
    "SYNTHETIC_IDENTITY_RING": {
        "name": "Synthetic Identity Ring with Shared PII & Collusive Device Network",
        "description": "Fraud ring manufactures fictitious identities by blending real SSNs with fabricated names, addresses, and phone numbers. They share common physical devices or IP subnets to build credit history, then execute coordinated bust-outs.",
        "indicators": [
            "Multiple distinct customer IDs sharing the same device fingerprint or physical address",
            "High degree of graph connectivity between seemingly unrelated accounts",
            "Recently opened accounts with rapidly increasing credit lines",
            "Thin credit file followed by sudden high-velocity applications"
        ],
        "primary_evidence_needed": "Physical ID proof verification & multi-account graph expansion",
        "default_pre_nba": "FREEZE_ACCOUNT and REQUEST_ANALYST_COLLUSION_REVIEW",
        "default_post_nba_confirmed": "FREEZE_ALL_RING_ACCOUNTS and FILE_SAR_REPORT",
        "default_post_nba_cleared": "CLOSE_FALSE_POSITIVE"
    },
    "BUST_OUT_FRAUD": {
        "name": "Bust-Out Fraud / Rapid Credit Line Depletion",
        "description": "An account holder or fraudster deliberately maxes out a line of credit or overdraws an account with no intention of repayment, often preceded by bounced fake payments to temporarily inflate available credit.",
        "indicators": [
            "Credit line utilization jumps to > 90% within 48 hours",
            "Transaction velocity spikes > 300% above customer's 6-month historical baseline",
            "Large purchases at high-liquidity merchants (electronics, gift cards, luxury goods)",
            "Recent payment reversal or NSF (non-sufficient funds) notice"
        ],
        "primary_evidence_needed": "Payment clearing confirmation & manual credit line freeze",
        "default_pre_nba": "DECLINE_TRANSACTION and SUSPEND_CREDIT_LINE",
        "default_post_nba_confirmed": "PERMANENT_ACCOUNT_TERMINATION and FILE_SAR_REPORT",
        "default_post_nba_cleared": "RESTORE_CREDIT_LINE"
    },
    "CARDING_AND_MULE_FUNNELING": {
        "name": "High-Velocity Carding / Mule Account Funneling",
        "description": "Automated scripts test stolen credit card numbers using micro-transactions, followed by rapid multi-hop peer-to-peer transfers that funnel stolen funds into intermediary mule accounts for cash-out via ATMs or crypto.",
        "indicators": [
            "Rapid sequence of small authorization charges followed by large transfer",
            "Multiple distinct cards used on a single device within minutes",
            "Graph path reveals immediate outward transfer to known mule nodes",
            "High out-degree on receiving account with near-zero holding time"
        ],
        "primary_evidence_needed": "Card brand velocity alert & multi-hop transfer trace",
        "default_pre_nba": "BLOCK_CARD and FREEZE_OUTWARD_TRANSFERS",
        "default_post_nba_confirmed": "BLOCK_ALL_LINKED_CARDS and FILE_SAR_REPORT",
        "default_post_nba_cleared": "CLOSE_FALSE_POSITIVE"
    },
    "FRIENDLY_FRAUD": {
        "name": "Friendly Fraud / First-Party Dispute Abuse",
        "description": "The legitimate account holder or an authorized household member makes a valid transaction, but later files an unauthorized charge dispute or chargeback to evade payment.",
        "indicators": [
            "Transaction executed from customer's long-standing trusted home device and IP",
            "Delivery address matches verified customer home address on file",
            "Pattern of repeated prior chargeback disputes that were subsequently withdrawn",
            "No foreign IP or credential changes detected"
        ],
        "primary_evidence_needed": "Merchant proof of delivery and historical dispute record",
        "default_pre_nba": "REQUEST_CUSTOMER_TRANSACTION_CLARIFICATION",
        "default_post_nba_confirmed": "DENY_CHARGEBACK_DISPUTE and WARN_CUSTOMER",
        "default_post_nba_cleared": "ISSUE_PROVISIONAL_CREDIT"
    }
}
