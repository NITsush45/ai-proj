import re
from pathlib import Path
from worker.schemas import Observation

def tool_browser_open(url: str = ""):
    """Simulated browser: reads local vendor-portal mirror in data/web/."""
    try:
        web = Path("data/web")
        slug = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-") or "portal"
        cands = list(web.glob("*.html"))
        if not cands:
            return Observation(False, None, "browser: no portal pages cached")
        # pick best match or latest-invoice page
        best = None
        for c in cands:
            if slug.split("-")[0] in c.stem.lower():
                best = c
                break
        best = best or cands[0]
        html = best.read_text(encoding="utf-8")
        m = re.search(r"\{.*\}", html, re.S)
        return Observation(True, {"page": best.name, "html": html[:2000], "embedded": m.group(0) if m else ""},
                           evidence=f"browser opened {best.name}")
    except Exception as e:
        return Observation(False, None, f"browser error: {e}")

def tool_files_read(path: str):
    try:
        p = Path(path)
        if not p.exists():
            return Observation(False, None, f"file not found: {path}")
        return Observation(True, {"path": path, "content": p.read_text(encoding="utf-8")[:4000]},
                           evidence=f"read {path}")
    except Exception as e:
        return Observation(False, None, f"read error: {e}")

def tool_files_scan(keyword: str = ""):
    from pathlib import Path as P
    hits = []
    for f in P("data/inbox").glob("*.json"):
        t = f.read_text(encoding="utf-8")
        if keyword.lower() in t.lower():
            hits.append(f.name)
    if not hits:
        return Observation(False, None, f"scan: no files match '{keyword}'")
    return Observation(True, hits, evidence=f"scan matched {hits}")
