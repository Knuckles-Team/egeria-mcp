"""Productivity harvest — the Microsoft 365 layer.

Reads SharePoint sites and Teams/groups live from Microsoft Graph and catalogs each
as an Egeria ``Collection`` — the M365 collaboration estate joins the catalog.
Idempotent.

Config-driven (``MSGRAPH_TOKEN`` bearer, optional ``MSGRAPH_URL`` default
``https://graph.microsoft.com/v1.0``); tolerant.
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
    base: str, token: str, path: str, params, tls_profile: ResolvedTLSProfile | None
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(
                f"{base.rstrip('/')}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("value") or []
    except Exception:
        return []


def harvest_m365(
    api: Any,
    token: str | None = None,
    *,
    base_url: str | None = None,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog M365 SharePoint sites + groups into Egeria as Collections."""
    report: dict[str, Any] = {"sites": [], "groups": [], "errors": []}

    token = token or setting("MSGRAPH_TOKEN") or setting("MS_GRAPH_TOKEN")
    base = base_url or setting("MSGRAPH_URL") or "https://graph.microsoft.com/v1.0"
    if not token:
        report["skipped"] = "no Microsoft Graph token (set MSGRAPH_TOKEN)"
        return report

    sites = _get(base, token, "/sites", {"search": "*", "$top": 100}, tls_profile)
    groups = _get(
        base,
        token,
        "/groups",
        {"$top": 100, "$select": "displayName,id,visibility"},
        tls_profile,
    )
    report["source"] = {"sites": len(sites), "groups": len(groups)}
    if not sites and not groups:
        report["skipped"] = "no sites/groups returned (unreachable or unauthorized)"
        return report

    for s in sites:
        name = s.get("displayName") or s.get("name")
        if not name:
            continue
        res = api.create_collection(
            f"SharePoint: {name}",
            description=f"SharePoint site '{name}'.",
            category="SharePointSite",
        )
        note_error(report, f"site:{name}", res)
        report["sites"].append({"name": name, **res})
    for g in groups:
        name = g.get("displayName")
        if not name:
            continue
        res = api.create_collection(
            f"M365 Group: {name}",
            description=f"Microsoft 365 group/team '{name}'.",
            category="M365Group",
        )
        note_error(report, f"group:{name}", res)
        report["groups"].append({"name": name, **res})

    report["summary"] = {
        "sites": count_created(report["sites"]),
        "groups": count_created(report["groups"]),
        "errors": len(report["errors"]),
    }
    return report
