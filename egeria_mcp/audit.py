"""Completeness audit — find unlinked "island" assets across the catalogue.

After harvesting + reconciliation, this reports which catalogued assets have **no**
lineage connections (islands) — i.e. what cross-linking is still missing — with a
per-layer coverage breakdown. It loads every catalogued asset but only scans the
low-cardinality hubs for edges (every cross-layer edge touches a hub), so it is cheap
relative to its coverage.

Entry point: :func:`audit`.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from egeria_mcp.lineage_scan import (
    ALL_PREFIXES,
    HUB_PREFIXES,
    load_assets,
    scan_lineage_edges,
)
from egeria_mcp.reconcile import _capability_of, _source_of


def _layer(qn: str) -> str:
    if "::" in qn:
        head = qn.split("::", 1)[0]
        return "servicenow" if head == "CI" else head.lower()
    if ":" in qn:
        return qn.split(":", 1)[0].lower()
    return "other"


def audit(
    api: Any, prefixes: list[str] | None = None, *, max_islands: int = 25
) -> dict[str, Any]:
    """Report island (unlinked) assets + per-layer lineage coverage."""
    index = load_assets(api, prefixes or ALL_PREFIXES)
    hub_recs = [
        r
        for r in index.values()
        if any((r.get("qualifiedName") or "").startswith(p) for p in HUB_PREFIXES)
    ]
    edges = scan_lineage_edges(api, hub_recs)
    connected: set[str] = set()
    for e in edges:
        connected.add(e["source"])
        connected.add(e["target"])

    layers: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "linked": 0, "islands": []}
    )
    total_islands = 0
    for g, rec in index.items():
        qn = rec.get("qualifiedName") or g
        lyr = layers[_layer(qn)]
        lyr["total"] += 1
        if g in connected:
            lyr["linked"] += 1
        else:
            total_islands += 1
            if len(lyr["islands"]) < max_islands:
                lyr["islands"].append(qn)

    coverage = {
        name: {
            "total": d["total"],
            "linked": d["linked"],
            "islands": d["total"] - d["linked"],
            "coverage_pct": round(100 * d["linked"] / d["total"], 1)
            if d["total"]
            else 0.0,
            "island_examples": d["islands"],
        }
        for name, d in sorted(layers.items())
    }
    # Per-capability roll-up: vendor breadth + coverage for each canonical capability.
    caps: dict[str, dict] = defaultdict(
        lambda: {"assets": 0, "linked": 0, "vendors": set()}
    )
    for g, rec in index.items():
        cap = _capability_of(rec)
        if not cap:
            continue
        c = caps[cap]
        c["assets"] += 1
        c["vendors"].add(_source_of(rec))
        if g in connected:
            c["linked"] += 1
    by_capability = {
        cap: {
            "assets": d["assets"],
            "linked": d["linked"],
            "vendors": sorted(d["vendors"]),
            "vendor_count": len(d["vendors"]),
            "cross_vendor": len(d["vendors"]) >= 2,
            "cohort": len(d["vendors"]) >= 2,
            "coverage_pct": round(100 * d["linked"] / d["assets"], 1)
            if d["assets"]
            else 0.0,
        }
        for cap, d in sorted(caps.items())
    }

    total = len(index)
    return {
        "summary": {
            "assets": total,
            "edges": len(edges),
            "linked": len(connected & set(index)),
            "islands": total_islands,
            "coverage_pct": round(100 * (total - total_islands) / total, 1)
            if total
            else 0.0,
            "capabilities": len(by_capability),
            "cross_vendor_capabilities": sum(
                1 for c in by_capability.values() if c["cross_vendor"]
            ),
        },
        "by_layer": coverage,
        "by_capability": by_capability,
    }
