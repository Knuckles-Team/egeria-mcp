# CONN-EGERIA-MCP-ERROR-SURFACE — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Level | Setup and input | Expected observation | Evidence |
|---|---|---|---|---|---|
| T-001 | FR-001 | Unit | Mock transport refusing the connection, then answering 503 | `tests/test_error_surface.py::test_connection_refused_is_a_tool_error` and `test_http_503_is_unavailable` must pass. | `tests/test_error_surface.py` |
| T-002 | FR-002 | Unit | Mock transport answering 200 with `relatedHTTPCode` 503 or 400 and `exceptionErrorMessage` | `tests/test_error_surface.py::test_in_body_503_is_a_tool_error` and `test_in_body_client_error_is_api_error` must pass. | `tests/test_error_surface.py` |
| T-003 | FR-003 | Unit | Mock transport answering a normal 200 and an empty 200 | `tests/test_error_surface.py::test_normal_200_returns_data` and `test_genuine_empty_result_is_not_an_error` must pass. | `tests/test_error_surface.py` |
| T-004 | FR-004 | Unit | Mock transport raising a read timeout; `EGERIA_TIMEOUT_SECONDS` unset then 45 | `tests/test_error_surface.py::test_read_timeout_is_named_and_timeout_is_configurable` must pass. | `tests/test_error_surface.py` |

## Negative and boundary cases

The tests make no network call; they use an in-process mock transport and an in-memory MCP client.

## Quality and release proof

Run `pytest tests/test_error_surface.py` and the full suite.
