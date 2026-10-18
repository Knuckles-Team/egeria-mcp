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

Apache Egeria open-metadata **API + MCP Server** for the Arbora ecosystem.

*Version: 2.3.0*

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

#### Intent tools

| MCP Tool | Kind | Description |
|----------|------|-------------|
| `egeria_actors` | intent | Browse people/teams, projects, communities, locations, cohorts. |
| `egeria_assert_lineage` | intent | Assert a data-flow lineage edge (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_asset_for_kg_node` | intent | Resolve a KG node id to its Egeria GUID. |
| `egeria_asset_search` | intent | Search the Egeria asset catalog; returns flat asset records with GUIDs. |
| `egeria_audit` | intent | Completeness audit: report unlinked 'island' assets + per-layer coverage. |
| `egeria_catalog` | intent | Browse the technical catalog: assets, connections, endpoints, schema. |
| `egeria_classify` | intent | Apply a classification to an element (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_collection` | intent | Browse collections and digital products. |
| `egeria_create_asset` | intent | Create a data asset, optionally classified (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_create_collection` | intent | Create a collection / digital-product folder (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_create_project` | intent | Create a project (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_create_term` | intent | Create a glossary term (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_data_design` | intent | Browse data-designer artifacts: data structures, fields, value specs. |
| `egeria_glossary_categories` | intent | List the glossary category tree. |
| `egeria_glossary_lookup` | intent | Look up business glossary terms (definitions, categories, relationships). |
| `egeria_governance_catalog` | intent | Browse governance definitions, external references, valid-value sets. |
| `egeria_governance_for` | intent | Return governance definitions + classifications applying to an element. |
| `egeria_governed_route` | intent | Policy-aware routing decision for acting on an Egeria-catalogued asset. |
| `egeria_harvest` | intent | Run a bottom-up harvest layer (or 'all') into Egeria. |
| `egeria_harvest_archer` | intent | Catalog RSA Archer GRC records (risks/controls/findings) into Egeria. |
| `egeria_harvest_aris` | intent | Catalog ARIS models into Egeria — process models (BPM) + architecture |
| `egeria_harvest_containers` | intent | Catalog the Docker Swarm estate (nodes + services) into Egeria — the |
| `egeria_harvest_crm` | intent | Catalog Twenty CRM companies + people into Egeria (crm cohort with Odoo). |
| `egeria_harvest_datastores` | intent | Catalog the data-store estate into Egeria (bottom-up harvest, anchor layer). |
| `egeria_harvest_erpnext` | intent | Catalog ERPNext DocTypes into Egeria (ERP layer). |
| `egeria_harvest_finance` | intent | Catalog Firefly-III accounts into Egeria (financial data assets). |
| `egeria_harvest_github` | intent | Catalog GitHub repositories into Egeria (GITHUB_TOKEN [+ GITHUB_ORG]). |
| `egeria_harvest_identity` | intent | Catalog Keycloak realms (security domains) + clients (apps) into Egeria. |
| `egeria_harvest_odoo` | intent | Catalog Odoo CRM customers + leads into Egeria (crm cohort with Twenty). |
| `egeria_harvest_processes` | intent | Catalog Camunda BPMN process definitions into Egeria (process layer). |
| `egeria_harvest_projects` | intent | Catalog Plane/Jira projects into Egeria as Projects. |
| `egeria_harvest_repositories` | intent | Catalog GitLab projects into Egeria (code/CI layer). |
| `egeria_harvest_servicenow` | intent | Catalog ServiceNow CMDB configuration items into Egeria. |
| `egeria_ingest_catalog` | intent | Natively ingest the Egeria catalog into epistemic-graph as typed OWL nodes. |
| `egeria_lineage` | intent | Return the data-lineage graph (upstream/downstream assets + processes). |
| `egeria_lineage_scan` | intent | Scan the catalog's hub prefixes and return every DataFlow lineage edge. |
| `egeria_list_policies` | intent | List Egeria governance policies/rules (optionally filtered by domain). |
| `egeria_metadata` | intent | Generic open-metadata access: search across all types, or get by GUID. |
| `egeria_reconcile` | intent | Cross-link the harvested layers into one connected lineage/governance graph. |
| `egeria_reconcile_openlineage_asset` | intent | Reconcile one OpenLineage dataset into Egeria (requires EGERIA_ENABLE_WRITE=true). |
| `egeria_solution` | intent | Browse solution architecture: supply chains, blueprints, components. |

_41 intent tool(s) · 0 operation(s). Call an operation as `act(action='<operation>', params={...})` (`ask` for reads); `find(action='describe', params={'action': '<operation>'})` returns its arguments. An operation is enabled unless its `<DOMAIN>TOOL` toggle is set false. Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

## Configuration (environment)

| Var | Default | Meaning |
|---|---|---|
| `EGERIA_PLATFORM_URL` | `https://localhost:9443` | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | `qs-view-server` | View server name |
| `EGERIA_USER` | _(unset)_ | User id |
| `EGERIA_USER_PASSWORD` | _(unset)_ | Password / token, injected at runtime |
| `EGERIA_TLS_PROFILE` | _(unset)_ | Optional runtime TLS profile selector; peer and hostname verification are mandatory |
| `EGERIA_ENABLE_WRITE` | `False` | Gate every write/harvest tool |
| `EGERIATOOL` | `True` | Register the Egeria tool set |

The table above is the **required** set. The bottom-up harvest connectors
(ServiceNow, ERPNext, GitLab, Camunda, Keycloak, Grafana, Portainer, …) each read
their own optional credential vars — every variable, grouped by source system with
required-vs-optional separation, is documented in [`.env.example`](.env.example).
Copy it to `.env` and populate only the connectors the operator use; blank connector
credentials leave the corresponding harvest inactive.

## Install & run

Pick the extra that matches what the operator want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `egeria-mcp[mcp]` | Connector-focused MCP server (`agent-connector-sdk[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | The operator run the **MCP server** (smallest install / image) |
| `egeria-mcp[harvest]` | Bottom-up harvest deps (`pymongo`, `pyyaml`) | The operator run the data-store / connector harvests |
| `egeria-mcp[all]` | Everything (`mcp` + `agent` + `harvest`) | Development / full surface |

```bash
# Connector-focused MCP server (includes the shared graph engine)
uv pip install "egeria-mcp[mcp]"          # or: pip install -e ".[mcp]"

# Everything (development)
uv pip install "egeria-mcp[all]"          # or: python -m pip install "egeria-mcp[all]"

egeria-mcp                       # stdio MCP server (default transport)
egeria-mcp --transport http --host 0.0.0.0 --port 8000
```

The multi-stage `docker/Dockerfile` builds one immutable image (`registry.example.invalid/egeria-mcp@sha256:<digest>`) that
installs `egeria-mcp[all]` and runs the `egeria-mcp` console script; `docker/mcp.compose.yml`
runs it as a streamable-http service.

Run the bottom-up data-store harvest (needs write enabled):

```bash
EGERIA_PLATFORM_URL=https://your-egeria-platform:9443 EGERIA_ENABLE_WRITE=true \
  python -m egeria_mcp.harvest
```

### Knowledge-graph database (`epistemic-graph`)

Both `[mcp]` and `[agent]` carry `epistemic-graph[full]` through the required
Agent Utilities core. The `[mcp]` surface is connector-focused; `[agent]` also
enables model orchestration.

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

`egeria-mcp` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/egeria-mcp/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
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


<!-- BEGIN agent-connector-sdk-deployment (generated; do not edit between markers) -->

## Deploy with `agent-connector-sdk-deployment`

Provision this package with the consolidated **`agent-connector-sdk-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `egeria-mcp` with agent-connector-sdk-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "egeria-mcp[mcp]"`, then run `egeria-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `egeria-mcp` |
| Immutable container | deploy `registry.example.invalid/egeria-mcp@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-connector-sdk-deployment -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | REQUIRED — MCP server runtime |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | stdio \| streamable-http \| sse |
| `AUTH_TYPE` | `none` | none \| oauth \| oidc (agent-connector-sdk auth) |
| `EGERIA_PLATFORM_URL` | `https://egeria.example.invalid:9443` | REQUIRED — Apache Egeria platform / View Server (OMVS) |
| `EGERIA_VIEW_SERVER` | `qs-view-server` |  |
| `EGERIA_USER` | — |  |
| `EGERIA_USER_PASSWORD` | secret-injected |  |
| `EGERIA_TLS_PROFILE` | — | named AgentConfig TLS profile |
| `EGERIA_TLS_PROFILE_REF` | — | direct runtime TLS profile reference (transport_security.py) |
| `EGERIA_ENABLE_WRITE` | `False` | gates every write/harvest tool |
| `EGERIATOOL` | `True` | register the Egeria tool set |
| `EGERIA_HARVEST_TOPOLOGY` | — | path to a topology.json override (blank = built-in) |
| `HOST_INVENTORY` | — | path to an Ansible-style hosts inventory |
| `EGERIA_HARVEST_ENV` | `${XDG_CONFIG_HOME}/agent-connector-sdk/egeria-harvest.env` | EGERIA_HARVEST_ENV defaults to ~/.config/agent-connector-sdk/egeria-harvest.env; uncomment with an ABSOLUTE path to override (a literal ~ is not expanded here). |
| `EGERIA_KG_INGEST` | `True` | default-on: mirror the harvested catalog into the KG; set False to skip |
| `EGERIA_MCP_AGENT_IMAGE` | `registry.example.com/egeria-mcp-agent@sha256:...` | OPTIONAL — Container image pins (docker/*compose*.yml; set by CI/CD, not local dev) |
| `ENABLE_OTEL` | `True` | OPTIONAL — OTEL tracing (agent-connector-sdk framework) |
| `LANGFUSE_BASE_URL` | — | OPTIONAL — Langfuse / LLMOps harvest connector (egeria_mcp.harvest.llmops) |
| `LANGFUSE_PUBLIC_KEY` | secret-injected |  |
| `LANGFUSE_SECRET_KEY` | secret-injected |  |
| `EUNOMIA_TYPE` | `none` | none \| embedded \| remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `ANSIBLE_TOWER_URL` | — |  |
| `ANSIBLE_TOWER_TOKEN` | secret-injected |  |
| `TOWER_URL` | — |  |
| `TOWER_TOKEN` | secret-injected |  |
| `ARCHIVEBOX_URL` | — |  |
| `ARCHIVEBOX_TOKEN` | secret-injected |  |
| `ARCHIVEBOX_API_KEY` | secret-injected |  |
| `ARCHI_MODEL_PATH` | — |  |
| `ARCHER_URL` | — |  |
| `ARCHER_TOKEN` | secret-injected |  |
| `ARCHER_SESSION_ID` | — | alias fallback for ARCHER_TOKEN |
| `ARCHER_APPLICATIONS` | `risks,controls,findings` | comma-separated app list |
| `ARIS_URL` | — |  |
| `ARIS_TOKEN` | secret-injected |  |
| `ARIS_API_TOKEN` | secret-injected | alias fallback for ARIS_TOKEN |
| `ARIS_API_PATH` | `/abs/api/models` | ARIS REST API path |
| `ATLASSIAN_AGENT_URL` | — |  |
| `ATLASSIAN_AGENT_TOKEN` | secret-injected |  |
| `ATLASSIAN_AGENT_USER` | — |  |
| `JIRA_URL` | — |  |
| `JIRA_TOKEN` | secret-injected |  |
| `JIRA_USER` | — |  |
| `CONFLUENCE_URL` | — |  |
| `CONFLUENCE_TOKEN` | secret-injected |  |
| `CONFLUENCE_USER` | — |  |
| `CADDY_ADMIN_URL` | `http://localhost:2019` |  |
| `CAMUNDA_URL` | — |  |
| `CAMUNDA7_URL` | — |  |
| `DATA_SCIENCE_URL` | — |  |
| `DATA_SCIENCE_TOKEN` | secret-injected |  |
| `DATA_SCIENCE_MCP_URL` | — |  |
| `DATA_SCIENCE_MCP_TOKEN` | secret-injected |  |
| `EMERALD_URL` | — |  |
| `EMERALD_TOKEN` | secret-injected |  |
| `EMERALD_PORTFOLIO` | — |  |
| `ERPNEXT_URL` | — |  |
| `ERPNEXT_TOKEN` | secret-injected |  |
| `FIREFLY_URL` | — |  |
| `FIREFLY_TOKEN` | secret-injected |  |
| `GITHUB_ORG` | — |  |
| `GITHUB_TOKEN` | secret-injected |  |
| `GITLAB_URL` | — |  |
| `GITLAB_HOST` | — |  |
| `GITLAB_TOKEN` | secret-injected |  |
| `GITLAB_PRIVATE_TOKEN` | secret-injected |  |
| `GRAFANA_URL` | — |  |
| `GRAFANA_TOKEN` | secret-injected |  |
| `LGTM_TOKEN` | secret-injected |  |
| `HOME_ASSISTANT_URL` | — |  |
| `HOME_ASSISTANT_TOKEN` | secret-injected |  |
| `JENA_URL` | — |  |
| `JENA_FUSEKI_URL` | — |  |
| `JENA_USERNAME` | — |  |
| `JENA_PASSWORD` | secret-injected |  |
| `JENA_TOKEN` | secret-injected |  |
| `KAFKA_REST_URL` | — |  |
| `KAFKA_TOKEN` | secret-injected |  |
| `KEYCLOAK_URL` | — |  |
| `KEYCLOAK_REALM` | `master` |  |
| `KEYCLOAK_CLIENT_ID` | — |  |
| `KEYCLOAK_CLIENT_SECRET` | secret-injected |  |
| `KEYCLOAK_TOKEN` | secret-injected |  |
| `LEANIX_URL` | — |  |
| `LEANIX_TOKEN` | secret-injected |  |
| `LEANIX_API_TOKEN` | secret-injected |  |
| `LISTMONK_URL` | — |  |
| `LISTMONK_TOKEN` | secret-injected |  |
| `LISTMONK_USER` | — |  |
| `MATTERMOST_URL` | — |  |
| `MATTERMOST_TOKEN` | secret-injected |  |
| `MONGODB_URI` | — |  |
| `MONGODB_HOST` | — |  |
| `MONGODB_PORT` | `27017` |  |
| `MSGRAPH_URL` | `https://graph.microsoft.com/v1.0` |  |
| `MSGRAPH_TOKEN` | secret-injected |  |
| `MS_GRAPH_TOKEN` | secret-injected | alias fallback for MSGRAPH_TOKEN |
| `NEXTCLOUD_URL` | — |  |
| `NEXTCLOUD_USERNAME` | — |  |
| `NEXTCLOUD_PASSWORD` | secret-injected |  |
| `ODOO_URL` | — |  |
| `ODOO_DB` | — |  |
| `ODOO_USER` | — |  |
| `ODOO_PASSWORD` | secret-injected |  |
| `ODOO_API_KEY` | secret-injected | alias fallback for ODOO_PASSWORD |
| `OPENAPI_USERNAME` | — |  |
| `OPENAPI_PASSWORD` | secret-injected |  |
| `OPENBAO_URL` | — |  |
| `OPENBAO_TOKEN` | secret-injected |  |
| `BAO_ADDR` | — |  |
| `VAULT_ADDR` | — |  |
| `VAULT_TOKEN` | secret-injected |  |
| `PLANE_URL` | — |  |
| `PLANE_TOKEN` | secret-injected |  |
| `PLANE_WORKSPACE` | — |  |
| `PORTAINER_URL` | — |  |
| `PORTAINER_TOKEN` | secret-injected |  |
| `PORTAINER_API_KEY` | secret-injected |  |
| `PORTAINER_ENDPOINT_ID` | `3` |  |
| `QDRANT_URL` | — |  |
| `QDRANT_API_KEY` | secret-injected |  |
| `SERVICENOW_URL` | — |  |
| `SERVICENOW_TOKEN` | secret-injected |  |
| `SERVICENOW_USER` | — |  |
| `SERVICENOW_PASSWORD` | secret-injected |  |
| `TECHNITIUM_DNS_URL` | — |  |
| `TECHNITIUM_DNS_TOKEN` | secret-injected |  |
| `TWENTY_URL` | — |  |
| `TWENTY_TOKEN` | secret-injected |  |
| `TWENTY_API_PREFIX` | `/rest` |  |
| `UPTIME_KUMA_URL` | — |  |
| `UPTIME_KUMA_TOKEN` | secret-injected |  |
| `VECTOR_URL` | — |  |
| `VECTOR_TOKEN` | secret-injected |  |

#### Inherited agent-connector-sdk variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | — | Operator-configured LLM provider for the agent |
| `MODEL_ID` | — | Operator-configured model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_136 package + 17 inherited variable(s). Auto-generated from `.env.example` + the shared agent-connector-sdk set — do not edit._
<!-- ENV-VARS-TABLE:END -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, Arbora delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
