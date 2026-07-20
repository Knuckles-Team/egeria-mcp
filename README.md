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

*Version: 1.0.1*

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

#### Condensed action-routed tools (default — `MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `egeria_actors` | `EGERIATOOL` | Browse people/teams, projects, communities, locations, cohorts. |
| `egeria_audit` | `EGERIATOOL` | Completeness audit: report unlinked 'island' assets + per-layer coverage. |
| `egeria_catalog` | `EGERIATOOL` | Browse the technical catalog: assets, connections, endpoints, schema. |
| `egeria_collection` | `EGERIATOOL` | Browse collections and digital products. |
| `egeria_data_design` | `EGERIATOOL` | Browse data-designer artifacts: data structures, fields, value specs. |
| `egeria_governance_catalog` | `EGERIATOOL` | Browse governance definitions, external references, valid-value sets. |
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
| `egeria_metadata` | `EGERIATOOL` | Generic open-metadata access: search across all types, or get by GUID. |
| `egeria_reconcile` | `EGERIATOOL` | Cross-link the harvested layers into one connected lineage/governance graph. |
| `egeria_solution` | `EGERIATOOL` | Browse solution architecture: supply chains, blueprints, components. |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>54 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `egeria_assert_lineage` | `EGERIATOOL` | Assert source → process → target as two ``DataFlow`` edges. |
| `egeria_asset_search` | `EGERIATOOL` | Invoke the asset_search operation. |
| `egeria_classify` | `EGERIATOOL` | Invoke the classify operation. |
| `egeria_create_asset` | `EGERIATOOL` | Create (or reuse) a data asset, optionally classified at creation. |
| `egeria_create_collection` | `EGERIATOOL` | Create (or reuse) a collection (e.g. a digital-product folder). |
| `egeria_create_glossary` | `EGERIA_APITOOL` | Create (or reuse) a business glossary; returns ``{guid, reused?}``. |
| `egeria_create_project` | `EGERIATOOL` | Create (or reuse) a project. |
| `egeria_create_term` | `EGERIATOOL` | Create (or reuse) a glossary term anchored to ``glossary`` (its GUID). |
| `egeria_delete_element` | `EGERIA_APITOOL` | Delete an asset element by GUID. |
| `egeria_find_actor_profiles` | `EGERIA_APITOOL` | Invoke the find_actor_profiles operation. |
| `egeria_find_actor_roles` | `EGERIA_APITOOL` | Invoke the find_actor_roles operation. |
| `egeria_find_asset` | `EGERIA_APITOOL` | Return the GUID of an existing asset by qualifiedName, or None. |
| `egeria_find_cohorts` | `EGERIA_APITOOL` | Invoke the find_cohorts operation. |
| `egeria_find_collections` | `EGERIA_APITOOL` | Invoke the find_collections operation. |
| `egeria_find_communities` | `EGERIA_APITOOL` | Invoke the find_communities operation. |
| `egeria_find_connections` | `EGERIA_APITOOL` | Invoke the find_connections operation. |
| `egeria_find_connector_types` | `EGERIA_APITOOL` | Invoke the find_connector_types operation. |
| `egeria_find_data_assets` | `EGERIA_APITOOL` | Invoke the find_data_assets operation. |
| `egeria_find_data_fields` | `EGERIA_APITOOL` | Invoke the find_data_fields operation. |
| `egeria_find_data_structures` | `EGERIA_APITOOL` | Invoke the find_data_structures operation. |
| `egeria_find_data_value_specifications` | `EGERIA_APITOOL` | Invoke the find_data_value_specifications operation. |
| `egeria_find_digital_products` | `EGERIA_APITOOL` | Invoke the find_digital_products operation. |
| `egeria_find_endpoints` | `EGERIA_APITOOL` | Invoke the find_endpoints operation. |
| `egeria_find_external_references` | `EGERIA_APITOOL` | Invoke the find_external_references operation. |
| `egeria_find_glossary` | `EGERIA_APITOOL` | Return the GUID of an existing glossary by qualifiedName, or None. |
| `egeria_find_information_supply_chains` | `EGERIA_APITOOL` | Invoke the find_information_supply_chains operation. |
| `egeria_find_infrastructure_assets` | `EGERIA_APITOOL` | Invoke the find_infrastructure_assets operation. |
| `egeria_find_locations` | `EGERIA_APITOOL` | Invoke the find_locations operation. |
| `egeria_find_metadata_elements` | `EGERIA_APITOOL` | Search across all open-metadata element types (generic find). |
| `egeria_find_projects` | `EGERIA_APITOOL` | Invoke the find_projects operation. |
| `egeria_find_schema_attributes` | `EGERIA_APITOOL` | Invoke the find_schema_attributes operation. |
| `egeria_find_schema_types` | `EGERIA_APITOOL` | Invoke the find_schema_types operation. |
| `egeria_find_solution_blueprints` | `EGERIA_APITOOL` | Invoke the find_solution_blueprints operation. |
| `egeria_find_solution_components` | `EGERIA_APITOOL` | Invoke the find_solution_components operation. |
| `egeria_find_technology_types` | `EGERIA_APITOOL` | Invoke the find_technology_types operation. |
| `egeria_find_term` | `EGERIA_APITOOL` | Return the GUID of an existing glossary term by qualifiedName, or None. |
| `egeria_find_user_identities` | `EGERIA_APITOOL` | Invoke the find_user_identities operation. |
| `egeria_find_valid_values` | `EGERIA_APITOOL` | Invoke the find_valid_values operation. |
| `egeria_get_element` | `EGERIA_APITOOL` | Retrieve any element by GUID (with its classifications). |
| `egeria_glossary_categories` | `EGERIATOOL` | Invoke the glossary_categories operation. |
| `egeria_glossary_lookup` | `EGERIATOOL` | Invoke the glossary_lookup operation. |
| `egeria_governance_for` | `EGERIATOOL` | Return classifications + confidentiality level applying to an element. |
| `egeria_lineage` | `EGERIATOOL` | Return the asset lineage graph (``AssetLineageGraph``) for a GUID. |
| `egeria_link_data_flow` | `EGERIA_APITOOL` | Create a ``DataFlow`` lineage edge ``source → target``. |
| `egeria_list_assets` | `EGERIA_APITOOL` | Invoke the list_assets operation. |
| `egeria_list_connections` | `EGERIA_APITOOL` | Invoke the list_connections operation. |
| `egeria_list_data_flows` | `EGERIA_APITOOL` | Enumerate ``DataFlow`` lineage edges across the catalogue. |
| `egeria_list_glossary_categories` | `EGERIA_APITOOL` | Invoke the list_glossary_categories operation. |
| `egeria_list_glossary_terms` | `EGERIA_APITOOL` | Invoke the list_glossary_terms operation. |
| `egeria_list_governance_definitions` | `EGERIA_APITOOL` | Invoke the list_governance_definitions operation. |
| `egeria_list_policies` | `EGERIATOOL` | Invoke the list_policies operation. |
| `egeria_list_software_servers` | `EGERIA_APITOOL` | Invoke the list_software_servers operation. |
| `egeria_set_classification` | `EGERIA_APITOOL` | Apply any classification to an element (generic). |
| `egeria_set_confidentiality` | `EGERIA_APITOOL` | Apply/refresh a ``Confidentiality`` classification at ``level`` (0–4). |

</details>

_25 action-routed tool(s) (default) · 54 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (`condensed` default · `verbose` 1:1 · `both`). Auto-generated — do not edit._
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
Copy it to `.env` and populate only the connectors you use; blank connector
credentials leave the corresponding harvest inactive.

## Install & run

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `egeria-mcp[mcp]` | Connector-focused MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | You run the **MCP server** (smallest install / image) |
| `egeria-mcp[harvest]` | Bottom-up harvest deps (`pymongo`, `pyyaml`) | You run the data-store / connector harvests |
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
Agent Utilities core. The `[mcp]` surface is connector-focused; `[agent]` additionally
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


<!-- BEGIN agent-utilities-deployment (generated; do not edit between markers) -->

## Deploy with `agent-utilities-deployment`

Provision this package with the consolidated **`agent-utilities-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `egeria-mcp` with agent-utilities-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "egeria-mcp[mcp]"`, then run `egeria-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `egeria-mcp` |
| Immutable container | deploy `registry.example.invalid/egeria-mcp@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-utilities-deployment -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | REQUIRED — MCP server runtime |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | stdio | streamable-http | sse |
| `AUTH_TYPE` | `none` | none | oauth | oidc (agent-utilities auth) |
| `EGERIA_PLATFORM_URL` | `https://localhost:9443` | REQUIRED — Apache Egeria platform / View Server (OMVS) |
| `EGERIA_VIEW_SERVER` | `qs-view-server` |  |
| `EGERIA_USER` | _(unset)_ |  |
| `EGERIA_USER_PASSWORD` | _(unset)_ | Runtime secret |
| `EGERIA_TLS_PROFILE` | _(unset)_ | Optional runtime TLS profile selector; trust anchors, mTLS, and proxies come from AgentConfig/runtime policy |
| `EGERIA_ENABLE_WRITE` | `False` | gates every write/harvest tool |
| `EGERIATOOL` | `True` | register the Egeria tool set |
| `EGERIA_HARVEST_TOPOLOGY` | — | path to a topology.json override (blank = built-in) |
| `HOST_INVENTORY` | — | path to an Ansible-style hosts inventory |
| `EGERIA_HARVEST_ENV` | — | Optional runtime-injected configuration reference; do not persist a machine path. |
| `ENABLE_OTEL` | `True` | OPTIONAL — OTEL tracing (agent-utilities framework) |
| `LANGFUSE_BASE_URL` | — | OPTIONAL — Langfuse / LLMOps harvest connector (egeria_mcp.harvest.llmops) |
| `LANGFUSE_PUBLIC_KEY` | — |  |
| `LANGFUSE_SECRET_KEY` | — |  |
| `EUNOMIA_TYPE` | `none` | none | embedded | remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `ANSIBLE_TOWER_URL` | — |  |
| `ANSIBLE_TOWER_TOKEN` | — |  |
| `TOWER_URL` | — |  |
| `TOWER_TOKEN` | — |  |
| `ARCHIVEBOX_URL` | — |  |
| `ARCHIVEBOX_TOKEN` | — |  |
| `ARCHIVEBOX_API_KEY` | — |  |
| `ARCHI_MODEL_PATH` | — |  |
| `ARCHER_URL` | — |  |
| `ARCHER_TOKEN` | — |  |
| `ARCHER_SESSION_ID` | — | alias fallback for ARCHER_TOKEN |
| `ARCHER_APPLICATIONS` | `risks,controls,findings` | comma-separated app list |
| `ARIS_URL` | — |  |
| `ARIS_TOKEN` | — |  |
| `ARIS_API_TOKEN` | — | alias fallback for ARIS_TOKEN |
| `ARIS_API_PATH` | `/abs/api/models` | ARIS REST API path |
| `ATLASSIAN_AGENT_URL` | — |  |
| `ATLASSIAN_AGENT_TOKEN` | — |  |
| `ATLASSIAN_AGENT_USER` | — |  |
| `JIRA_URL` | — |  |
| `JIRA_TOKEN` | — |  |
| `JIRA_USER` | — |  |
| `CONFLUENCE_URL` | — |  |
| `CONFLUENCE_TOKEN` | — |  |
| `CONFLUENCE_USER` | — |  |
| `CADDY_ADMIN_URL` | `http://localhost:2019` |  |
| `CAMUNDA_URL` | — |  |
| `CAMUNDA7_URL` | — |  |
| `DATA_SCIENCE_URL` | — |  |
| `DATA_SCIENCE_TOKEN` | — |  |
| `DATA_SCIENCE_MCP_URL` | — |  |
| `DATA_SCIENCE_MCP_TOKEN` | — |  |
| `EMERALD_URL` | — |  |
| `EMERALD_TOKEN` | — |  |
| `EMERALD_PORTFOLIO` | — |  |
| `ERPNEXT_URL` | — |  |
| `ERPNEXT_TOKEN` | — |  |
| `FIREFLY_URL` | — |  |
| `FIREFLY_TOKEN` | — |  |
| `GITHUB_ORG` | — |  |
| `GITHUB_TOKEN` | — |  |
| `GITLAB_URL` | — |  |
| `GITLAB_HOST` | — |  |
| `GITLAB_TOKEN` | — |  |
| `GITLAB_PRIVATE_TOKEN` | — |  |
| `GRAFANA_URL` | — |  |
| `GRAFANA_TOKEN` | — |  |
| `LGTM_TOKEN` | — |  |
| `HOME_ASSISTANT_URL` | — |  |
| `HOME_ASSISTANT_TOKEN` | — |  |
| `JENA_URL` | — |  |
| `JENA_FUSEKI_URL` | — |  |
| `JENA_USERNAME` | — |  |
| `JENA_PASSWORD` | — |  |
| `JENA_TOKEN` | — |  |
| `KAFKA_REST_URL` | — |  |
| `KAFKA_TOKEN` | — |  |
| `KEYCLOAK_URL` | — |  |
| `KEYCLOAK_REALM` | `master` |  |
| `KEYCLOAK_CLIENT_ID` | — |  |
| `KEYCLOAK_CLIENT_SECRET` | — |  |
| `KEYCLOAK_TOKEN` | — |  |
| `LEANIX_URL` | — |  |
| `LEANIX_TOKEN` | — |  |
| `LEANIX_API_TOKEN` | — |  |
| `LISTMONK_URL` | — |  |
| `LISTMONK_TOKEN` | — |  |
| `LISTMONK_USER` | — |  |
| `MATTERMOST_URL` | — |  |
| `MATTERMOST_TOKEN` | — |  |
| `MONGODB_URI` | — |  |
| `MONGODB_HOST` | — |  |
| `MONGODB_PORT` | `27017` |  |
| `MSGRAPH_URL` | `https://graph.microsoft.com/v1.0` |  |
| `MSGRAPH_TOKEN` | — |  |
| `MS_GRAPH_TOKEN` | — | alias fallback for MSGRAPH_TOKEN |
| `NEXTCLOUD_URL` | — |  |
| `NEXTCLOUD_USERNAME` | — |  |
| `NEXTCLOUD_PASSWORD` | — |  |
| `ODOO_URL` | — |  |
| `ODOO_DB` | — |  |
| `ODOO_USER` | — |  |
| `ODOO_PASSWORD` | — |  |
| `ODOO_API_KEY` | — | alias fallback for ODOO_PASSWORD |
| `OPENAPI_USERNAME` | — |  |
| `OPENAPI_PASSWORD` | — |  |
| `OPENBAO_URL` | — |  |
| `OPENBAO_TOKEN` | — |  |
| `BAO_ADDR` | — |  |
| `VAULT_ADDR` | — |  |
| `VAULT_TOKEN` | — |  |
| `PLANE_URL` | — |  |
| `PLANE_TOKEN` | — |  |
| `PLANE_WORKSPACE` | — |  |
| `PORTAINER_URL` | — |  |
| `PORTAINER_TOKEN` | — |  |
| `PORTAINER_API_KEY` | — |  |
| `PORTAINER_ENDPOINT_ID` | `3` |  |
| `QDRANT_URL` | — |  |
| `QDRANT_API_KEY` | — |  |
| `SERVICENOW_URL` | — |  |
| `SERVICENOW_TOKEN` | — |  |
| `SERVICENOW_USER` | — |  |
| `SERVICENOW_PASSWORD` | — |  |
| `TECHNITIUM_DNS_URL` | — |  |
| `TECHNITIUM_DNS_TOKEN` | — |  |
| `TWENTY_URL` | — |  |
| `TWENTY_TOKEN` | — |  |
| `TWENTY_API_PREFIX` | `/rest` |  |
| `UPTIME_KUMA_URL` | — |  |
| `UPTIME_KUMA_TOKEN` | — |  |
| `VECTOR_URL` | — |  |
| `VECTOR_TOKEN` | — |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_TOOL_MODE` | `condensed` | Tool surface: `condensed` | `verbose` | `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP auth (`oidc-client-credentials` for fleet calls) |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET` | — | OIDC client secret (service-account auth) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_133 package + 16 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
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
network transport, connector ingestion, GraphOS delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
