"""LLM-ops harvest — the Langfuse layer.

Reads datasets live from Langfuse and catalogs each as an Egeria data asset — the
LLM evaluation/training datasets join the governed catalog. Idempotent.

Config-driven (``LANGFUSE_BASE_URL`` + ``LANGFUSE_PUBLIC_KEY`` + ``LANGFUSE_SECRET_KEY``,
basic auth); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_datasets(
    url: str, public: str, secret: str, *, verify_ssl: bool = False
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/public/datasets",
                auth=(public, secret),
                params={"limit": 100},
            )
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("data") or []
    except Exception:
        return []


def harvest_llmops(
    api: Any,
    url: str | None = None,
    public: str | None = None,
    secret: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Langfuse datasets into Egeria as LLM data assets."""
    report: dict[str, Any] = {"datasets": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("LANGFUSE_BASE_URL")
    public = public or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret = secret or os.getenv("LANGFUSE_SECRET_KEY")
    if not url or not public or not secret:
        report["skipped"] = (
            "no Langfuse creds (set LANGFUSE_BASE_URL / PUBLIC_KEY / SECRET_KEY)"
        )
        return report

    datasets = fetch_datasets(url, public, secret, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "datasets": len(datasets)}
    if not datasets:
        report["skipped"] = "no datasets returned (unreachable or unauthorized)"
        return report

    for ds in datasets:
        name = ds.get("name")
        if not name:
            continue
        qn = f"Dataset::Langfuse::{name}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            name,
            description=ds.get("description") or f"Langfuse dataset '{name}'.",
            deployed_implementation_type="Langfuse Dataset",
            confidentiality_level=1,
            additional_properties={"source": "Langfuse"},
        )
        record_error(f"dataset:{name}", res)
        report["datasets"].append({"name": name, **res})

    report["summary"] = {
        "datasets": len([d for d in report["datasets"] if d.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
