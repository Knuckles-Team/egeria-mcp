"""Automation harvest — the Ansible (AWX/Tower) layer.

Reads job templates and inventories live from AWX/Ansible Tower's REST API and
catalogs job templates as Egeria ``Process`` assets and inventories as
``Collection``s — automation/deployment lineage joins the catalog. Idempotent.

Config-driven (``TOWER_URL`` + ``TOWER_TOKEN`` bearer); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _fetch(url: str, token: str, path: str, verify_ssl: bool) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/v2/{path}/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                params={"page_size": 100},
            )
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("results") or []
    except Exception:
        return []


def harvest_automation(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog AWX/Tower job templates (Process) + inventories (Collection)."""
    report: dict[str, Any] = {"job_templates": [], "inventories": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("TOWER_URL") or setting("ANSIBLE_TOWER_URL")
    token = token or setting("TOWER_TOKEN") or setting("ANSIBLE_TOWER_TOKEN")
    if not url or not token:
        report["skipped"] = "no Tower URL/token (set TOWER_URL / TOWER_TOKEN)"
        return report

    inventories = _fetch(url, token, "inventories", verify_ssl)
    templates = _fetch(url, token, "job_templates", verify_ssl)
    report["source"] = {
        "url": url,
        "inventories": len(inventories),
        "job_templates": len(templates),
    }
    if not inventories and not templates:
        report["skipped"] = "no Tower data returned (unreachable or unauthorized)"
        return report

    for inv in inventories:
        name = inv.get("name")
        if not name:
            continue
        res = api.create_collection(
            f"Inventory {name}",
            description=inv.get("description") or f"Ansible inventory '{name}'.",
            category="AnsibleInventory",
        )
        record_error(f"inventory:{name}", res)
        report["inventories"].append({"name": name, **res})

    for jt in templates:
        name = jt.get("name")
        if not name:
            continue
        qn = f"Process::Ansible::{name.replace(' ', '')}"
        res = api.create_asset(
            "Process",
            qn,
            name,
            description=jt.get("description") or f"Ansible job template '{name}'.",
            deployed_implementation_type="Ansible Job Template",
            confidentiality_level=1,
            additional_properties={
                "playbook": jt.get("playbook"),
                "jobType": jt.get("job_type"),
                "source": "Ansible",
            },
        )
        record_error(f"job_template:{name}", res)
        report["job_templates"].append({"name": name, "qualifiedName": qn, **res})

    report["summary"] = {
        "inventories": len([i for i in report["inventories"] if i.get("guid")]),
        "job_templates": len([j for j in report["job_templates"] if j.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
