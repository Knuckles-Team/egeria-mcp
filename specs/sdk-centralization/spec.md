# CONN-EGERIA-MCP-SDK-CENTRALIZATION — SDK centralized capabilities

Owner: egeria-mcp. Cross-repo IDs: SDK-CENTRALIZED-CAPABILITIES.

## Purpose and user stories

An operator must run the Egeria connector on the shared SDK capabilities. The connector must send every request through the governed client.

## Requirements and acceptance

- FR-001: Every harvest module and the OMVS client must build HTTP clients with `governed_client`, which wraps `create_http_client` with the resolved TLS profile.
- FR-002: The OpenBao harvest must resolve its token through the SDK credential resolver when the value is a reference.
- FR-003: The `harvest` and `all` extras must take the database driver from `agent-connector-sdk[db]` and must not pin it.
- SC-001: `tests/test_sdk_centralization.py::test_no_direct_httpx_client` must pass, and `governed_client` must return a client on the SDK governed transport.
- SC-002: `tests/test_sdk_centralization.py::test_openbao_token_reference_is_resolved` must pass.
- SC-003: `tests/test_sdk_centralization.py::test_database_driver_comes_from_sdk_extra` must pass.

## Why a new spec

The `specs/` tree held only the template and the index.
No local spec owned how this connector uses the shared SDK capabilities, so this spec owns it.
It cites the SDK-CENTRALIZED-CAPABILITIES rows by ID and adds no capability of its own.

## Scope and interfaces

The connector owns its vendor operations and tool names, which stay unchanged.
The connector SDK owns the governed HTTP client, TLS profiles, credential resolution and extras.
Code: ../../egeria_mcp/governed_http.py ../../egeria_mcp/harvest/secrets.py ../../pyproject.toml ../../tests/test_sdk_centralization.py

## Traceability

| Requirement | Design section | Test ID | Evidence |
|---|---|---|---|
| FR-001 | plan.md#architecture | T-001 | `tests/test_sdk_centralization.py` |
| FR-002 | plan.md#architecture | T-002 | `tests/test_sdk_centralization.py` |
| FR-003 | plan.md#architecture | T-003 | `tests/test_sdk_centralization.py` |

## Open questions

- None.
