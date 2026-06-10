"""GRC / risk harvest — the RSA Archer layer.

Reads governance, risk & compliance records live from **RSA Archer** (the Archer
Platform REST content API) and catalogs each as an Egeria data asset under an
Archer store — risks, controls, and findings join the governed catalog as the
``grc`` capability, classified ``Confidential``. The opinionated first-party GRC
suite, federated so risk/control inventory cross-links with the rest of the
estate. Idempotent (by ``qualifiedName``).

Config-driven (``ARCHER_URL`` + ``ARCHER_TOKEN``, optional ``ARCHER_APPLICATIONS``
default ``risks,controls,findings``); tolerant — skipped when unconfigured.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

_DEFAULT_APPLICATIONS = ["risks", "controls", "findings"]


def fetch_records(
    url: str, token: str, application: str, *, verify_ssl: bool = False
) -> list[dict]:
    """Fetch records for an Archer application (tolerant; ``[]`` on any failure)."""
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/core/content/{application}",
                headers={
                    "Authorization": f"Archer session-id={token}",
                    "Accept": "application/json",
                },
                params={"$top": 200},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        # Archer OData-ish: {"value":[{"RequestedObject":{...}}]} | [...]
        if isinstance(data, dict):
            recs = data.get("value") or data.get("Records") or data.get("data") or []
        else:
            recs = data
        out = []
        for rec in recs if isinstance(recs, list) else []:
            out.append(
                rec.get("RequestedObject", rec) if isinstance(rec, dict) else rec
            )
        return out
    except Exception:
        return []


def harvest_archer(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    applications: list[str] | None = None,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog RSA Archer GRC records into Egeria (risks/controls/findings)."""
    report: dict[str, Any] = {"records": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("ARCHER_URL")
    token = token or os.getenv("ARCHER_TOKEN") or os.getenv("ARCHER_SESSION_ID")
    apps = applications or [
        a.strip()
        for a in os.getenv(
            "ARCHER_APPLICATIONS", ",".join(_DEFAULT_APPLICATIONS)
        ).split(",")
        if a.strip()
    ]
    if not url or not token:
        report["skipped"] = "no Archer URL/token (set ARCHER_URL / ARCHER_TOKEN)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::archer",
        "rsa-archer-grc",
        description="RSA Archer GRC store — risk/control/compliance master data.",
        deployed_implementation_type="RSA Archer",
        confidentiality_level=2,
    )
    record_error("store:archer", store)

    total = 0
    for application in apps:
        recs = fetch_records(url, token, application, verify_ssl=verify_ssl)
        total += len(recs)
        kind = application.rstrip("s").capitalize() or application
        for rec in recs:
            name = (
                rec.get("Name")
                or rec.get("name")
                or rec.get("Title")
                or rec.get("id")
                or rec.get("Id")
            )
            rid = rec.get("Id") or rec.get("id") or name
            if not name:
                continue
            qn = f"RiskAsset::Archer::{kind}::{rid}"
            res = api.create_asset(
                "DeployedDatabaseSchema",
                qn,
                str(name),
                description=f"RSA Archer {kind} '{name}'.",
                deployed_implementation_type=f"Archer {kind}",
                confidentiality_level=2,
                additional_properties={
                    "grcKind": kind,
                    "archerId": str(rid),
                    "application": application,
                    "capability": "grc",
                    "source": "Archer",
                },
            )
            record_error(f"{application}:{name}", res)
            report["records"].append({"kind": kind, "name": str(name), **res})

    report["source"] = {"url": url, "records": total}
    if total == 0:
        report["skipped"] = "no GRC records returned (unreachable or unauthorized)"
    report["summary"] = {
        "records": len([r for r in report["records"] if r.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
