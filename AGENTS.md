# egeria-mcp — AGENTS

> Claude Code loads this file via `CLAUDE.md` (`@AGENTS.md` import) — the two stay
> in sync. Edit **this** file, not `CLAUDE.md`.

## What this is

`egeria-mcp` is the **API + MCP server** for Apache Egeria (the OMAG open-metadata
platform), federated into the agent-utilities ecosystem as the
**metadata / governance / lineage system-of-record** alongside the epistemic-graph
Knowledge Graph (the cognition/orchestration plane).

Two hard invariants of the federation:
- **The KG never becomes the lineage store** — Egeria is system-of-record for data
  lineage, business glossary, and data-governance classifications.
- **Egeria never orchestrates** — `graph_orchestrate` / the policy router stay the
  orchestration brain; Egeria is the metadata oracle they *query* and write
  provenance back to.

## Project Structure
- `egeria_mcp/api/api_client_egeria.py` — `EgeriaApi`, a tolerant **raw-httpx REST**
  facade over the Egeria View Server (OMVS). Organized by OMVS service; every call
  degrades to `[]` / a clear error rather than raising.
- `egeria_mcp/mcp/mcp_egeria.py` — thin FastMCP tool wrappers (read, write-gated,
  harvest, governed-routing). No business logic — all API surface lives in `api/`.
- `egeria_mcp/governed_routing.py` — `governed_route()`: the federation delivering a
  policy-aware decision (proceed / review / require_approval) from Egeria
  governance + lineage.
- `egeria_mcp/harvest/` — bottom-up connectors that **populate** Egeria from the data
  estate (data stores first, then ERPNext/Camunda/GitLab). `topology.py` is the
  declared estate; `datastores.py` is the substrate/anchor harvest.
- `egeria_mcp/auth.py` — `get_client()` builds an `EgeriaApi` from the environment.

## Tech Stack
- Python 3.11+ (raw `httpx` REST — **no pyegeria runtime dependency**; pyegeria's
  sync wrappers call `asyncio.get_event_loop()`, which raises on Python 3.14).
- agent-utilities `[mcp]` (FastMCP, `create_mcp_server`).
- Apache Egeria 6.0 OMAG platform / View Server (OMVS) REST.

## Egeria REST contract (confirmed against Egeria 6.0)
- Token: `POST {platform}/api/token` `{userId,password}` → bearer JWT.
- Find: `POST {platform}/servers/{view_server}/api/open-metadata/{service}/{noun}/by-search-string`
  with `{"class":"SearchStringRequestBody","searchString": <term>}`. **Empty string =
  match-all**; `.*` matches nothing (it is a contains/regex match, not "any").
- Create: `POST .../{service}/{noun}` with a `NewElementRequestBody`
  (`properties.class` is the typed properties bean, e.g. `AssetProperties`).
- Read-back with classifications: `POST .../asset-maker/assets/{guid}/retrieve`
  `{"class":"AnyTimeRequestBody"}` → `element.elementHeader.<name>` (each
  classification is a *named* `ElementClassification`, not a list).
- Classify: `POST .../classification-explorer/elements/{guid}/{classification}`
  (the bean field is `confidentialityLevel`, **not** `levelIdentifier`).
- Lineage: `POST .../lineage-linker/from-elements/{a}/via/DataFlow/to-elements/{b}/attach`;
  read via `.../asset-catalog/assets/{guid}/as-lineage-graph` → edges in
  `element.lineageLinkage`.

## Commands
- `pytest` — run tests
- `pre-commit run --all-files` — lint
- `python -m egeria_mcp.harvest` — run the data-store harvest (needs
  `EGERIA_ENABLE_WRITE=true`)

## Configuration (environment)
`EGERIA_PLATFORM_URL`, `EGERIA_VIEW_SERVER`, `EGERIA_USER`, `EGERIA_USER_PASSWORD`,
`EGERIA_VERIFY_SSL` (default False — self-signed homelab), `EGERIA_ENABLE_WRITE`
(default False — gates every write/harvest tool), `EGERIATOOL` (default True).

## Conventions
- All write tools are gated by `EGERIA_ENABLE_WRITE`; never write unless enabled.
- MCP tool tags are strictly lowercase with hyphens (e.g. `tags={"governance"}`).
- Keep `api/` the single source of API surface; `mcp/` tools add no logic.
- Federation key: every Egeria-sourced KG node carries `externalToolId` (the Egeria
  GUID) + `domain="egeria"` (see the KG `egeria` extractor in agent-utilities).

## ⛔ Keep the Repository Root Pristine
The repository ROOT must contain only canonical project files (packaging, config,
docs, lockfiles). Never write debug/migration/scratch scripts, data dumps, logs, or
build artifacts to the repo — scratch goes in `~/workspace/scratch/`, command output
in `~/workspace/reports/`, tests in `tests/` only. Run `git status` before finishing.
