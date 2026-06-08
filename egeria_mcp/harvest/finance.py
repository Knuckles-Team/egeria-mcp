"""Finance harvest — the Firefly-III layer.

Reads accounts live from a Firefly-III instance and catalogs each as an Egeria data
asset anchored to the Firefly store, classified ``Confidential`` (financial data).
Strengthens governed routing with a real, sensibly-classified data source.
Idempotent (by ``qualifiedName``).

Config-driven (``FIREFLY_URL`` + ``FIREFLY_TOKEN`` personal access token); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _resolve(base_url: str | None, token: str | None):
    return base_url or os.getenv("FIREFLY_URL"), token or os.getenv("FIREFLY_TOKEN")


def fetch_accounts(
    base_url: str, token: str, *, verify_ssl: bool = False, limit: int = 100
) -> list[dict]:
    """Fetch accounts from Firefly-III (v1 API)."""
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{base_url.rstrip('/')}/api/v1/accounts",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                params={"limit": limit},
            )
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("data") or []
    except Exception:
        return []


def harvest_finance(
    api: Any,
    base_url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Firefly-III accounts into Egeria (financial data assets)."""
    report: dict[str, Any] = {"accounts": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url, token = _resolve(base_url, token)
    if not base_url or not token:
        report["skipped"] = "no Firefly URL/token (set FIREFLY_URL / FIREFLY_TOKEN)"
        return report

    accounts = fetch_accounts(base_url, token, verify_ssl=verify_ssl)
    report["source"] = {"base_url": base_url, "accounts": len(accounts)}
    if not accounts:
        report["skipped"] = "no accounts returned (unreachable or unauthorized)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::firefly",
        "firefly-iii",
        description="Firefly-III personal-finance store.",
        deployed_implementation_type="Firefly-III",
        confidentiality_level=2,
    )
    record_error("store:firefly", store)
    store_guid = store.get("guid")

    for acct in accounts:
        attrs = acct.get("attributes") or {}
        name = attrs.get("name")
        if not name:
            continue
        qn = f"Dataset::Firefly::{acct.get('id')}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            name,
            description=f"Firefly-III {attrs.get('type', 'account')} '{name}'.",
            deployed_implementation_type="Firefly Account",
            confidentiality_level=2,  # Confidential — financial
            additional_properties={
                "accountType": attrs.get("type"),
                "currency": attrs.get("currency_code"),
                "source": "Firefly-III",
            },
        )
        record_error(f"account:{name}", res)
        report["accounts"].append({"name": name, "qualifiedName": qn, **res})
        if store_guid and res.get("guid"):
            api.link_data_flow(store_guid, res["guid"], label="hosts")

    report["summary"] = {
        "accounts": len([a for a in report["accounts"] if a.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
