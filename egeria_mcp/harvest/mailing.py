"""Mailing harvest — the Listmonk layer.

Reads mailing lists live from Listmonk and catalogs each as an Egeria data asset
(subscriber lists hold PII → ``Confidential``). Idempotent.

Config-driven (``LISTMONK_URL`` + ``LISTMONK_USER`` + ``LISTMONK_TOKEN``); tolerant.
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


def fetch_lists(
    url: str,
    user: str | None,
    token: str,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    auth = (user, token) if user else None
    headers = {} if user else {"Authorization": f"token {token}"}
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/lists",
                auth=auth,
                headers=headers,
                params={"per_page": 100},
            )
        if r.status_code != 200:
            return []
        return ((r.json() or {}).get("data") or {}).get("results") or []
    except Exception:
        return []


def _catalog_lists(api: Any, lists: list[dict], report: dict[str, Any]) -> None:
    """Catalog Listmonk mailing lists as PII data assets."""
    for lst in lists:
        name = lst.get("name")
        if not name:
            continue
        qn = f"Dataset::Listmonk::{lst.get('id')}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            name,
            description=f"Listmonk mailing list '{name}' ({lst.get('subscriber_count', '?')} subscribers).",
            deployed_implementation_type="Mailing List",
            confidentiality_level=2,  # PII
            additional_properties={
                "type": lst.get("type"),
                "subscriberCount": lst.get("subscriber_count"),
                "source": "Listmonk",
            },
        )
        note_error(report, f"list:{name}", res)
        report["lists"].append({"name": name, **res})


def harvest_mailing(
    api: Any,
    url: str | None = None,
    user: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Listmonk mailing lists into Egeria as PII data assets."""
    report: dict[str, Any] = {"lists": [], "errors": []}

    url = url or setting("LISTMONK_URL")
    user = user or setting("LISTMONK_USER") or setting("OPENAPI_USERNAME")
    token = token or setting("LISTMONK_TOKEN") or setting("OPENAPI_PASSWORD")
    if not url or not token:
        report["skipped"] = "no Listmonk URL/token (set LISTMONK_URL / LISTMONK_TOKEN)"
        return report

    lists = fetch_lists(url, user, token, tls_profile=tls_profile)
    report["source"] = {"url": url, "lists": len(lists)}
    if not lists:
        report["skipped"] = "no lists returned (unreachable or unauthorized)"
        return report

    _catalog_lists(api, lists, report)

    report["summary"] = {
        "lists": count_created(report["lists"]),
        "errors": len(report["errors"]),
    }
    return report
