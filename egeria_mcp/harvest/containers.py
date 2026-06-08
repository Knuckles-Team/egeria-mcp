"""Infrastructure harvest — the container/Portainer layer.

Reads the running Docker Swarm estate via the Portainer API and catalogs swarm
**nodes** as Egeria ``SoftwareServer`` hosts and **services** as
``DeployedSoftwareComponent`` assets — the substrate every other harvest layer runs
on, reconciled with the data-store layer by hostname. Idempotent (by
``qualifiedName``).

Config-driven (``PORTAINER_URL`` + ``PORTAINER_API_KEY``, optional
``PORTAINER_ENDPOINT_ID``, default ``3``); tolerant — skipped (reported, not raised)
when unconfigured/unreachable.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _resolve(
    base_url: str | None, api_key: str | None
) -> tuple[str | None, str | None]:
    return (
        base_url or os.getenv("PORTAINER_URL"),
        api_key or os.getenv("PORTAINER_API_KEY") or os.getenv("PORTAINER_TOKEN"),
    )


def _get(base_url: str, api_key: str, path: str, verify_ssl: bool) -> Any:
    if not HTTPX_AVAILABLE:
        return None
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(f"{base_url.rstrip('/')}{path}", headers={"X-API-Key": api_key})
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def harvest_containers(
    api: Any,
    base_url: str | None = None,
    api_key: str | None = None,
    *,
    endpoint_id: str | int | None = None,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog the Docker Swarm estate (nodes + services) into Egeria."""
    report: dict[str, Any] = {"nodes": [], "services": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url, api_key = _resolve(base_url, api_key)
    if not base_url or not api_key:
        report["skipped"] = (
            "no Portainer URL/key (set PORTAINER_URL / PORTAINER_API_KEY)"
        )
        return report

    eid = endpoint_id or os.getenv("PORTAINER_ENDPOINT_ID", "3")
    nodes = (
        _get(base_url, api_key, f"/api/endpoints/{eid}/docker/nodes", verify_ssl) or []
    )
    services = (
        _get(base_url, api_key, f"/api/endpoints/{eid}/docker/services", verify_ssl)
        or []
    )
    report["source"] = {
        "base_url": base_url,
        "endpoint": eid,
        "nodes": len(nodes),
        "services": len(services),
    }
    if not nodes and not services:
        report["skipped"] = "no swarm data returned (unreachable or unauthorized)"
        return report

    for n in nodes:
        host = (n.get("Description") or {}).get("Hostname")
        if not host:
            continue
        res = api.create_asset(
            "SoftwareServer",
            f"Node::{host}",
            host,
            description=f"Docker Swarm node '{host}'.",
            deployed_implementation_type="Docker Swarm Node",
            confidentiality_level=1,
            additional_properties={
                "role": (n.get("Spec") or {}).get("Role"),
                "availability": (n.get("Spec") or {}).get("Availability"),
                "state": (n.get("Status") or {}).get("State"),
                "addr": (n.get("Status") or {}).get("Addr"),
                "source": "Portainer",
            },
        )
        record_error(f"node:{host}", res)
        report["nodes"].append({"host": host, **res})

    for s in services:
        name = (s.get("Spec") or {}).get("Name")
        if not name:
            continue
        image = (
            ((s.get("Spec") or {}).get("TaskTemplate") or {}).get("ContainerSpec") or {}
        ).get("Image")
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"Service::{name}",
            name,
            description=f"Swarm service '{name}'.",
            deployed_implementation_type="Docker Swarm Service",
            confidentiality_level=1,
            additional_properties={
                "image": (image or "").split("@")[0],
                "source": "Portainer",
            },
        )
        record_error(f"service:{name}", res)
        report["services"].append({"name": name, **res})

    report["summary"] = {
        "nodes": len([n for n in report["nodes"] if n.get("guid")]),
        "services": len([s for s in report["services"] if s.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
