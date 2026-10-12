from worker.schemas import Observation
from worker.tools.inbox import tool_inbox_search
from worker.tools.parse import tool_invoice_parse
from worker.tools.erp import tool_erp_lookup, tool_erp_book
from worker.tools.webfiles import tool_browser_open, tool_files_read, tool_files_scan

REGISTRY = {
    "inbox.search": tool_inbox_search,
    "invoice.parse": tool_invoice_parse,
    "erp.lookup": tool_erp_lookup,
    "erp.book": tool_erp_book,
    "browser.open": tool_browser_open,
    "files.read": tool_files_read,
    "files.scan": tool_files_scan,
}

# fallback chain on failure
FALLBACKS = {
    "inbox.search": ["files.scan", "browser.open"],
    "invoice.parse": ["files.read"],
    "browser.open": ["files.scan"],
}

def call(tool: str, args: dict) -> Observation:
    fn = REGISTRY.get(tool)
    if not fn:
        return Observation(False, None, f"unknown tool: {tool}")
    try:
        return fn(**{k: v for k, v in args.items()})
    except TypeError as e:
        return Observation(False, None, f"bad args for {tool}: {e}")
    except Exception as e:
        return Observation(False, None, f"{tool} crashed: {e}")
