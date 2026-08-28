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

from egeria_mcp.harvest._reporting import count_created, note_error

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _route_hosts(route: dict) -> list[str]:
    """Every matched hostname for one Caddy route (across its ``match`` blocks)."""
    hosts: list[str] = []
    for m in route.get("match", []) or []:
        hosts.extend(m.get("host", []) or [])
    return hosts


def _route_upstream(route: dict) -> str:
    """The first upstream dial address handling one Caddy route, if any."""
    for h in route.get("handle", []) or []:
        upstreams = h.get("upstreams") or []
        if upstreams:
            return upstreams[0].get("dial", "")
    return ""


def _server_routes(server: dict) -> list[dict]:
    """[{host, upstream}] for every route on one Caddy http server."""
    upstream_by_route = [
        (_route_hosts(route), _route_upstream(route))
        for route in (server or {}).get("routes", []) or []
    ]
    return [
        {"host": host, "upstream": upstream}
        for hosts, upstream in upstream_by_route
        for host in hosts
    ]


def _fetch_server_configs(
    admin_url: str, tls_profile: ResolvedTLSProfile | None
) -> dict:
    """Fetch Caddy's ``apps.http.servers`` config (``{}`` on any failure)."""
    if not HTTPX_AVAILABLE:
        return {}
    try:
        with httpx.Client(
            timeout=15.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(f"{admin_url.rstrip('/')}/config/apps/http/servers")
        return r.json() or {} if r.status_code == 200 else {}
    except Exception:
        return {}


def fetch_routes(
    admin_url: str, *, tls_profile: ResolvedTLSProfile | None = None
) -> list[dict]:
    """Return [{host, upstream}] from Caddy's http servers config."""
    servers = _fetch_server_configs(admin_url, tls_profile)
    out: list[dict] = []
    for srv in (servers or {}).values():
        out.extend(_server_routes(srv))
    return out


def harvest_proxy(
    api: Any,
    admin_url: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Caddy routed hosts into Egeria as exposed-service endpoints."""
    report: dict[str, Any] = {"routes": [], "errors": []}

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
        note_error(report, f"route:{host}", res)
        report["routes"].append({"host": host, **res})

    report["summary"] = {
        "routes": count_created(report["routes"]),
        "errors": len(report["errors"]),
    }
    return report
