# CONN-EGERIA-MCP-SDK-CENTRALIZATION — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001` | **Governed HTTP client.** Harvest and OMVS code must not call `httpx.Client` directly. `egeria_mcp/governed_http.py` builds the client with the SDK retry policy and the `EGERIA` TLS profile (SDK-CENTRALIZED-CAPABILITIES-R001, SDK-CENTRALIZED-CAPABILITIES-R008). | `tests/test_sdk_centralization.py::test_no_direct_httpx_client` must pass, and `governed_client` must return a client on the SDK governed transport. |
| `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002` | **OpenBao token by reference.** `egeria_mcp/harvest/secrets.py` must resolve `env://` and `openbao://` token references with the SDK resolver and must not parse them itself (SDK-CENTRALIZED-CAPABILITIES-R009). | `tests/test_sdk_centralization.py::test_openbao_token_reference_is_resolved` must pass. |
| `CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003` | **Database driver from the SDK extra.** `pyproject.toml` must declare `agent-connector-sdk[db]` in the `harvest` and `all` extras and must not pin `pymongo` (SDK-CENTRALIZED-CAPABILITIES-R040). | `tests/test_sdk_centralization.py::test_database_driver_comes_from_sdk_extra` must pass. |
