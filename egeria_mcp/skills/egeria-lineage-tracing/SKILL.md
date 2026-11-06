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
  author: Knuckles-Team
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
| `EGERIA_ENABLE_WRITE` | for writes | Gates `egeria_assert_lineage` + `egeria_reconcile` + `egeria_reconcile_openlineage_asset` |

## Tools & actions
| Tool | Purpose |
|------|---------|
| `egeria_asset_search` | Search assets (`query`, `type_filter` substring) |
| `egeria_lineage` | Lineage graph for a GUID (`asset_guid`, `direction`, `depth`) |
| `egeria_lineage_scan` | Bulk-scan the hub prefixes for every DataFlow edge (read) |
| `egeria_assert_lineage` | Create a DataFlow edge (write) |
| `egeria_reconcile_openlineage_asset` | Look up/create an Egeria DataAsset for an OpenLineage-named Iceberg dataset and assert its lineage (write) |
| `egeria_asset_for_kg_node` | KG node id → Egeria GUID (read) |
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
Bulk-scan every hub-prefix lineage edge at once (what `egeria_reconcile`/
`egeria_ingest_catalog` already do internally, exposed directly):
```
egeria_lineage_scan  max_total=2000
```
Reconcile an OpenLineage-fed Iceberg dataset into Egeria (CA-25's Kafka
consumer calls this once per dataset; DEC-CA-05's naming rule) — Egeria is a
peer/exchange here, never the lineage store of record:
```
egeria_reconcile_openlineage_asset  dataset_name="iceberg://lakehouse/sales/orders@snap-42"  job_name="etl-orders"  produced_from="iceberg://lakehouse/raw/orders_raw@snap-7"
```
Resolve a KG node id back to its Egeria GUID (the reverse of
`egeria_ingest_catalog`'s GUID→node-id mapping):
```
egeria_asset_for_kg_node  node_id="egeria:DataAsset:<guid>"
```

## Gotchas
- `egeria_lineage` unwraps the `AssetLineageGraph` envelope; connected edges are in
  `lineageLinkage` / `lineageRelationships`. An empty list usually means the asset
  is an unreconciled island — run `egeria_reconcile`.
- `egeria_reconcile` is idempotent and conservative (deterministic matchers); safe
  to re-run, and it propagates confidentiality up hosting chains.
- `egeria_reconcile_openlineage_asset` is idempotent by `(dataset_name, snapshot)`
  — re-running it never duplicates the asset or the lineage edge. A `dataset_name`
  (or `produced_from`) that doesn't parse as
  `iceberg://<catalog>/<ns>/<table>@<snapshot>` is quarantined (a typed error),
  never guessed.
- Lineage/reconcile writes require `EGERIA_ENABLE_WRITE=true`.
- `type_filter` is a case-insensitive `typeName` **substring**, not an exact type.

## Related
- **Glossary:** `egeria-glossary-terms`.
- **Governance:** `egeria-governance-classification`.
- **KG ingestion:** the `egeria_ingest_catalog` tool mirrors DataFlow edges into the
  epistemic-graph as `:flowsTo` links between `:DataAsset` nodes; `egeria_asset_for_kg_node`
  is its reverse lookup.

## Task workflows

Every step below is one typed tool call; there is no `action` or JSON-string argument. Resolve ids by name first, read before you change, and ask for approval before anything destructive.

## Register data asset

Register a data asset once, with its confidentiality.

1. `egeria_find_asset` (qualified_name)
2. `egeria_create_asset` (type_name, qualified_name, display_name, description, deployed_implementation_type, confidentiality_level, additional_properties)
3. `egeria_set_confidentiality` (element_guid, level)
4. `egeria_classify` (element_guid, classification, properties)
5. `egeria_get_element` (guid)

## Find data elements

Search the catalog for assets, schemas, fields, values, connections and technology.

1. `egeria_asset_search` (query, type_filter)
2. `egeria_find_data_assets` (search)
3. `egeria_find_metadata_elements` (search)
4. `egeria_find_data_structures` (search)
5. `egeria_find_schema_types` (search)
6. `egeria_find_schema_attributes` (search)
7. `egeria_find_data_fields` (search)
8. `egeria_find_data_value_specifications` (search)
9. `egeria_find_valid_values` (search)
10. `egeria_find_external_references` (search)
11. `egeria_find_connections` (search)
12. `egeria_find_connector_types` (search)
13. `egeria_find_endpoints` (search)
14. `egeria_find_technology_types` (search)
15. `egeria_find_infrastructure_assets` (search)
16. `egeria_find_locations` (search)

## Trace lineage

Trace where an asset's data comes from and goes to.

1. `egeria_asset_search` (query, type_filter)
2. `egeria_lineage` (asset_guid, direction, depth)
3. `egeria_list_data_flows`
4. `egeria_lineage_scan` (max_total)
5. `egeria_asset_for_kg_node` (node_id)

## Record lineage

Record a data flow from a source through a process to a target, or reconcile an OpenLineage dataset.

1. `egeria_find_asset` (qualified_name)
2. `egeria_assert_lineage` (source_guid, process_guid, target_guid)
3. `egeria_link_data_flow` (source_guid, target_guid, label, description)
4. `egeria_reconcile_openlineage_asset` (dataset_name, job_name, produced_from)

## Harvest estate

Catalog the estate into Egeria layer by layer, cross-link the layers and audit completeness.

1. `egeria_harvest` (layer)
2. `egeria_harvest_datastores`
3. `egeria_harvest_processes`
4. `egeria_harvest_erpnext`
5. `egeria_harvest_repositories`
6. `egeria_harvest_github`
7. `egeria_harvest_containers`
8. `egeria_harvest_servicenow`
9. `egeria_harvest_identity`
10. `egeria_harvest_finance`
11. `egeria_harvest_projects`
12. `egeria_harvest_aris`
13. `egeria_harvest_archer`
14. `egeria_harvest_crm`
15. `egeria_harvest_odoo`
16. `egeria_reconcile`
17. `egeria_audit`

## Guardrails

- Never print tokens, passwords or webhook secrets.
- Public or destructive actions need the requester's confirmation of the target and text.
- Report ids (and refusal codes) for every call.
