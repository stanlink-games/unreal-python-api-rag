import types

from unreal_api_rag import build
from unreal_api_rag.search import ApiIndex, _words, _norm

CORPUS = [
    {"symbol": "unreal.EditorActorSubsystem", "kind": "class", "class": None,
     "signature": "", "doc": "Subsystem for editor actor operations."},
    {"symbol": "unreal.EditorActorSubsystem.spawn_actor_from_class", "kind": "method",
     "class": "EditorActorSubsystem",
     "signature": "(actor_class, location, rotation) -> Actor",
     "doc": "Spawn an actor of the given class at a transform."},
    {"symbol": "unreal.AIController.set_actor_location", "kind": "method",
     "class": "AIController",
     "signature": "set_actor_location(new_location, sweep=False) -> bool",
     "doc": "Move the actor instantly to the specified location."},
    {"symbol": "unreal.AIController.receive_hit", "kind": "method",
     "class": "AIController",
     "signature": "receive_hit(my_comp, other, hit_location, hit_normal) -> None",
     "doc": "Event when this actor bumps into a blocking object with a hit location."},
    {"symbol": "unreal.Vector", "kind": "class", "class": None,
     "signature": "", "doc": "A 3D vector x y z."},
    {"symbol": "unreal.Landscape.set_heightmap", "kind": "method",
     "class": "Landscape",
     "signature": "set_heightmap(data) -> None",
     "doc": "Apply a heightmap to sculpt the terrain."},
]


# ---- tokenizer -------------------------------------------------------------

def test_words_splits_snake_camel_and_digits():
    assert _words("set_actor_location") == ["set", "actor", "location"]
    assert _words("SetActorLocation") == ["set", "actor", "location"]
    assert _words("GetHUD2") == ["get", "hud", "2"]
    assert _words("") == []


def test_norm_is_separator_free():
    assert _norm("set_actor_location") == "setactorlocation"
    assert _norm("SetActorLocation") == "setactorlocation"


# ---- ranking ---------------------------------------------------------------

def test_snake_query_matches_snake_symbol_first():
    # The core bug: "set actor location" must rank set_actor_location #1,
    # NOT receive_hit (which only shares "location" via its doc).
    idx = ApiIndex(CORPUS)
    res = idx.search("set actor location", k=3)
    assert res[0]["symbol"].endswith("set_actor_location")


def test_search_ranks_symbol_name_matches_first():
    idx = ApiIndex(CORPUS)
    res = idx.search("spawn actor", k=3)
    assert res[0]["symbol"].endswith("spawn_actor_from_class")


def test_discriminative_term_wins():
    idx = ApiIndex(CORPUS)
    res = idx.search("heightmap terrain", k=3)
    assert res[0]["symbol"].endswith("set_heightmap")


def test_exact_member_name_query():
    idx = ApiIndex(CORPUS)
    res = idx.search("set_actor_location", k=3)
    assert res[0]["symbol"].endswith("set_actor_location")


def test_kind_filter():
    idx = ApiIndex(CORPUS)
    res = idx.search("actor", k=10, kind="class")
    assert res and all(e["kind"] == "class" for e in res)


# ---- get_symbol ------------------------------------------------------------

def test_get_symbol_exact_and_suffix_and_miss():
    idx = ApiIndex(CORPUS)
    assert idx.get_symbol("unreal.Vector")["kind"] == "class"
    assert idx.get_symbol("spawn_actor_from_class")["class"] == "EditorActorSubsystem"
    assert idx.get_symbol("does_not_exist") is None


def test_get_symbol_case_insensitive():
    idx = ApiIndex(CORPUS)
    assert idx.get_symbol("unreal.vector")["symbol"] == "unreal.Vector"


def test_search_empty_query_returns_nothing():
    assert ApiIndex(CORPUS).search("") == []


# ---- builder (unchanged behaviour) -----------------------------------------

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
