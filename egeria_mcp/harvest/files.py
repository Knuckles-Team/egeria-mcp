"""Content harvest — the Nextcloud layer.

Reads shares live from Nextcloud's OCS API and catalogs each shared file/folder as an
Egeria data asset (collaborative content, ``Confidential``). Idempotent.

Config-driven (``NEXTCLOUD_URL`` + ``NEXTCLOUD_USERNAME`` + ``NEXTCLOUD_PASSWORD``);
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


def fetch_shares(
    url: str, user: str, password: str, *, verify_ssl: bool = False
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
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


def harvest_files(
    api: Any,
    url: str | None = None,
    user: str | None = None,
    password: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Nextcloud shares into Egeria as content data assets."""
    report: dict[str, Any] = {"shares": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("NEXTCLOUD_URL")
    user = user or os.getenv("NEXTCLOUD_USERNAME")
    password = password or os.getenv("NEXTCLOUD_PASSWORD")
    if not url or not user or not password:
        report["skipped"] = (
            "no Nextcloud creds (set NEXTCLOUD_URL / USERNAME / PASSWORD)"
        )
        return report

    shares = fetch_shares(url, user, password, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "shares": len(shares)}
    if not shares:
        report["skipped"] = "no shares returned (unreachable or none shared)"
        return report

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
        record_error(f"share:{path}", res)
        report["shares"].append({"path": path, **res})

    report["summary"] = {
        "shares": len([s for s in report["shares"] if s.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
