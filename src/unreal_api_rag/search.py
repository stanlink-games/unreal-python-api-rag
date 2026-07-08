"""Retrieval over the UE API corpus.

Dependency-light **lexical** search (zero extra deps) with quality tuned for the
way developers actually query an engine API:

* a tokenizer that splits ``snake_case``, ``CamelCase`` and digit runs into
  words, so ``"set actor location"`` matches the symbol ``set_actor_location``;
* **IDF weighting** so discriminative terms (``heightmap``) outweigh ubiquitous
  ones (``get``, ``actor``);
* **field boosting** — a hit in the symbol/member name counts far more than a
  hit buried in the docstring;
* **phrase/prefix** bonuses so an exact or near-exact member name wins outright.

Semantic embedding search is a planned optional upgrade behind the same
interface, so callers never change.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

# Split on non-alphanumerics, then break CamelCase and letter/digit boundaries.
_CAMEL = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])"        # fooBar   -> foo Bar
    r"|(?<=[A-Z])(?=[A-Z][a-z])"     # HUDWidget-> HUD Widget
    r"|(?<=[a-zA-Z])(?=[0-9])"       # Vector2  -> Vector 2
    r"|(?<=[0-9])(?=[a-zA-Z])"       # 2D       -> 2 D
)
_NONWORD = re.compile(r"[^A-Za-z0-9]+")


def _stem(w: str) -> str:
    """Conservative plural -> singular so 'materials' matches 'material'.

    Deliberately minimal (no aggressive suffix stripping) to protect precision:
    only the common English plural endings, and never below 4 chars.
    """
    if len(w) > 4:
        if w.endswith("ies"):
            return w[:-3] + "y"          # properties -> property
        if w.endswith(("ses", "xes", "zes", "ches", "shes")):
            return w[:-2]                # meshes -> mesh, boxes -> box
        if w.endswith("s") and not w.endswith(("ss", "us", "is")):
            return w[:-1]                # lights -> light, actors -> actor
    return w


def _words(s: Optional[str]) -> List[str]:
    """``'SetActorLocation2'`` / ``'set_actor_location_2'`` -> [set, actor, location, 2]."""
    if not s:
        return []
    spaced = _CAMEL.sub(" ", s)
    return [_stem(w) for w in _NONWORD.sub(" ", spaced).lower().split() if w]


def _norm(s: Optional[str]) -> str:
    """Normalised, separator-free form for phrase/prefix comparison."""
    return "".join(_words(s))


# Field weights: a name hit dwarfs a doc hit; the member (leaf) name dwarfs the
# owning class name.
_W_MEMBER = 8.0
_W_CLASS = 3.0
_W_DOC = 1.0


class _Entry:
    __slots__ = ("raw", "member_words", "class_words", "doc_words",
                 "member_norm", "kind")

    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw
        symbol = raw.get("symbol", "") or ""
        member = symbol.rsplit(".", 1)[-1]
        class_name = raw.get("class") or ""
        self.member_words = set(_words(member))
        self.class_words = set(_words(class_name))
        self.doc_words = set(_words(raw.get("doc", ""))) | set(_words(raw.get("signature", "")))
        self.member_norm = _norm(member)
        self.kind = (raw.get("kind") or "").lower()


class ApiIndex:
    """In-memory lexical index over corpus entries."""

    def __init__(self, entries: List[Dict[str, Any]]):
        self.entries = entries
        self.by_symbol = {e.get("symbol"): e for e in entries if e.get("symbol")}
        self._by_symbol_low = {s.lower(): e for s, e in self.by_symbol.items()}
        self._items = [_Entry(e) for e in entries]

        # Document frequency across the union of all word fields per entry, for IDF.
        n = max(1, len(self._items))
        df: Dict[str, int] = {}
        for it in self._items:
            for w in (it.member_words | it.class_words | it.doc_words):
                df[w] = df.get(w, 0) + 1
        # Smoothed IDF: common words -> ~0, rare words -> high.
        self._idf = {w: math.log(1.0 + n / c) for w, c in df.items()}
        self._n = n

    def _w(self, word: str) -> float:
        return self._idf.get(word, math.log(1.0 + self._n))

    def get_symbol(self, name: str) -> Optional[Dict[str, Any]]:
        """Exact symbol, then case-insensitive exact, then a suffix match
        (bare member name like ``'set_actor_location'``)."""
        if not name:
            return None
        if name in self.by_symbol:
            return self.by_symbol[name]
        hit = self._by_symbol_low.get(name.lower())
        if hit is not None:
            return hit
        suffix = "." + name
        suffix_low = suffix.lower()
        fallback = None
        for sym, entry in self.by_symbol.items():
            if sym.endswith(suffix):
                return entry            # exact-case suffix wins
            if fallback is None and sym.lower().endswith(suffix_low):
                fallback = entry
        return fallback

    def search(self, query: str, k: int = 8,
               kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """Rank corpus entries against a free-text query.

        ``kind`` optionally filters to ``'class'`` / ``'method'`` / ``'function'``.
        """
        q_words = _words(query)
        if not q_words:
            return []
        q_set = set(q_words)
        q_norm = "".join(q_words)
        kind_f = kind.lower() if kind else None

        scored = []
        for it in self._items:
            if kind_f and it.kind != kind_f:
                continue

            member_hits = q_set & it.member_words
            class_hits = q_set & it.class_words
            doc_hits = q_set & it.doc_words
            if not (member_hits or class_hits or doc_hits):
                continue

            score = (_W_MEMBER * sum(self._w(w) for w in member_hits)
                     + _W_CLASS * sum(self._w(w) for w in class_hits)
                     + _W_DOC * sum(self._w(w) for w in doc_hits))

            # Coverage: reward matching ALL query words in the member name.
            if member_hits:
                score *= 1.0 + len(member_hits) / len(q_set)

            # Phrase / prefix bonuses on the member name (separator-free).
            if it.member_norm:
                if it.member_norm == q_norm:
                    score += 1000.0                     # exact member name
                elif it.member_norm.startswith(q_norm) or q_norm.startswith(it.member_norm):
                    score += 120.0                      # prefix either way
                elif q_norm in it.member_norm:
                    score += 40.0                       # substring

            if score > 0:
                # Tie-break toward shorter (more canonical) symbols.
                scored.append((score, -len(it.raw.get("symbol", "")), it.raw))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [raw for _, _, raw in scored[:k]]
