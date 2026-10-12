from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

@dataclass
class Step:
    id: int
    goal: str
    tool: str
    args: Dict[str, Any] = field(default_factory=dict)
    why: str = ""
    done: bool = False

@dataclass
class Plan:
    goal: str
    steps: List[Step]

@dataclass
class Observation:
    success: bool
    data: Any = None
    error: str = ""
    evidence: str = ""

    def to_dict(self):
        return {"success": self.success, "data": self.data, "error": self.error, "evidence": self.evidence}
