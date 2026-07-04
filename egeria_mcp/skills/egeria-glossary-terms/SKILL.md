---
name: egeria-glossary-terms
description: >-
  Business-glossary operations on Apache Egeria via the egeria-mcp MCP server —
  look up GlossaryTerms and GlossaryCategories, and author new terms in the
  open-metadata repository with the domain-typed tools (not raw OMVS calls). Use
  when the agent must resolve the business meaning of a term, browse the glossary
  taxonomy, or create/curate a semantic definition. Do NOT use for asset lineage
  (egeria-lineage-tracing), governance classification / confidentiality routing
  (egeria-governance-classification), or bulk KG mirroring (use the
  egeria_ingest_catalog tool); prefer those.
license: MIT
tags: [egeria, glossary, open-metadata, governance, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# Egeria Glossary Terms

Domain-typed access to Apache Egeria's **business glossary** (GlossaryTerm /
GlossaryCategory) through the Glossary Manager OMVS. Prefer these tools over raw
by-search-string calls — they return flat, GUID-bearing records.

## When to use
- Resolve the meaning of a business term (semantic lookup by name).
- Browse the glossary category taxonomy.
- Author a new GlossaryTerm (idempotent by qualifiedName).

## When NOT to use
- Tracing where data flows between assets → `egeria-lineage-tracing`.
- Confidentiality classification / governed routing → `egeria-governance-classification`.
- Pushing the whole catalog into the knowledge graph → the `egeria_ingest_catalog`
  tool (typed `:GlossaryTerm` / `:DataAsset` nodes; see **Related**).

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`egeria-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `EGERIA_PLATFORM_URL` | ✅ | OMAG platform URL (default `https://localhost:9443`) |
| `EGERIA_VIEW_SERVER` | ✅ | View server name (default `qs-view-server`) |
| `EGERIA_USER` / `EGERIA_USER_PASSWORD` | ✅ | View-server credentials |
| `EGERIA_VERIFY_SSL` | optional | TLS verify (default `False` — self-signed homelab) |
| `EGERIA_ENABLE_WRITE` | for writes | Gates `egeria_create_term` (default `False`) |

`MCP_TOOL_MODE` (`condensed`|`verbose`|`both`) selects the tool surface.

## Tools & actions
| Tool | Purpose |
|------|---------|
| `egeria_glossary_lookup` | Search terms by string (`query`, `glossary`); `*`/`""` = all |
| `egeria_glossary_categories` | List all glossary categories |
| `egeria_create_term` | Create a term (needs `EGERIA_ENABLE_WRITE=true`) |

Records are flat: `guid`, `displayName`, `qualifiedName`, `summary`, `typeName`.

## Recipes
Look up a term:
```
egeria_glossary_lookup  query="Customer"
```
List the category taxonomy:
```
egeria_glossary_categories
```
Author a term (write-gated):
```
egeria_create_term  glossary_name="Business Glossary"  display_name="Churn Rate"  description="Fraction of customers lost in a period."
```

## Gotchas
- An empty `query` (`""`) means match-all on glossary search; other catalogs reject
  empty strings, so this behaviour is glossary-specific.
- Writes fail closed with `EgeriaWriteDisabled` unless `EGERIA_ENABLE_WRITE=true`.
- `create_term` is idempotent by `qualifiedName` — re-running returns the existing GUID.
- `summary` may fall back to `description`; the record flattener surfaces whichever is set.

## Related
- **Lineage:** `egeria-lineage-tracing` (assets + flows).
- **Governance:** `egeria-governance-classification` (confidentiality + policy).
- **KG ingestion:** the `egeria_ingest_catalog` tool mirrors glossary terms into the
  epistemic-graph as typed `:GlossaryTerm` nodes + definition `:Document`s.
