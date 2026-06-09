"""Productivity harvest — the Microsoft 365 layer.

Reads SharePoint sites and Teams/groups live from Microsoft Graph and catalogs each
as an Egeria ``Collection`` — the M365 collaboration estate joins the catalog.
Idempotent.

Config-driven (``MSGRAPH_TOKEN`` bearer, optional ``MSGRAPH_URL`` default
``https://graph.microsoft.com/v1.0``); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _get(base: str, token: str, path: str, params, verify_ssl: bool) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
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
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog M365 SharePoint sites + groups into Egeria as Collections."""
    report: dict[str, Any] = {"sites": [], "groups": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    token = token or os.getenv("MSGRAPH_TOKEN") or os.getenv("MS_GRAPH_TOKEN")
    base = base_url or os.getenv("MSGRAPH_URL") or "https://graph.microsoft.com/v1.0"
    if not token:
        report["skipped"] = "no Microsoft Graph token (set MSGRAPH_TOKEN)"
        return report

    sites = _get(base, token, "/sites", {"search": "*", "$top": 100}, verify_ssl)
    groups = _get(
        base,
        token,
        "/groups",
        {"$top": 100, "$select": "displayName,id,visibility"},
        verify_ssl,
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
        record_error(f"site:{name}", res)
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
        record_error(f"group:{name}", res)
        report["groups"].append({"name": name, **res})

    report["summary"] = {
        "sites": len([s for s in report["sites"] if s.get("guid")]),
        "groups": len([g for g in report["groups"] if g.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
