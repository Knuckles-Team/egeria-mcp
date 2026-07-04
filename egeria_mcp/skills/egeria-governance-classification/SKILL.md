---
name: egeria-governance-classification
description: >-
  Governance, classification, and confidentiality-based routing on Apache Egeria
  via the egeria-mcp MCP server — read the classifications + confidentiality level
  applying to an element, list governance definitions / policies, apply a
  classification, and make a governed routing decision that gates on
  confidentiality. Use when the agent must check whether an asset is
  Confidential/Restricted, enforce a data-handling policy, or decide if a
  destination may receive an element. Do NOT use for glossary definitions
  (egeria-glossary-terms) or raw lineage tracing (egeria-lineage-tracing); prefer
  those.
license: MIT
tags: [egeria, governance, classification, confidentiality, policy, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# Egeria Governance & Classification

Domain-typed access to Apache Egeria's **governance definitions**, **element
classifications**, and the **confidentiality-gated router**. Answer "how is this
governed / how sensitive is it / may it go here".

## When to use
- Read the classifications + confidentiality level applying to an element.
- List governance definitions / policies (optionally by domain).
- Apply a classification (e.g. Confidentiality) to an element.
- Make a governed routing decision that thresholds on confidentiality.

## When NOT to use
- Business-term definitions / glossary → `egeria-glossary-terms`.
- Tracing data flow between assets → `egeria-lineage-tracing`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`egeria-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `EGERIA_PLATFORM_URL` | ✅ | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | ✅ | View server name |
| `EGERIA_USER` / `EGERIA_USER_PASSWORD` | ✅ | View-server credentials |
| `EGERIA_ENABLE_WRITE` | for writes | Gates `egeria_classify` (default `False`) |

## Tools & actions
| Tool | Purpose |
|------|---------|
| `egeria_governance_for` | Classifications + confidentiality level for an `element_guid` |
| `egeria_list_policies` | List governance definitions (optional `domain`) |
| `egeria_governance_catalog` | Browse governance definitions (action-dispatch) |
| `egeria_governed_route` | Confidentiality-gated routing decision for an `asset_guid` |
| `egeria_classify` | Apply a classification (write) |

Confidentiality scale (Egeria): `0` Unclassified, `1` Internal, `2` Confidential,
`3` Sensitive, `4` Restricted.

## Recipes
Check how an element is governed:
```
egeria_governance_for  element_guid="<guid>"
```
List retention/confidentiality policies in a domain:
```
egeria_list_policies  domain="data-protection"
```
Make a governed routing decision:
```
egeria_governed_route  asset_guid="<guid>"
```
Apply a Confidentiality classification (write-gated):
```
egeria_classify  element_guid="<guid>"  classification="Confidentiality"  properties={"confidentialityLevel":2}
```

## Gotchas
- `egeria_governance_for` reads the *named* `elementHeader` classification entries
  (`ElementClassification`), not a flat `classifications` list; the structural
  `Anchors` entry is filtered out.
- `confidentialityLevel` is surfaced only for the `Confidentiality` classification;
  other classifications carry no level.
- `egeria_governed_route` thresholds on that integer level — an unclassified asset
  (`null` level) is treated as ungated.
- `egeria_classify` requires `EGERIA_ENABLE_WRITE=true`.

## Related
- **Glossary:** `egeria-glossary-terms`.
- **Lineage:** `egeria-lineage-tracing`.
- **KG ingestion:** the `egeria_ingest_catalog` tool mirrors governance definitions
  into the epistemic-graph as typed `:GovernanceRule` nodes.
