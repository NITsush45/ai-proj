"""CLI: python run.py --task "..." [--auto-approve]"""
import argparse, uuid
from worker.config import load_config
from worker.agent import Agent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--auto-approve", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    run_dir = f"runs/{uuid.uuid4().hex[:8]}"
    agent = Agent(cfg, run_dir, auto_approve=args.auto_approve)
    result = agent.run(args.task)
    print("=" * 60)
    print(result["summary"])
    if result.get("needs_user"):
        print("ACTION REQUIRED:", result["needs_user"])
        print("Re-run with --auto-approve to approve, or approve in web UI.")
    print(f"Evidence: {run_dir}/ledger.jsonl + {run_dir}/summary.md")

if __name__ == "__main__":
    main()
