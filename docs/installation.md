# Installation

`egeria-mcp` is a standard Python package and a prebuilt container image. Pick the
path that matches how you want to run it.

## Requirements

- **Python 3.11 – 3.14** (the raw-`httpx` client avoids `pyegeria`'s 3.14 break).
- A reachable **Apache Egeria OMAG platform / View Server** — see
  [Backing Platform](platform.md) to stand one up locally.

## From PyPI (recommended)

```bash
pip install egeria-mcp
```

### Optional extras

The base install is intentionally minimal. Install the extra for what you need:

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "egeria-mcp[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "egeria-mcp[agent]"` | Pydantic-AI agent + Logfire tracing |
| `harvest` | `pip install "egeria-mcp[harvest]"` | `pymongo`, `pyyaml` for the bottom-up harvest |
| `egeria` | `pip install "egeria-mcp[egeria]"` | `pyegeria` (only on Python ≥ 3.12) |
| `all` | `pip install "egeria-mcp[all]"` | Everything above |

```bash
# Typical: run the MCP server + the harvest connectors
pip install "egeria-mcp[mcp,harvest]"
```

## From source

```bash
git clone https://github.com/Knuckles-Team/egeria-mcp.git
cd egeria-mcp
pip install -e ".[all]"          # editable install with every extra
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv pip install -e ".[all]"
uv run egeria-mcp
```

## Prebuilt Docker image

A multi-stage, slim image is published on every release (installs
`egeria-mcp[all]`, entrypoint `egeria-mcp`):

```bash
docker pull knucklessg1/egeria-mcp:latest

docker run --rm -i \
  -e EGERIA_PLATFORM_URL=https://your-egeria:9443 \
  -e EGERIA_VIEW_SERVER=qs-view-server \
  knucklessg1/egeria-mcp:latest        # stdio transport (default)
```

For an HTTP server with a published port, see [Deployment](deployment.md).

## Verify the install

```bash
egeria-mcp --help
python -c "import egeria_mcp; print(egeria_mcp.__version__)"
```

## Next steps

- **[Deployment](deployment.md)** — run it as a long-lived MCP server behind Caddy + DNS.
- **[Usage](usage.md)** — call the tools, the API, and the harvest CLI.
- **[Configuration](deployment.md#configuration-environment)** — every environment variable.
