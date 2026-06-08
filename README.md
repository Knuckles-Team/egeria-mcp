# egeria-mcp

Apache Egeria open-metadata **API + MCP Server** for the agent-utilities ecosystem.

*Version: 0.2.0*

Egeria is federated as the **metadata / governance / lineage system-of-record**
alongside the epistemic-graph Knowledge Graph (the cognition/orchestration plane).
This package provides the *typed, deterministic* Egeria tools a policy router calls,
the bottom-up harvest that **populates** Egeria from the data estate, and the
`governed_route` decision that is the federation delivering value.

Two hard invariants: the **KG never becomes the lineage store**; **Egeria never
orchestrates**.

## What it provides

- **`EgeriaApi`** (`egeria_mcp.api.api_client_egeria`) — a tolerant **raw-httpx REST**
  facade over the Egeria View Server (OMVS). No `pyegeria` runtime dependency
  (pyegeria's sync wrappers call `asyncio.get_event_loop()`, which raises on Python
  3.14; `httpx` works on 3.11 and 3.14). It is the injected `config["client"]` for
  the KG `egeria` enrichment extractor and backs all MCP tools. Every call degrades
  to `[]` / a clear error rather than raising.
- **21 MCP tools** (`egeria-mcp` console script): granular reads, broad
  action-dispatch readers across 11 OMVS services, `governed_route`, the data-store
  harvest, and write-gated create/classify/lineage tools. See
  [`docs/overview.md`](docs/overview.md) for the full list and the verified Egeria
  6.0 REST contract.

## Configuration (environment)

| Var | Default | Meaning |
|---|---|---|
| `EGERIA_PLATFORM_URL` | `https://localhost:9443` | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | `qs-view-server` | View server name |
| `EGERIA_USER` | `erinoverview` | User id |
| `EGERIA_USER_PASSWORD` | `secret` | Password / token |
| `EGERIA_VERIFY_SSL` | `False` | Verify TLS (self-signed homelab) |
| `EGERIA_ENABLE_WRITE` | `False` | Gate every write/harvest tool |
| `EGERIATOOL` | `True` | Register the Egeria tool set |

## Install & run

```bash
pip install -e .
egeria-mcp                       # stdio MCP server (default transport)
egeria-mcp --transport http --host 0.0.0.0 --port 8000
```

Run the bottom-up data-store harvest (needs write enabled):

```bash
EGERIA_PLATFORM_URL=https://your-egeria-platform:9443 EGERIA_ENABLE_WRITE=true \
  python -m egeria_mcp.harvest
```

## MCP config

Register in the multiplexer under nickname `eg` (tools surface as `eg__lineage`,
`eg__governed_route`, `eg__catalog`, …). See `egeria_mcp/mcp_config.json`.

## Docs

- [docs/overview.md](docs/overview.md) — tools, REST contract, harvest, federation.
- [docs/concepts.md](docs/concepts.md) — concept registry (`CONCEPT:EG-*`).
- `AGENTS.md` — canonical contributor guidance.
