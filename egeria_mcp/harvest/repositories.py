"""Repository harvest — the GitLab layer of the bottom-up federation.

Reads projects live from a GitLab instance over its REST API (v4) and catalogs each
as an Egeria ``DeployedSoftwareComponent`` asset (code/CI produces and deploys
everything beneath it — the outermost lineage layer). Confidentiality is derived
from project visibility (private/internal → Internal, public → Unclassified).
Idempotent — reconciles by ``qualifiedName``.

Connection is config-driven (``GITLAB_URL`` + ``GITLAB_TOKEN`` — a personal/group
access token, e.g. ``http://gitlab:8080``); nothing about a specific deployment is
baked into the package. If unset/unreachable, the harvest is skipped (reported, not
raised).
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

# GitLab visibility → Egeria Confidentiality level.
_VISIBILITY_LEVEL = {"private": 1, "internal": 1, "public": 0}


def _resolve(base_url: str | None, token: str | None) -> tuple[str | None, str | None]:
    return (
        base_url or setting("GITLAB_URL") or setting("GITLAB_HOST"),
        token or setting("GITLAB_TOKEN") or setting("GITLAB_PRIVATE_TOKEN"),
    )


def fetch_projects(
    base_url: str,
    token: str,
    *,
    membership: bool = True,
    max_projects: int = 100,
    verify_ssl: bool = False,
) -> list[dict]:
    """Fetch projects from GitLab REST v4 (paginated, up to ``max_projects``)."""
    if not HTTPX_AVAILABLE:
        return []
    out: list[dict] = []
    headers = {"PRIVATE-TOKEN": token}
    per_page = min(100, max_projects)
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            page = 1
            while len(out) < max_projects:
                r = c.get(
                    f"{base_url.rstrip('/')}/api/v4/projects",
                    headers=headers,
                    params={
                        "membership": str(membership).lower(),
                        "per_page": per_page,
                        "page": page,
                        "order_by": "last_activity_at",
                        "simple": "true",
                    },
                )
                if r.status_code != 200:
                    break
                batch = r.json()
                if not isinstance(batch, list) or not batch:
                    break
                out.extend(batch)
                if len(batch) < per_page:
                    break
                page += 1
    except Exception:
        return out
    return out[:max_projects]


def harvest_repositories(
    api: Any,
    base_url: str | None = None,
    token: str | None = None,
    *,
    max_projects: int = 100,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog GitLab projects into Egeria; return a report.

    Parameters
    ----------
    api:
        A write-enabled ``EgeriaApi`` (``enable_write=True``).
    base_url, token:
        GitLab URL and access token. Fall back to ``GITLAB_URL`` / ``GITLAB_TOKEN``.
        If unset, the harvest is skipped (reported, not raised).
    """
    report: dict[str, Any] = {"repositories": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    base_url, token = _resolve(base_url, token)
    if not base_url or not token:
        report["skipped"] = "no GitLab URL/token (set GITLAB_URL / GITLAB_TOKEN)"
        return report

    projects = fetch_projects(
        base_url, token, max_projects=max_projects, verify_ssl=verify_ssl
    )
    report["source"] = {"base_url": base_url, "projects": len(projects)}
    if not projects:
        report["skipped"] = "no projects returned (unreachable or unauthorized)"
        return report

    for proj in projects:
        path = proj.get("path_with_namespace") or proj.get("name")
        if not path:
            continue
        qn = f"Repository::GitLab::{path}"
        visibility = str(proj.get("visibility", "private")).lower()
        res = api.create_asset(
            "DeployedSoftwareComponent",
            qn,
            proj.get("name") or path,
            description=proj.get("description") or f"GitLab repository '{path}'.",
            deployed_implementation_type="Git Repository",
            confidentiality_level=_VISIBILITY_LEVEL.get(visibility, 1),
            additional_properties={
                "pathWithNamespace": path,
                "defaultBranch": proj.get("default_branch"),
                "visibility": visibility,
                "webUrl": proj.get("web_url"),
                "capability": "vcs",
                "source": "GitLab",
            },
        )
        record_error(f"repo:{path}", res)
        report["repositories"].append({"path": path, "qualifiedName": qn, **res})

    report["summary"] = {
        "repositories": len([r for r in report["repositories"] if r.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report


def fetch_github_repos(
    token: str,
    *,
    org: str | None = None,
    max_repos: int = 100,
    base_url: str = "https://api.github.com",
) -> list[dict]:
    """Fetch repos from GitHub (an org's, or the token owner's)."""
    if not HTTPX_AVAILABLE:
        return []
    path = f"/orgs/{org}/repos" if org else "/user/repos"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    out: list[dict] = []
    try:
        with httpx.Client(timeout=20.0) as c:
            page = 1
            while len(out) < max_repos:
                r = c.get(
                    f"{base_url.rstrip('/')}{path}",
                    headers=headers,
                    params={
                        "per_page": min(100, max_repos),
                        "page": page,
                        "sort": "updated",
                    },
                )
                if r.status_code != 200:
                    break
                batch = r.json()
                if not isinstance(batch, list) or not batch:
                    break
                out.extend(batch)
                if len(batch) < min(100, max_repos):
                    break
                page += 1
    except Exception:
        return out
    return out[:max_repos]


def harvest_github(
    api: Any,
    token: str | None = None,
    *,
    org: str | None = None,
    max_repos: int = 100,
) -> dict[str, Any]:
    """Catalog GitHub repositories into Egeria as ``DeployedSoftwareComponent`` assets.

    Config: ``GITHUB_TOKEN`` (+ optional ``GITHUB_ORG``). Tolerant — skipped when
    unconfigured/unreachable.
    """
    report: dict[str, Any] = {"repositories": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    token = token or setting("GITHUB_TOKEN")
    org = org or setting("GITHUB_ORG")
    if not token:
        report["skipped"] = "no GitHub token (set GITHUB_TOKEN)"
        return report

    repos = fetch_github_repos(token, org=org, max_repos=max_repos)
    report["source"] = {"org": org or "(user)", "repos": len(repos)}
    if not repos:
        report["skipped"] = "no repos returned (unreachable or unauthorized)"
        return report

    for repo in repos:
        full = repo.get("full_name") or repo.get("name")
        if not full:
            continue
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"Repository::GitHub::{full}",
            repo.get("name") or full,
            description=repo.get("description") or f"GitHub repository '{full}'.",
            deployed_implementation_type="Git Repository",
            confidentiality_level=1 if repo.get("private") else 0,
            additional_properties={
                "fullName": full,
                "defaultBranch": repo.get("default_branch"),
                "visibility": "private" if repo.get("private") else "public",
                "webUrl": repo.get("html_url"),
                "capability": "vcs",
                "source": "GitHub",
            },
        )
        record_error(f"repo:{full}", res)
        report["repositories"].append({"path": full, **res})

    report["summary"] = {
        "repositories": len([r for r in report["repositories"] if r.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
