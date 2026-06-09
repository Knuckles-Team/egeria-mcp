# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Documentation site overhaul (the ecosystem docs standard): polished Material theme
  (tabs, instant nav, 3-way palette, social), new `docs/{installation,deployment,
  usage,platform}.md` covering pip/Docker install, MCP-server deployment with
  Caddy + Technitium, API/CLI/MCP usage, and a Compose recipe for the Apache Egeria
  backing platform. README now points to
  [the published site](https://knuckles-team.github.io/egeria-mcp/) as the official
  reference.

### Changed
- Removed the redundant `docs.yml` workflow; `pages.yml` (GitHub Pages via Actions)
  is the single docs-deploy path now that Pages is enabled with `build_type=workflow`.

### Added (earlier)
- Repository scaffolding parity with the agent-packages ecosystem: GitHub Actions
  workflows (`.github/workflows/{pipeline,docs,pages}.yml` — PyPI publish, Docker
  build, MkDocs deploy), README shields.io badge header, `mkdocs.yml`, Docker build
  scaffolding (`docker/` — MCP-only `Dockerfile`, `debug.Dockerfile`,
  `mcp.compose.yml`, `starship.toml`), and repo-hygiene files (`.gitattributes`,
  `.dockerignore`, `.codespellignore`, `.vulture_ignore`, `.env.example`,
  `pytest.ini`, `opencode.json`).
- Full environment-variable tracking in `.env.example`: every code-referenced var
  (112) now documented, grouped by source system with REQUIRED-vs-OPTIONAL
  separation; README points to it for the harvest-connector credential surface.
- Concept traceability: `CONCEPT:EG-001…009` markers added to their implementing
  docstrings (`EgeriaApi`, `governed_route`, `reconcile`, `_capability_of`, `audit`,
  `harvest_datastores`, `register_egeria_tools`, `list_data_flows`, package init),
  the pytest suite, and a Concept Registry section in `AGENTS.md`.

### Fixed
- Resolved all 12 `mypy` type errors (reconcile loop-variable shadowing, optional
  narrowing in `EgeriaApi._norm`, harvest connector default-URL chains, missing
  `_loaded_optional_modules` annotation) — no behavioral change.
- Converted cross-repo doc links in `docs/concepts.md` / `docs/harvesters.md` to
  absolute GitHub URLs so the rendered MkDocs site builds under `--strict`.

### Added (Egeria features)
- Cross-layer reconciliation (`egeria_mcp.reconcile.reconcile` / `egeria_reconcile`
  MCP tool / `python -m egeria_mcp.harvest reconcile`) — weaves the independently
  harvested layers into one connected lineage/governance graph via 13 deterministic
  matchers (host-hosting, service↔store identity, dataset + source containment,
  ingress exposure, monitoring, CMDB identity, access-control, repo→service
  deployment, datasource→store, EA→reality realization, glossary semantic
  assignment) that create labelled `DataFlow` edges, plus confidentiality propagation
  up hosting chains. Idempotent. Makes `governed_route` cross-layer-aware.
- Bidirectional KG federation: `EgeriaApi.list_data_flows()` now enumerates the
  catalogue's lineage edges (shared scanner in `lineage_scan.py`), and the
  agent-utilities `egeria` extractor maps each to a `:flowsTo` (data movement) or
  `:dependsOn` (structural) KG edge — so reconciled cross-links flow back into the
  epistemic-graph. New `:dependsOn` object property in `ontology_egeria.ttl`.
- Completeness audit (`egeria_mcp.audit.audit` / `egeria_audit` MCP tool) — reports
  unlinked "island" assets and per-layer lineage coverage %.
- Vendor-neutral capability tagging + cross-vendor reconciliation: every asset carries
  a canonical `capability` (ERPNext now `ERP`/`ITSM`/`PM` — it is the open-source
  ServiceNow/Jira alternative; ServiceNow `ITSM`; GitLab/GitHub `vcs`; LeanIX/ArchiMate
  `enterprise-architecture`). Two new reconcile matchers — `capability-cohort`
  (first-party + open-source assets of the same capability grouped under a
  `Capability::<cap>` collection) and `cross-vendor-identity` (same entity tracked in
  two vendor tools) — so a query spans both regardless of vendor. Documented as a
  first-party ↔ open-source capability matrix in agent-utilities + egeria-mcp docs.

## [0.2.0] - 2026-06-08
### Added
- `EgeriaApi` — tolerant raw-httpx REST facade over the Egeria View Server (OMVS),
  with no `pyegeria` runtime dependency (works on Python 3.11–3.14).
- Comprehensive OMVS coverage across 11 View Services (asset catalog, data designer,
  collections, solution architecture, governance, actors/projects/communities,
  generic metadata) plus glossary, lineage, and classification.
- `governed_route()` and the `egeria_governed_route` MCP tool — policy-aware routing
  decisions (proceed / review / require_approval) from Egeria Confidentiality +
  downstream `DataFlow` lineage.
- Bottom-up harvest (`egeria_mcp.harvest`) — idempotent data-store anchor layer that
  populates Egeria with the business-glossary backbone, data-store assets (with
  Confidentiality classifications), and lineage. CLI: `python -m egeria_mcp.harvest`.
  Topology is a generic example by default; override with a private JSON file via
  `EGERIA_HARVEST_TOPOLOGY` so internal infrastructure detail is never published.
- Process harvest (`harvest_processes` / `egeria_harvest_processes`) — reads BPMN
  process definitions live from a Camunda 7 engine (`CAMUNDA7_URL` / `CAMUNDA_URL`)
  and catalogs each as an Egeria `Process` asset; optional declared process→dataset
  lineage via the topology config's `process_flows`.
- ERP harvest (`harvest_erpnext` / `egeria_harvest_erpnext`) — reads business-critical
  DocTypes live from ERPNext/Frappe (`ERPNEXT_URL` + `ERPNEXT_TOKEN`) and catalogs each
  as an Egeria data asset anchored to the ERPNext store, with confidentiality by data
  kind (HR/payroll → Sensitive, PII/financial → Confidential).
- Repository harvest (`harvest_repositories` / `egeria_harvest_repositories`) — reads
  GitLab projects live (`GITLAB_URL` + `GITLAB_TOKEN`) and catalogs each as an Egeria
  `DeployedSoftwareComponent`, confidentiality from project visibility.
- Additional harvest layers (same config-driven, tolerant pattern):
  - **Container/Portainer** (`harvest_containers`) — Swarm nodes → `SoftwareServer`,
    services → `DeployedSoftwareComponent`; the infrastructure substrate
    (`PORTAINER_URL` + `PORTAINER_API_KEY`).
  - **ServiceNow** (`harvest_servicenow`) — CMDB CIs → infrastructure assets
    (`SERVICENOW_URL` + USER/PASSWORD or TOKEN).
  - **Keycloak** (`harvest_identity`) — realms → `Collection` security domains,
    clients → `DeployedSoftwareComponent` (access-aware governance)
    (`KEYCLOAK_URL` + TOKEN or CLIENT_ID/SECRET).
  - **Firefly-III** (`harvest_finance`) — accounts → `Confidential` financial data
    assets (`FIREFLY_URL` + `FIREFLY_TOKEN`).
  - **Plane / Jira** (`harvest_projects`) — projects → Egeria `Project`
    (`PLANE_URL`/TOKEN/WORKSPACE or `JIRA_URL`/USER/TOKEN).
  - **GitHub** (`harvest_github`) — repos → `DeployedSoftwareComponent`
    (`GITHUB_TOKEN` [+ `GITHUB_ORG`]).
- Unified harvest runner (`harvest.runner.harvest_all`) and CLI: `python -m
  egeria_mcp.harvest [layer ...]` runs every configured layer in bottom-up order,
  sourcing a private env file first (`EGERIA_HARVEST_ENV`, default
  `~/.config/agent-utilities/egeria-harvest.env`) so credentials stay out of the repo.
- Extended source coverage to **24 harvest layers**, each config-driven and tolerant:
  ArchiMate models (`ARCHI_MODEL_PATH`), Kafka topics (`KAFKA_REST_URL`), Twenty CRM
  (`TWENTY_URL`/TOKEN), LeanIX fact sheets (`LEANIX_URL`/TOKEN), Ansible/AWX
  (`TOWER_URL`/TOKEN), OpenBao/Vault mounts+policies (`OPENBAO_URL`/TOKEN), MongoDB
  (`MONGODB_URI`), Nextcloud shares (`NEXTCLOUD_*`), Confluence spaces
  (`CONFLUENCE_*`), Technitium DNS zones (`TECHNITIUM_DNS_*`), Caddy routes
  (`CADDY_ADMIN_URL`), Microsoft 365 (`MSGRAPH_TOKEN`), Qdrant collections
  (`QDRANT_URL`), and a host-inventory layer (`HOST_INVENTORY`).
- Generic `egeria_harvest(layer)` MCP tool dispatches any layer (or `all`) via the
  runner — full coverage without a tool per source. Optional deps under the
  `harvest` extra (`pymongo`, `pyyaml`).
- Extended to **34 harvest layers** with the long-tail sources: emerald-exchange
  markets (`EMERALD_URL`/`EMERALD_PORTFOLIO`), Jena Fuseki RDF datasets
  (`JENA_FUSEKI_URL`), Listmonk lists (`LISTMONK_URL`/TOKEN, PII), Home Assistant
  domains (`HOME_ASSISTANT_URL`/TOKEN), data-science models+datasets
  (`DATA_SCIENCE_MCP_URL`), Mattermost teams (`MATTERMOST_URL`/TOKEN), Grafana
  datasources+dashboards (`GRAFANA_URL`/`LGTM_TOKEN`), Uptime Kuma monitors
  (`UPTIME_KUMA_URL`/TOKEN), ArchiveBox snapshots (`ARCHIVEBOX_URL`/KEY), and Langfuse
  datasets (`LANGFUSE_*`). (Lookup/proxy services with no owned inventory — scholarx,
  legal-peripherals — are intentionally not harvested.)
- Write-gated tools (`EGERIA_ENABLE_WRITE`): create asset / term / collection /
  project, classify, assert lineage, harvest.
- Standard package files (AGENTS.md, CLAUDE.md, .bumpversion.cfg, pre-commit, docs).
