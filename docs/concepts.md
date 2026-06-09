# Concept Registry — egeria-mcp

> **Prefix**: `CONCEPT:EG-*`
> **Bridge**: [`CONCEPT:KG-2.9`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concept_map.md)
> (Vendor-Neutral Enterprise Ontology · Self-Registering Extractors)

## Project-Specific Concepts

| Concept ID | Name | Description |
|---|---|---|
| `CONCEPT:EG-001` | Egeria Metadata Federation | Apache Egeria as the metadata/governance/lineage system-of-record, federated with the epistemic-graph KG. Two invariants: the KG is never the lineage store; Egeria never orchestrates. |
| `CONCEPT:EG-002` | Raw-REST OMVS Facade | `EgeriaApi`, a tolerant httpx client over the View Server (OMVS) — no `pyegeria` runtime dep (its `asyncio.get_event_loop()` raises on 3.14). Every call degrades to `[]`. |
| `CONCEPT:EG-003` | Governed Routing | `governed_route()` turns Egeria Confidentiality + downstream lineage into an enforceable decision (proceed / review / require_approval) the policy router acts on. |
| `CONCEPT:EG-004` | Bottom-Up Harvest | Connectors that populate Egeria *from* the data estate in lineage order (data stores → ERPNext → Camunda → GitLab). The data-store layer is the anchor every downstream edge resolves to. |
| `CONCEPT:EG-005` | Broad OMVS Coverage | Action-dispatch tools (`egeria_catalog`, `egeria_data_design`, `egeria_collection`, `egeria_solution`, `egeria_governance_catalog`, `egeria_actors`, `egeria_metadata`) spanning 11 View Services without a tool per noun. |
| `CONCEPT:EG-006` | Cross-Layer Reconciliation | `reconcile()` weaves the independently-harvested layers into one graph — 15 deterministic matchers (host-hosting, service↔store, dataset/source containment, ingress exposure, monitoring, CMDB identity, access-control, repo→service deployment, datasource→store, EA→reality realization, semantic assignment, **capability-cohort + cross-vendor-identity**) create labelled `DataFlow` edges and propagate confidentiality up hosting chains. Idempotent. Makes `governed_route` cross-layer- and cross-vendor-aware. |
| `CONCEPT:EG-009` | Vendor-Neutral Capability Tagging | Every asset carries a canonical `capability` (e.g. ERPNext `ERP`/`ITSM`/`PM`, ServiceNow `ITSM`, GitLab/GitHub `vcs`, LeanIX/ArchiMate `enterprise-architecture`). First-party and open-source adapters for the same capability cross-link through a shared `Capability::<cap>` cohort — supporting both side-by-side. See the [capability matrix](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/architecture/vendor_neutral_enterprise_ontology.md#capability-matrix--first-party-and-open-source). |
| `CONCEPT:EG-007` | Bidirectional KG Federation | `EgeriaApi.list_data_flows()` enumerates the catalogue's lineage edges; the KG `egeria` extractor turns them into `:flowsTo` (data movement) / `:dependsOn` (structural) edges — so the reconciled cross-links flow back into the epistemic-graph and the KG sees the whole estate as one dependency graph. |
| `CONCEPT:EG-008` | Completeness Audit | `audit()` reports unlinked "island" assets, **per-layer** lineage coverage %, and a **per-capability** roll-up (vendors, asset count, linked %, cohort presence) — what reconciliation/harvest still misses + vendor breadth per capability. Loads all assets but scans only the hubs for edges. Read-only. |

## Cross-Project References (from agent-utilities)

| Concept ID | Name | Origin |
|---|---|---|
| `CONCEPT:KG-2.9` | Vendor-Neutral Enterprise Ontology | agent-utilities |
| `CONCEPT:KG-2.8` | Enrichment & Interlinking | agent-utilities |
| `CONCEPT:ORCH-1.2` | Confidence/Policy-Gated Router | agent-utilities |

## Synergy with agent-utilities

`egeria-mcp` integrates via **CONCEPT:KG-2.9**. The self-registering `egeria`
extractor (`knowledge_graph/enrichment/extractors/egeria.py`) consumes Egeria
metadata through `EgeriaApi` and folds it into the epistemic-graph KG using
canonical ArchiMate node types (`ontology_egeria.ttl`), enabling federation with
ServiceNow, ERPNext, Camunda, LeanIX, and infrastructure metadata by GUID/hostname.
The reverse direction — `governed_route` and the bottom-up harvest — writes
governance decisions and provenance back into Egeria, closing the loop.
