"""Canned demo: reset ERP, run invoice task, show evidence."""
import json, shutil
from pathlib import Path
from worker.config import load_config
from worker.agent import Agent

Path("data/erp.json").write_text(json.dumps({"entries": []}, indent=2))
cfg = load_config()
agent = Agent(cfg, "runs/demo", auto_approve=True)
r = agent.run("Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done.")
print(r["summary"])
print("ERP now:", Path("data/erp.json").read_text())
