"""
Benchmark Evaluation Runner
Executes the Autonomous Fraud Agent against the 20 hackathon benchmark cases (Months 5 & 6)
and outputs standard answer files in `output/cases/case_XX_answer.json`.
"""

import os
import json
import logging
from typing import Dict, List, Any

from ..graph.tigergraph_connector import TigerGraphConnector
from ..agent.investigation_agent import InvestigationAgent
from .benchmark_dataset import BENCHMARK_CASES, seed_graph_with_benchmark_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class BenchmarkRunner:
    def __init__(self, output_dir: str = "output/cases"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize Graph Engine & Agent
        self.connector = TigerGraphConnector(mode="embedded")
        seed_graph_with_benchmark_data(self.connector)
        self.agent = InvestigationAgent(self.connector)

    def run_all_cases(self) -> Dict[str, Any]:
        """Runs the agent across all 20 cases and writes individual answer files."""
        results_summary = []
        
        logger.info(f"Starting Benchmark Evaluation on {len(BENCHMARK_CASES)} Cases...")
        
        for idx, case in enumerate(BENCHMARK_CASES, start=1):
            case_id = case["case_id"]
            logger.info(f"Running Agent on {case_id}: {case['title']}")
            
            # Execute investigation
            answer = self.agent.run_investigation(case)
            
            # Format filename case_01_answer.json ... case_20_answer.json
            num_str = f"{idx:02d}"
            filename = f"case_{num_str}_answer.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(answer, f, indent=2)
                
            sar_status = "FILED" if isinstance(answer.get("suspicious_activity_report"), dict) else "NOT_REQUIRED"
            pre_nba = answer["next_best_action"]["before_additional_evidence"]["recommended_action"]
            post_nba = answer["next_best_action"]["after_additional_evidence"]["recommended_action"]
            
            summary_entry = {
                "case_id": case_id,
                "case_file": filename,
                "title": case["title"],
                "trigger": case["trigger_type"],
                "amount": case["transaction"]["amount"],
                "final_status": answer["case_summary"]["status"],
                "risk_score": answer["case_summary"]["assessed_risk_score"],
                "pattern": answer["case_summary"]["detected_pattern"],
                "sar_status": sar_status,
                "pre_evidence_nba": pre_nba,
                "post_evidence_nba": post_nba,
                "approval_route": answer["next_best_action"]["after_additional_evidence"]["required_approval_route"]
            }
            results_summary.append(summary_entry)
            logger.info(f"-> Completed {case_id} => Status: {answer['case_summary']['status']} | Pre-NBA: {pre_nba} | Post-NBA: {post_nba} | SAR: {sar_status}")

        # Save benchmark summary
        summary_path = os.path.join("output", "benchmark_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_cases_evaluated": len(BENCHMARK_CASES),
                "fraud_cases_detected": sum(1 for r in results_summary if "FRAUD" in r["final_status"]),
                "cleared_cases": sum(1 for r in results_summary if "CLEARED" in r["final_status"]),
                "sar_filings_generated": sum(1 for r in results_summary if r["sar_status"] == "FILED"),
                "cases": results_summary
            }, f, indent=2)

        logger.info(f"Benchmark evaluation complete! All 20 answer files saved in {self.output_dir}/")
        return {"total": len(BENCHMARK_CASES), "summary_path": summary_path}

if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run_all_cases()
