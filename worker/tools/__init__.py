"""Tool package. Use worker.tools.registry.REGISTRY / call (import registry lazily to avoid cycles)."""
__all__ = ["REGISTRY", "call"]

def __getattr__(name):
    if name in ("REGISTRY", "call"):
        from worker.tools import registry as _r
        return getattr(_r, name)
    raise AttributeError(name)

