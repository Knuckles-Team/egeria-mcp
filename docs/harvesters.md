# Harvesters, Cross-Links & Federation — Complete Map

The full reference for what `egeria-mcp` ingests, how the layers are cross-linked, and
how it federates back into the knowledge graph. All layers are **config-driven** (read
their connection from the environment), **tolerant** (skip with a clear message when a
source/credential is absent), and **idempotent** (reconcile by `qualifiedName`).

Run order and dispatch: `python -m egeria_mcp.harvest [layer … | all | reconcile | audit]`
or the `egeria_harvest(layer)` MCP tool. A full run does **harvest → reconcile → audit**.
Confidentiality scale: **0** Unclassified · **1** Internal · **2** Confidential ·
**3** Sensitive · **4** Restricted.

## 1. Ingesters (34 source layers)

### Infrastructure substrate
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `hosts` | inventory file | `HOST_INVENTORY` | `SoftwareServer` | 1 | managed hosts from a YAML/JSON inventory (systems/tunnel-manager) |
| `datastores` | declared estate | `EGERIA_HARVEST_TOPOLOGY` | `SoftwareServer`, `RelationalDatabase` | per-store | data-store servers + databases + DataFlow lineage (anchor layer) |
| `containers` | Portainer/Swarm | `PORTAINER_URL`,`PORTAINER_API_KEY`,`PORTAINER_ENDPOINT_ID` | `SoftwareServer` (nodes), `DeployedSoftwareComponent` (services) | 1 | swarm nodes + services |
| `dns` | Technitium DNS | `TECHNITIUM_DNS_URL`,`TECHNITIUM_DNS_TOKEN` | `Collection` (zone) | — | authoritative DNS zones |
| `proxy` | Caddy admin | `CADDY_ADMIN_URL` | `DeployedSoftwareComponent` (route) | 1 | reverse-proxy routed hosts + upstreams |

### Data stores
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `documentdb` | MongoDB | `MONGODB_URI` / `MONGODB_HOST` | `RelationalDatabase` (db), `DeployedDatabaseSchema` (collection) | 2 | databases + collections (needs `pymongo`) |
| `vectors` | Qdrant | `QDRANT_URL`,`QDRANT_API_KEY` | `SoftwareServer` (store), `DeployedDatabaseSchema` (collection) | 1 | vector collections |
| `semantic` | Apache Jena Fuseki | `JENA_FUSEKI_URL`,`JENA_USERNAME`/`JENA_PASSWORD` | `SoftwareServer` (store), `DeployedDatabaseSchema` (dataset) | 1 | RDF datasets / named graphs |
| `kafka` | Kafka REST proxy | `KAFKA_REST_URL`,`KAFKA_TOKEN` | `DeployedDatabaseSchema` (topic) | 1 | Kafka topics |

### Business & finance
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `finance` | Firefly-III | `FIREFLY_URL`,`FIREFLY_TOKEN` | `SoftwareServer` (store), `DeployedDatabaseSchema` (account) | 2 | personal-finance accounts |
| `markets` | emerald-exchange | `EMERALD_URL`,`EMERALD_TOKEN` / `EMERALD_PORTFOLIO` | `SoftwareServer` (store), `DeployedDatabaseSchema` (instrument) | 2 | financial instruments / holdings |
| `crm` | Twenty CRM | `TWENTY_URL`,`TWENTY_TOKEN`,`TWENTY_API_PREFIX` | `SoftwareServer` (store), `DeployedDatabaseSchema` (record) | 2–3 | companies (2) + people (3, PII) |
| `erpnext` | ERPNext/Frappe | `ERPNEXT_URL`,`ERPNEXT_TOKEN` | `SoftwareServer`, `RelationalDatabase`, `DeployedDatabaseSchema` (DocType) | 1–3 | business DocTypes; HR/payroll→3, PII/financial→2 |
| `mailing` | Listmonk | `LISTMONK_URL`,`LISTMONK_USER`,`LISTMONK_TOKEN` | `DeployedDatabaseSchema` (list) | 2 | mailing lists (PII) |
| `files` | Nextcloud | `NEXTCLOUD_URL`,`NEXTCLOUD_USERNAME`,`NEXTCLOUD_PASSWORD` | `DeployedDatabaseSchema` (share) | 2 | shared files/folders |
| `ml` | data-science | `DATA_SCIENCE_MCP_URL`,`DATA_SCIENCE_MCP_TOKEN` | `DeployedSoftwareComponent` (model), `DeployedDatabaseSchema` (dataset) | 1–2 | ML models (1) + training datasets (2) |

### Identity & governance
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `identity` | Keycloak | `KEYCLOAK_URL`,`KEYCLOAK_TOKEN` / `KEYCLOAK_CLIENT_ID`+`KEYCLOAK_CLIENT_SECRET`,`KEYCLOAK_REALM` | `Collection` (realm), `DeployedSoftwareComponent` (client) | 1 | security realms + OIDC clients |
| `secrets` | OpenBao/Vault | `OPENBAO_URL`/`VAULT_ADDR`,`OPENBAO_TOKEN`/`VAULT_TOKEN` | `DeployedSoftwareComponent` (engine 2, policy 1) | 1–2 | secret-engine mounts + ACL policy names (never values) |
| `servicenow` | ServiceNow CMDB | `SERVICENOW_URL`,`SERVICENOW_USER`+`SERVICENOW_PASSWORD` / `SERVICENOW_TOKEN` | `SoftwareServer` (CI) | 1 | CMDB configuration items |

### Knowledge & enterprise architecture
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `knowledge` | Confluence | `CONFLUENCE_URL`,`CONFLUENCE_USER`,`CONFLUENCE_TOKEN` (or `ATLASSIAN_AGENT_*`) | `Collection` (space) | — | Confluence spaces |
| `m365` | Microsoft Graph | `MSGRAPH_TOKEN`,`MSGRAPH_URL` | `Collection` (site/group) | — | SharePoint sites + M365 groups |
| `iot` | Home Assistant | `HOME_ASSISTANT_URL`,`HOME_ASSISTANT_TOKEN` | `SoftwareServer` (hub), `Collection` (domain) | 1 | integration domains |
| `archimate` | ArchiMate model | `ARCHI_MODEL_PATH` | layer-mapped (`DeployedSoftwareComponent`/`Process`/`SoftwareServer`/`DeployedDatabaseSchema`) | 1 | ArchiMate Open Exchange elements |
| `leanix` | SAP LeanIX | `LEANIX_URL`,`LEANIX_API_TOKEN` | `Collection` (portfolio), `DeployedSoftwareComponent`/`Process`/… (fact sheet) | 1 | EA fact sheets |

### Automation, code & work
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `automation` | Ansible/AWX Tower | `TOWER_URL`,`TOWER_TOKEN` | `Collection` (inventory), `Process` (job template) | 1 | inventories + job templates |
| `processes` | Camunda 7 | `CAMUNDA7_URL` / `CAMUNDA_URL` | `Process` | 1 | BPMN process definitions |
| `projects` | Plane / Jira | `PLANE_URL`,`PLANE_TOKEN`,`PLANE_WORKSPACE` / `JIRA_URL`,`JIRA_USER`,`JIRA_TOKEN` | `Project` | — | work-tracking projects |
| `gitlab` | GitLab | `GITLAB_URL`,`GITLAB_TOKEN` | `DeployedSoftwareComponent` (repo) | by visibility | repositories |
| `github` | GitHub | `GITHUB_TOKEN`,`GITHUB_ORG` | `DeployedSoftwareComponent` (repo) | by visibility | repositories |

### Collaboration & observability
| Layer | Source | Env | Egeria asset(s) | Conf | Catalogs |
|---|---|---|---|---|---|
| `chat` | Mattermost | `MATTERMOST_URL`,`MATTERMOST_TOKEN` | `Collection` (team) | — | teams |
| `observability` | Grafana | `GRAFANA_URL`,`LGTM_TOKEN`/`GRAFANA_TOKEN` | `DeployedSoftwareComponent` (datasource), `Collection` (dashboard) | 1 | data sources + dashboards |
| `monitoring` | Uptime Kuma | `UPTIME_KUMA_URL`,`UPTIME_KUMA_TOKEN` | `DeployedSoftwareComponent` (monitor) | 1 | monitored targets (via `/metrics`) |
| `archive` | ArchiveBox | `ARCHIVEBOX_URL`,`ARCHIVEBOX_API_KEY` | `Collection` (corpus), `DeployedDatabaseSchema` (snapshot) | 1 | web snapshots |
| `llmops` | Langfuse | `LANGFUSE_BASE_URL`,`LANGFUSE_PUBLIC_KEY`,`LANGFUSE_SECRET_KEY` | `DeployedDatabaseSchema` (dataset) | 1 | LLM datasets |

> Excluded by design (lookup/search proxies with no owned inventory): `scholarx`,
> `legal-peripherals`. Excluded as non-governable: media/personal peripherals.

### First-party ↔ open-source coverage

The federation is **vendor-pluggable**: a capability is served by a first-party tool,
an open-source equivalent, or both — and every adapter catalogs into the *same* Egeria
types, so reasoning is identical. egeria-mcp ships harvesters for **both columns**
where the estate runs both:

| Capability | First-party harvester | Open-source harvester |
|---|---|---|
| ITSM / service mgmt | `servicenow` | `erpnext` (DocTypes `Issue`/`HD Ticket`, `capability=ITSM`) |
| Enterprise architecture | `leanix` | `archimate` |
| VCS / code | `github` | `gitlab` |
| Productivity / knowledge | `m365`, `knowledge` (Confluence) | `files` (Nextcloud) |
| Project / work tracking | `projects` (Jira) | `projects` (Plane), `erpnext` (`capability=PM`) |
| BPM / process | — | `processes` (Camunda), `automation` (Ansible) |
| Metadata / catalog | — | Apache Egeria (the SoR) |

ERPNext is intentionally **multi-role** — its `capability` property (`ERP` / `ITSM` /
`PM`) lets the federation reconcile it with whichever first-party tool it substitutes
for. The canonical capability map (every capability × first-party × open-source ×
canonical concept) lives in the agent-utilities
[vendor-neutral ontology doc](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/architecture/vendor_neutral_enterprise_ontology.md#capability-matrix--first-party-and-open-source).

## 2. Cross-link patterns (13) — `reconcile()`

Each matcher creates a labelled `DataFlow` edge (or, for P10, propagates
confidentiality). Matching is deterministic; linking reads existing lineage first so
re-runs add nothing.

| # | Pattern | Match rule | Edge label | Layers joined |
|---|---|---|---|---|
| P1 | host-hosting | `asset.additionalProperties.hostNode == Node.name` | `hosts` | containers ↔ data/erp/finance |
| P3 | service-store | `Service::*_<name>` ≍ `DataStore::<name>` | `realizes` | containers ↔ datastores |
| P4 | dataset-store | `Dataset::<store>::*` parent → `DataStore::<store>` | `hosts` | within/across data |
| P11 | source-store | `asset.source` ∈ {Kafka,Qdrant,Jena,Firefly,Twenty,ERPNext,Emerald,HA} → its `DataStore` | `hosts` | data layers ↔ store layer |
| P5 | ingress-exposure | `Route.upstream` host == Service name | `routes-to` | proxy ↔ containers |
| P6 | monitoring | `Monitor.name` ≍ Route/Service/Node/Store | `monitors` | monitoring ↔ infra |
| P7 | cmdb-identity | `CI::ServiceNow::<name>` == infra name | `same-as` | servicenow ↔ infra |
| P8 | access-control | Keycloak `Client::*::<id>` ≍ Service | `secures` | identity ↔ containers |
| P12 | repo-service | `Repository::*/<name>` ≍ Service name | `deploys` | code ↔ infra |
| P16 | datasource-store | `Datasource::Grafana::<name>` ≍ `DataStore::<name>` | `reads` | observability ↔ data |
| P21 | ea-realization | ArchiMate/LeanIX element name ≍ Service/Store/Repo | `realized-by` | EA ↔ running reality |
| P9 | semantic-assignment | `asset.displayName == Glossary Term` | `means` | any ↔ glossary |
| P22 | capability-cohort | assets sharing a `capability` from ≥2 sources → a `Capability::<cap>` collection | `groups` | **same-capability, cross-vendor** (ITSM: ServiceNow+ERPNext; vcs: GitLab+GitHub; EA: LeanIX+ArchiMate) |
| P23 | cross-vendor-identity | same `displayName`, same capability, different `source` | `same-as` | the same entity tracked in two vendor tools |
| P10 | confidentiality-propagation | store hosts higher-classified data | *(raises store level)* | governance enrichment |

**Capability tagging.** Each asset carries a canonical `capability` property
(`ERP`/`ITSM`/`PM` on ERPNext, `vcs` on GitLab/GitHub, `enterprise-architecture` on
LeanIX/ArchiMate, `ITSM` on ServiceNow, …); where untagged, reconcile derives it from
the asset's `source`/prefix. P22/P23 use it to connect first-party and open-source
adapters that serve the same capability, so a query spans both regardless of vendor.

The **audit** (`audit()` / `egeria_audit`) reports which assets remain unlinked
islands and per-layer coverage % — the radar for which layers to harvest next.

## 3. Federation back into the KG (bidirectional)

`EgeriaApi.list_data_flows()` enumerates the catalogue's `DataFlow` edges (shared
scanner `lineage_scan.py`, scanning the low-cardinality hubs). The agent-utilities
`egeria` extractor turns them into KG edges:

| Reconcile edge label | KG edge type |
|---|---|
| `routes-to`, `produces`, `consumes`, harvest flows | `:flowsTo` |
| `hosts`, `realizes`, `secures`, `monitors`, `same-as`, `means`, `deploys`, `reads` | `:dependsOn` |

Egeria asset typeName → KG node type: `SoftwareServer`→`Server`,
`DeployedSoftwareComponent`→`Tool`, `RelationalDatabase`/`DeployedDatabaseSchema`→`DataObject`,
`Process`→`ProcessModel`, `Collection`→`Concept`, else `DataConnector`. Every node
carries `externalToolId` (Egeria GUID) + `domain="egeria"` (federation key).

See [architecture.md](architecture.md) for the pipeline diagrams.
