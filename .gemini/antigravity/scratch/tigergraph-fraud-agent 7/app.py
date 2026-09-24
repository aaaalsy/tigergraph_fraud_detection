"""
TigerGraph Agentic Fraud Investigation Server
Flask backend serving the Analyst Dashboard, TigerGraph Graph Visualizer API,
Autonomous Investigation Agent, and 20 Benchmark Case outputs.
"""

import os
import json
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory

from src.graph.tigergraph_connector import TigerGraphConnector
from src.agent.investigation_agent import InvestigationAgent
from src.benchmark.benchmark_dataset import BENCHMARK_CASES, seed_graph_with_benchmark_data
from src.benchmark.benchmark_runner import BenchmarkRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

# Initialize global graph connector and seed benchmark graph
connector = TigerGraphConnector()
seed_graph_with_benchmark_data(connector)
agent = InvestigationAgent(connector)

# Ensure benchmark answer files exist
output_dir = os.path.join(os.path.dirname(__file__), "output", "cases")
if not os.path.exists(output_dir) or len(os.listdir(output_dir)) < 20:
    logger.info("Initializing 20 benchmark case outputs...")
    runner = BenchmarkRunner(output_dir=output_dir)
    runner.run_all_cases()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cases", methods=["GET"])
def list_cases():
    """Returns list of benchmark cases and their execution statuses."""
    cases_summary = []
    for idx, b_case in enumerate(BENCHMARK_CASES, start=1):
        num_str = f"{idx:02d}"
        answer_file = os.path.join(output_dir, f"case_{num_str}_answer.json")
        status = "PENDING"
        risk_score = 0.0
        pattern = "Unknown"
        sar_filed = False
        pre_action = ""
        post_action = ""

        if os.path.exists(answer_file):
            try:
                with open(answer_file, "r") as f:
                    ans = json.load(f)
                    status = ans.get("case_summary", {}).get("status", "COMPLETED")
                    risk_score = ans.get("case_summary", {}).get("assessed_risk_score", 0.0)
                    pattern = ans.get("case_summary", {}).get("detected_pattern", "Unknown")
                    sar_filed = isinstance(ans.get("suspicious_activity_report"), dict)
                    pre_action = ans.get("next_best_action", {}).get("before_additional_evidence", {}).get("recommended_action", "")
                    post_action = ans.get("next_best_action", {}).get("after_additional_evidence", {}).get("recommended_action", "")
            except Exception as e:
                logger.error(f"Error reading {answer_file}: {e}")

        cases_summary.append({
            "case_id": b_case["case_id"],
            "case_index": idx,
            "title": b_case["title"],
            "trigger_type": b_case["trigger_type"],
            "amount": b_case["transaction"]["amount"],
            "status": status,
            "assessed_risk_score": risk_score,
            "detected_pattern": pattern,
            "sar_filed": sar_filed,
            "pre_action": pre_action,
            "post_action": post_action
        })
    return jsonify(cases_summary)

@app.route("/api/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    """Retrieves full investigation record and answer for a specific case."""
    # Find matching benchmark case
    matched_benchmark = next((c for c in BENCHMARK_CASES if c["case_id"] == case_id), None)
    
    # Try loading pre-calculated answer
    idx = next((i for i, c in enumerate(BENCHMARK_CASES, 1) if c["case_id"] == case_id), None)
    if idx:
        num_str = f"{idx:02d}"
        answer_file = os.path.join(output_dir, f"case_{num_str}_answer.json")
        if os.path.exists(answer_file):
            with open(answer_file, "r") as f:
                answer = json.load(f)
                return jsonify({
                    "benchmark_case": matched_benchmark,
                    "answer": answer
                })

    # If not on disk, run dynamically
    if matched_benchmark:
        answer = agent.run_investigation(matched_benchmark)
        return jsonify({
            "benchmark_case": matched_benchmark,
            "answer": answer
        })

    return jsonify({"error": f"Case {case_id} not found"}), 404

@app.route("/api/investigate", methods=["POST"])
def run_investigation():
    """Runs autonomous investigation on a case or on-the-fly custom transaction."""
    payload = request.get_json() or {}
    case_id = payload.get("case_id")
    simulated_evidence = payload.get("simulated_evidence")

    target_case = next((c for c in BENCHMARK_CASES if c["case_id"] == case_id), None)
    if not target_case:
        # Create ad-hoc case from payload
        target_case = {
            "case_id": case_id or "CASE_CUSTOM",
            "trigger_type": payload.get("trigger_type", "MODEL_SCORE"),
            "customer_id": payload.get("customer_id", "CUST_CUSTOM"),
            "transaction": payload.get("transaction", {})
        }

    result = agent.run_investigation(target_case, simulated_evidence_response=simulated_evidence)
    return jsonify(result)

@app.route("/api/graph/subgraph/<center_id>", methods=["GET"])
def get_subgraph(center_id):
    """Returns D3-formatted node-link data centered on an entity or case."""
    hops = int(request.args.get("hops", 2))
    # Look for matching transaction or account
    subgraph = connector.fetch_case_subgraph(center_id, hops=hops)
    return jsonify(subgraph)

@app.route("/api/copilot/chat", methods=["POST"])
def copilot_chat():
    """Allows investigators to ask questions in plain English to the AI Copilot."""
    payload = request.get_json() or {}
    case_id = payload.get("case_id", "CASE_01")
    message = payload.get("message", "")

    # Retrieve case answer
    matched_benchmark = next((c for c in BENCHMARK_CASES if c["case_id"] == case_id), None)
    idx = next((i for i, c in enumerate(BENCHMARK_CASES, 1) if c["case_id"] == case_id), None)
    case_answer = {}
    if idx:
        num_str = f"{idx:02d}"
        answer_file = os.path.join(output_dir, f"case_{num_str}_answer.json")
        if os.path.exists(answer_file):
            with open(answer_file, "r") as f:
                case_answer = json.load(f)

    if not case_answer and matched_benchmark:
        case_answer = agent.run_investigation(matched_benchmark)

    reply = agent.chat_with_copilot(message, case_answer)
    return jsonify({"reply": reply, "case_id": case_id})

@app.route("/api/benchmark/summary", methods=["GET"])
def get_benchmark_summary():
    """Returns evaluation metrics across the 20 benchmark cases."""
    summary_file = os.path.join(os.path.dirname(__file__), "output", "benchmark_summary.json")
    if os.path.exists(summary_file):
        with open(summary_file, "r") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Benchmark summary not generated"}), 404

@app.route("/api/tigergraph/status", methods=["GET"])
def tigergraph_status():
    """Returns status of TigerGraph connector (embedded vs live Savanna)."""
    return jsonify({
        "mode": connector.mode,
        "host": connector.host,
        "graph_name": connector.graph_name,
        "total_vertices": len(connector.graph.nodes),
        "total_edges": len(connector.graph.edges),
        "connected_to_savanna": bool(connector.live_client is not None)
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    host = os.getenv("HOST", "127.0.0.1")
    logger.info(f"Starting TigerGraph Fraud Agent Web Server on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
