"""Enterprise-architecture harvest — the ArchiMate layer.

Parses an ArchiMate model (Open Exchange XML, e.g. an Archi export) and catalogs
each element as an Egeria asset mapped by ArchiMate layer — application components,
business processes, technology nodes, and data objects join the catalog as governed
architecture. Idempotent (by ``qualifiedName``).

Config-driven (``ARCHI_MODEL_PATH`` = path to the model XML); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

from agent_utilities.core.config import setting

from egeria_mcp.harvest.xml_security import parse_xml_root

# ArchiMate element type (xsi:type local name) → Egeria asset type.
_LAYER_TYPE = {
    "ApplicationComponent": "DeployedSoftwareComponent",
    "ApplicationService": "DeployedSoftwareComponent",
    "ApplicationFunction": "DeployedSoftwareComponent",
    "SystemSoftware": "DeployedSoftwareComponent",
    "BusinessProcess": "Process",
    "BusinessFunction": "Process",
    "BusinessService": "Process",
    "Node": "SoftwareServer",
    "Device": "SoftwareServer",
    "Artifact": "DeployedDatabaseSchema",
    "DataObject": "DeployedDatabaseSchema",
}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_model(path: str) -> list[dict]:
    """Parse ArchiMate Open Exchange XML → [{id, name, type}]."""
    try:
        root = parse_xml_root(path)
    except Exception:
        return []
    out: list[dict] = []
    xsi_type = "{http://www.w3.org/2001/XMLSchema-instance}type"
    for el in root.iter():
        if _local(el.tag) != "element":
            continue
        etype = (el.get(xsi_type) or el.get("type") or "").rsplit(":", 1)[-1]
        name = None
        for child in el:
            if _local(child.tag) == "name":
                name = (child.text or "").strip()
                break
        name = name or el.get("name")
        if name and etype:
            out.append(
                {
                    "id": el.get("identifier") or el.get("id"),
                    "name": name,
                    "type": etype,
                }
            )
    return out


def harvest_archimate(api: Any, model_path: str | None = None) -> dict[str, Any]:
    """Catalog ArchiMate model elements into Egeria as architecture assets."""
    report: dict[str, Any] = {"elements": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    path = model_path or setting("ARCHI_MODEL_PATH")
    if not path or not os.path.isfile(path):
        report["skipped"] = (
            "no ArchiMate model (set ARCHI_MODEL_PATH to the Open Exchange XML)"
        )
        return report

    elements = parse_model(path)
    report["source"] = {"configured": True, "elements": len(elements)}
    if not elements:
        report["skipped"] = "no elements parsed (not an ArchiMate Open Exchange model?)"
        return report

    for el in elements:
        etype = el["type"]
        asset_type = _LAYER_TYPE.get(etype, "DeployedSoftwareComponent")
        qn = f"ArchiMate::{etype}::{el['name'].replace(' ', '')}"
        res = api.create_asset(
            asset_type,
            qn,
            el["name"],
            description=f"ArchiMate {etype} '{el['name']}'.",
            deployed_implementation_type=f"ArchiMate {etype}",
            confidentiality_level=1,
            additional_properties={
                "archimateType": etype,
                "archimateId": el.get("id"),
                "capability": "enterprise-architecture",
                "source": "ArchiMate",
            },
        )
        record_error(f"element:{el['name']}", res)
        report["elements"].append({"name": el["name"], "type": etype, **res})

    report["summary"] = {
        "elements": len([e for e in report["elements"] if e.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
