# CONN-EGERIA-MCP-ERROR-SURFACE — Typed tool errors for Egeria failures

Owner: egeria-mcp. Cross-repo IDs: none.

## Purpose and user stories

An operator must be told when the Egeria platform is down. A tool call against an unreachable or failing platform must return an MCP error, never empty success content.

## Why a new spec

No local spec owns how the connector reports vendor failures. The SDK centralization spec covers transport only, and the content spec covers packaged content.

## Scope and interfaces

The connector owns its vendor operations and tool names, which stay unchanged. Failures now raise `EgeriaUnavailableError` and `EgeriaApiError`, both fastmcp `ToolError` subclasses.
Code: ../../egeria_mcp/api/api_client_egeria.py ../../egeria_mcp/lineage_scan.py ../../egeria_mcp/reconcile.py ../../tests/test_error_surface.py

## Traceability

| Requirement | Design section | Test ID | Evidence |
|---|---|---|---|
| FR-001 | plan.md#architecture | T-001 | `tests/test_error_surface.py` |
| FR-002 | plan.md#architecture | T-002 | `tests/test_error_surface.py` |
| FR-003 | plan.md#architecture | T-003 | `tests/test_error_surface.py` |

## Open questions

- None.

## User Scenarios & Testing

### User Story 1 - Failures are visible (Priority: P1)

An operator must be told when the Egeria platform is down. A tool call against an unreachable or failing platform must return an MCP error, never empty success content.

**Acceptance Scenarios**:

1. **Given** the connector is configured, **When** the behaviour of row `CONN-EGERIA-MCP-ERROR-SURFACE-R001` (unreachable platform is a tool error) is exercised, **Then** `tests/test_error_surface.py::test_connection_refused_is_a_tool_error` and `test_http_503_is_unavailable` must pass.
2. **Given** the connector is configured, **When** the behaviour of row `CONN-EGERIA-MCP-ERROR-SURFACE-R002` (in-body egeria errors are tool errors) is exercised, **Then** `tests/test_error_surface.py::test_in_body_503_is_a_tool_error` and `test_in_body_client_error_is_api_error` must pass.
3. **Given** the connector is configured, **When** the behaviour of row `CONN-EGERIA-MCP-ERROR-SURFACE-R003` (success and empty results are unchanged) is exercised, **Then** `tests/test_error_surface.py::test_normal_200_returns_data` and `test_genuine_empty_result_is_not_an_error` must pass.

### Edge Cases

- If `CONN-EGERIA-MCP-ERROR-SURFACE-R001` is not met, its proving test fails: unreachable platform is a tool error.
- If `CONN-EGERIA-MCP-ERROR-SURFACE-R002` is not met, its proving test fails: in-body egeria errors are tool errors.
- If `CONN-EGERIA-MCP-ERROR-SURFACE-R003` is not met, its proving test fails: success and empty results are unchanged.

## Requirements

- **FR-001**: Unreachable platform is a tool error. Rows: `CONN-EGERIA-MCP-ERROR-SURFACE-R001`.
- **FR-002**: In-body Egeria errors are tool errors. Rows: `CONN-EGERIA-MCP-ERROR-SURFACE-R002`.
- **FR-003**: Success and empty results are unchanged. Rows: `CONN-EGERIA-MCP-ERROR-SURFACE-R003`.

## Success Criteria

- **SC-001**: `tests/test_error_surface.py::test_connection_refused_is_a_tool_error` and `test_http_503_is_unavailable` must pass. Rows: `CONN-EGERIA-MCP-ERROR-SURFACE-R001`.
- **SC-002**: `tests/test_error_surface.py::test_in_body_503_is_a_tool_error` and `test_in_body_client_error_is_api_error` must pass. Rows: `CONN-EGERIA-MCP-ERROR-SURFACE-R002`.
- **SC-003**: `tests/test_error_surface.py::test_normal_200_returns_data` and `test_genuine_empty_result_is_not_an_error` must pass. Rows: `CONN-EGERIA-MCP-ERROR-SURFACE-R003`.

## Assumptions

- The external system is reachable with operator-supplied credentials when it is healthy.
- The SDK and engine contracts the rows cite are at the floors declared in `pyproject.toml`.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-EGERIA-MCP-ERROR-SURFACE-R001` | [plan.md](plan.md) | T-001 | [test-spec.md](test-spec.md) |
| FR-002 | `CONN-EGERIA-MCP-ERROR-SURFACE-R002` | [plan.md](plan.md) | T-002 | [test-spec.md](test-spec.md) |
| FR-003 | `CONN-EGERIA-MCP-ERROR-SURFACE-R003` | [plan.md](plan.md) | T-003 | [test-spec.md](test-spec.md) |
