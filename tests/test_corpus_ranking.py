"""Ranking quality guardrails against the REAL bundled UE 5.8 corpus.

These lock in retrieval quality so a future change to scoring can't silently
regress the queries the agent actually issues. Skipped only if the bundled
corpus is unavailable (it ships inside the package).
"""
import pytest

from unreal_api_rag.corpus import load_corpus
from unreal_api_rag.search import ApiIndex

try:
    _ENTRIES = load_corpus()
except Exception:  # pragma: no cover - corpus should ship with the package
    _ENTRIES = []

pytestmark = pytest.mark.skipif(len(_ENTRIES) < 1000,
                                reason="bundled UE corpus not available")


@pytest.fixture(scope="module")
def idx():
    return ApiIndex(_ENTRIES)


# (query, substring the #1 result's symbol must contain)
TOP1 = [
    ("set actor location", "set_actor_location"),
    ("spawn actor from class", "spawn_actor_from_class"),
    ("create dynamic material instance", "create_dynamic_material_instance"),
    ("line trace single", "line_trace_single"),
]

# (query, substring that must appear somewhere in the top-5)
TOP5 = [
    ("sky atmosphere", "SkyAtmosphere"),
    ("play level sequence", "play_level_sequence"),
    ("load asset", "load_asset"),
    ("set directional light intensity", "intensity"),
]


@pytest.mark.parametrize("query,needle", TOP1)
def test_top1(idx, query, needle):
    res = idx.search(query, k=5)
    assert res, f"no results for {query!r}"
    assert needle.lower() in res[0]["symbol"].lower(), \
        f"{query!r} -> {res[0]['symbol']} (wanted {needle})"


@pytest.mark.parametrize("query,needle", TOP5)
def test_top5(idx, query, needle):
    syms = [r["symbol"].lower() for r in idx.search(query, k=5)]
    assert any(needle.lower() in s for s in syms), \
        f"{query!r} top5={syms} (wanted {needle})"


def test_kind_filter_only_returns_that_kind(idx):
    res = idx.search("component", k=20, kind="class")
    assert res and all(r["kind"] == "class" for r in res)
