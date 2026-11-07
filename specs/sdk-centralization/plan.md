# CONN-EGERIA-MCP-SDK-CENTRALIZATION — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

The connector reused SDK capabilities already: see the cited SDK rows. This spec moves the remaining direct vendor-library use onto the SDK. - Governed HTTP client: SCION-CENTRALIZED-CAPABILITIES-R001, SCION-CENTRALIZED-CAPABILITIES-R008 - OpenBao token by reference: SCION-CENTRALIZED-CAPABILITIES-R009 - Database driver from the SDK extra: SCION-CENTRALIZED-CAPABILITIES-R040.

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
egeria_mcp/governed_http.py  existing
egeria_mcp/harvest/secrets.py  existing
pyproject.toml  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

### Interfaces and data model

No tool, argument or result changes. Only the transport and dependency declarations change.

### Live integration path

The fleet gateway calls a tool. The SDK tool surface calls the client method, which sends through the governed path named above.

### Quality and release gates

Run `pytest` in the repository and the pipelines `spec-status` hook. The change ships as a connector release.

### Risks, alternatives, and decisions

The governed client does not follow redirects and ignores ambient proxy variables. The TLS profile decides proxies.

### Adoption of scion-sdk 0.10.0 (CONN-EGERIA-MCP-SDK-CENTRALIZATION-R004)

- Owner. This repository, the import lines named in `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R004`. The paths belong to scion-sdk.
- Cohesion. The import edits, the pin and the lock change together and sit in one change.
- Dependency direction. The connector imports public modules of the SDK units; no import points to a private module.
- Interface depth. The connector uses the public surface only.
- Special cases. None. Every removed path takes the same replacement, with no alias.
- State. None.
- Environment. None. The pin is package metadata, not environment code.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001`: the egeria_harvest tool (egeria_mcp/mcp/mcp_egeria.py:68) calls harvest_all (egeria_mcp/harvest/runner.py:92), whose layer modules such as egeria_mcp/harvest/identity.py:38 and kafka.py:40 open clients through governed_client; the python -m egeria_mcp.harvest CLI (egeria_mcp/harvest/__main__.py) reaches the same layers.
2. `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002`: the egeria_harvest tool (egeria_mcp/mcp/mcp_egeria.py:68) calls harvest_all (egeria_mcp/harvest/runner.py:92), which runs the secrets layer in egeria_mcp/harvest/secrets.py; _resolve (secrets.py:41) calls _token (secrets.py:26).
3. `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003`: the egeria_harvest tool (egeria_mcp/mcp/mcp_egeria.py:68) calls harvest_all (egeria_mcp/harvest/runner.py:92), whose documentdb layer (egeria_mcp/harvest/documentdb.py:42) imports pymongo lazily; the driver is installed through the harvest or all extra in pyproject.toml.

## Cross-repo seams

none
