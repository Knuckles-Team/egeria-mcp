"""CRM harvest — the Odoo layer.

Reads customers (``res.partner``) and CRM leads (``crm.lead``) live from **Odoo**
via its JSON-RPC API and catalogs them as Egeria data assets under an Odoo store —
the open-source CRM joins the ``crm`` cohort alongside Twenty (so cross-vendor CRM
redundancy surfaces for consolidation). Customer/party data classified
``Confidential`` (PII). Idempotent (by ``qualifiedName``).

Config-driven (``ODOO_URL`` + ``ODOO_DB`` + ``ODOO_USER`` + ``ODOO_PASSWORD``);
tolerant — skipped when unconfigured/unreachable.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

# (odoo model, asset display kind, confidentiality level)
_MODELS = [
    ("res.partner", "Customer", 2),
    ("crm.lead", "Lead", 2),
]


def _rpc(url: str, payload: dict, verify_ssl: bool) -> Any:
    """One Odoo JSON-RPC call; returns the ``result`` or ``None`` on any failure."""
    if not HTTPX_AVAILABLE:
        return None
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.post(
                f"{url.rstrip('/')}/jsonrpc",
                json={"jsonrpc": "2.0", "method": "call", "params": payload},
            )
        if r.status_code != 200:
            return None
        return (r.json() or {}).get("result")
    except Exception:
        return None


def authenticate(
    url: str, db: str, user: str, password: str, *, verify_ssl: bool = False
) -> int | None:
    """Resolve an Odoo uid via the ``common.authenticate`` JSON-RPC method."""
    uid = _rpc(
        url,
        {
            "service": "common",
            "method": "authenticate",
            "args": [db, user, password, {}],
        },
        verify_ssl,
    )
    return int(uid) if isinstance(uid, int) and uid else None


def fetch_records(
    url: str,
    db: str,
    uid: int,
    password: str,
    model: str,
    *,
    verify_ssl: bool = False,
    limit: int = 200,
) -> list[dict]:
    """``search_read`` a model via the ``object.execute_kw`` JSON-RPC method."""
    res = _rpc(
        url,
        {
            "service": "object",
            "method": "execute_kw",
            "args": [
                db,
                uid,
                password,
                model,
                "search_read",
                [[]],
                {"fields": ["id", "name", "display_name"], "limit": limit},
            ],
        },
        verify_ssl,
    )
    return res if isinstance(res, list) else []


def harvest_odoo(
    api: Any,
    url: str | None = None,
    db: str | None = None,
    user: str | None = None,
    password: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Odoo CRM customers + leads into Egeria."""
    report: dict[str, Any] = {"records": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("ODOO_URL")
    db = db or setting("ODOO_DB")
    user = user or setting("ODOO_USER")
    password = password or setting("ODOO_PASSWORD") or setting("ODOO_API_KEY")
    if not url or not db or not user or not password:
        report["skipped"] = (
            "no Odoo config (set ODOO_URL / ODOO_DB / ODOO_USER / ODOO_PASSWORD)"
        )
        return report

    uid = authenticate(url, db, user, password, verify_ssl=verify_ssl)
    if not uid:
        report["skipped"] = (
            "Odoo authentication failed (unreachable or bad credentials)"
        )
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::odoo",
        "odoo-crm",
        description="Odoo CRM store — customer/lead master data.",
        deployed_implementation_type="Odoo CRM",
        confidentiality_level=2,
    )
    record_error("store:odoo", store)

    total = 0
    for model, kind, level in _MODELS:
        recs = fetch_records(url, db, uid, password, model, verify_ssl=verify_ssl)
        total += len(recs)
        for rec in recs:
            name = rec.get("display_name") or rec.get("name") or rec.get("id")
            rid = rec.get("id") or name
            if not name:
                continue
            qn = f"Dataset::Odoo::{kind}::{rid}"
            res = api.create_asset(
                "DeployedDatabaseSchema",
                qn,
                str(name),
                description=f"Odoo CRM {kind.lower()} '{name}'.",
                deployed_implementation_type=f"Odoo {kind}",
                confidentiality_level=level,
                additional_properties={
                    "crmObject": kind,
                    "odooModel": model,
                    "odooId": str(rid),
                    "capability": "crm",
                    "source": "Odoo",
                },
            )
            record_error(f"{model}:{name}", res)
            report["records"].append({"kind": kind, "name": str(name), **res})

    report["source"] = {"url": url, "records": total}
    if total == 0:
        report["skipped"] = "no CRM records returned (unreachable or unauthorized)"
    report["summary"] = {
        "records": len([r for r in report["records"] if r.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
