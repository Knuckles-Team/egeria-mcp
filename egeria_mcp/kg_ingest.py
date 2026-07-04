"""Native epistemic-graph ingestion for Egeria open-metadata records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The record-source twin of the
gitlab/media connectors: egeria-mcp natively pushes Egeria's metadata /
governance / lineage system-of-record into the ONE epistemic-graph engine as
**typed OWL nodes** (``:GlossaryTerm``, ``:GovernanceRule``, ``:DataAsset``,
``:GlossaryCategory``) plus ``:flowsTo`` / ``:dependsOn`` **lineage edges**, and
the term/policy definition text as ``:Document`` nodes (semantic-search fodder).

The txn write path is the shared primitive
``agent_utilities.knowledge_graph.memory.native_ingest`` when it is importable;
otherwise a self-contained, engine-guarded fallback (the primitive is not yet in
the installed ``agent_utilities`` on every host). Either way everything is
dependency-/engine-guarded: with no KG stack or no reachable engine every entry
point **no-ops** (returns ``None``), so the connector runs with zero KG
infrastructure. Node ids follow ``egeria:<class>:<guid>``; ``type`` on each entity
matches a class federated by ``egeria_mcp.ontology`` (``egeria.ttl``).
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("egeria_mcp.kg")

_SOURCE = "egeria-mcp"
_DOMAIN = "egeria"
_DEFAULT_GRAPH = "__commons__"


# ── engine client resolution + self-contained txn fallback ───────────────────
def _client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` when unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or _DEFAULT_GRAPH)
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def _fallback_write(
    client: Any,
    graph: str,
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
) -> dict[str, int] | None:
    """Self-contained txn write (used when the shared primitive is unavailable)."""
    nodes = [n for n in nodes if n.get("id")]
    if not nodes:
        return None
    try:
        txn = client.txn.begin(graph=graph)
        for node in nodes:
            props = {k: v for k, v in node.items() if k != "id" and v is not None}
            props.setdefault("source", _SOURCE)
            props.setdefault("domain", _DOMAIN)
            client.txn.add_node(txn, node["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest: wrote %d nodes, %d edges", len(nodes), edges)
    return {"nodes": len(nodes), "edges": edges}


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed OWL nodes (+ edges) into epistemic-graph.

    ``entities``: ``[{"id":..., "type":<owl:Class>, ...props}]``.
    ``relationships``: ``[{"source":id, "target":id, "type":<link>}]``.
    Prefers the shared ``native_ingest`` primitive; falls back to a local txn.
    Returns ``{"nodes":n, "edges":m}`` or ``None`` (never raises).
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None
    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_entities as _shared,
            )

            return _shared(entities, relationships, source=_SOURCE, domain=_DOMAIN)
        except Exception as e:  # noqa: BLE001 — primitive absent → local fallback
            logger.debug("KG ingest: shared primitive unavailable: %s", e)
        client, graph = _client()
    if client is None:
        return None
    return _fallback_write(client, graph or _DEFAULT_GRAPH, entities, relationships)


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write text records as ``:Document`` nodes (semantic-search fodder).

    Each doc: ``{"id":..., "text":..., "title"?:..., "source_uri"?:..., ...props}``.
    Prefers the shared ``native_ingest`` primitive; falls back to a local txn.
    Returns ``{"nodes":n, "edges":0}`` or ``None``.
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nodes: list[dict[str, Any]] = []
    for doc in documents or []:
        did = doc.get("id")
        text = doc.get("text") or doc.get("content")
        if not did or not text:
            continue
        node = {k: v for k, v in doc.items() if k != "content" and v is not None}
        node["id"] = did
        node["type"] = "Document"
        node["text"] = text
        node.setdefault("created_at", now)
        nodes.append(node)
    if not nodes:
        return None
    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_documents as _shared,
            )

            return _shared(documents, source=_SOURCE, domain=_DOMAIN)
        except Exception as e:  # noqa: BLE001 — primitive absent → local fallback
            logger.debug("KG ingest: shared primitive unavailable: %s", e)
        client, graph = _client()
    if client is None:
        return None
    return _fallback_write(client, graph or _DEFAULT_GRAPH, nodes, None)


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
                "type": "GlossaryTerm",
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
                "type": "GlossaryCategory",
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
                "type": "GovernanceRule",
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
                "type": "DataAsset",
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
                "type": "DataAsset",
                "name": f.get("sourceName"),
                "typeName": f.get("sourceType"),
                "externalToolId": str(s_guid),
            },
        )
        endpoints.setdefault(
            t_id,
            {
                "id": t_id,
                "type": "DataAsset",
                "name": f.get("targetName"),
                "typeName": f.get("targetType"),
                "externalToolId": str(t_guid),
            },
        )
        rels.append({"source": s_id, "target": t_id, "type": "flowsTo"})
    return list(endpoints.values()), rels


# ── high-level ingest entry points (Wire-First + default-on) ─────────────────
def ingest_catalog(
    api: Any,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """List the Egeria catalog via ``api`` and push it into the KG (typed + docs + lineage).

    Pulls glossary terms/categories, governance definitions, assets, and DataFlow
    lineage edges, maps them to OWL nodes/edges/documents, and writes them. Every
    ``api`` call is best-effort (degrades to ``[]``). Returns aggregate
    ``{"nodes":n, "edges":m, "documents":d}`` or ``None`` when nothing was written.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    def _safe(fn: Any) -> list[dict[str, Any]]:
        try:
            return fn() or []
        except Exception as e:  # noqa: BLE001 — one source empty must not abort
            logger.debug(
                "KG ingest: source failed (%s): %s", getattr(fn, "__name__", fn), e
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
    doc_res = ingest_documents(documents, client=client, graph=graph)
    if node_res is None and doc_res is None:
        return None
    return {
        "nodes": (node_res or {}).get("nodes", 0),
        "edges": (node_res or {}).get("edges", 0),
        "documents": (doc_res or {}).get("nodes", 0),
    }
