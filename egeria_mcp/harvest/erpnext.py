"""ERPNext harvest — the ERP layer of the bottom-up federation.

Reads DocType metadata live from an ERPNext (Frappe) instance over its REST API and
catalogs business-critical DocTypes as Egeria data assets, anchored to the ERPNext
database store, with confidentiality classifications driven by the kind of data each
DocType holds (HR/payroll → Sensitive, PII/financial → Confidential, else Internal).
Idempotent — reconciles by ``qualifiedName``.

Connection is config-driven (``ERPNEXT_URL`` + ``ERPNEXT_TOKEN`` = ``api_key:api_secret``,
e.g. ``http://erpnext:8000``); nothing about a specific deployment is baked into the
package. If unset/unreachable, the harvest is skipped (reported, not raised).
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

# Curated, business-critical DocTypes (a full ERPNext has ~800 — this is the
# meaningful master/transaction core). ERPNext is multi-role: alongside ERP it is the
# stack's **ITSM** (HelpDesk Issue / HD Ticket — the open-source ServiceNow
# alternative) and **project/work tracking** (Project / Task). Override via
# ``erpnext_doctypes`` in the topology config.
_DEFAULT_DOCTYPES: list[str] = [
    # ── masters / transactions (ERP) ──
    "Customer",
    "Supplier",
    "Contact",
    "Address",
    "Lead",
    "Item",
    "Warehouse",
    "Employee",
    "Salary Slip",
    "Sales Order",
    "Sales Invoice",
    "Purchase Order",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",
    "Delivery Note",
    # ── ITSM (ServiceNow-equivalent: HelpDesk / Support) ──
    "Issue",
    "HD Ticket",
    # ── project / work tracking (Jira/Plane-equivalent) ──
    "Project",
    "Task",
]

# Confidentiality by data kind (Egeria scale: 1 Internal, 2 Confidential, 3 Sensitive).
_SENSITIVE = {"Employee", "Salary Slip"}  # HR / payroll PII
_CONFIDENTIAL = {
    "Customer",
    "Supplier",
    "Contact",
    "Address",
    "Lead",  # counterparty PII
    "Sales Invoice",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",  # financial
    "Issue",
    "HD Ticket",  # support tickets reference customers
}


def _confidentiality(doctype: str) -> int:
    if doctype in _SENSITIVE:
        return 3
    if doctype in _CONFIDENTIAL:
        return 2
    return 1


# Canonical capability each DocType serves — lets the federation reconcile ERPNext
# with first-party tools for the same capability (ITSM↔ServiceNow, PM↔Jira/Plane).
_ITSM = {"Issue", "HD Ticket"}
_PM = {"Project", "Task"}


def _capability(doctype: str) -> str:
    if doctype in _ITSM:
        return "ITSM"
    if doctype in _PM:
        return "PM"
    return "ERP"


def _resolve(base_url: str | None, token: str | None) -> tuple[str | None, str | None]:
    return (
        base_url or setting("ERPNEXT_URL"),
        token or setting("ERPNEXT_TOKEN"),
    )


def fetch_doctype(
    base_url: str, token: str, name: str, *, verify_ssl: bool = False
) -> dict | None:
    """Fetch a single DocType definition (module, fields count) from Frappe REST."""
    if not HTTPX_AVAILABLE:
        return None
    url = f"{base_url.rstrip('/')}/api/resource/DocType/{name.replace(' ', '%20')}"
    try:
        with httpx.Client(verify=verify_ssl, timeout=15.0) as c:
            r = c.get(url, headers={"Authorization": f"token {token}"})
        if r.status_code != 200:
            return None
        return (r.json() or {}).get("data")
    except Exception:
        return None


def harvest_erpnext(
    api: Any,
    base_url: str | None = None,
    token: str | None = None,
    *,
    doctypes: list[str] | None = None,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog ERPNext DocTypes into Egeria; return a report.

    Parameters
    ----------
    api:
        A write-enabled ``EgeriaApi`` (``enable_write=True``).
    base_url, token:
        ERPNext URL and ``api_key:api_secret`` token. Fall back to ``ERPNEXT_URL`` /
        ``ERPNEXT_TOKEN``. If unset, the harvest is skipped (reported, not raised).
    doctypes:
        DocTypes to catalog (defaults to the curated business core).
    """
    report: dict[str, Any] = {"datasets": [], "flows": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url, token = _resolve(base_url, token)
    if not base_url or not token:
        report["skipped"] = "no ERPNext URL/token (set ERPNEXT_URL / ERPNEXT_TOKEN)"
        return report

    # Anchor: the ERPNext database store (MariaDB).
    store = api.create_asset(
        "SoftwareServer",
        "DataStore::erpnext-db",
        "erpnext-db",
        description="ERPNext (Frappe) MariaDB store — ERP master & transaction data.",
        deployed_implementation_type="MariaDB Server",
        confidentiality_level=2,
    )
    record_error("store:erpnext-db", store)
    report["store"] = {"qualifiedName": "DataStore::erpnext-db", **store}
    db = api.create_asset(
        "RelationalDatabase",
        "Dataset::erpnext-db::erpnext",
        "erpnext",
        description="ERPNext application database.",
        deployed_implementation_type="MariaDB Relational Database",
        confidentiality_level=2,
    )
    record_error("database:erpnext", db)
    db_guid = db.get("guid")

    names = doctypes or _DEFAULT_DOCTYPES
    for name in names:
        meta = fetch_doctype(base_url, token, name, verify_ssl=verify_ssl)
        if meta is None:
            report["errors"].append(
                {"item": f"doctype:{name}", "error": "not found / unauthorized"}
            )
            continue
        qn = f"Dataset::ERPNext::{name.replace(' ', '')}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            name,
            description=f"ERPNext DocType '{name}' (module {meta.get('module', '?')}).",
            deployed_implementation_type="ERPNext DocType",
            confidentiality_level=_confidentiality(name),
            additional_properties={
                "module": meta.get("module"),
                "doctype": name,
                "capability": _capability(name),
                "isSubmittable": meta.get("is_submittable"),
                "source": "ERPNext",
            },
        )
        record_error(f"doctype:{name}", res)
        report["datasets"].append({"name": name, "qualifiedName": qn, **res})
        # Lineage: the ERPNext database supplies each DocType dataset.
        if db_guid and res.get("guid"):
            flow = api.link_data_flow(db_guid, res["guid"], label="hosts")
            record_error(f"flow:erpnext->{name}", flow)

    report["summary"] = {
        "datasets": len([d for d in report["datasets"] if d.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
