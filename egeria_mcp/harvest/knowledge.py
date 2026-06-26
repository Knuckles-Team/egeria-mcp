"""Knowledge-base harvest — the Confluence layer.

Reads spaces live from Confluence's REST API and catalogs each as an Egeria
``Collection`` — the knowledge base joins the catalog. Idempotent.

Config-driven (``CONFLUENCE_URL`` / ``ATLASSIAN_AGENT_URL`` + ``CONFLUENCE_USER`` /
``ATLASSIAN_AGENT_USER`` + ``CONFLUENCE_TOKEN`` / ``ATLASSIAN_AGENT_TOKEN``); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _resolve():
    return (
        setting("CONFLUENCE_URL") or setting("ATLASSIAN_AGENT_URL"),
        setting("CONFLUENCE_USER") or setting("ATLASSIAN_AGENT_USER"),
        setting("CONFLUENCE_TOKEN") or setting("ATLASSIAN_AGENT_TOKEN"),
    )


def fetch_spaces(
    url: str, user: str, token: str, *, verify_ssl: bool = False
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/wiki/rest/api/space",
                auth=(user, token),
                headers={"Accept": "application/json"},
                params={"limit": 200},
            )
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("results") or []
    except Exception:
        return []


def harvest_knowledge(
    api: Any,
    url: str | None = None,
    user: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Confluence spaces into Egeria as Collections."""
    report: dict[str, Any] = {"spaces": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    env_url, env_user, env_token = _resolve()
    url, user, token = url or env_url, user or env_user, token or env_token
    if not url or not user or not token:
        report["skipped"] = "no Confluence creds (set CONFLUENCE_URL / USER / TOKEN)"
        return report

    spaces = fetch_spaces(url, user, token, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "spaces": len(spaces)}
    if not spaces:
        report["skipped"] = "no spaces returned (unreachable or unauthorized)"
        return report

    for sp in spaces:
        name = sp.get("name") or sp.get("key")
        if not name:
            continue
        res = api.create_collection(
            f"Confluence: {name}",
            description=f"Confluence space '{name}' ({sp.get('key')}).",
            category="KnowledgeBase",
        )
        record_error(f"space:{name}", res)
        report["spaces"].append({"name": name, "key": sp.get("key"), **res})

    report["summary"] = {
        "spaces": len([s for s in report["spaces"] if s.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
