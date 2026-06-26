"""ITSM harvest — the ServiceNow layer.

Reads CMDB configuration items live from ServiceNow's Table API and catalogs each as
an Egeria ``SoftwareServer`` / infrastructure asset, reconciled with the
container/data-store layers by name. The classic IT-service governance companion to
the data-governance SoR. Idempotent (by ``qualifiedName``).

Config-driven (``SERVICENOW_URL`` + ``SERVICENOW_USER`` + ``SERVICENOW_PASSWORD``, or
``SERVICENOW_TOKEN``); tolerant — skipped when unconfigured/unreachable.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

# CMDB CI tables to catalog (servers/databases/apps). Override via the harvest args.
_DEFAULT_TABLES = ["cmdb_ci_server", "cmdb_ci_database", "cmdb_ci_appl"]


def _resolve(
    base_url: str | None, user: str | None, password: str | None, token: str | None
):
    return (
        base_url or setting("SERVICENOW_URL"),
        user or setting("SERVICENOW_USER"),
        password or setting("SERVICENOW_PASSWORD"),
        token or setting("SERVICENOW_TOKEN"),
    )


def fetch_cis(
    base_url: str,
    table: str,
    *,
    auth=None,
    headers=None,
    limit: int = 100,
    verify_ssl: bool = False,
) -> list[dict]:
    """Fetch configuration items from a ServiceNow CMDB table."""
    if not HTTPX_AVAILABLE:
        return []
    url = f"{base_url.rstrip('/')}/api/now/table/{table}"
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                url,
                params={
                    "sysparm_limit": limit,
                    "sysparm_fields": "name,sys_class_name,sys_id,short_description",
                },
                auth=auth,
                headers={**(headers or {}), "Accept": "application/json"},
            )
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("result") or []
    except Exception:
        return []


def harvest_servicenow(
    api: Any,
    base_url: str | None = None,
    user: str | None = None,
    password: str | None = None,
    token: str | None = None,
    *,
    tables: list[str] | None = None,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog ServiceNow CMDB configuration items into Egeria."""
    report: dict[str, Any] = {"items": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url, user, password, token = _resolve(base_url, user, password, token)
    if not base_url or not (token or (user and password)):
        report["skipped"] = (
            "no ServiceNow URL/credentials (set SERVICENOW_URL + USER/PASSWORD or TOKEN)"
        )
        return report
    auth = (user, password) if (user and password) else None
    headers = {"Authorization": f"Bearer {token}"} if token else None

    total = 0
    for table in tables or _DEFAULT_TABLES:
        cis = fetch_cis(
            base_url, table, auth=auth, headers=headers, verify_ssl=verify_ssl
        )
        total += len(cis)
        for ci in cis:
            name = ci.get("name")
            if not name:
                continue
            res = api.create_asset(
                "SoftwareServer",
                f"CI::ServiceNow::{name}",
                name,
                description=ci.get("short_description")
                or f"ServiceNow CMDB CI '{name}' ({table}).",
                deployed_implementation_type=ci.get("sys_class_name") or table,
                confidentiality_level=1,
                additional_properties={
                    "table": table,
                    "sysId": ci.get("sys_id"),
                    "capability": "ITSM",
                    "source": "ServiceNow",
                },
            )
            record_error(f"ci:{name}", res)
            report["items"].append({"name": name, "table": table, **res})

    report["source"] = {"base_url": base_url, "configuration_items": total}
    if total == 0:
        report["skipped"] = "no CIs returned (unreachable or unauthorized)"
    report["summary"] = {
        "items": len([i for i in report["items"] if i.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
