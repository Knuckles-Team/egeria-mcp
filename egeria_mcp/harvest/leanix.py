"""Enterprise-architecture harvest — the LeanIX layer.

Reads fact sheets live from LeanIX (SAP LeanIX) via its GraphQL API and catalogs each
as an Egeria asset under the workspace collection — the application/technology
portfolio joins the governed catalog. Idempotent.

Config-driven (``LEANIX_URL`` base + ``LEANIX_API_TOKEN``); tolerant. LeanIX exchanges
the API token for a bearer via its MTM OAuth endpoint, then queries Pathfinder GraphQL.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

_QUERY = "{allFactSheets(first:500){edges{node{id name type}}}}"


def _bearer(base_url: str, api_token: str, verify_ssl: bool) -> str | None:
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.post(
                f"{base_url.rstrip('/')}/services/mtm/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=("apitoken", api_token),
            )
        return r.json().get("access_token") if r.status_code == 200 else None
    except Exception:
        return None


def fetch_factsheets(
    base_url: str, api_token: str, *, verify_ssl: bool = False
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    bearer = _bearer(base_url, api_token, verify_ssl)
    if not bearer:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=30.0) as c:
            r = c.post(
                f"{base_url.rstrip('/')}/services/pathfinder/v1/graphql",
                headers={
                    "Authorization": f"Bearer {bearer}",
                    "Content-Type": "application/json",
                },
                json={"query": _QUERY},
            )
        if r.status_code != 200:
            return []
        edges = (((r.json() or {}).get("data") or {}).get("allFactSheets") or {}).get(
            "edges"
        ) or []
        return [e["node"] for e in edges if e.get("node")]
    except Exception:
        return []


def harvest_leanix(
    api: Any,
    base_url: str | None = None,
    api_token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog LeanIX fact sheets into Egeria as architecture assets."""
    report: dict[str, Any] = {"factsheets": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url = base_url or setting("LEANIX_URL")
    api_token = api_token or setting("LEANIX_API_TOKEN") or setting("LEANIX_TOKEN")
    if not base_url or not api_token:
        report["skipped"] = "no LeanIX URL/token (set LEANIX_URL / LEANIX_API_TOKEN)"
        return report

    sheets = fetch_factsheets(base_url, api_token, verify_ssl=verify_ssl)
    report["source"] = {"url": base_url, "factsheets": len(sheets)}
    if not sheets:
        report["skipped"] = "no fact sheets returned (unreachable or unauthorized)"
        return report

    col = api.create_collection(
        "LeanIX Portfolio",
        description="LeanIX EA fact-sheet portfolio.",
        category="Portfolio",
    )
    record_error("collection:leanix", col)

    # FactSheet type → Egeria asset type.
    type_map = {
        "Application": "DeployedSoftwareComponent",
        "ITComponent": "DeployedSoftwareComponent",
        "TechnologyStack": "SoftwareServer",
        "DataObject": "DeployedDatabaseSchema",
        "BusinessCapability": "Process",
        "Process": "Process",
    }
    for fs in sheets:
        name = fs.get("name")
        fstype = fs.get("type") or "FactSheet"
        if not name:
            continue
        qn = f"FactSheet::LeanIX::{fstype}::{fs.get('id')}"
        res = api.create_asset(
            type_map.get(fstype, "DeployedSoftwareComponent"),
            qn,
            name,
            description=f"LeanIX {fstype} fact sheet '{name}'.",
            deployed_implementation_type=f"LeanIX {fstype}",
            confidentiality_level=1,
            additional_properties={
                "factSheetType": fstype,
                "leanixId": fs.get("id"),
                "capability": "enterprise-architecture",
                "source": "LeanIX",
            },
        )
        record_error(f"factsheet:{name}", res)
        report["factsheets"].append({"name": name, "type": fstype, **res})

    report["summary"] = {
        "factsheets": len([f for f in report["factsheets"] if f.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
