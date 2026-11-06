# CONN-EGERIA-MCP-ERROR-SURFACE — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

Every vendor call passes one chokepoint that raises typed errors instead of returning empty results.

## Technical Context

- **Language/Version**: Python 3.14 (floor 3.12)
- **Primary Dependencies**: scion-sdk, fastmcp
- **Storage**: N/A; the connector stores nothing
- **Testing**: pytest; the proof level each row names
- **Target Platform**: Linux containers
- **Project Type**: connector (MCP server)
- **Performance Goals**: N/A
- **Constraints**: one tool per API operation; shared capabilities come from the SDK
- **Scale/Scope**: 3 rows

## Constitution Check

- One owner per concept: pass. The connector owns one external system's calls, mappings and tools only.
- Connectors depend on the SDK and are called through arbora: pass.
- No ratchets: pass. The rows add no suppression.

## Project Structure

```text
egeria_mcp/api/api_client_egeria.py  existing
egeria_mcp/lineage_scan.py  existing
egeria_mcp/reconcile.py  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

### Interfaces and data model

Tool names and arguments are unchanged. A failing call now returns an MCP error instead of an empty list.

### Live integration path

The fleet gateway calls a tool. The SDK tool surface calls the client method, which sends through the governed path named above.

### Quality and release gates

Run `pytest` in the repository and the pipelines `spec-status` hook. The change ships as a connector release.

### Risks, alternatives, and decisions

The KG ingest path keeps its per-source tolerance and logs the failure.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-EGERIA-MCP-ERROR-SURFACE-R001`: any MCP tool such as egeria_catalog or egeria_metadata (egeria_mcp/mcp/mcp_egeria.py) calls an EgeriaApi method, which calls `_request`.
2. `CONN-EGERIA-MCP-ERROR-SURFACE-R002`: same as R001.
3. `CONN-EGERIA-MCP-ERROR-SURFACE-R003`: same as R001.

## Cross-repo seams

none
