"""Process / enterprise-architecture harvest — the ARIS layer.

Reads models live from Software AG **ARIS** (Connect / Cloud REST) and catalogs
each as an Egeria asset — process models join the BPM cohort (alongside Camunda),
architecture models join the enterprise-architecture cohort (alongside LeanIX /
ArchiMate). The opinionated first-party EA+BPM suite, federated into the governed
catalog. Idempotent (by ``qualifiedName``).

Config-driven (``ARIS_URL`` + ``ARIS_TOKEN``, optional ``ARIS_API_PATH`` default
``/abs/api/models``); tolerant — skipped when unconfigured/unreachable.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

# Model-type substrings that mark a *process* model (BPM) rather than an
# architecture/application model (enterprise-architecture).
_BPM_HINTS = ("process", "epc", "bpmn", "value", "vad")


def _is_process(model_type: str) -> bool:
    t = (model_type or "").lower()
    return any(h in t for h in _BPM_HINTS)


def fetch_models(
    url: str, token: str, path: str, *, verify_ssl: bool = False
) -> list[dict]:
    """Fetch models from the ARIS REST API (tolerant; ``[]`` on any failure)."""
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}{path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                params={"limit": 500},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        # ARIS shapes vary: {"models":[...]} | {"items":[...]} | [...]
        if isinstance(data, dict):
            recs = data.get("models") or data.get("items") or data.get("data") or []
        else:
            recs = data
        return recs if isinstance(recs, list) else []
    except Exception:
        return []


def harvest_aris(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    api_path: str | None = None,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog ARIS models into Egeria (process + architecture)."""
    report: dict[str, Any] = {"models": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("ARIS_URL")
    token = token or os.getenv("ARIS_TOKEN") or os.getenv("ARIS_API_TOKEN")
    api_path = api_path or os.getenv("ARIS_API_PATH", "/abs/api/models")
    if not url or not token:
        report["skipped"] = "no ARIS URL/token (set ARIS_URL / ARIS_TOKEN)"
        return report

    models = fetch_models(url, token, api_path, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "models": len(models)}
    if not models:
        report["skipped"] = "no models returned (unreachable or unauthorized)"
        return report

    for m in models:
        name = m.get("name") or m.get("id")
        mid = m.get("id") or name
        if not name:
            continue
        mtype = m.get("type") or m.get("modelType") or "Model"
        if _is_process(mtype):
            asset_type, qn, cap = (
                "Process",
                f"Process::ARIS::{mid}",
                "bpm",
            )
        else:
            asset_type, qn, cap = (
                "DeployedSoftwareComponent",
                f"ArchiMate::ARIS::{mtype}::{mid}",
                "enterprise-architecture",
            )
        res = api.create_asset(
            asset_type,
            qn,
            str(name),
            description=f"ARIS {mtype} model '{name}'.",
            deployed_implementation_type=f"ARIS {mtype}",
            confidentiality_level=1,
            additional_properties={
                "modelType": mtype,
                "arisId": str(mid),
                "capability": cap,
                "source": "ARIS",
            },
        )
        record_error(f"model:{name}", res)
        report["models"].append({"name": str(name), "type": mtype, **res})

    report["summary"] = {
        "models": len([m for m in report["models"] if m.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
