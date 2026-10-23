# CONN-EGERIA-MCP-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `egeria-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `egeria_mcp` from it.
