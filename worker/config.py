"""Config loader — stdlib only, YAML optional."""
from pathlib import Path

DEFAULTS = {"approval_threshold": 5000, "max_steps": 12, "auto_approve": False}

def load_config(path="config.yaml"):
    cfg = dict(DEFAULTS)
    p = Path(path)
    if p.exists():
        try:
            import yaml  # optional
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            cfg.update(data)
        except ImportError:
            # minimal fallback parser for key: value lines
            for line in p.read_text(encoding="utf-8").splitlines():
                if ":" in line and not line.strip().startswith("#"):
                    k, v = line.split(":", 1)
                    k, v = k.strip(), v.strip()
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
                    else:
                        try:
                            v = int(v)
                        except ValueError:
                            pass
                    cfg[k] = v
        except Exception:
            pass
    return cfg

