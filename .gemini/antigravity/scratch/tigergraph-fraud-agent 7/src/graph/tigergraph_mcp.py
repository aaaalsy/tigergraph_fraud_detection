"""
TigerGraph Model Context Protocol (MCP) Interface
Exposes TigerGraph graph traversal, GSQL algorithms, and graph updates as MCP tools
for AI agent tool-calling and autonomous investigation workflows.
Reference: https://github.com/tigergraph/tigergraph-mcp
"""

import json
from typing import Dict, Any, List
from .tigergraph_connector import TigerGraphConnector

class TigerGraphMCP:
    def __init__(self, connector: TigerGraphConnector):
        self.connector = connector

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns standard MCP tool specifications."""
        return [
            {
                "name": "get_subgraph",
                "description": "Extracts the connected entity subgraph surrounding a transaction, account, or customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "center_id": {"type": "string", "description": "The ID of the target vertex"},
                        "hops": {"type": "integer", "description": "Number of graph hops (default: 2)", "default": 2}
                    },
                    "required": ["center_id"]
                }
            },
            {
                "name": "detect_shared_device_ring",
                "description": "Executes GSQL graph traversal to identify multiple accounts sharing devices or IP subnets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Target account ID"}
                    },
                    "required": ["account_id"]
                }
            },
            {
                "name": "trace_fund_flow",
                "description": "Traces directed money movement and rapid layering paths to detect money mules.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Source account ID"},
                        "max_depth": {"type": "integer", "description": "Max hop depth for transfer trace", "default": 3}
                    },
                    "required": ["account_id"]
                }
            },
            {
                "name": "detect_bust_out_risk",
                "description": "Evaluates credit line exhaustion velocity and sudden transaction bursts against baseline.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Account ID to analyze"}
                    },
                    "required": ["account_id"]
                }
            },
            {
                "name": "check_ato_indicators",
                "description": "Traverses transaction graph to check new device fingerprints, TOR/VPN IP flags, and geolocation jumps.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string", "description": "Transaction ID to analyze"}
                    },
                    "required": ["transaction_id"]
                }
            },
            {
                "name": "write_case_to_graph",
                "description": "Persists completed investigation findings, decision, and SAR filing back into TigerGraph.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "case_record": {"type": "object", "description": "Full case document with decisions and SAR"}
                    },
                    "required": ["case_record"]
                }
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution to the TigerGraph engine."""
        if tool_name == "get_subgraph":
            center_id = arguments.get("center_id")
            hops = int(arguments.get("hops", 2))
            return self.connector.fetch_case_subgraph(center_id, hops)

        elif tool_name == "detect_shared_device_ring":
            account_id = arguments.get("account_id")
            return self.connector.detect_shared_device_ring(account_id)

        elif tool_name == "trace_fund_flow":
            account_id = arguments.get("account_id")
            max_depth = int(arguments.get("max_depth", 3))
            return self.connector.trace_fund_flow(account_id, max_depth)

        elif tool_name == "detect_bust_out_risk":
            account_id = arguments.get("account_id")
            return self.connector.detect_bust_out(account_id)

        elif tool_name == "check_ato_indicators":
            transaction_id = arguments.get("transaction_id")
            return self.connector.account_takeover_subgraph(transaction_id)

        elif tool_name == "write_case_to_graph":
            case_record = arguments.get("case_record", {})
            case_id = self.connector.write_case_to_graph(case_record)
            return {"status": "SUCCESS", "case_id": case_id, "message": "Written to TigerGraph knowledge graph"}

        else:
            return {"error": f"Unknown TigerGraph MCP tool: {tool_name}"}
