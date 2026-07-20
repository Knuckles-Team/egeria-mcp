"""Native epistemic-graph ingestion for Egeria open-metadata records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The record-source twin of the
gitlab/media connectors: egeria-mcp natively pushes Egeria's metadata /
governance / lineage system-of-record into the ONE epistemic-graph engine as
**typed OWL nodes** (``:GlossaryTerm``, ``:GovernanceRule``, ``:DataAsset``,
``:GlossaryCategory``) plus ``:flowsTo`` / ``:dependsOn`` **lineage edges**, and
the term/policy definition text as ``:Document`` nodes (semantic-search fodder).

The txn write path is the required
``agent_utilities.knowledge_graph.memory.native_ingest`` authority. Node ids follow
``egeria:<class>:<guid>``; ``node_type`` on each entity
matches a class federated by ``egeria_mcp.ontology`` (``egeria.ttl``).
"""

from __future__ import annotations

import logging
from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_documents as _native_ingest_documents,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)

logger = logging.getLogger("egeria_mcp.kg")

_SOURCE = "egeria-mcp"
_DOMAIN = "egeria"


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships through native ingestion."""
    return _native_ingest_entities(
        entities,
        relationships,
        source=_SOURCE,
        domain=_DOMAIN,
        client=client,
        graph=graph,
    )


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write text records as ``:Document`` nodes (semantic-search fodder).

    Each doc: ``{"id":..., "text":..., "title"?:..., "source_uri"?:..., ...props}``.
    Validation and engine failures are surfaced as ``NativeIngestError``.
    """
    return _native_ingest_documents(
        documents,
        source=_SOURCE,
        domain=_DOMAIN,
        client=client,
        graph=graph,
    )


# ── record → entity/document mappers ─────────────────────────────────────────
def _asset_id(guid: str | None) -> str | None:
    return f"egeria:DataAsset:{guid}" if guid else None


def map_glossary_terms(
    terms: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Egeria glossary-term records → ``:GlossaryTerm`` entities + definition docs."""
    entities: list[dict[str, Any]] = []
    docs: list[dict[str, Any]] = []
    for t in terms or []:
        guid = t.get("guid")
        if not guid:
            continue
        nid = f"egeria:GlossaryTerm:{guid}"
        name = t.get("displayName") or t.get("qualifiedName")
        summary = t.get("summary") or t.get("description")
        entities.append(
            {
                "id": nid,
                "node_type": "GlossaryTerm",
                "name": name,
                "qualifiedName": t.get("qualifiedName"),
                "summary": summary,
                "externalToolId": str(guid),
            }
        )
        if summary:
            docs.append(
                {
                    "id": f"{nid}:def",
                    "text": f"{name}: {summary}" if name else summary,
                    "title": name,
                    "doc_type": "glossary_term",
                    "externalToolId": str(guid),
                }
            )
    return entities, docs


def map_glossary_categories(
    categories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Egeria glossary-category records → ``:GlossaryCategory`` entities."""
    out: list[dict[str, Any]] = []
    for c in categories or []:
        guid = c.get("guid")
        if not guid:
            continue
        out.append(
            {
                "id": f"egeria:GlossaryCategory:{guid}",
                "node_type": "GlossaryCategory",
                "name": c.get("displayName") or c.get("qualifiedName"),
                "qualifiedName": c.get("qualifiedName"),
                "summary": c.get("summary"),
                "externalToolId": str(guid),
            }
        )
    return out


def map_governance(
    definitions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Egeria governance-definition records → ``:GovernanceRule`` entities + docs."""
    entities: list[dict[str, Any]] = []
    docs: list[dict[str, Any]] = []
    for d in definitions or []:
        guid = d.get("guid")
        if not guid:
            continue
        nid = f"egeria:GovernanceRule:{guid}"
        name = d.get("displayName") or d.get("qualifiedName")
        summary = d.get("summary") or d.get("description")
        entities.append(
            {
                "id": nid,
                "node_type": "GovernanceRule",
                "name": name,
                "qualifiedName": d.get("qualifiedName"),
                "summary": summary,
                "typeName": d.get("typeName"),
                "domain": d.get("domainIdentifier") or d.get("domain"),
                "externalToolId": str(guid),
            }
        )
        if summary:
            docs.append(
                {
                    "id": f"{nid}:def",
                    "text": f"{name}: {summary}" if name else summary,
                    "title": name,
                    "doc_type": "governance_rule",
                    "externalToolId": str(guid),
                }
            )
    return entities, docs


def map_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Egeria asset records → ``:DataAsset`` entities."""
    out: list[dict[str, Any]] = []
    for a in assets or []:
        guid = a.get("guid")
        if not guid:
            continue
        out.append(
            {
                "id": _asset_id(guid),
                "node_type": "DataAsset",
                "name": a.get("displayName") or a.get("qualifiedName"),
                "qualifiedName": a.get("qualifiedName"),
                "typeName": a.get("typeName"),
                "summary": a.get("summary"),
                "confidentialityLevel": a.get("confidentialityLevel"),
                "externalToolId": str(guid),
            }
        )
    return out


def map_lineage(
    flows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Egeria DataFlow edge records → lightweight ``:DataAsset`` endpoints + ``:flowsTo`` edges.

    Each flow: ``{source, target, label, sourceName, targetName, sourceType, targetType}``
    with GUIDs in ``source``/``target`` (see ``EgeriaApi.list_data_flows``).
    """
    endpoints: dict[str, dict[str, Any]] = {}
    rels: list[dict[str, Any]] = []
    for f in flows or []:
        s_guid, t_guid = f.get("source"), f.get("target")
        if not s_guid or not t_guid:
            continue
        s_id, t_id = _asset_id(s_guid), _asset_id(t_guid)
        endpoints.setdefault(
            s_id,
            {
                "id": s_id,
                "node_type": "DataAsset",
                "name": f.get("sourceName"),
                "typeName": f.get("sourceType"),
                "externalToolId": str(s_guid),
            },
        )
        endpoints.setdefault(
            t_id,
            {
                "id": t_id,
                "node_type": "DataAsset",
                "name": f.get("targetName"),
                "typeName": f.get("targetType"),
                "externalToolId": str(t_guid),
            },
        )
        rels.append({"source": s_id, "target": t_id, "relationship": "flowsTo"})
    return list(endpoints.values()), rels


# ── high-level ingest entry points (Wire-First + default-on) ─────────────────
def ingest_catalog(
    api: Any,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """List the Egeria catalog via ``api`` and push it into the KG (typed + docs + lineage).

    Pulls glossary terms/categories, governance definitions, assets, and DataFlow
    lineage edges, maps them to OWL nodes/edges/documents, and writes them. Every
    Individual source reads may degrade to ``[]``; native write failures propagate.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    def _safe(fn: Any) -> list[dict[str, Any]]:
        try:
            return fn() or []
        except Exception as e:  # noqa: BLE001 — one source empty must not abort
            logger.debug(
                "KG ingest source failed: error_type=%s", type(e).__name__
            )
            return []

    term_ents, term_docs = map_glossary_terms(_safe(api.list_glossary_terms))
    entities += term_ents
    documents += term_docs
    entities += map_glossary_categories(_safe(api.list_glossary_categories))
    gov_ents, gov_docs = map_governance(_safe(api.list_governance_definitions))
    entities += gov_ents
    documents += gov_docs
    entities += map_assets(_safe(api.list_assets))
    flow_ents, flow_rels = map_lineage(_safe(api.list_data_flows))
    entities += flow_ents
    relationships += flow_rels

    node_res = ingest_entities(entities, relationships, client=client, graph=graph)
    doc_res = (
        ingest_documents(documents, client=client, graph=graph)
        if documents
        else {"nodes": 0}
    )
    return {
        "nodes": node_res["nodes"],
        "edges": node_res["edges"],
        "documents": doc_res["nodes"],
    }
