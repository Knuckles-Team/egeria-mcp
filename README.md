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

*Version: 0.7.0*

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

## Available MCP Tools

_Auto-generated — do not edit (synced by the `mcp-readme-table` pre-commit hook)._

<!-- MCP-TOOLS-TABLE:START -->

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `egeria_actors` | `EGERIATOOL` | Browse people/teams, projects, communities, locations, cohorts. |
| `egeria_assert_lineage` | `EGERIATOOL` | Assert a data-flow lineage edge (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_asset_search` | `EGERIATOOL` | Search the Egeria asset catalog; returns flat asset records with GUIDs. |
| `egeria_audit` | `EGERIATOOL` | Completeness audit: report unlinked 'island' assets + per-layer coverage. |
| `egeria_catalog` | `EGERIATOOL` | Browse the technical catalog: assets, connections, endpoints, schema. |
| `egeria_classify` | `EGERIATOOL` | Apply a classification to an element (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_collection` | `EGERIATOOL` | Browse collections and digital products. |
| `egeria_create_asset` | `EGERIATOOL` | Create a data asset, optionally classified (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_create_collection` | `EGERIATOOL` | Create a collection / digital-product folder (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_create_project` | `EGERIATOOL` | Create a project (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_create_term` | `EGERIATOOL` | Create a glossary term (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_data_design` | `EGERIATOOL` | Browse data-designer artifacts: data structures, fields, value specs. |
| `egeria_glossary_categories` | `EGERIATOOL` | List the glossary category tree. |
| `egeria_glossary_lookup` | `EGERIATOOL` | Look up business glossary terms (definitions, categories, relationships). |
| `egeria_governance_catalog` | `EGERIATOOL` | Browse governance definitions, external references, valid-value sets. |
| `egeria_governance_for` | `EGERIATOOL` | Return governance definitions + classifications applying to an element. |
| `egeria_governed_route` | `EGERIATOOL` | Policy-aware routing decision for acting on an Egeria-catalogued asset. |
| `egeria_harvest` | `EGERIATOOL` | Run a bottom-up harvest layer (or 'all') into Egeria. |
| `egeria_harvest_archer` | `EGERIATOOL` | Catalog RSA Archer GRC records (risks/controls/findings) into Egeria. |
| `egeria_harvest_aris` | `EGERIATOOL` | Catalog ARIS models into Egeria — process models (BPM) + architecture |
| `egeria_harvest_containers` | `EGERIATOOL` | Catalog the Docker Swarm estate (nodes + services) into Egeria — the |
| `egeria_harvest_crm` | `EGERIATOOL` | Catalog Twenty CRM companies + people into Egeria (crm cohort with Odoo). |
| `egeria_harvest_datastores` | `EGERIATOOL` | Catalog the data-store estate into Egeria (bottom-up harvest, anchor layer). |
| `egeria_harvest_erpnext` | `EGERIATOOL` | Catalog ERPNext DocTypes into Egeria (ERP layer). |
| `egeria_harvest_finance` | `EGERIATOOL` | Catalog Firefly-III accounts into Egeria (financial data assets). |
| `egeria_harvest_github` | `EGERIATOOL` | Catalog GitHub repositories into Egeria (GITHUB_TOKEN [+ GITHUB_ORG]). |
| `egeria_harvest_identity` | `EGERIATOOL` | Catalog Keycloak realms (security domains) + clients (apps) into Egeria. |
| `egeria_harvest_odoo` | `EGERIATOOL` | Catalog Odoo CRM customers + leads into Egeria (crm cohort with Twenty). |
| `egeria_harvest_processes` | `EGERIATOOL` | Catalog Camunda BPMN process definitions into Egeria (process layer). |
| `egeria_harvest_projects` | `EGERIATOOL` | Catalog Plane/Jira projects into Egeria as Projects. |
| `egeria_harvest_repositories` | `EGERIATOOL` | Catalog GitLab projects into Egeria (code/CI layer). |
| `egeria_harvest_servicenow` | `EGERIATOOL` | Catalog ServiceNow CMDB configuration items into Egeria. |
| `egeria_lineage` | `EGERIATOOL` | Return the data-lineage graph (upstream/downstream assets + processes). |
| `egeria_list_policies` | `EGERIATOOL` | List Egeria governance policies/rules (optionally filtered by domain). |
| `egeria_metadata` | `EGERIATOOL` | Generic open-metadata access: search across all types, or get by GUID. |
| `egeria_reconcile` | `EGERIATOOL` | Cross-link the harvested layers into one connected lineage/governance graph. |
| `egeria_solution` | `EGERIATOOL` | Browse solution architecture: supply chains, blueprints, components. |

_37 action-routed tools (default `MCP_TOOL_MODE=condensed`). Each is enabled unless its toggle is set false; set `MCP_TOOL_MODE=verbose` (or `both`) for the 1:1 per-operation surface. Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

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

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `egeria-mcp[mcp]` | Slim MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI) | You run the **MCP server** (smallest install / image) |
| `egeria-mcp[egeria]` | The optional `pyegeria` SDK (Python ≥ 3.12) | You want the `pyegeria` client alongside the raw-httpx facade |
| `egeria-mcp[harvest]` | Bottom-up harvest deps (`pymongo`, `pyyaml`) | You run the data-store / connector harvests |
| `egeria-mcp[all]` | Everything (`mcp` + `agent` + `egeria` + `harvest`) | Development / full surface |

```bash
# MCP server only (recommended for tool hosting — slim deps)
uv pip install "egeria-mcp[mcp]"          # or: pip install -e ".[mcp]"

# Everything (development)
uv pip install "egeria-mcp[all]"          # or: python -m pip install "egeria-mcp[all]"

egeria-mcp                       # stdio MCP server (default transport)
egeria-mcp --transport http --host 0.0.0.0 --port 8000
```

The slim `docker/Dockerfile` builds one image (`knucklessg1/egeria-mcp:latest`) that
installs `egeria-mcp[all]` and runs the `egeria-mcp` console script; `docker/mcp.compose.yml`
runs it as a streamable-http service.

Run the bottom-up data-store harvest (needs write enabled):

```bash
EGERIA_PLATFORM_URL=https://your-egeria-platform:9443 EGERIA_ENABLE_WRITE=true \
  python -m egeria_mcp.harvest
```

### Knowledge-graph database (`epistemic-graph`)

Egeria is federated alongside the **epistemic-graph** Knowledge Graph: Egeria is the
metadata / governance / lineage system-of-record, the KG is the cognition / orchestration
plane (the **KG never becomes the lineage store**; **Egeria never orchestrates**). For
production — or to share one knowledge graph across multiple agents — run **epistemic-graph
as its own database container**. Deployment recipes (single-node + Raft HA), connection
config, and the full database architecture (with diagrams) are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).

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


<!-- BEGIN agent-os-genesis-deploy (generated; do not edit between markers) -->

## Deploy with `agent-os-genesis`

This package can be provisioned for you — skill-guided — by the **`agent-os-genesis`**
universal skill (its *single-package deploy mode*): it picks your install method, seeds
secrets to OpenBao/Vault (or `.env`), trusts your enterprise CA, registers the MCP
server, and verifies it — the same machinery that stands up the whole Agent OS, narrowed
to just this package. Ask your agent to **"deploy `egeria-mcp` with agent-os-genesis"**.

| Install mode | Command |
|------|---------|
| Bare-metal, prod (PyPI) | `uvx egeria-mcp` · or `uv tool install egeria-mcp` |
| Bare-metal, dev (editable) | `uv pip install -e ".[all]"` · or `pip install -e ".[all]"` |
| Container, prod | deploy `knucklessg1/egeria-mcp:latest` via docker-compose / swarm / podman / podman-compose / kubernetes |
| Container, dev (editable) | deploy `docker/compose.dev.yml` (source-mounted at `/src`; edits live on restart) |

Secrets are read-existing + seeded via `vault_sync` — you are only prompted for what's missing.

<!-- END agent-os-genesis-deploy -->
