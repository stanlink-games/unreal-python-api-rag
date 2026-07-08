import types

from unreal_api_rag import build
from unreal_api_rag.search import ApiIndex

CORPUS = [
    {"symbol": "unreal.EditorActorSubsystem", "kind": "class", "class": None,
     "signature": "", "doc": "Subsystem for editor actor operations."},
    {"symbol": "unreal.EditorActorSubsystem.spawn_actor_from_class", "kind": "method",
     "class": "EditorActorSubsystem",
     "signature": "(actor_class, location, rotation) -> Actor",
     "doc": "Spawn an actor of the given class at a transform."},
    {"symbol": "unreal.Vector", "kind": "class", "class": None,
     "signature": "", "doc": "A 3D vector x y z."},
]


def test_search_ranks_symbol_name_matches_first():
    idx = ApiIndex(CORPUS)
    res = idx.search("spawn actor", k=3)
    assert res and res[0]["symbol"].endswith("spawn_actor_from_class")


def test_get_symbol_exact_and_suffix_and_miss():
    idx = ApiIndex(CORPUS)
    assert idx.get_symbol("unreal.Vector")["kind"] == "class"
    assert idx.get_symbol("spawn_actor_from_class")["class"] == "EditorActorSubsystem"
    assert idx.get_symbol("does_not_exist") is None


def test_search_empty_query_returns_nothing():
    assert ApiIndex(CORPUS).search("") == []


class _Vector:
    """A 3D vector."""
    def dot(self, other):
        """Dot product."""


def _spawn():
    """Spawn something."""


def test_iter_entries_walks_classes_and_methods():
    fake = types.SimpleNamespace(Vector=_Vector, spawn=_spawn)
    syms = {e["symbol"] for e in build.iter_entries(fake)}
    assert "unreal.Vector" in syms          # class
    assert "unreal.Vector.dot" in syms      # method
    assert "unreal.spawn" in syms           # function
