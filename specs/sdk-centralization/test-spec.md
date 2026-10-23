# CONN-EGERIA-MCP-SDK-CENTRALIZATION — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Level | Setup and input | Expected observation | Evidence |
|---|---|---|---|---|---|
| T-001 | FR-001 | Unit | Scan of `egeria_mcp/**/*.py`; call `governed_client("https://x.invalid")` | `tests/test_sdk_centralization.py::test_no_direct_httpx_client` must pass, and `governed_client` must return a client on the SDK governed transport. | `tests/test_sdk_centralization.py` |
| T-002 | FR-002 | Unit | `OPENBAO_TOKEN_REF=env://EGERIA_TEST_TOKEN` with the variable set | `tests/test_sdk_centralization.py::test_openbao_token_reference_is_resolved` must pass. | `tests/test_sdk_centralization.py` |
| T-003 | FR-003 | Unit | Parse `pyproject.toml` | `tests/test_sdk_centralization.py::test_database_driver_comes_from_sdk_extra` must pass. | `tests/test_sdk_centralization.py` |

## Negative and boundary cases

The tests make no network call.

## Quality and release proof

Run `pytest tests/test_sdk_centralization.py` and the full suite.
