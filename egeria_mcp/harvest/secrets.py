"""Secrets-governance harvest — the OpenBao / Vault layer.

Reads secret-engine **mounts** and **ACL policy names** (never secret *values*) from
OpenBao/Vault and catalogs mounts as Egeria ``DeployedSoftwareComponent`` assets and
policies as governance-component assets — a sensitive-resource + policy inventory for
governance. Idempotent.

Config-driven (``OPENBAO_URL`` / ``VAULT_ADDR`` + ``OPENBAO_TOKEN`` / ``VAULT_TOKEN``);
tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _resolve(url: str | None, token: str | None):
    return (
        url
        or os.getenv("OPENBAO_URL")
        or os.getenv("BAO_ADDR")
        or os.getenv("VAULT_ADDR"),
        token or os.getenv("OPENBAO_TOKEN") or os.getenv("VAULT_TOKEN"),
    )


def _get(url: str, token: str, path: str, verify_ssl: bool, params=None) -> Any:
    if not HTTPX_AVAILABLE:
        return None
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}{path}",
                headers={"X-Vault-Token": token},
                params=params or {},
            )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def harvest_secrets(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog OpenBao/Vault secret-engine mounts + policy names into Egeria."""
    report: dict[str, Any] = {"mounts": [], "policies": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url, token = _resolve(url, token)
    if not url or not token:
        report["skipped"] = "no OpenBao URL/token (set OPENBAO_URL / OPENBAO_TOKEN)"
        return report

    mounts_resp = _get(url, token, "/v1/sys/mounts", verify_ssl) or {}
    mounts = mounts_resp.get("data") or {
        k: v for k, v in mounts_resp.items() if isinstance(v, dict) and "type" in v
    }
    policies = (
        (
            _get(url, token, "/v1/sys/policies/acl", verify_ssl, {"list": "true"}) or {}
        ).get("data")
        or {}
    ).get("keys") or []
    report["source"] = {"url": url, "mounts": len(mounts), "policies": len(policies)}
    if not mounts and not policies:
        report["skipped"] = "no mounts/policies returned (unreachable or unauthorized)"
        return report

    for path, meta in (mounts or {}).items():
        name = path.rstrip("/")
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"SecretEngine::{name}",
            name,
            description=f"Vault secret engine '{name}' (type {(meta or {}).get('type')}).",
            deployed_implementation_type="Vault Secret Engine",
            confidentiality_level=2,
            additional_properties={
                "engineType": (meta or {}).get("type"),
                "source": "OpenBao",
            },
        )
        record_error(f"mount:{name}", res)
        report["mounts"].append({"name": name, **res})

    for pol in policies:
        if pol in ("root", "default"):
            continue
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"VaultPolicy::{pol}",
            pol,
            description=f"Vault ACL policy '{pol}'.",
            deployed_implementation_type="Vault ACL Policy",
            confidentiality_level=1,
            additional_properties={"kind": "acl-policy", "source": "OpenBao"},
        )
        record_error(f"policy:{pol}", res)
        report["policies"].append({"name": pol, **res})

    report["summary"] = {
        "mounts": len([m for m in report["mounts"] if m.get("guid")]),
        "policies": len([p for p in report["policies"] if p.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
