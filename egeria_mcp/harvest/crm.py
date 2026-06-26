"""CRM harvest — the Twenty layer.

Reads companies and people live from Twenty's REST API and catalogs them as Egeria
data assets under a Twenty store — customer/party master data, classified
``Confidential`` (companies) / ``Sensitive`` (people, PII). Idempotent.

Config-driven (``TWENTY_URL`` + ``TWENTY_TOKEN``, optional ``TWENTY_API_PREFIX``
default ``/rest``); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _fetch(
    url: str, token: str, prefix: str, resource: str, verify_ssl: bool
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
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


def harvest_crm(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Twenty CRM companies + people into Egeria."""
    report: dict[str, Any] = {"records": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

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
    record_error("store:twenty", store)

    total = 0
    for resource, level, kind in (("companies", 2, "Company"), ("people", 3, "Person")):
        recs = _fetch(url, token, prefix, resource, verify_ssl)
        total += len(recs)
        for rec in recs:
            name = rec.get("name")
            if isinstance(name, dict):  # person name {firstName,lastName}
                name = " ".join(
                    filter(None, [name.get("firstName"), name.get("lastName")])
                ) or rec.get("id")
            name = name or rec.get("id")
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
            record_error(f"{resource}:{name}", res)
            report["records"].append({"kind": kind, "name": str(name), **res})

    report["source"] = {"url": url, "records": total}
    if total == 0:
        report["skipped"] = "no CRM records returned (unreachable or unauthorized)"
    report["summary"] = {
        "records": len([r for r in report["records"] if r.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
