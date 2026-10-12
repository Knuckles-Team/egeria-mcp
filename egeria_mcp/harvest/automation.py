"""Automation harvest — the Ansible (AWX/Tower) layer.

Reads job templates and inventories live from AWX/Ansible Tower's REST API and
catalogs job templates as Egeria ``Process`` assets and inventories as
``Collection``s — automation/deployment lineage joins the catalog. Idempotent.

Config-driven (``TOWER_URL`` + ``TOWER_TOKEN`` bearer); tolerant.
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
    url: str, token: str, path: str, tls_profile: ResolvedTLSProfile | None
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
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


def _catalog_inventories(
    api: Any, inventories: list[dict], report: dict[str, Any]
) -> None:
    """Catalog Tower inventories as Egeria Collections."""
    for inv in inventories:
        name = inv.get("name")
        if not name:
            continue
        res = api.create_collection(
            f"Inventory {name}",
            description=inv.get("description") or f"Ansible inventory '{name}'.",
            category="AnsibleInventory",
        )
        note_error(report, f"inventory:{name}", res)
        report["inventories"].append({"name": name, **res})


def _catalog_job_templates(
    api: Any, templates: list[dict], report: dict[str, Any]
) -> None:
    """Catalog Tower job templates as Egeria Process assets."""
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
        note_error(report, f"job_template:{name}", res)
        report["job_templates"].append({"name": name, "qualifiedName": qn, **res})


def harvest_automation(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog AWX/Tower job templates (Process) + inventories (Collection)."""
    report: dict[str, Any] = {"job_templates": [], "inventories": [], "errors": []}

    url = url or setting("TOWER_URL") or setting("ANSIBLE_TOWER_URL")
    token = token or setting("TOWER_TOKEN") or setting("ANSIBLE_TOWER_TOKEN")
    if not url or not token:
        report["skipped"] = "no Tower URL/token (set TOWER_URL / TOWER_TOKEN)"
        return report

    inventories = _fetch(url, token, "inventories", tls_profile)
    templates = _fetch(url, token, "job_templates", tls_profile)
    report["source"] = {
        "url": url,
        "inventories": len(inventories),
        "job_templates": len(templates),
    }
    if not inventories and not templates:
        report["skipped"] = "no Tower data returned (unreachable or unauthorized)"
        return report

    _catalog_inventories(api, inventories, report)
    _catalog_job_templates(api, templates, report)

    report["summary"] = {
        "inventories": count_created(report["inventories"]),
        "job_templates": count_created(report["job_templates"]),
        "errors": len(report["errors"]),
    }
    return report
