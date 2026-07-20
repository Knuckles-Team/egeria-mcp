# egeria-mcp Overview

`egeria-mcp` wraps the Apache Egeria OMAG platform's **View Server (OMVS)** REST
surface with thin MCP tools, and is the write side of the Egeria↔KG federation.

Egeria is federated into agent-utilities as the **metadata / governance / lineage
system-of-record**, alongside the epistemic-graph Knowledge Graph (the
cognition/orchestration plane). Two hard invariants hold:

- **The KG never becomes the lineage store** — Egeria owns data lineage, the
  business glossary, and data-governance classifications.
- **Egeria never orchestrates** — `graph_orchestrate` / the policy router stay the
  orchestration brain; Egeria is the metadata oracle they *query* and write
  provenance back to.

## What it provides

- **`EgeriaApi`** (`egeria_mcp.api.api_client_egeria`) — a tolerant **raw-httpx REST**
  facade over the View Server. It deliberately avoids the `pyegeria` runtime
  dependency: pyegeria's synchronous wrappers call `asyncio.get_event_loop()`, which
  raises on Python 3.14; plain `httpx` works identically on 3.11 and 3.14. Every call
  degrades to `[]` / a clear error rather than raising. It is also the injected
  `config["client"]` for the KG `egeria` enrichment extractor.

- **MCP tools** (`egeria-mcp` console script) — 21 tools:
  - **Read (granular):** `egeria_asset_search`, `egeria_glossary_lookup`,
    `egeria_glossary_categories`, `egeria_lineage`, `egeria_governance_for`,
    `egeria_list_policies`.
  - **Read (broad, action-dispatch):** `egeria_catalog` (assets, connections,
    connector-types, endpoints, infrastructure, technology types, schema
    types/attributes), `egeria_data_design` (data structures/fields/value specs),
    `egeria_collection` (collections, digital products), `egeria_solution`
    (information supply chains, blueprints, components), `egeria_governance_catalog`
    (governance definitions, external references, valid values), `egeria_actors`
    (actor profiles/roles, user identities, projects, communities, locations,
    cohorts), `egeria_metadata` (generic find/get across all element types).
  - **Routing:** `egeria_governed_route` — the federation delivering a decision.
  - **Harvest (write-gated):** `egeria_harvest(layer)` dispatches any of **34
    bottom-up source layers** (or `all`) via the runner — spanning infrastructure
    (hosts, Swarm/containers, DNS, Caddy), data stores (Postgres, MongoDB, Qdrant,
    Jena RDF, Kafka), business systems (Firefly + emerald-exchange markets, Twenty
    CRM, ERPNext, Listmonk, Nextcloud, data-science ML), identity/governance
    (Keycloak, OpenBao, ServiceNow), knowledge/EA (Confluence, M365, ArchiMate,
    LeanIX), automation/code/work (Ansible, Camunda, Plane/Jira, GitLab, GitHub), and
    collaboration/observability (Mattermost, Grafana, Uptime Kuma, ArchiveBox,
    Langfuse). (The original ten also keep dedicated `egeria_harvest_*` tools.)
  - **Reconcile (write-gated):** `egeria_reconcile` cross-links the harvested layers
    into one graph (`reconcile()`) — deterministic matchers create labelled `DataFlow`
    edges across layers (host→asset, service↔store, dataset→store, ingress→service,
    monitor→target, CMDB identity, access-control, glossary semantic assignment) and
    propagate confidentiality up hosting chains, so `governed_route` impact is
    cross-layer-aware. Idempotent. Also `python -m egeria_mcp.harvest reconcile`.
  - **Audit (read-only):** `egeria_audit` reports unlinked "island" assets and
    per-layer lineage coverage % — what reconciliation/harvest still misses.

The reconciled graph also federates **back into the KG**: `EgeriaApi.list_data_flows()`
enumerates the catalogue's lineage edges and the agent-utilities `egeria` extractor
turns each into a `:flowsTo` (data movement) or `:dependsOn` (structural) edge — so
the epistemic-graph sees the whole estate as one dependency graph.
  - **Write (gated by `EGERIA_ENABLE_WRITE`):** `egeria_classify`,
    `egeria_create_term`, `egeria_create_asset`, `egeria_create_collection`,
    `egeria_create_project`, `egeria_assert_lineage`.

## Governed routing — the federation delivering value

`egeria_governed_route(asset_guid)` consults Egeria's `Confidentiality`
classification and downstream `DataFlow` lineage for an asset and returns an
enforceable decision the policy router acts on:

| Confidentiality level | Downstream lineage | Decision |
|---|---|---|
| ≥ 2 (Confidential/Sensitive/Restricted) | any | `require_approval` |
| < 2 | > 0 | `review` |
| < 2 | 0 | `proceed` |

Egeria's `Confidentiality` scale: 0 Unclassified · 1 Internal · 2 Confidential ·
3 Sensitive · 4 Restricted.

## Bottom-up harvest

`egeria_mcp.harvest` populates Egeria *from* the data estate in lineage order so
every edge resolves to an already-catalogued target. The **data-store layer**
(`harvest/datastores.py`, declared in `harvest/topology.py`) is the anchor: it
idempotently catalogs the business-glossary backbone, the data-store servers +
databases (with Confidentiality classifications), and the `DataFlow` lineage
between them. Run it with `python -m egeria_mcp.harvest` (needs
`EGERIA_ENABLE_WRITE=true`). Higher layers follow the same config-driven, tolerant pattern: **Camunda**
(`harvest_processes`, BPMN definitions → `Process` assets, `CAMUNDA7_URL`), **ERPNext**
(`harvest_erpnext`, DocTypes → data assets with confidentiality by data kind,
`ERPNEXT_URL`+`ERPNEXT_TOKEN`), and **GitLab** (`harvest_repositories`, projects →
`DeployedSoftwareComponent` assets, `GITLAB_URL`+`GITLAB_TOKEN`). Each skips
gracefully (reported, not raised) when its source is unconfigured/unreachable.

The estate is declared in `harvest/topology.py` as a **generic, non-sensitive
example**. Point the harvest at your real data stores with the
`EGERIA_HARVEST_TOPOLOGY` environment variable (path to a JSON file of the same
shape) — keep that file outside any public repository so internal
hostnames/addresses are never published.

## Egeria 6.0 REST contract (verified)

| Operation | Endpoint | Notes |
|---|---|---|
| Token | `POST {platform}/api/token` | `{userId,password}` → bearer JWT |
| Find | `POST .../{service}/{noun}/by-search-string` | `SearchStringRequestBody`; **empty string = match-all** |
| Create | `POST .../{service}/{noun}` | `NewElementRequestBody`, typed `properties.class` |
| Read-back | `POST .../asset-maker/assets/{guid}/retrieve` | classifications are named `elementHeader` keys |
| Classify | `POST .../classification-explorer/elements/{guid}/{name}` | bean field is `confidentialityLevel` |
| Lineage write | `POST .../lineage-linker/from-elements/{a}/via/DataFlow/to-elements/{b}/attach` | `DataFlowProperties` |
| Lineage read | `POST .../asset-catalog/assets/{guid}/as-lineage-graph` | edges in `element.lineageLinkage` |

## Integration with agent-utilities

- **Extractor:** `agent_utilities/knowledge_graph/enrichment/extractors/egeria.py`
  (CONCEPT:AU-KG.ingest.enterprise-source-extractor) — pure transform; `EgeriaApi` injected as `config["client"]`.
- **Ontology:** `agent_utilities/knowledge_graph/ontology_egeria.ttl` — ArchiMate
  crosswalk reusing the enterprise classes (GlossaryTerm→`:Concept`,
  Asset/Connection→`:DataConnector`, Policy→`:Policy`, DataFlow→`:flowsTo`).
- **Federation key:** every Egeria-sourced node carries `externalToolId` (the Egeria
  GUID) + `domain="egeria"`, so it reconciles with ServiceNow / ERPNext / Camunda /
  infra nodes by GUID/hostname rather than forking parallel nodes.

## Configuration (environment)

| Var | Default | Meaning |
|---|---|---|
| `EGERIA_PLATFORM_URL` | `https://localhost:9443` | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | `qs-view-server` | View server name |
| `EGERIA_USER` | _(unset)_ | User id |
| `EGERIA_USER_PASSWORD` | _(unset)_ | Password / token, injected at runtime |
| `EGERIA_TLS_PROFILE` | _(unset)_ | Optional runtime TLS profile selector; verification is mandatory |
| `EGERIA_ENABLE_WRITE` | `False` | Gate every write/harvest tool |
| `EGERIATOOL` | `True` | Register the Egeria tool set |
