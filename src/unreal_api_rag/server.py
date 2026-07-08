"""MCP server exposing UE API retrieval — plugs into any MCP client (Forge,
Claude, kiro, GPT). Stateless Streamable HTTP, mounted at /mcp (same shape as
the ForgeMCP editor + Clay servers)."""
from __future__ import annotations

import json
from typing import AsyncIterator, Optional

import mcp.types as mcp_types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount

from unreal_api_rag.corpus import load_corpus
from unreal_api_rag.search import ApiIndex


def build_server(corpus_path: Optional[str] = None) -> Server:
    index = ApiIndex(load_corpus(corpus_path))
    server = Server("unreal-api-rag")

    @server.list_tools()
    async def _list_tools():
        return [
            mcp_types.Tool(
                name="search_ue_api",
                description=("Search the Unreal Engine Python API (`unreal` module) for classes/"
                             "methods matching a task, returning signatures + docs. Call this "
                             "BEFORE writing UE editor Python so you use real API, not guesses."),
                inputSchema={"type": "object",
                             "properties": {"query": {"type": "string"},
                                            "k": {"type": "integer"},
                                            "kind": {"type": "string",
                                                     "enum": ["class", "method", "function"],
                                                     "description": "Optional filter."}},
                             "required": ["query"]},
            ),
            mcp_types.Tool(
                name="get_symbol",
                description=("Exact lookup of a UE Python symbol (e.g. "
                             "'unreal.EditorActorSubsystem' or 'spawn_actor_from_class') → "
                             "its signature + docstring."),
                inputSchema={"type": "object",
                             "properties": {"name": {"type": "string"}},
                             "required": ["name"]},
            ),
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict):
        if name == "search_ue_api":
            res = index.search(str(arguments.get("query", "")),
                               int(arguments.get("k", 8) or 8),
                               kind=arguments.get("kind") or None)
            # Lean payload: full signature, trimmed doc (use get_symbol for the rest).
            lean = [{"symbol": r.get("symbol"), "kind": r.get("kind"),
                     "signature": r.get("signature"),
                     "doc": (r.get("doc") or "")[:400]} for r in res]
            return [mcp_types.TextContent(type="text", text=json.dumps(lean, indent=1))]
        if name == "get_symbol":
            res = index.get_symbol(str(arguments.get("name", "")))
            return [mcp_types.TextContent(type="text", text=json.dumps(res))]
        return [mcp_types.TextContent(type="text", text=json.dumps({"error": f"unknown tool {name}"}))]

    return server


def create_app(corpus_path: Optional[str] = None) -> Starlette:
    server = build_server(corpus_path)
    manager = StreamableHTTPSessionManager(app=server, json_response=True, stateless=True)

    async def handle(scope, receive, send):
        await manager.handle_request(scope, receive, send)

    async def lifespan(_app) -> AsyncIterator[None]:
        async with manager.run():
            yield

    return Starlette(routes=[Mount("/mcp", app=handle)], lifespan=lifespan)


def run(host: str = "127.0.0.1", port: int = 8780, corpus_path: Optional[str] = None) -> None:
    import uvicorn
    n = len(load_corpus(corpus_path))
    print(f"Unreal API RAG MCP — http://{host}:{port}/mcp/ ({n} symbols)")
    uvicorn.run(create_app(corpus_path), host=host, port=port)
