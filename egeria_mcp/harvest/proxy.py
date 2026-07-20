"""Ingress harvest — the Caddy layer.

Reads the live Caddy reverse-proxy config (admin API) and catalogs each routed host
as an Egeria ``DeployedSoftwareComponent`` (an exposed service endpoint) with its
upstream — the ingress topology joins the catalog. Idempotent.

Config-driven (``CADDY_ADMIN_URL``, default ``http://localhost:2019``); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_tls_profile,
)

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_routes(
    admin_url: str, *, tls_profile: ResolvedTLSProfile | None = None
) -> list[dict]:
    """Return [{host, upstream}] from Caddy's http servers config."""
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(timeout=15.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(f"{admin_url.rstrip('/')}/config/apps/http/servers")
        if r.status_code != 200:
            return []
        servers = r.json() or {}
    except Exception:
        return []
    out: list[dict] = []
    for srv in (servers or {}).values():
        for route in (srv or {}).get("routes", []) or []:
            hosts: list[str] = []
            for m in route.get("match", []) or []:
                hosts.extend(m.get("host", []) or [])
            upstream = ""
            for h in route.get("handle", []) or []:
                ups = h.get("upstreams") or []
                if ups:
                    upstream = ups[0].get("dial", "")
                    break
            for host in hosts:
                out.append({"host": host, "upstream": upstream})
    return out


def harvest_proxy(
    api: Any,
    admin_url: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Caddy routed hosts into Egeria as exposed-service endpoints."""
    report: dict[str, Any] = {"routes": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    admin_url = admin_url or setting("CADDY_ADMIN_URL") or "http://localhost:2019"
    routes = fetch_routes(admin_url, tls_profile=tls_profile)
    report["source"] = {"admin_url": admin_url, "routes": len(routes)}
    if not routes:
        report["skipped"] = "no routes (Caddy admin unreachable; set CADDY_ADMIN_URL)"
        return report

    for rt in routes:
        host = rt["host"]
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"Route::{host}",
            host,
            description=f"Caddy ingress route '{host}' → {rt.get('upstream') or '?'}.",
            deployed_implementation_type="HTTP Route",
            confidentiality_level=1,
            additional_properties={"upstream": rt.get("upstream"), "source": "Caddy"},
        )
        record_error(f"route:{host}", res)
        report["routes"].append({"host": host, **res})

    report["summary"] = {
        "routes": len([r for r in report["routes"] if r.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
