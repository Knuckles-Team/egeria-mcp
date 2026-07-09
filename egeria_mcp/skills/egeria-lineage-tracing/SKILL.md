---
name: egeria-lineage-tracing
skill_type: skill
description: >-
  Data-lineage and asset-catalog operations on Apache Egeria via the egeria-mcp
  MCP server — search the open-metadata asset catalog, trace an asset's upstream
  / downstream lineage graph, assert new DataFlow edges, reconcile harvested
  layers into one graph, and audit lineage coverage. Use when the agent must
  answer "where does this data come from / go to", stitch cross-layer
  dependencies, or find unlinked island assets. Do NOT use for glossary term
  definitions (egeria-glossary-terms) or confidentiality classification
  (egeria-governance-classification); prefer those.
license: MIT
tags: [egeria, lineage, dataflow, asset-catalog, open-metadata, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# Egeria Lineage Tracing

Domain-typed access to Apache Egeria's **asset catalog** and **DataFlow lineage**.
Trace how a data asset connects to the rest of the estate and keep the lineage
graph connected.

## When to use
- Search the asset catalog for a store / dataset / server by name or type.
- Trace an asset's upstream + downstream lineage graph from its GUID.
- Assert a new lineage (`DataFlow`) edge between two assets.
- Reconcile independently-harvested layers into one connected graph, or audit
  which assets are still unlinked "islands".

## When NOT to use
- Business term meaning / glossary taxonomy → `egeria-glossary-terms`.
- Confidentiality level, policies, governed routing → `egeria-governance-classification`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`egeria-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `EGERIA_PLATFORM_URL` | ✅ | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | ✅ | View server name (default `qs-view-server`) |
| `EGERIA_USER` / `EGERIA_USER_PASSWORD` | ✅ | View-server credentials |
| `EGERIA_ENABLE_WRITE` | for writes | Gates `egeria_assert_lineage` + `egeria_reconcile` |

## Tools & actions
| Tool | Purpose |
|------|---------|
| `egeria_asset_search` | Search assets (`query`, `type_filter` substring) |
| `egeria_lineage` | Lineage graph for a GUID (`asset_guid`, `direction`, `depth`) |
| `egeria_assert_lineage` | Create a DataFlow edge (write) |
| `egeria_reconcile` | Cross-link harvested layers into one graph (write) |
| `egeria_audit` | Report unlinked island assets + per-layer coverage (read) |

Assets are flat records with `guid`, `displayName`, `qualifiedName`, `typeName`.

## Recipes
Find an asset, then trace its lineage:
```
egeria_asset_search  query="CustomerDB"  type_filter="Database"
egeria_lineage  asset_guid="<guid>"  direction="both"  depth=2
```
Assert a flow (write-gated):
```
egeria_assert_lineage  source_guid="<upstream>"  target_guid="<downstream>"
```
Weave harvested layers together, then check coverage:
```
egeria_reconcile
egeria_audit
```

## Gotchas
- `egeria_lineage` unwraps the `AssetLineageGraph` envelope; connected edges are in
  `lineageLinkage` / `lineageRelationships`. An empty list usually means the asset
  is an unreconciled island — run `egeria_reconcile`.
- `egeria_reconcile` is idempotent and conservative (deterministic matchers); safe
  to re-run, and it propagates confidentiality up hosting chains.
- Lineage/reconcile writes require `EGERIA_ENABLE_WRITE=true`.
- `type_filter` is a case-insensitive `typeName` **substring**, not an exact type.

## Related
- **Glossary:** `egeria-glossary-terms`.
- **Governance:** `egeria-governance-classification`.
- **KG ingestion:** the `egeria_ingest_catalog` tool mirrors DataFlow edges into the
  epistemic-graph as `:flowsTo` links between `:DataAsset` nodes.
