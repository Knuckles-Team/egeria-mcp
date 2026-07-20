"""Work-tracking harvest — the Plane / Jira layer.

Reads projects live from Plane and/or Jira and catalogs each as an Egeria
``Project``, so work-tracking projects join the catalog and reconcile with Camunda
``:BusinessProcess`` nodes by key — "the same process across whichever tool" becomes
one query. Whichever source is configured is harvested (both, if both are). Idempotent.

Config-driven:
* Plane — ``PLANE_URL`` + ``PLANE_TOKEN`` (+ ``PLANE_WORKSPACE`` slug)
* Jira  — ``JIRA_URL`` + ``JIRA_USER`` + ``JIRA_TOKEN``
Tolerant — skipped when nothing is configured/reachable.
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


def _plane_projects(tls_profile: ResolvedTLSProfile | None) -> list[dict]:
    url = setting("PLANE_URL")
    token = setting("PLANE_TOKEN")
    workspace = setting("PLANE_WORKSPACE")
    if not (url and token and workspace and HTTPX_AVAILABLE):
        return []
    try:
        with httpx.Client(timeout=20.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/v1/workspaces/{workspace}/projects/",
                headers={"X-API-Key": token, "Accept": "application/json"},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        results = data.get("results") if isinstance(data, dict) else data
        return [
            {
                "source": "Plane",
                "key": p.get("identifier") or p.get("id"),
                "name": p.get("name"),
                "description": p.get("description"),
            }
            for p in (results or [])
        ]
    except Exception:
        return []


def _jira_projects(tls_profile: ResolvedTLSProfile | None) -> list[dict]:
    url = setting("JIRA_URL")
    user = setting("JIRA_USER")
    token = setting("JIRA_TOKEN")
    if not (url and user and token and HTTPX_AVAILABLE):
        return []
    try:
        with httpx.Client(timeout=20.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(
                f"{url.rstrip('/')}/rest/api/3/project/search",
                auth=(user, token),
                headers={"Accept": "application/json"},
                params={"maxResults": 100},
            )
        if r.status_code != 200:
            return []
        return [
            {
                "source": "Jira",
                "key": p.get("key"),
                "name": p.get("name"),
                "description": None,
            }
            for p in (r.json() or {}).get("values", [])
        ]
    except Exception:
        return []


def harvest_projects(
    api: Any, *, tls_profile: ResolvedTLSProfile | None = None
) -> dict[str, Any]:
    """Catalog Plane and/or Jira projects into Egeria as Projects."""
    report: dict[str, Any] = {"projects": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    projects = _plane_projects(tls_profile) + _jira_projects(tls_profile)
    report["source"] = {"projects": len(projects)}
    if not projects:
        report["skipped"] = (
            "no Plane/Jira projects (set PLANE_URL/TOKEN/WORKSPACE or JIRA_URL/USER/TOKEN)"
        )
        return report

    for p in projects:
        name = p.get("name") or p.get("key")
        if not name:
            continue
        res = api.create_project(
            f"{p['source']}: {name}",
            description=p.get("description") or f"{p['source']} project '{name}'.",
        )
        record_error(f"project:{p['source']}/{name}", res)
        report["projects"].append(
            {"source": p["source"], "name": name, "key": p.get("key"), **res}
        )

    report["summary"] = {
        "projects": len([p for p in report["projects"] if p.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
