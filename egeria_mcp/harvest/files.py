"""Content harvest — the Nextcloud layer.

Reads shares live from Nextcloud's OCS API and catalogs each shared file/folder as an
Egeria data asset (collaborative content, ``Confidential``). Idempotent.

Config-driven (``NEXTCLOUD_URL`` + ``NEXTCLOUD_USERNAME`` + ``NEXTCLOUD_PASSWORD``);
tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_connector_sdk.config import setting
from agent_connector_sdk.tls.profile import ResolvedTLSProfile

from egeria_mcp.governed_http import governed_client
from egeria_mcp.harvest._reporting import count_created, note_error


def fetch_shares(
    url: str,
    user: str,
    password: str,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> list[dict]:
    try:
        with governed_client(url, timeout=20.0, tls_profile=tls_profile) as c:
            r = c.get(
                f"{url.rstrip('/')}/ocs/v2.php/apps/files_sharing/api/v1/shares",
                auth=(user, password),
                headers={"OCS-APIRequest": "true", "Accept": "application/json"},
                params={"format": "json"},
            )
        if r.status_code != 200:
            return []
        return (((r.json() or {}).get("ocs") or {}).get("data")) or []
    except Exception:
        return []


def _catalog_shares(api: Any, shares: list[dict], report: dict[str, Any]) -> None:
    """Catalog Nextcloud shares as content data assets, deduped by path."""
    seen: set[str] = set()
    for sh in shares:
        path = sh.get("path") or sh.get("file_target")
        if not path or path in seen:
            continue
        seen.add(path)
        qn = f"Content::Nextcloud::{path}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            path.lstrip("/") or path,
            description=f"Nextcloud shared item '{path}'.",
            deployed_implementation_type="Nextcloud Share",
            confidentiality_level=2,
            additional_properties={
                "itemType": sh.get("item_type"),
                "owner": sh.get("uid_owner"),
                "source": "Nextcloud",
            },
        )
        note_error(report, f"share:{path}", res)
        report["shares"].append({"path": path, **res})


def harvest_files(
    api: Any,
    url: str | None = None,
    user: str | None = None,
    password: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Nextcloud shares into Egeria as content data assets."""
    report: dict[str, Any] = {"shares": [], "errors": []}

    url = url or setting("NEXTCLOUD_URL")
    user = user or setting("NEXTCLOUD_USERNAME")
    password = password or setting("NEXTCLOUD_PASSWORD")
    if not url or not user or not password:
        report["skipped"] = (
            "no Nextcloud creds (set NEXTCLOUD_URL / USERNAME / PASSWORD)"
        )
        return report

    shares = fetch_shares(url, user, password, tls_profile=tls_profile)
    report["source"] = {"url": url, "shares": len(shares)}
    if not shares:
        report["skipped"] = "no shares returned (unreachable or none shared)"
        return report

    _catalog_shares(api, shares, report)

    report["summary"] = {
        "shares": count_created(report["shares"]),
        "errors": len(report["errors"]),
    }
    return report
