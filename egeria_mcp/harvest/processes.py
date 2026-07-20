"""Process harvest — the Camunda layer of the bottom-up federation.

Reads BPMN process definitions live from a Camunda 7 engine and catalogs each as an
Egeria ``Process`` asset (``Process`` ⊑ ``Asset``), so business processes join the
unified catalog and ``governed_route`` / lineage can span them. Idempotent —
reconciles by ``qualifiedName``.

Connection is config-driven (``CAMUNDA7_URL`` / ``CAMUNDA_URL``, e.g.
``http://camunda:8090/engine-rest``); nothing about a specific deployment is baked
into the package. Process → dataset lineage is deployment-specific and only emitted
when an explicit ``process_flows`` mapping is supplied (see
:func:`egeria_mcp.harvest.topology.load_topology`).
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_tls_profile,
)

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

from egeria_mcp.harvest import topology


def _camunda_base_url(base_url: str | None) -> str | None:
    return base_url or setting("CAMUNDA7_URL") or setting("CAMUNDA_URL") or None


def fetch_process_definitions(
    base_url: str,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
    latest_only: bool = True,
    timeout: float = 15.0,
) -> list[dict]:
    """Fetch process definitions from a Camunda 7 engine-REST endpoint."""
    if not HTTPX_AVAILABLE:
        return []
    url = f"{base_url.rstrip('/')}/process-definition"
    params = {"latestVersion": "true"} if latest_only else {}
    try:
        with httpx.Client(timeout=timeout, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(url, params=params)
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def harvest_processes(
    api: Any,
    base_url: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Camunda process definitions into Egeria; return a report.

    Parameters
    ----------
    api:
        A write-enabled ``EgeriaApi`` (``enable_write=True``).
    base_url:
        Camunda 7 engine-REST base URL. Falls back to ``CAMUNDA7_URL`` /
        ``CAMUNDA_URL``. If unset, the harvest is skipped (reported, not raised).
    """
    report: dict[str, Any] = {"processes": [], "flows": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = _camunda_base_url(base_url)
    if not url:
        report["skipped"] = "no Camunda URL (set CAMUNDA7_URL / CAMUNDA_URL)"
        return report

    defs = fetch_process_definitions(url, tls_profile=tls_profile)
    report["source"] = {"base_url": url, "definitions": len(defs)}
    if not defs:
        report["skipped"] = (
            "no process definitions returned (unreachable or empty engine)"
        )
        return report

    # Catalog each process (latest version) as an Egeria Process asset.
    estate = topology.load_topology()
    key_to_guid: dict[str, str] = {}
    seen_keys: set[str] = set()
    for pd in defs:
        key = pd.get("key")
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        qn = f"Process::Camunda::{key}"
        res = api.create_asset(
            "Process",
            qn,
            pd.get("name") or key,
            description=pd.get("description") or f"Camunda BPMN process '{key}'.",
            deployed_implementation_type="BPMN Process",
            confidentiality_level=1,  # Internal
            additional_properties={
                "processKey": key,
                "engine": "Camunda 7",
                "latestVersion": pd.get("version"),
                "versionTag": pd.get("versionTag"),
                "resource": pd.get("resource"),
            },
        )
        record_error(f"process:{key}", res)
        if res.get("guid"):
            key_to_guid[key] = res["guid"]
        report["processes"].append(
            {"key": key, "name": pd.get("name"), "qualifiedName": qn, **res}
        )

    # Optional, declared process → dataset lineage (deployment-specific; only when
    # the topology config supplies a ``process_flows`` list of {process, dataset}).
    for flow in estate.get("process_flows", []) if isinstance(estate, dict) else []:
        proc_guid = key_to_guid.get(flow.get("process"))
        ds_qn = f"Dataset::{flow.get('dataset')}"
        ds_guid = api.find_asset(ds_qn) if flow.get("dataset") else None
        if not proc_guid or not ds_guid:
            report["errors"].append(
                {
                    "item": f"flow:{flow.get('dataset')}->{flow.get('process')}",
                    "error": "unresolved endpoint",
                }
            )
            continue
        # The dataset feeds the process (dataset → process consumes).
        res = api.link_data_flow(
            ds_guid, proc_guid, label=flow.get("label", "consumes")
        )
        record_error(f"flow:{flow.get('dataset')}->{flow.get('process')}", res)
        report["flows"].append(
            {"dataset": flow.get("dataset"), "process": flow.get("process"), **res}
        )

    report["summary"] = {
        "processes": len([p for p in report["processes"] if p.get("guid")]),
        "flows": len([f for f in report["flows"] if not f.get("error")]),
        "errors": len(report["errors"]),
    }
    return report
