---
name: egeria-mcp-operations
skill_type: skill
description: >-
  Operate egeria-mcp through its governed MCP and Arbora capabilities, including egeria glossary terms, egeria governance classification, egeria lineage tracing. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Egeria Mcp Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current condensed tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.

## Task workflows

Every step below is one typed tool call; there is no `action` or JSON-string argument. Resolve ids by name first, read before you change, and ask for approval before anything destructive.

## Verify catalog

Confirm which Egeria servers answer and what the catalog holds.

1. `egeria_list_software_servers`
2. `egeria_list_assets`
3. `egeria_list_connections`

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

## Find people and organization

Find actors, roles, user identities, communities and cohorts.

1. `egeria_find_actor_profiles` (search)
2. `egeria_find_actor_roles` (search)
3. `egeria_find_user_identities` (search)
4. `egeria_find_communities` (search)
5. `egeria_find_cohorts` (search)

## Find products and solutions

Find digital products, collections, projects, solution blueprints and components, and information supply chains.

1. `egeria_find_digital_products` (search)
2. `egeria_find_collections` (search)
3. `egeria_find_projects` (search)
4. `egeria_find_solution_blueprints` (search)
5. `egeria_find_solution_components` (search)
6. `egeria_find_information_supply_chains` (search)

## Create collection or project

Create a collection or a project to group metadata.

1. `egeria_create_collection` (display_name, description, category)
2. `egeria_create_project` (display_name, description)

## Retire element

Delete a catalog element after reading it.

1. `egeria_get_element` (guid)
2. `egeria_delete_element` (element_guid, confirm)

## Guardrails

- Never print tokens, passwords or webhook secrets.
- Public or destructive actions need the requester's confirmation of the target and text.
- Report ids (and refusal codes) for every call.
