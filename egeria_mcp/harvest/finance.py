"""Finance harvest — the Firefly-III layer.

Reads accounts live from a Firefly-III instance and catalogs each as an Egeria data
asset anchored to the Firefly store, classified ``Confidential`` (financial data).
Strengthens governed routing with a real, sensibly-classified data source.
Idempotent (by ``qualifiedName``).

Config-driven (``FIREFLY_URL`` + ``FIREFLY_TOKEN`` personal access token); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_connector_sdk.config import setting
from agent_connector_sdk.tls.profile import ResolvedTLSProfile
from agent_connector_sdk.tls.resolve import resolve_tls_profile

from egeria_mcp.harvest._reporting import count_created, note_error

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _resolve(base_url: str | None, token: str | None):
    return base_url or setting("FIREFLY_URL"), token or setting("FIREFLY_TOKEN")


def fetch_accounts(
    base_url: str,
    token: str,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
    limit: int = 100,
) -> list[dict]:
    """Fetch accounts from Firefly-III (v1 API)."""
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
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
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Firefly-III accounts into Egeria (financial data assets)."""
    report: dict[str, Any] = {"accounts": [], "errors": []}

    base_url, token = _resolve(base_url, token)
    if not base_url or not token:
        report["skipped"] = "no Firefly URL/token (set FIREFLY_URL / FIREFLY_TOKEN)"
        return report

    accounts = fetch_accounts(base_url, token, tls_profile=tls_profile)
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
    note_error(report, "store:firefly", store)
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
        note_error(report, f"account:{name}", res)
        report["accounts"].append({"name": name, "qualifiedName": qn, **res})
        if store_guid and res.get("guid"):
            api.link_data_flow(store_guid, res["guid"], label="hosts")

    report["summary"] = {
        "accounts": count_created(report["accounts"]),
        "errors": len(report["errors"]),
    }
    return report
