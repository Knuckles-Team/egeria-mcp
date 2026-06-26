"""Web-archive harvest — the ArchiveBox layer.

Reads snapshots live from ArchiveBox and catalogs them under an archive ``Collection``
as Egeria data assets — the captured web corpus joins the catalog. Idempotent
(bounded by ``max_snapshots``).

Config-driven (``ARCHIVEBOX_URL`` + ``ARCHIVEBOX_API_KEY`` / ``ARCHIVEBOX_TOKEN``);
tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_snapshots(
    url: str, token: str, *, max_snapshots: int = 200, verify_ssl: bool = False
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/v1/core/snapshots",
                headers={"Authorization": f"Bearer {token}"},
                params={"limit": max_snapshots},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        recs = data.get("results") if isinstance(data, dict) else data
        return recs if isinstance(recs, list) else []
    except Exception:
        return []


def harvest_archive(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    max_snapshots: int = 200,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog ArchiveBox snapshots into Egeria as content data assets."""
    report: dict[str, Any] = {"snapshots": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("ARCHIVEBOX_URL")
    token = token or setting("ARCHIVEBOX_API_KEY") or setting("ARCHIVEBOX_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no ArchiveBox URL/token (set ARCHIVEBOX_URL / ARCHIVEBOX_API_KEY)"
        )
        return report

    snaps = fetch_snapshots(
        url, token, max_snapshots=max_snapshots, verify_ssl=verify_ssl
    )
    report["source"] = {"url": url, "snapshots": len(snaps)}
    if not snaps:
        report["skipped"] = "no snapshots returned (unreachable or empty)"
        return report

    api.create_collection(
        "ArchiveBox Corpus",
        description="ArchiveBox web-archive corpus.",
        category="WebArchive",
    )
    for sn in snaps:
        target = sn.get("url") or sn.get("id")
        if not target:
            continue
        qn = f"Snapshot::ArchiveBox::{sn.get('id') or target}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            (sn.get("title") or target)[:200],
            description=f"Archived snapshot of {target}.",
            deployed_implementation_type="Web Snapshot",
            confidentiality_level=1,
            additional_properties={"url": target, "source": "ArchiveBox"},
        )
        record_error(f"snapshot:{target}", res)
        report["snapshots"].append({"url": target, **res})

    report["summary"] = {
        "snapshots": len([s for s in report["snapshots"] if s.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
