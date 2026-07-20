"""Observability harvest — the Grafana / LGTM layer.

Reads data sources and dashboards live from Grafana and catalogs data sources as
Egeria ``DeployedSoftwareComponent`` assets (they are upstream lineage endpoints) and
dashboards as ``Collection``s. Idempotent.

Config-driven (``GRAFANA_URL`` + ``LGTM_TOKEN`` / ``GRAFANA_TOKEN`` bearer); tolerant.
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


def _get(url: str, token: str, path: str, params, tls_profile: ResolvedTLSProfile | None) -> Any:
    if not HTTPX_AVAILABLE:
        return None
    try:
        with httpx.Client(timeout=20.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(
                f"{url.rstrip('/')}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
            )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def harvest_observability(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Grafana data sources + dashboards into Egeria."""
    report: dict[str, Any] = {"datasources": [], "dashboards": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("GRAFANA_URL")
    token = token or setting("LGTM_TOKEN") or setting("GRAFANA_TOKEN")
    if not url or not token:
        report["skipped"] = "no Grafana URL/token (set GRAFANA_URL / LGTM_TOKEN)"
        return report

    datasources = _get(url, token, "/api/datasources", None, tls_profile) or []
    dashboards = (
        _get(url, token, "/api/search", {"type": "dash-db", "limit": 200}, tls_profile)
        or []
    )
    report["source"] = {
        "url": url,
        "datasources": len(datasources),
        "dashboards": len(dashboards),
    }
    if not datasources and not dashboards:
        report["skipped"] = (
            "no datasources/dashboards returned (unreachable or unauthorized)"
        )
        return report

    for ds in datasources:
        name = ds.get("name")
        if not name:
            continue
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"Datasource::Grafana::{name}",
            name,
            description=f"Grafana data source '{name}' ({ds.get('type')}).",
            deployed_implementation_type=ds.get("type") or "Grafana Datasource",
            confidentiality_level=1,
            additional_properties={"dsType": ds.get("type"), "source": "Grafana"},
        )
        record_error(f"datasource:{name}", res)
        report["datasources"].append({"name": name, **res})
    for db in dashboards:
        title = db.get("title")
        if not title:
            continue
        res = api.create_collection(
            f"Dashboard: {title}",
            description=f"Grafana dashboard '{title}'.",
            category="GrafanaDashboard",
        )
        record_error(f"dashboard:{title}", res)
        report["dashboards"].append({"title": title, **res})

    report["summary"] = {
        "datasources": len([d for d in report["datasources"] if d.get("guid")]),
        "dashboards": len([d for d in report["dashboards"] if d.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
