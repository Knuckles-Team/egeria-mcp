# Egeria Mcp
## API | MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/egeria-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/egeria-mcp)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/egeria-mcp)
![GitHub forks](https://img.shields.io/github/forks/Knuckles-Team/egeria-mcp)
![GitHub contributors](https://img.shields.io/github/contributors/Knuckles-Team/egeria-mcp)
![PyPI - License](https://img.shields.io/pypi/l/egeria-mcp)
![GitHub](https://img.shields.io/github/license/Knuckles-Team/egeria-mcp)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/egeria-mcp)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Knuckles-Team/egeria-mcp)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/Knuckles-Team/egeria-mcp)
![GitHub issues](https://img.shields.io/github/issues/Knuckles-Team/egeria-mcp)
![GitHub top language](https://img.shields.io/github/languages/top/Knuckles-Team/egeria-mcp)
![GitHub language count](https://img.shields.io/github/languages/count/Knuckles-Team/egeria-mcp)
![GitHub repo size](https://img.shields.io/github/repo-size/Knuckles-Team/egeria-mcp)
![GitHub repo file count (file type)](https://img.shields.io/github/directory-file-count/Knuckles-Team/egeria-mcp)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/egeria-mcp)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/egeria-mcp)

Apache Egeria open-metadata **API + MCP Server** for the agent-utilities ecosystem.

*Version: 0.5.0*

> **Documentation** — Installation, deployment, usage across the API, CLI, and MCP
> interfaces, and guidance for provisioning the Apache Egeria platform are maintained
> in the [official documentation](https://knuckles-team.github.io/egeria-mcp/).

Egeria is federated as the **metadata / governance / lineage system-of-record**
alongside the epistemic-graph Knowledge Graph (the cognition/orchestration plane).
This package provides the *typed, deterministic* Egeria tools a policy router calls,
the bottom-up harvest that **populates** Egeria from the data estate, and the
`governed_route` decision that is the federation delivering value.

Two hard invariants: the **KG never becomes the lineage store**; **Egeria never
orchestrates**.

## What it provides

- **`EgeriaApi`** (`egeria_mcp.api.api_client_egeria`) — a tolerant **raw-httpx REST**
  facade over the Egeria View Server (OMVS). No `pyegeria` runtime dependency
  (pyegeria's sync wrappers call `asyncio.get_event_loop()`, which raises on Python
  3.14; `httpx` works on 3.11 and 3.14). It is the injected `config["client"]` for
  the KG `egeria` enrichment extractor and backs all MCP tools. Every call degrades
  to `[]` / a clear error rather than raising.
- **21 MCP tools** (`egeria-mcp` console script): granular reads, broad
  action-dispatch readers across 11 OMVS services, `governed_route`, the data-store
  harvest, and write-gated create/classify/lineage tools. See
  [`docs/overview.md`](docs/overview.md) for the full list and the verified Egeria
  6.0 REST contract.

## Configuration (environment)

| Var | Default | Meaning |
|---|---|---|
| `EGERIA_PLATFORM_URL` | `https://localhost:9443` | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | `qs-view-server` | View server name |
| `EGERIA_USER` | `erinoverview` | User id |
| `EGERIA_USER_PASSWORD` | `secret` | Password / token |
| `EGERIA_VERIFY_SSL` | `False` | Verify TLS (self-signed homelab) |
| `EGERIA_ENABLE_WRITE` | `False` | Gate every write/harvest tool |
| `EGERIATOOL` | `True` | Register the Egeria tool set |

The table above is the **required** set. The bottom-up harvest connectors
(ServiceNow, ERPNext, GitLab, Camunda, Keycloak, Grafana, Portainer, …) each read
their own optional credential vars — every variable, grouped by source system with
required-vs-optional separation, is documented in [`.env.example`](.env.example).
Copy it to `.env` and populate only the connectors you use; blank connector
credentials leave the corresponding harvest inactive.

## Install & run

```bash
pip install -e .
egeria-mcp                       # stdio MCP server (default transport)
egeria-mcp --transport http --host 0.0.0.0 --port 8000
```

Run the bottom-up data-store harvest (needs write enabled):

```bash
EGERIA_PLATFORM_URL=https://your-egeria-platform:9443 EGERIA_ENABLE_WRITE=true \
  python -m egeria_mcp.harvest
```

## MCP config

Register in the multiplexer under nickname `eg` (tools surface as `eg__lineage`,
`eg__governed_route`, `eg__catalog`, …). See `egeria_mcp/mcp_config.json`.

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`egeria-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/egeria-mcp/deployment/) has full, copy-paste
`mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://egeria-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

## Documentation

The complete documentation is published as the
[official documentation site](https://knuckles-team.github.io/egeria-mcp/) and is the
recommended reference for installation, deployment, and day-to-day operation.

| Page | Contents |
|---|---|
| [Installation](https://knuckles-team.github.io/egeria-mcp/installation/) | pip, source, extras, prebuilt Docker image |
| [Deployment](https://knuckles-team.github.io/egeria-mcp/deployment/) | run the MCP server, Compose, Caddy + Technitium, env config |
| [Usage](https://knuckles-team.github.io/egeria-mcp/usage/) | the MCP tools, the `EgeriaApi` client, the harvest CLI |
| [Backing Platform](https://knuckles-team.github.io/egeria-mcp/platform/) | deploy Apache Egeria with Docker |
| [Overview](https://knuckles-team.github.io/egeria-mcp/overview/) | tools, REST contract, harvest, federation |
| [Architecture](https://knuckles-team.github.io/egeria-mcp/architecture/) | pipeline, layered client, KG federation diagrams |
| [Concepts](https://knuckles-team.github.io/egeria-mcp/concepts/) | concept registry (`CONCEPT:EG-*`) |

`AGENTS.md` is the canonical contributor/agent guidance.
