"""Load the UE API corpus (JSONL) — bundled with the package or an explicit path."""
from __future__ import annotations

import gzip
import json
import os
from typing import Any, Dict, List, Optional


def default_corpus_path() -> str:
    """Path to the corpus bundled in the package, or $UAPI_CORPUS, or ''."""
    try:
        from importlib import resources
        base = resources.files("unreal_api_rag.data")
        for name in ("ue_api.jsonl.gz", "ue_api_5.8.jsonl.gz",
                     "ue_api.jsonl", "ue_api_5.8.jsonl"):
            cand = base / name
            if cand.is_file():
                return str(cand)
    except Exception:
        pass
    return os.environ.get("UAPI_CORPUS", "")


def load_corpus(path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = path or default_corpus_path()
    entries: List[Dict[str, Any]] = []
    if path and os.path.isfile(path):
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    return entries
