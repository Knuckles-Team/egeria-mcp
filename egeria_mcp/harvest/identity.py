"""Identity/access harvest — the Keycloak layer.

Reads realms and clients live from the Keycloak Admin REST API and catalogs each
realm as an Egeria ``Collection`` (a security domain) and each client as a
``DeployedSoftwareComponent`` (an access-controlled application). This makes the
federation **access-aware** — governance can reason about *who/what may act on* a
classified asset, not just how sensitive it is. Idempotent (by ``qualifiedName``).

Config-driven (``KEYCLOAK_URL`` + ``KEYCLOAK_TOKEN`` admin bearer, or
``KEYCLOAK_CLIENT_ID`` + ``KEYCLOAK_CLIENT_SECRET`` for client-credentials, optional
``KEYCLOAK_REALM`` default ``master``); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _resolve(base_url: str | None, token: str | None):
    return base_url or setting("KEYCLOAK_URL"), token or setting("KEYCLOAK_TOKEN")


def _bearer(base_url: str, verify_ssl: bool) -> str | None:
    """Obtain an admin bearer token via client-credentials, if configured."""
    cid = setting("KEYCLOAK_CLIENT_ID")
    secret = setting("KEYCLOAK_CLIENT_SECRET")
    realm = setting("KEYCLOAK_REALM", "master")
    if not (cid and secret) or not HTTPX_AVAILABLE:
        return None
    url = f"{base_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
    try:
        with httpx.Client(verify=verify_ssl, timeout=15.0) as c:
            r = c.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": cid,
                    "client_secret": secret,
                },
            )
        return r.json().get("access_token") if r.status_code == 200 else None
    except Exception:
        return None


def _get(base_url: str, token: str, path: str, verify_ssl: bool) -> Any:
    if not HTTPX_AVAILABLE:
        return None
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{base_url.rstrip('/')}{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def harvest_identity(
    api: Any,
    base_url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Keycloak realms (security domains) + clients (apps) into Egeria."""
    report: dict[str, Any] = {"realms": [], "clients": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url, token = _resolve(base_url, token)
    token = token or (_bearer(base_url, verify_ssl) if base_url else None)
    if not base_url or not token:
        report["skipped"] = (
            "no Keycloak URL/token (set KEYCLOAK_URL + KEYCLOAK_TOKEN or CLIENT_ID/SECRET)"
        )
        return report

    realms = _get(base_url, token, "/admin/realms", verify_ssl) or []
    report["source"] = {"base_url": base_url, "realms": len(realms)}
    if not realms:
        report["skipped"] = "no realms returned (unreachable or unauthorized)"
        return report

    for realm in realms:
        rname = realm.get("realm")
        if not rname:
            continue
        col = api.create_collection(
            f"Keycloak Realm {rname}",
            description=f"Keycloak security realm '{rname}'.",
            category="SecurityDomain",
        )
        record_error(f"realm:{rname}", col)
        report["realms"].append({"realm": rname, **col})
        for client in (
            _get(base_url, token, f"/admin/realms/{rname}/clients", verify_ssl) or []
        ):
            cid = client.get("clientId")
            if not cid:
                continue
            res = api.create_asset(
                "DeployedSoftwareComponent",
                f"Client::{rname}::{cid}",
                cid,
                description=client.get("description")
                or f"Keycloak client '{cid}' in realm '{rname}'.",
                deployed_implementation_type="OIDC Client",
                confidentiality_level=1,
                additional_properties={
                    "realm": rname,
                    "enabled": client.get("enabled"),
                    "publicClient": client.get("publicClient"),
                    "source": "Keycloak",
                },
            )
            record_error(f"client:{rname}/{cid}", res)
            report["clients"].append({"realm": rname, "clientId": cid, **res})

    report["summary"] = {
        "realms": len([r for r in report["realms"] if r.get("guid")]),
        "clients": len([c for c in report["clients"] if c.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
