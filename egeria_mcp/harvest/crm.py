"""CRM harvest — the Twenty layer.

Reads companies and people live from Twenty's REST API and catalogs them as Egeria
data assets under a Twenty store — customer/party master data, classified
``Confidential`` (companies) / ``Sensitive`` (people, PII). Idempotent.

Config-driven (``TWENTY_URL`` + ``TWENTY_TOKEN``, optional ``TWENTY_API_PREFIX``
default ``/rest``); tolerant.
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


def _fetch(
    url: str,
    token: str,
    prefix: str,
    resource: str,
    tls_profile: ResolvedTLSProfile | None,
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(
                f"{url.rstrip('/')}{prefix}/{resource}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                params={"limit": 100},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        # Twenty REST: {"data": {"<resource>": [...]}}
        node = (data.get("data") if isinstance(data, dict) else None) or {}
        recs = node.get(resource) if isinstance(node, dict) else None
        return (
            recs if isinstance(recs, list) else (data if isinstance(data, list) else [])
        )
    except Exception:
        return []


def _record_name(rec: dict) -> str | None:
    """A record's display name; Twenty person names are {firstName,lastName}."""
    name = rec.get("name")
    if isinstance(name, dict):  # person name {firstName,lastName}
        name = (
            " ".join(filter(None, [name.get("firstName"), name.get("lastName")]))
            or rec.get("id")
        )
    return name or rec.get("id")


def _catalog_records(
    api: Any, resource: str, kind: str, level: int, recs: list[dict], report: dict[str, Any]
) -> None:
    """Catalog one CRM resource's records (companies/people) as data assets."""
    for rec in recs:
        name = _record_name(rec)
        if not name:
            continue
        qn = f"Dataset::Twenty::{kind}::{rec.get('id')}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            str(name),
            description=f"Twenty CRM {kind.lower()} '{name}'.",
            deployed_implementation_type=f"Twenty {kind}",
            confidentiality_level=level,
            additional_properties={"crmObject": kind, "source": "Twenty"},
        )
        note_error(report, f"{resource}:{name}", res)
        report["records"].append({"kind": kind, "name": str(name), **res})


def harvest_crm(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Twenty CRM companies + people into Egeria."""
    report: dict[str, Any] = {"records": [], "errors": []}

    url = url or setting("TWENTY_URL")
    token = token or setting("TWENTY_TOKEN")
    prefix = setting("TWENTY_API_PREFIX", "/rest")
    if not url or not token:
        report["skipped"] = "no Twenty URL/token (set TWENTY_URL / TWENTY_TOKEN)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::twenty",
        "twenty-crm",
        description="Twenty CRM store — customer/party master data.",
        deployed_implementation_type="Twenty CRM",
        confidentiality_level=2,
    )
    note_error(report, "store:twenty", store)

    total = 0
    for resource, level, kind in (("companies", 2, "Company"), ("people", 3, "Person")):
        recs = _fetch(url, token, prefix, resource, tls_profile)
        total += len(recs)
        _catalog_records(api, resource, kind, level, recs, report)

    report["source"] = {"url": url, "records": total}
    if total == 0:
        report["skipped"] = "no CRM records returned (unreachable or unauthorized)"
    report["summary"] = {
        "records": count_created(report["records"]),
        "errors": len(report["errors"]),
    }
    return report
