"""Host-inventory harvest — the systems-manager / tunnel-manager layer.

Reads a host inventory file (the same kind tunnel-manager / systems-manager use) and
catalogs each host as an Egeria ``SoftwareServer`` — managed hosts join the catalog,
reconciled with the container/data-store layers by name. Idempotent.

Config-driven (``HOST_INVENTORY`` = path to a YAML or JSON inventory); tolerant.
Accepted shapes: a list of hosts, ``{"hosts": [...]}``, or a name→info mapping. Each
host may carry ``name``/``hostname``, ``address``/``host``/``ansible_host``, ``role``.
"""

from __future__ import annotations

import json
import os
from typing import Any


def _load(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    try:
        import yaml

        return yaml.safe_load(text)
    except Exception:
        return None


def _normalize(data: Any) -> list[dict]:
    if isinstance(data, dict) and isinstance(data.get("hosts"), list):
        data = data["hosts"]
    if isinstance(data, list):
        out = []
        for h in data:
            if isinstance(h, str):
                out.append({"name": h})
            elif isinstance(h, dict):
                out.append(h)
        return out
    if isinstance(data, dict):  # name -> info mapping
        return [
            {"name": k, **(v if isinstance(v, dict) else {})} for k, v in data.items()
        ]
    return []


def harvest_hosts(api: Any, inventory_path: str | None = None) -> dict[str, Any]:
    """Catalog hosts from an inventory file into Egeria as SoftwareServers."""
    report: dict[str, Any] = {"hosts": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    path = inventory_path or os.getenv("HOST_INVENTORY")
    if not path or not os.path.isfile(path):
        report["skipped"] = "no host inventory (set HOST_INVENTORY to a YAML/JSON file)"
        return report

    hosts = _normalize(_load(path))
    report["source"] = {"inventory": path, "hosts": len(hosts)}
    if not hosts:
        report["skipped"] = "no hosts parsed from inventory"
        return report

    for h in hosts:
        name = h.get("name") or h.get("hostname")
        if not name:
            continue
        addr = h.get("address") or h.get("host") or h.get("ansible_host")
        res = api.create_asset(
            "SoftwareServer",
            f"Host::{name}",
            str(name),
            description=f"Managed host '{name}'" + (f" ({addr})." if addr else "."),
            deployed_implementation_type="Host",
            confidentiality_level=1,
            additional_properties={
                "address": addr,
                "role": h.get("role"),
                "source": "inventory",
            },
        )
        record_error(f"host:{name}", res)
        report["hosts"].append({"name": str(name), **res})

    report["summary"] = {
        "hosts": len([h for h in report["hosts"] if h.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
