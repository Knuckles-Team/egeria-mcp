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

from egeria_mcp.harvest._reporting import count_created, note_error

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _get(
    url: str, token: str, path: str, params, tls_profile: ResolvedTLSProfile | None
) -> Any:
    if not HTTPX_AVAILABLE:
        return None
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(
                f"{url.rstrip('/')}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
            )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _catalog_datasources(api: Any, datasources: list[dict], report: dict[str, Any]) -> None:
    """Catalog Grafana data sources as ``DeployedSoftwareComponent`` assets."""
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
        note_error(report, f"datasource:{name}", res)
        report["datasources"].append({"name": name, **res})


def _catalog_dashboards(api: Any, dashboards: list[dict], report: dict[str, Any]) -> None:
    """Catalog Grafana dashboards as Egeria Collections."""
    for db in dashboards:
        title = db.get("title")
        if not title:
            continue
        res = api.create_collection(
            f"Dashboard: {title}",
            description=f"Grafana dashboard '{title}'.",
            category="GrafanaDashboard",
        )
        note_error(report, f"dashboard:{title}", res)
        report["dashboards"].append({"title": title, **res})


def _fetch_datasources_and_dashboards(
    url: str, token: str, tls_profile: ResolvedTLSProfile | None
) -> tuple[list[dict], list[dict]]:
    """Fetch Grafana data sources + dashboards (``[]`` for either on failure)."""
    datasources = _get(url, token, "/api/datasources", None, tls_profile) or []
    dashboards = (
        _get(url, token, "/api/search", {"type": "dash-db", "limit": 200}, tls_profile)
        or []
    )
    return datasources, dashboards


def harvest_observability(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Grafana data sources + dashboards into Egeria."""
    report: dict[str, Any] = {"datasources": [], "dashboards": [], "errors": []}

    url = url or setting("GRAFANA_URL")
    token = token or setting("LGTM_TOKEN") or setting("GRAFANA_TOKEN")
    if not url or not token:
        report["skipped"] = "no Grafana URL/token (set GRAFANA_URL / LGTM_TOKEN)"
        return report

    datasources, dashboards = _fetch_datasources_and_dashboards(url, token, tls_profile)
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

    _catalog_datasources(api, datasources, report)
    _catalog_dashboards(api, dashboards, report)

    report["summary"] = {
        "datasources": count_created(report["datasources"]),
        "dashboards": count_created(report["dashboards"]),
        "errors": len(report["errors"]),
    }
    return report
