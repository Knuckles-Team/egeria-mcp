"""Shared catalog/lineage scanning helpers.

Used by the KG federation (``EgeriaApi.list_data_flows``), the completeness audit
(:mod:`egeria_mcp.audit`), and reconciliation (:mod:`egeria_mcp.reconcile`): paginate
the asset catalogue by ``qualifiedName`` prefix and collect the ``DataFlow`` lineage
edges incident on those assets (directed, with their semantic label).
"""

from __future__ import annotations

import json as _json
from typing import Any

# Low-cardinality "hub" prefixes — every cross-layer edge touches one of these, so
# scanning the hubs captures all edges cheaply (services-as-source are seen via the
# store/node they link to). Used for lineage federation.
HUB_PREFIXES = [
    "Node::",
    "Host::",
    "DataStore::",
    "Dataset::",
    "Route::",
    "Monitor::",
    "CI::ServiceNow::",
    "Client::",
    "Process::",
    "Topic::",
    "Instrument::",
    "Content::",
    "Model::",
    "Repository::",
    "Datasource::",
    "ArchiMate::",
    "FactSheet::",
]
# Everything catalogued (for the completeness audit's island detection).
ALL_PREFIXES = HUB_PREFIXES + [
    "Service::",
    "Snapshot::",
    "SecretEngine::",
    "VaultPolicy::",
]


def paginated_search(api: Any, term: str, *, max_total: int = 2000) -> list[dict]:
    """Page through asset-catalog by-search-string for one (prefix) term."""
    out: list[dict] = []
    try:
        tok = api._bearer()
    except Exception:
        return out
    url = api._omvs("asset-catalog", "assets/in-domain/by-search-string")
    start, page = 0, 100
    while len(out) < max_total:
        try:
            r = api._http().post(
                f"{url}?startFrom={start}&pageSize={page}",
                headers={
                    "Authorization": f"Bearer {tok}",
                    "Content-Type": "application/json",
                },
                content=_json.dumps(
                    {
                        "class": "SearchStringRequestBody",
                        "searchString": term,
                        "ignoreCase": True,
                    }
                ),
            )
        except Exception:
            break
        if r.status_code != 200:
            break
        batch = api._elements(r)
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page:
            break
        start += page
    return out


def load_assets(api: Any, prefixes: list[str]) -> dict[str, dict]:
    """Return ``{guid: record}`` for catalogued assets under any of ``prefixes``."""
    index: dict[str, dict] = {}
    for pre in prefixes:
        for rec in paginated_search(api, pre):
            qn = rec.get("qualifiedName") or ""
            g = rec.get("guid")
            if g and qn.startswith(pre) and g not in index:
                index[g] = rec
    return index


def scan_lineage_edges(api: Any, recs: list[dict]) -> list[dict]:
    """Collect directed ``DataFlow`` edges incident on ``recs``.

    Returns deduped ``[{source, target, label, sourceName, targetName, sourceType,
    targetType}]`` (GUIDs in ``source``/``target``).
    """
    edges: dict[tuple, dict] = {}
    for rec in recs:
        g = rec.get("guid")
        if not g:
            continue
        lin = api.lineage(g) or {}
        for e in lin.get("lineageLinkage") or []:
            rel = e.get("relatedElement") or {}
            rhdr = rel.get("elementHeader") if isinstance(rel, dict) else {}
            other = (
                (rhdr or {}).get("guid") if isinstance(rhdr, dict) else rel.get("guid")
            )
            if not other:
                continue
            other_name = (rel.get("properties") or {}).get("qualifiedName") or (
                rel.get("properties") or {}
            ).get("displayName")
            other_type = ((rhdr or {}).get("type") or {}).get("typeName")
            label = (e.get("relationshipProperties") or {}).get("label") or "flow"
            this_name = rec.get("qualifiedName")
            this_type = rec.get("typeName")
            if e.get("relatedElementAtEnd1"):  # related is end1 (source)
                src, tgt = other, g
                src_n, tgt_n, src_t, tgt_t = (
                    other_name,
                    this_name,
                    other_type,
                    this_type,
                )
            else:
                src, tgt = g, other
                src_n, tgt_n, src_t, tgt_t = (
                    this_name,
                    other_name,
                    this_type,
                    other_type,
                )
            edges.setdefault(
                (src, tgt),
                {
                    "source": src,
                    "target": tgt,
                    "label": label,
                    "sourceName": src_n,
                    "targetName": tgt_n,
                    "sourceType": src_t,
                    "targetType": tgt_t,
                },
            )
    return list(edges.values())


def catalog_lineage_edges(api: Any, *, max_total: int = 2000) -> list[dict]:
    """Convenience: scan the hub prefixes and return all DataFlow edges."""
    return scan_lineage_edges(api, list(load_assets(api, HUB_PREFIXES).values()))
