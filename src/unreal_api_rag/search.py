"""Retrieval over the UE API corpus.

Dependency-light **keyword/overlap** scoring (works with zero extra deps).
Semantic embedding search is an optional upgrade (see the `semantic` extra) and
the same interface — so callers don't change.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _tokens(s: Optional[str]) -> set:
    return set(re.findall(r"[a-z0-9_]+", (s or "").lower()))


class ApiIndex:
    """In-memory index over corpus entries."""

    def __init__(self, entries: List[Dict[str, Any]]):
        self.entries = entries
        self.by_symbol = {e.get("symbol"): e for e in entries if e.get("symbol")}

    def get_symbol(self, name: str) -> Optional[Dict[str, Any]]:
        """Exact symbol, then a suffix match (e.g. bare 'spawn_actor_from_class')."""
        if not name:
            return None
        if name in self.by_symbol:
            return self.by_symbol[name]
        suffix = "." + name
        for sym, entry in self.by_symbol.items():
            if sym.endswith(suffix):
                return entry
        return None

    def search(self, query: str, k: int = 8) -> List[Dict[str, Any]]:
        """Token-overlap ranking; matches on the symbol name are boosted."""
        q = _tokens(query)
        if not q:
            return []
        scored = []
        for e in self.entries:
            sym_tokens = _tokens(e.get("symbol", ""))
            hay = sym_tokens | _tokens(e.get("doc", "")) | _tokens(e.get("signature", ""))
            overlap = len(q & hay)
            if overlap:
                score = overlap + 2 * len(q & sym_tokens)   # boost symbol-name hits
                scored.append((score, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:k]]
