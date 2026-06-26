"""Collaboration harvest — the Mattermost layer.

Reads teams live from Mattermost and catalogs each as an Egeria ``Collection`` — the
collaboration estate joins the catalog (and reconciles with identity/governance).
Idempotent.

Config-driven (``MATTERMOST_URL`` + ``MATTERMOST_TOKEN`` bearer); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_teams(url: str, token: str, *, verify_ssl: bool = False) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/v4/teams",
                headers={"Authorization": f"Bearer {token}"},
                params={"per_page": 200},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def harvest_chat(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Mattermost teams into Egeria as Collections."""
    report: dict[str, Any] = {"teams": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("MATTERMOST_URL")
    token = token or setting("MATTERMOST_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no Mattermost URL/token (set MATTERMOST_URL / MATTERMOST_TOKEN)"
        )
        return report

    teams = fetch_teams(url, token, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "teams": len(teams)}
    if not teams:
        report["skipped"] = "no teams returned (unreachable or unauthorized)"
        return report

    for t in teams:
        name = t.get("display_name") or t.get("name")
        if not name:
            continue
        res = api.create_collection(
            f"Mattermost: {name}",
            description=f"Mattermost team '{name}'.",
            category="MattermostTeam",
        )
        record_error(f"team:{name}", res)
        report["teams"].append({"name": name, **res})

    report["summary"] = {
        "teams": len([t for t in report["teams"] if t.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
