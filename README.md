# unreal-python-api-rag

> The Unreal Engine Python API as a **retrieval / MCP knowledge server** — so any
> AI agent writes **correct, version-exact** UE Editor Python instead of guessing.

LLMs hallucinate the `unreal` API (wrong class names, arg orders, deprecated
calls). This grounds them: it introspects the API **straight from your engine**
and serves it over **MCP**, so agents retrieve the real signatures/docs before
they write code. Plugs into **Forge, Claude, kiro, GPT** — anything that speaks MCP.

## Install
```bash
pip install git+https://github.com/stanlink-games/unreal-python-api-rag.git
```
Python 3.10+. Lexical search needs no extra deps; semantic search is the optional
`[semantic]` extra.

## 1. Build the corpus (version-exact, from your engine)
Run **inside the UE editor's Python** (only there is `import unreal` available) —
e.g. via ForgeMCP's `run_editor_python` or the editor console:
```python
import unreal_api_rag.build as b
b.dump("/path/to/ue_api_5.8.jsonl")   # one JSON line per class/method/function
```
Ship that JSONL in `src/unreal_api_rag/data/` and it's bundled with the package.

## 2. Serve it over MCP
```bash
unreal-api-rag mcp --host 127.0.0.1 --port 8780
# → http://127.0.0.1:8780/mcp/   (Streamable HTTP, stateless)
```
Tools:
- **`search_ue_api(query, k=8, kind=None)`** — rank matching classes/methods by
  relevance (signatures + docs). `kind` optionally filters to
  `class` / `method` / `function`.
- **`get_symbol(name)`** — exact lookup (e.g. `unreal.EditorActorSubsystem` or
  `spawn_actor_from_class`; case-insensitive, accepts the bare member name).

Query it from the terminal too (no server needed):
```bash
unreal-api-rag search set actor location
unreal-api-rag search sky atmosphere --kind class -k 5
```

## 3. Plug into an agent
Add it as an MCP server (e.g. Forge `game.yaml`):
```yaml
mcp_servers:
  editor: http://127.0.0.1:8000/mcp
  clay:   http://127.0.0.1:8770/mcp/
  ue_api: http://127.0.0.1:8780/mcp/
```
Then the agent calls `search_ue_api` **before writing UE Python**, so it uses the
real API — dramatically fewer tracebacks.

## Design
- **Corpus** (`data/*.jsonl`) — one entry per API symbol, introspected from the engine (authoritative, version-pinned).
- **Retrieval** — dependency-light **lexical** ranking tuned for API queries:
  - a tokenizer that splits `snake_case`, `CamelCase` and letter/digit runs into
    words, so `"set actor location"` matches `set_actor_location`;
  - **IDF weighting** so discriminative terms (`heightmap`) beat ubiquitous ones (`get`);
  - **field boosting** — a name hit outweighs a docstring hit;
  - phrase/prefix bonuses + conservative plural stemming (`materials`→`material`).

  Optional embedding search (`[semantic]` extra) is a drop-in upgrade behind the
  same interface. Ranking quality is guarded by a benchmark suite that runs
  against the real 27k-symbol corpus.
- **Server** — stateless MCP Streamable HTTP, mounted at `/mcp` (same shape as ForgeMCP/Clay), so it's multi-worker + edge-hostable.

Hosted (`mcp.stanl.ink/unreal`, Cloudflare Workers + Vectorize) is tracked
separately. This repo is the open, local-first core.

## License
MIT.
