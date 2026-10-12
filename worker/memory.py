from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class Memory:
    facts: Dict[str, Any] = field(default_factory=dict)
    entities: Dict[str, Any] = field(default_factory=dict)
    trajectory: List[Dict[str, Any]] = field(default_factory=list)

    def remember(self, key: str, value: Any):
        self.facts[key] = value

    def note(self, entry: Dict[str, Any]):
        self.trajectory.append(entry)
