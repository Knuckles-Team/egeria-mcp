"""Mailing harvest — the Listmonk layer.

Reads mailing lists live from Listmonk and catalogs each as an Egeria data asset
(subscriber lists hold PII → ``Confidential``). Idempotent.

Config-driven (``LISTMONK_URL`` + ``LISTMONK_USER`` + ``LISTMONK_TOKEN``); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_lists(
    url: str, user: str | None, token: str, *, verify_ssl: bool = False
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    auth = (user, token) if user else None
    headers = {} if user else {"Authorization": f"token {token}"}
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
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


def harvest_mailing(
    api: Any,
    url: str | None = None,
    user: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Listmonk mailing lists into Egeria as PII data assets."""
    report: dict[str, Any] = {"lists": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("LISTMONK_URL")
    user = user or os.getenv("LISTMONK_USER") or os.getenv("OPENAPI_USERNAME")
    token = token or os.getenv("LISTMONK_TOKEN") or os.getenv("OPENAPI_PASSWORD")
    if not url or not token:
        report["skipped"] = "no Listmonk URL/token (set LISTMONK_URL / LISTMONK_TOKEN)"
        return report

    lists = fetch_lists(url, user, token, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "lists": len(lists)}
    if not lists:
        report["skipped"] = "no lists returned (unreachable or unauthorized)"
        return report

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
        record_error(f"list:{name}", res)
        report["lists"].append({"name": name, **res})

    report["summary"] = {
        "lists": len([x for x in report["lists"] if x.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
