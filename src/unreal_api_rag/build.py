"""Introspect the live ``unreal`` module into a JSONL corpus.

Runs **inside the Unreal Editor's Python** (only there is ``import unreal``
available) — e.g. via ForgeMCP's ``run_editor_python`` or the editor console:

    import unreal_api_rag.build as b
    b.dump("/path/to/ue_api_5.8.jsonl")

Each line is one API symbol:
    {"symbol": "unreal.EditorActorSubsystem.spawn_actor_from_class",
     "kind": "method", "class": "EditorActorSubsystem",
     "signature": "...", "doc": "..."}
"""
from __future__ import annotations

import inspect
import json
from typing import Any, Dict, Iterator


def _entry(symbol: str, kind: str, obj: Any, cls: str | None = None) -> Dict[str, Any]:
    doc = inspect.getdoc(obj) or ""
    signature = ""
    try:
        signature = str(inspect.signature(obj))
    except (ValueError, TypeError):
        # UE C++-backed callables often lack a Python signature; the docstring's
        # first line usually carries it (e.g. "x.foo(a, b) -> T").
        signature = doc.splitlines()[0] if doc else ""
    return {"symbol": symbol, "kind": kind, "class": cls,
            "signature": signature, "doc": doc[:2000]}


def iter_entries(module: Any) -> Iterator[Dict[str, Any]]:
    """Yield one entry per public class/function/method of ``module``."""
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name, None)
        if obj is None:
            continue
        if inspect.isclass(obj):
            yield _entry(f"unreal.{name}", "class", obj)
            for mname in dir(obj):
                if mname.startswith("_"):
                    continue
                member = getattr(obj, mname, None)
                if callable(member):
                    yield _entry(f"unreal.{name}.{mname}", "method", member, cls=name)
        elif callable(obj):
            yield _entry(f"unreal.{name}", "function", obj)


def dump(out_path: str, dedup_methods: bool = True) -> int:
    """Introspect the live ``unreal`` module and write the JSONL corpus.

    ``dedup_methods`` collapses methods that share a name + signature across
    subclasses (UE's `dir()` re-lists inherited members on every class), which
    shrinks the corpus by ~5x with negligible information loss.
    """
    import unreal  # only importable inside the UE editor
    count = 0
    seen_symbols: set = set()
    seen_methods: set = set()  # (method_name, signature) global dedup
    with open(out_path, "w") as f:
        for entry in iter_entries(unreal):
            sym = entry["symbol"]
            if sym in seen_symbols:
                continue
            if dedup_methods and entry["kind"] == "method":
                key = (sym.rsplit(".", 1)[-1], entry["signature"][:160])
                if key in seen_methods:
                    continue
                seen_methods.add(key)
            seen_symbols.add(sym)
            f.write(json.dumps(entry) + "\n")
            count += 1
    return count
