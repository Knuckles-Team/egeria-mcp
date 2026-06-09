# egeria-mcp

Apache Egeria open-metadata **API + MCP Server** for the agent-utilities ecosystem
— the metadata / governance / lineage **system-of-record** federated with the
epistemic-graph Knowledge Graph.

!!! info "Official documentation"
    This site is the canonical reference for `egeria-mcp`, maintained alongside every
    release.

[![PyPI](https://img.shields.io/pypi/v/egeria-mcp)](https://pypi.org/project/egeria-mcp/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/egeria-mcp)](https://github.com/Knuckles-Team/egeria-mcp/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/egeria-mcp)

## Overview

`egeria-mcp` wraps the Apache Egeria OMAG platform's **View Server (OMVS)** REST
surface with typed, deterministic MCP tools, and is the write side of the
Egeria↔Knowledge-Graph federation. It provides:

- **`EgeriaApi`** — a tolerant raw-`httpx` REST facade over the View Server (no
  `pyegeria` runtime dependency; works on Python 3.11 → 3.14).
- **21 MCP tools** — granular and broad action-dispatch readers across 11 OMVS
  services, `governed_route`, and write-gated create/classify/lineage/harvest tools.
- **A 34-source bottom-up harvest** that *populates* Egeria from the data estate.

Two hard invariants: the **KG never becomes the lineage store**; **Egeria never
orchestrates**.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP server, Docker Compose, Caddy + Technitium.
- :material-console: **[Usage](usage.md)** — the MCP tools, the `EgeriaApi` client, and the harvest CLI.
- :material-database-cog: **[Backing Platform](platform.md)** — deploy Apache Egeria with Docker.
- :material-sitemap: **[Architecture](architecture.md)** — pipeline, layered client, KG federation.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:EG-*` registry.

</div>

## Quick start

```bash
pip install "egeria-mcp[mcp]"
egeria-mcp                       # stdio MCP server (default transport)
```

Connect it to an Egeria platform:

```bash
export EGERIA_PLATFORM_URL=https://your-egeria:9443
export EGERIA_VIEW_SERVER=qs-view-server
egeria-mcp --transport http --host 0.0.0.0 --port 8000
```

See **[Installation](installation.md)** and **[Deployment](deployment.md)** for the
full matrix (PyPI extras, Docker image, all transports, reverse proxy, DNS).
