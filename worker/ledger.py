import json, datetime
from pathlib import Path

class Ledger:
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / "ledger.jsonl"

    def log(self, entry: dict):
        entry = {"ts": datetime.datetime.utcnow().isoformat() + "Z", **entry}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry
