# Changelog

## 0.1.0 (2026-07-08)


### Features

* **build:** dedup inherited methods (335k-&gt;27k); feat(corpus): support gzipped corpus ([0f539d1](https://github.com/stanlink-games/unreal-python-api-rag/commit/0f539d1aa0308137d8ed86d3e55e0bef1e4aeeba))
* **build:** introspect the live unreal module into a JSONL API corpus ([c5e9ca3](https://github.com/stanlink-games/unreal-python-api-rag/commit/c5e9ca388c7333558eb7baf40e8510c68a5fe293))
* **cli:** build-corpus + mcp commands ([e0713d6](https://github.com/stanlink-games/unreal-python-api-rag/commit/e0713d6d9f673c726e777c4b1ab729d21e9c3f59))
* **corpus:** load the API corpus (bundled or explicit path) ([4b15664](https://github.com/stanlink-games/unreal-python-api-rag/commit/4b15664461a6da4e20dc9acba7e42ae0ad16f89f))
* **mcp:** stateless MCP server exposing search_ue_api + get_symbol ([309172f](https://github.com/stanlink-games/unreal-python-api-rag/commit/309172f9cd38bcb374f6ca79f177cff9fb44566e))
* **search:** conservative plural stemming for recall ([4d1194f](https://github.com/stanlink-games/unreal-python-api-rag/commit/4d1194fbade4badfae1da46ce0cadc69d2f90865))
* **search:** dependency-light keyword retrieval + exact symbol lookup ([c9fb37b](https://github.com/stanlink-games/unreal-python-api-rag/commit/c9fb37bc10a87c38e39d05acd4a401b73163903a))
* **search:** kind filter, terminal 'search' command, lean MCP payload ([0d0c2c0](https://github.com/stanlink-games/unreal-python-api-rag/commit/0d0c2c00be97680e53177381533aee18669d3089))
* **search:** word-splitting tokenizer + IDF field-weighted ranking ([0129fb3](https://github.com/stanlink-games/unreal-python-api-rag/commit/0129fb31f2bcce64bafe7251e229b2549045b014))


### Bug Fixes

* **build:** ship corpus via artifacts (drop force-include that duplicated data/__init__.py) ([5588a22](https://github.com/stanlink-games/unreal-python-api-rag/commit/5588a22656a6118bd0e456456219cb94abd4b17d))


### Documentation

* document ranked search, kind filter, CLI search + design ([6317c5c](https://github.com/stanlink-games/unreal-python-api-rag/commit/6317c5cffd763c088f429a6807405f2682f01ec7))
* README (grounding UE Python for any MCP agent) ([ec25b01](https://github.com/stanlink-games/unreal-python-api-rag/commit/ec25b01e336aff5b4aa8264e6c8d67122b42bea1))
