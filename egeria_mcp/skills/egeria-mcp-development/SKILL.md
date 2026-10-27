---
name: egeria-mcp-development
skill_type: skill
domain: development
description: >-
  Develop, test, gate, and release the egeria-mcp connector while preserving
  its raw OMVS client, metadata and lineage boundary, write policy, packaged
  resources, and shared publication contracts.
license: MIT
tags: [egeria, development, connector, mcp, lineage, glossary, governance]
tier: repository
metadata:
  author: Genius
  version: '0.1.0'
---

# Egeria MCP Development

Use this skill for changes inside `egeria-mcp`. The owning delivery row is
`PIPE-CONNSPEC-R117.4`; read it with `AGENTS.md` and the focused tests before
changing a connector surface.

## Repository and runtime map

- `egeria_mcp/__init__.py` is the SDK connector entry point. It binds the
  `Connector` to `EgeriaApi`, `get_client`, `egeria_mcp.mcp_server`, and the
  connector instructions.
- `egeria_mcp/api_client.py` is the public `EgeriaApi`/`Api` facade, while
  `egeria_mcp/api/api_client_egeria.py` owns the raw `httpx` OMVS client,
  normalized list methods, typed catalog searches, and metadata writes. Keep
  the Python 3.14-safe no-`pyegeria` runtime boundary intact.
- `egeria_mcp/auth.py` resolves `EGERIA_PLATFORM_URL`, `EGERIA_VIEW_SERVER`,
  `EGERIA_USER`, `EGERIA_USER_PASSWORD`, and the shared
  `EGERIA_TLS_PROFILE`, then passes the explicit `EGERIA_ENABLE_WRITE` policy
  to the client.
- `egeria_mcp/mcp/mcp_egeria.py` registers the lineage, glossary, catalog,
  governance, actor, metadata, harvest, reconciliation, audit, and KG-ingest
  tools, including `egeria_lineage_scan`, `egeria_governed_route`,
  `egeria_harvest`, `egeria_reconcile`, `egeria_audit`,
  `egeria_ingest_catalog`, and the catalog/action tools. `EGERIA_ENABLE_WRITE`
  gates harvest, classification, reconciliation, and other mutating paths.
- `egeria_mcp/connector_sources.py` declares the live `connector://resources`
  sources and their `GlossaryTerm`/`GovernanceRule` mappings. `egeria_mcp/ontology/`
  carries the packaged Egeria ontology contribution.
- `egeria_mcp/harvest/` contains the config-driven bottom-up estate harvest;
  `harvest/topology.py` reads an optional `EGERIA_HARVEST_TOPOLOGY` override,
  and `harvest/runner.py` owns layer selection and KG-ingest policy.
- `egeria_mcp/skills/**`, `prompts/**`, `ontology/**`, and `connectors/**` are
  package resources. The existing `pyproject.toml` package-data rule must keep
  them in wheels and sdists.

## Federation and safety boundary

Egeria is the metadata, governance, and lineage system of record. The
epistemic-graph KG consumes Egeria records; it does not become the lineage
store, and Egeria does not become the orchestration engine. Preserve
`externalToolId`/`domain="egeria"` identity on Egeria-sourced KG records.

Keep credentials and tenant data in injected environment secrets. TLS uses the
shared verified transport profile; never disable certificate verification or add
an insecure TLS escape hatch or a credential/endpoint dump. Keep write
operations disabled by default and require
`EGERIA_ENABLE_WRITE=true` for intentional writes. Do not reintroduce a
`pyegeria` runtime dependency: the committed client uses raw `httpx` against
the Apache Egeria 6.0 OMAG View Server (OMVS).

## Rapid delivery: the 5-minute contract

1. Read the owning spec row, this skill, `AGENTS.md`, and the directly bound
   tests before editing a connector surface.
2. Trace the changed behavior through the SDK `Connector`, `get_client`, raw
   OMVS facade, MCP registrar, source declarations, ontology, and package-data
   boundary. Reuse existing API methods and action dispatch; do not create a
   second connector or orchestration path.
3. Make the smallest connector-owned change. Preserve OMVS paths and response
   normalization, MCP tool/action names, KG node identity, source identifiers,
   TLS verification, and the `EGERIA_ENABLE_WRITE` gate.
4. Run the directly bound mock/focused tests with the locked environment, then
   run the normal repository hooks. Never bypass a failing hook or use a live
   Egeria tenant in a local test.
5. When package code or resources change, inspect the wheel and sdist for the
   intended `egeria_mcp/skills/**`, prompt, ontology, and connector content.
   Change a version or `uv.lock` only through the normal release process and
   only when a real release or dependency input changed.
6. Treat generated status and Pages as separate evidence. Pipelines owns
   `specs/**/status.json`; do not hand-edit status or promote a rollup from a
   connector change. After an exact main revision publishes, verify the
   successful Pages revision and public `spec-delivery/` snapshot before making
   a publication claim.

## Focused validation

For API or MCP changes, use mock HTTP responses and exercise the smallest
relevant test file. Keep read paths separate from write-gated harvest,
classification, lineage, and reconciliation paths. For a skill or package-data
change, check frontmatter, the required delivery heading, source-backed terms,
and packaged resource inclusion without importing a live Egeria tenant.

From the repository root, the normal commands are:

```bash
uv sync --locked
uv run --locked --extra test pytest -q tests/<focused-test>.py
uvx pre-commit run --all-files
```

## Publication and Pages

`.github/workflows/pipeline.yml` delegates package publication to
`Knuckles-Team/pipelines/.github/workflows/python_pipeline.yml@main` with
`connector: true`, then invokes
`Knuckles-Team/pipelines/.github/workflows/container_pipeline.yml@main` with
`render_connector: true`. `.github/workflows/pages.yml` delegates docs and the
spec dashboard to `pages_pipeline.yml@main` with the checked-in dashboard
configuration. Keep the existing triggers and shared caller contracts intact.

Never place credentials, tenant data, generated release artifacts, or bypass
instructions in a skill. Keep a change focused on `PIPE-CONNSPEC-R117.4` and
cite that row in the commit trailer when this development skill changes.
