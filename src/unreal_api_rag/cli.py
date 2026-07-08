"""CLI: build the corpus (in-editor) or run the retrieval MCP server."""
from __future__ import annotations

import argparse
from typing import Optional, Sequence


def main(argv: Optional[Sequence[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="unreal-api-rag",
                                description="Unreal Engine Python API — retrieval / MCP knowledge server.")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build-corpus",
                       help="Introspect the live `unreal` module -> JSONL (run inside the UE editor's Python).")
    b.add_argument("--out", required=True, help="Output JSONL path.")

    m = sub.add_parser("mcp", help="Run the retrieval MCP server (Streamable HTTP at /mcp).")
    m.add_argument("--host", default="127.0.0.1")
    m.add_argument("--port", type=int, default=8780)
    m.add_argument("--corpus", default=None, help="Corpus JSONL path (default: bundled / $UAPI_CORPUS).")

    s = sub.add_parser("search", help="Query the bundled corpus from the terminal.")
    s.add_argument("query", nargs="+", help="Free-text query.")
    s.add_argument("-k", type=int, default=8, help="Number of results.")
    s.add_argument("--kind", choices=["class", "method", "function"], default=None)
    s.add_argument("--corpus", default=None)

    args = p.parse_args(argv)
    if args.cmd == "build-corpus":
        from unreal_api_rag.build import dump
        n = dump(args.out)
        print(f"wrote {n} symbols -> {args.out}")
    elif args.cmd == "mcp":
        from unreal_api_rag.server import run
        run(args.host, args.port, args.corpus)
    elif args.cmd == "search":
        from unreal_api_rag.corpus import load_corpus
        from unreal_api_rag.search import ApiIndex
        idx = ApiIndex(load_corpus(args.corpus))
        for r in idx.search(" ".join(args.query), k=args.k, kind=args.kind):
            sig = (r.get("signature") or "").split("\n")[0][:100]
            print(f"{r.get('symbol')}  [{r.get('kind')}]\n    {sig}")


if __name__ == "__main__":
    main()
