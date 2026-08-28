"""Data-store harvest — the substrate (anchor) layer of the bottom-up federation.

Catalogs the declared data estate (:mod:`egeria_mcp.harvest.topology`) into Egeria:
the business-glossary backbone, the data-store servers + their databases (with
``Confidentiality`` classifications), and the ``DataFlow`` lineage between them.
Idempotent — re-running reconciles by ``qualifiedName`` rather than duplicating.

Result of this layer: ``governed_route`` returns real ``require_approval`` /
``review`` decisions for the catalogued stores, and the KG ``egeria`` extractor has
authoritative ``:Concept`` / ``:DataConnector`` / lineage to federate.
"""

from __future__ import annotations

from typing import Any

from egeria_mcp.harvest import topology
from egeria_mcp.harvest._reporting import note_error


def _catalog_glossary_terms(
    api: Any, estate: dict[str, Any], report: dict[str, Any]
) -> str | None:
    """Create the glossary backbone + its terms; return the glossary guid."""
    glossary = estate["glossary"]
    g = api.create_glossary(glossary["name"], glossary["description"])
    note_error(report, "glossary", g)
    glossary_guid = g.get("guid")
    report["glossary"] = {"name": glossary["name"], **g}

    if glossary_guid:
        for term in estate["terms"]:
            res = api.create_term(
                glossary_guid,
                term["name"],
                term.get("summary", ""),
                description=term.get("description", ""),
            )
            note_error(report, f"term:{term['name']}", res)
            report["terms"].append({"name": term["name"], **res})
    return glossary_guid


def _catalog_stores_and_datasets(
    api: Any, estate: dict[str, Any], report: dict[str, Any]
) -> dict[str, str]:
    """Catalog data-store servers + their datasets; return {key: guid}."""
    key_to_guid: dict[str, str] = {}

    for store in estate["stores"]:
        qn = f"DataStore::{store['name']}"
        res = api.create_asset(
            store["type_name"],
            qn,
            store["name"],
            description=store.get("description", ""),
            deployed_implementation_type=store.get("deployed_implementation_type", ""),
            confidentiality_level=store.get("confidentiality_level"),
            additional_properties=store.get("extended"),
        )
        note_error(report, f"store:{store['name']}", res)
        if res.get("guid"):
            key_to_guid[store["key"]] = res["guid"]
        report["stores"].append({"name": store["name"], "qualifiedName": qn, **res})

    for ds in estate["datasets"]:
        qn = f"Dataset::{ds['parent']}::{ds['name']}"
        res = api.create_asset(
            ds["type_name"],
            qn,
            ds["name"],
            description=ds.get("description", ""),
            deployed_implementation_type=ds.get("deployed_implementation_type", ""),
            confidentiality_level=ds.get("confidentiality_level"),
        )
        note_error(report, f"dataset:{ds['name']}", res)
        if res.get("guid"):
            key_to_guid[ds["key"]] = res["guid"]
        report["datasets"].append({"name": ds["name"], "qualifiedName": qn, **res})

    return key_to_guid


def _catalog_flows(
    api: Any,
    estate: dict[str, Any],
    key_to_guid: dict[str, str],
    report: dict[str, Any],
) -> None:
    """Catalog declared DataFlow lineage edges between cataloged assets."""
    for flow in estate["flows"]:
        src = key_to_guid.get(flow["source"])
        tgt = key_to_guid.get(flow["target"])
        if not src or not tgt:
            report["errors"].append(
                {
                    "item": f"flow:{flow['source']}->{flow['target']}",
                    "error": "unresolved endpoint",
                }
            )
            continue
        res = api.link_data_flow(
            src,
            tgt,
            label=flow.get("label", ""),
            description=flow.get("description", ""),
        )
        note_error(report, f"flow:{flow['source']}->{flow['target']}", res)
        report["flows"].append(
            {"source": flow["source"], "target": flow["target"], **res}
        )


def harvest_datastores(api: Any) -> dict[str, Any]:
    """Catalog the declared data-store estate into Egeria; return a report.

    CONCEPT:EA-KG.domains.bottom-up-harvest-data — Bottom-Up Harvest. The data-store layer is the anchor every
    downstream lineage edge (ERPNext → Camunda → GitLab) resolves to.

    Parameters
    ----------
    api:
        A write-enabled ``EgeriaApi`` (``enable_write=True``).

    Returns
    -------
    dict with per-category results: the glossary GUID, created/reused term and
    asset GUIDs, lineage edge results, and any errors collected (never raises on a
    single-item failure — it records and continues).
    """
    report: dict[str, Any] = {
        "glossary": None,
        "terms": [],
        "stores": [],
        "datasets": [],
        "flows": [],
        "errors": [],
    }
    # Topology: the generic built-in example, or an EGERIA_HARVEST_TOPOLOGY override.
    estate = topology.load_topology()

    # 1) glossary backbone ────────────────────────────────────────────────────
    _catalog_glossary_terms(api, estate, report)

    # 2) data-store servers + their datasets (assets w/ confidentiality) ───────
    key_to_guid = _catalog_stores_and_datasets(api, estate, report)

    # 3) lineage (DataFlow edges between catalogued assets) ────────────────────
    _catalog_flows(api, estate, key_to_guid, report)

    report["summary"] = {
        "terms": len(report["terms"]),
        "stores": len(report["stores"]),
        "datasets": len(report["datasets"]),
        "flows": len([f for f in report["flows"] if not f.get("error")]),
        "errors": len(report["errors"]),
    }
    return report
