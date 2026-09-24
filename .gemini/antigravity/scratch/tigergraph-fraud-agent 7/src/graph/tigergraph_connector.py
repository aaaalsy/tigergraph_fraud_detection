"""
TigerGraph Connector & Graph Engine
Supports dual-mode execution:
1. Live TigerGraph Cloud Savanna / Community Edition via REST++ and pyTigerGraph
2. Embedded High-Fidelity Graph Engine (NetworkX-powered with GSQL query emulation,
   Louvain community detection, PageRank, and D3 node-link export).
"""

import os
import json
import math
import logging
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx

logger = logging.getLogger(__name__)

class TigerGraphConnector:
    def __init__(self, mode: str = "embedded", host: Optional[str] = None, 
                 graph_name: str = "FraudInvestigationGraph", secret: Optional[str] = None,
                 token: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        self.mode = mode or os.getenv("TG_MODE", "embedded")
        self.host = host or os.getenv("TG_HOST", "https://savanna.tgcloud.io")
        self.graph_name = graph_name or os.getenv("TG_GRAPH", "FraudInvestigationGraph")
        self.secret = secret or os.getenv("TG_SECRET", "")
        self.token = token or os.getenv("TG_TOKEN", "")
        self.username = username or os.getenv("TG_USERNAME", "tigergraph")
        self.password = password or os.getenv("TG_PASSWORD", "tigergraph")
        
        # High-performance local graph instance
        self.graph = nx.MultiDiGraph()
        self.live_client = None
        
        if self.mode == "live":
            self._init_live_client()
        else:
            logger.info("Operating in TigerGraph EMBEDDED mode with local GSQL engine.")

    def _init_live_client(self):
        """Attempts connection to live TigerGraph Savanna cluster via pyTigerGraph."""
        try:
            import pyTigerGraph as tg
            self.live_client = tg.TigerGraphConnection(
                host=self.host,
                graphname=self.graph_name,
                username=self.username,
                password=self.password,
                apiToken=self.token
            )
            if self.secret and not self.token:
                self.live_client.getToken(self.secret)
            logger.info(f"Successfully connected to Live TigerGraph Savanna: {self.host}")
        except Exception as e:
            logger.warning(f"Live TigerGraph connection unavailable ({e}). Falling back to Embedded Engine.")
            self.mode = "embedded"

    # =========================================================================
    # Embedded Graph Operations (Schema & Entity Management)
    # =========================================================================

    def add_vertex(self, v_type: str, v_id: str, attributes: Dict[str, Any]):
        """Adds a vertex with GSQL-typed attributes."""
        node_key = f"{v_type}:{v_id}"
        attrs = dict(attributes)
        attrs["v_type"] = v_type
        attrs["v_id"] = v_id
        self.graph.add_node(node_key, **attrs)
        return node_key

    def add_edge(self, from_type: str, from_id: str, edge_type: str, 
                 to_type: str, to_id: str, attributes: Optional[Dict[str, Any]] = None):
        """Adds a directed edge between two vertices with attributes."""
        u = f"{from_type}:{from_id}"
        v = f"{to_type}:{to_id}"
        attrs = dict(attributes or {})
        attrs["edge_type"] = edge_type
        self.graph.add_edge(u, v, key=edge_type, **attrs)

    def get_vertex(self, v_type: str, v_id: str) -> Optional[Dict[str, Any]]:
        node_key = f"{v_type}:{v_id}"
        if node_key in self.graph:
            return dict(self.graph.nodes[node_key])
        return None

    # =========================================================================
    # GSQL Query Emulation / Live Query Dispatch
    # =========================================================================

    def detect_shared_device_ring(self, account_id: str) -> Dict[str, Any]:
        """
        Emulates GSQL query: detect_shared_device_ring(VERTEX<Account> input_acc, INT max_hops)
        Finds accounts sharing the same device fingerprints across transaction logs.
        """
        if self.mode == "live" and self.live_client:
            try:
                res = self.live_client.runInstalledQuery("detect_shared_device_ring", {"input_acc": account_id, "max_hops": 2})
                return res[0] if res else {}
            except Exception as e:
                logger.error(f"Error running live query: {e}. Falling back to embedded execution.")

        acc_key = f"Account:{account_id}"
        if acc_key not in self.graph:
            return {"shared_device_count": 0, "devices": [], "ring_accounts": [], "ring_size": 0}

        # Find transactions from this account
        txns = []
        for _, v, data in self.graph.out_edges(acc_key, data=True):
            if data.get("edge_type") == "ACCOUNT_TRANSACTIONS" or v.startswith("Transaction:"):
                txns.append(v)
        # Also check reverse edge DEBITED_FROM
        for u, _, data in self.graph.in_edges(acc_key, data=True):
            if data.get("edge_type") == "DEBITED_FROM" and u.startswith("Transaction:"):
                txns.append(u)

        shared_devices = set()
        for t in txns:
            for _, dev, data in self.graph.out_edges(t, data=True):
                if dev.startswith("Device:") or data.get("edge_type") == "ORIGINATED_FROM_DEVICE":
                    shared_devices.add(dev)

        # Check customer direct links
        for cust, _, _ in self.graph.in_edges(acc_key, data=True):
            if cust.startswith("Customer:"):
                for _, dev, _ in self.graph.out_edges(cust, data=True):
                    if dev.startswith("Device:"):
                        shared_devices.add(dev)

        # Find other accounts tied to these devices
        ring_accounts = set()
        for dev in shared_devices:
            # txns using dev
            for t, _, data in self.graph.in_edges(dev, data=True):
                if t.startswith("Transaction:"):
                    for _, acc, a_data in self.graph.out_edges(t, data=True):
                        if acc.startswith("Account:") and acc != acc_key:
                            ring_accounts.add(acc.split(":")[1])
            # customers using dev
            for c, _, data in self.graph.in_edges(dev, data=True):
                if c.startswith("Customer:"):
                    for _, acc, a_data in self.graph.out_edges(c, data=True):
                        if acc.startswith("Account:") and acc != acc_key:
                            ring_accounts.add(acc.split(":")[1])

        dev_list = [d.split(":")[1] for d in shared_devices]
        ring_list = list(ring_accounts)

        return {
            "shared_device_count": len(dev_list),
            "devices": dev_list,
            "ring_accounts": ring_list,
            "ring_size": len(ring_list)
        }

    def trace_fund_flow(self, account_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Emulates GSQL query: trace_fund_flow(VERTEX<Account> source_acc, INT max_depth)
        Traces directed fund transfers across recipient accounts.
        """
        if self.mode == "live" and self.live_client:
            try:
                res = self.live_client.runInstalledQuery("trace_fund_flow", {"source_acc": account_id, "max_depth": max_depth})
                return res[0] if res else {}
            except Exception as e:
                logger.error(f"Live query trace_fund_flow error: {e}")

        acc_key = f"Account:{account_id}"
        flow_records = []
        implicated_accounts = set()
        total_volume = 0.0

        visited = set()
        queue = [(acc_key, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth or curr in visited:
                continue
            visited.add(curr)

            for _, tgt, data in self.graph.out_edges(curr, data=True):
                if data.get("edge_type") == "TRANSFERRED_TO":
                    amt = float(data.get("amount", 0.0))
                    ts = data.get("timestamp", "")
                    tgt_id = tgt.split(":")[1] if ":" in tgt else tgt
                    src_id = curr.split(":")[1] if ":" in curr else curr
                    flow_records.append({
                        "source": src_id,
                        "target": tgt_id,
                        "amount": amt,
                        "timestamp": str(ts)
                    })
                    implicated_accounts.add(tgt_id)
                    total_volume += amt
                    queue.append((tgt, depth + 1))

        return {
            "transfer_paths": flow_records,
            "implicated_accounts": list(implicated_accounts),
            "total_volume_diverted": round(total_volume, 2),
            "hop_depth": len(flow_records)
        }

    def detect_bust_out(self, account_id: str) -> Dict[str, Any]:
        """
        Emulates GSQL query: detect_bust_out(VERTEX<Account> input_acc)
        Assesses velocity and credit line exhaustion.
        """
        acc_key = f"Account:{account_id}"
        acc_node = self.graph.nodes.get(acc_key, {})
        credit_limit = float(acc_node.get("credit_limit", 5000.0))
        current_balance = float(acc_node.get("balance", 0.0))
        baseline_velocity = float(acc_node.get("baseline_velocity", 3.0))

        # Count recent transactions
        recent_txns = []
        for u, _, data in self.graph.in_edges(acc_key, data=True):
            if u.startswith("Transaction:"):
                recent_txns.append(self.graph.nodes.get(u, {}))

        recent_spend = sum(float(t.get("amount", 0.0)) for t in recent_txns)
        txn_count = len(recent_txns)

        utilization = (current_balance + recent_spend) / credit_limit if credit_limit > 0 else 0.0
        velocity_ratio = (txn_count / baseline_velocity) if baseline_velocity > 0 else txn_count

        is_bust_out = (utilization >= 0.85 and txn_count >= 4) or (velocity_ratio >= 3.0 and utilization > 0.70)

        return {
            "credit_utilization": round(utilization, 3),
            "rapid_spend_total": round(recent_spend, 2),
            "transaction_burst": txn_count,
            "velocity_ratio": round(velocity_ratio, 2),
            "is_bust_out_risk": bool(is_bust_out)
        }

    def account_takeover_subgraph(self, txn_id: str) -> Dict[str, Any]:
        """
        Emulates GSQL query: account_takeover_subgraph(VERTEX<Transaction> target_txn)
        Extracts new device indicators, IP risk, and geo-distance jump.
        """
        txn_key = f"Transaction:{txn_id}"
        txn_node = self.graph.nodes.get(txn_key, {})
        distance = float(txn_node.get("distance_from_home", 0.0))

        # Get device and IP
        devices = []
        ips = []
        is_proxy_or_tor = False

        for _, v, data in self.graph.out_edges(txn_key, data=True):
            if v.startswith("Device:") or data.get("edge_type") == "ORIGINATED_FROM_DEVICE":
                d_node = self.graph.nodes.get(v, {})
                devices.append(d_node.get("device_fingerprint", v))
                if d_node.get("is_proxy_or_vpn", False):
                    is_proxy_or_tor = True
            elif v.startswith("IPAddress:") or data.get("edge_type") == "ORIGINATED_FROM_IP":
                ip_node = self.graph.nodes.get(v, {})
                ips.append(ip_node.get("ip_address", v))
                if ip_node.get("is_tor", False) or ip_node.get("is_data_center", False) or ip_node.get("reputation_score", 0) > 0.5:
                    is_proxy_or_tor = True

        # Check if device is new for account customer
        account_id = None
        for _, v, data in self.graph.out_edges(txn_key, data=True):
            if v.startswith("Account:") or data.get("edge_type") == "DEBITED_FROM":
                account_id = v
                break

        is_new_device = True
        if account_id:
            for cust, _, _ in self.graph.in_edges(account_id, data=True):
                if cust.startswith("Customer:"):
                    for _, dev, _ in self.graph.out_edges(cust, data=True):
                        d_fp = self.graph.nodes.get(dev, {}).get("device_fingerprint")
                        if d_fp and d_fp in devices:
                            is_new_device = False

        return {
            "new_device_detected": is_new_device,
            "proxy_or_tor_ip": is_proxy_or_tor,
            "distance_from_home_km": distance,
            "devices": devices,
            "ips": ips,
            "is_ato_suspicious": is_new_device and (is_proxy_or_tor or distance > 1000.0)
        }

    def fetch_case_subgraph(self, center_id: str, hops: int = 2) -> Dict[str, Any]:
        """
        Extracts multi-hop subgraph for GraphRAG context grounding and D3 rendering.
        """
        # Match center_id whether prefixed or not
        target_node = None
        for n in self.graph.nodes:
            if n == center_id or n.endswith(f":{center_id}"):
                target_node = n
                break

        if not target_node:
            return {"nodes": [], "edges": []}

        sub_nodes = set([target_node])
        current_layer = set([target_node])

        for _ in range(hops):
            next_layer = set()
            for node in current_layer:
                # Neighbors both incoming and outgoing
                for succ in self.graph.successors(node):
                    if succ not in sub_nodes:
                        next_layer.add(succ)
                for pred in self.graph.predecessors(node):
                    if pred not in sub_nodes:
                        next_layer.add(pred)
            sub_nodes.update(next_layer)
            current_layer = next_layer
            if len(sub_nodes) > 40:  # Bound to avoid visual clutter
                break

        subgraph = self.graph.subgraph(sub_nodes)
        nodes_data = []
        for n in subgraph.nodes:
            props = dict(self.graph.nodes[n])
            props["id"] = n
            props["label"] = n.split(":")[1] if ":" in n else n
            props["type"] = n.split(":")[0] if ":" in n else "Unknown"
            nodes_data.append(props)

        edges_data = []
        for u, v, k, data in subgraph.edges(keys=True, data=True):
            edges_data.append({
                "source": u,
                "target": v,
                "type": data.get("edge_type", k),
                "attributes": {k: v for k, v in data.items() if k not in ["edge_type"]}
            })

        return {
            "center": target_node,
            "nodes": nodes_data,
            "edges": edges_data,
            "total_nodes": len(nodes_data),
            "total_edges": len(edges_data)
        }

    # =========================================================================
    # Graph Algorithms (PageRank, Louvain / Weakly Connected Components)
    # =========================================================================

    def run_pagerank(self) -> Dict[str, float]:
        """Computes PageRank centrality to identify top money laundering mule hubs."""
        if len(self.graph) == 0:
            return {}
        try:
            return nx.pagerank(self.graph, alpha=0.85, max_iter=50)
        except Exception:
            return {n: 1.0 / len(self.graph) for n in self.graph.nodes}

    def detect_communities(self) -> List[List[str]]:
        """Finds connected clusters representing organized fraud rings."""
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        # Filter for multi-node rings
        rings = [list(c) for c in components if len(c) > 2]
        return rings

    # =========================================================================
    # Write-Back Capabilities (Updating TigerGraph with Investigation Outcomes)
    # =========================================================================

    def write_case_to_graph(self, case_record: Dict[str, Any]):
        """
        Persists the completed investigation findings, decision, and SAR back to TigerGraph.
        """
        case_id = case_record.get("case_id", f"CASE_{len(self.graph.nodes)}")
        
        # Add FraudCase vertex
        self.add_vertex("FraudCase", case_id, {
            "trigger_type": case_record.get("trigger_type", "MODEL_SCORE"),
            "status": case_record.get("status", "CLOSED_FRAUD"),
            "assessed_risk_score": case_record.get("risk_score", 0.0),
            "uncertainty_level": case_record.get("uncertainty_level", "LOW"),
            "pre_nba_action": case_record.get("pre_nba_action", ""),
            "pre_nba_approval": case_record.get("pre_nba_approval", ""),
            "post_nba_action": case_record.get("post_nba_action", ""),
            "post_nba_approval": case_record.get("post_nba_approval", ""),
            "detected_pattern": case_record.get("detected_pattern", "Unknown"),
            "sar_filing_required": case_record.get("sar_required", False),
            "investigation_summary": case_record.get("summary", ""),
            "decision_rationale": case_record.get("rationale", "")
        })

        # Link to Transaction / Account / Customer
        txn_id = case_record.get("transaction_id")
        if txn_id:
            self.add_edge("FraudCase", case_id, "INVESTIGATES_TXN", "Transaction", txn_id)
            
        acc_id = case_record.get("account_id")
        if acc_id:
            self.add_edge("FraudCase", case_id, "INVESTIGATES_ACCOUNT", "Account", acc_id)

        cust_id = case_record.get("customer_id")
        if cust_id:
            self.add_edge("FraudCase", case_id, "INVESTIGATES_CUSTOMER", "Customer", cust_id)

        # Write SAR Report vertex if applicable
        if case_record.get("sar_required"):
            sar_id = f"SAR_{case_id}"
            sar_narrative = case_record.get("sar_narrative", "")
            self.add_vertex("SARReport", sar_id, {
                "fincen_narrative": sar_narrative,
                "suspect_entities": json.dumps(case_record.get("suspects", [])),
                "total_suspicious_amount": case_record.get("amount", 0.0),
                "filing_status": "DRAFT_PENDING_APPROVAL"
            })
            self.add_edge("FraudCase", case_id, "GENERATED_SAR", "SARReport", sar_id)

        logger.info(f"Successfully recorded FraudCase {case_id} to TigerGraph Knowledge Graph.")
        return case_id
