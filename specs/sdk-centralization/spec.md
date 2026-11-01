# CONN-EGERIA-MCP-SDK-CENTRALIZATION — SDK centralized capabilities

Owner: egeria-mcp. Cross-repo IDs: SCION-CENTRALIZED-CAPABILITIES.

## Purpose and user stories

An operator must run the Egeria connector on the shared SDK capabilities. The connector must send every request through the governed client.

## Why a new spec

The `specs/` tree held only the template and the index.
No local spec owned how this connector uses the shared SDK capabilities, so this spec owns it.
It cites the SCION-CENTRALIZED-CAPABILITIES rows by ID and adds no capability of its own.

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

## User Scenarios & Testing

### User Story 1 - SDK centralized capabilities (Priority: P1)

An operator must run the Egeria connector on the shared SDK capabilities. The connector must send every request through the governed client.

**Acceptance Scenarios**:

1. **Given** the connector is configured, **When** the behaviour of row `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001` (governed http client) is exercised, **Then** `tests/test_sdk_centralization.py::test_no_direct_httpx_client` must pass, and `governed_client` must return a client on the SDK governed transport.
2. **Given** the connector is configured, **When** the behaviour of row `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002` (openbao token by reference) is exercised, **Then** `tests/test_sdk_centralization.py::test_openbao_token_reference_is_resolved` must pass.
3. **Given** the connector is configured, **When** the behaviour of row `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003` (database driver from the sdk extra) is exercised, **Then** `tests/test_sdk_centralization.py::test_database_driver_comes_from_sdk_extra` must pass.

### Edge Cases

- If `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001` is not met, its proving test fails: governed http client.
- If `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002` is not met, its proving test fails: openbao token by reference.
- If `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003` is not met, its proving test fails: database driver from the sdk extra.

## Requirements

- **FR-001**: Governed HTTP client. Rows: `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001`.
- **FR-002**: OpenBao token by reference. Rows: `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002`.
- **FR-003**: Database driver from the SDK extra. Rows: `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003`.

## Success Criteria

- **SC-001**: `tests/test_sdk_centralization.py::test_no_direct_httpx_client` must pass, and `governed_client` must return a client on the SDK governed transport. Rows: `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001`.
- **SC-002**: `tests/test_sdk_centralization.py::test_openbao_token_reference_is_resolved` must pass. Rows: `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002`.
- **SC-003**: `tests/test_sdk_centralization.py::test_database_driver_comes_from_sdk_extra` must pass. Rows: `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003`.

## Assumptions

- The external system is reachable with operator-supplied credentials.
- The SDK and engine contracts the rows cite are at the floors declared in `pyproject.toml`.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001` | [plan.md](plan.md) | T-001 | [test-spec.md](test-spec.md) |
| FR-002 | `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002` | [plan.md](plan.md) | T-002 | [test-spec.md](test-spec.md) |
| FR-003 | `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003` | [plan.md](plan.md) | T-003 | [test-spec.md](test-spec.md) |
