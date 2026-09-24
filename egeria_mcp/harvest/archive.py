"""Web-archive harvest — the ArchiveBox layer.

Reads snapshots live from ArchiveBox and catalogs them under an archive ``Collection``
as Egeria data assets — the captured web corpus joins the catalog. Idempotent
(bounded by ``max_snapshots``).

Config-driven (``ARCHIVEBOX_URL`` + ``ARCHIVEBOX_API_KEY`` / ``ARCHIVEBOX_TOKEN``);
tolerant.
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


def fetch_snapshots(
    url: str,
    token: str,
    *,
    max_snapshots: int = 200,
    tls_profile: ResolvedTLSProfile | None = None,
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
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


def _catalog_snapshots(api: Any, snaps: list[dict], report: dict[str, Any]) -> None:
    """Catalog ArchiveBox snapshots as content data assets."""
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
        note_error(report, f"snapshot:{target}", res)
        report["snapshots"].append({"url": target, **res})


def harvest_archive(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    max_snapshots: int = 200,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog ArchiveBox snapshots into Egeria as content data assets."""
    report: dict[str, Any] = {"snapshots": [], "errors": []}

    url = url or setting("ARCHIVEBOX_URL")
    token = token or setting("ARCHIVEBOX_API_KEY") or setting("ARCHIVEBOX_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no ArchiveBox URL/token (set ARCHIVEBOX_URL / ARCHIVEBOX_API_KEY)"
        )
        return report

    snaps = fetch_snapshots(
        url, token, max_snapshots=max_snapshots, tls_profile=tls_profile
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
    _catalog_snapshots(api, snaps, report)

    report["summary"] = {
        "snapshots": count_created(report["snapshots"]),
        "errors": len(report["errors"]),
    }
    return report
