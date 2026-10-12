"""Approval + clarification gate. Auto-approve reads, confirm money movement."""

class UserNeeded(Exception):
    def __init__(self, question: str, options=None):
        super().__init__(question)
        self.question = question
        self.options = options or []

def needs_approval(tool: str, args: dict, threshold: float) -> bool:
    if tool == "erp.book":
        try:
            return float(args.get("amount", 0)) >= threshold
        except Exception:
            return True
    return False

def check(tool: str, args: dict, cfg: dict, auto_approve: bool = False):
    # unresolved placeholders -> ask user instead of hallucinating
    for v in args.values():
        if isinstance(v, str) and v.startswith("__"):
            raise UserNeeded(f"Missing info for {tool}: {v}. Please provide it.",
                             options=["Provide value", "Abort"])
    if needs_approval(tool, args, cfg.get("approval_threshold", 5000)) and not (auto_approve or cfg.get("auto_approve")):
        raise UserNeeded(
            f"Approve booking {args.get('invoice_id')} for {args.get('vendor')} "
            f"${args.get('amount')} due {args.get('due_date')}?",
            options=["Approve", "Abort"])
