"""CLI: run the Egeria bottom-up harvest against the configured platform.

Usage::

    # full run: every configured layer → reconcile → coverage audit
    python -m egeria_mcp.harvest

    # specific layers (then a full run adds reconcile + audit)
    python -m egeria_mcp.harvest containers datastores

    # just the cross-cutting passes
    python -m egeria_mcp.harvest reconcile
    python -m egeria_mcp.harvest audit       # read-only; no write needed

Credentials/URLs come from the environment. A private env file is sourced first if
present (``EGERIA_HARVEST_ENV``, default ``~/.config/agent-utilities/egeria-harvest.env``)
— values already set in the environment win. Keep that file out of any public repo.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

from agent_utilities.core.config import setting

DEFAULT_ENV = os.path.expanduser("~/.config/agent-utilities/egeria-harvest.env")


@dataclass
class HarvestRequest:
    """What one CLI invocation asks for, parsed from ``sys.argv``."""

    layers: list[str] | None
    do_reconcile: bool
    do_audit: bool
    audit_only: bool
    no_harvest: bool


def _load_env_file() -> str | None:
    """Load KEY=VALUE lines from the private env file into os.environ (no override)."""
    path = setting("EGERIA_HARVEST_ENV", DEFAULT_ENV)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and val and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        return None
    return path


def _reject_unknown_layers(layers: list[str], layers_available: set[str]) -> int | None:
    """Print + return an error exit code if ``layers`` names an unknown one."""
    unknown = [name for name in layers if name not in layers_available]
    if not unknown:
        return None
    print(
        f"unknown layer(s): {unknown}; valid: {sorted(layers_available)} "
        "(+ 'reconcile', 'audit')",
        file=sys.stderr,
    )
    return 2


def _request_from_tokens(requested: list[str]) -> HarvestRequest:
    """Build the request's flags from the already-validated non-flag tokens.

    'reconcile' and 'audit' are cross-cutting passes, not harvest layers. A full
    run (no args, or 'all') does harvest → reconcile → audit.
    """
    full = not requested or requested == ["all"]
    layers = [a for a in requested if a not in ("reconcile", "audit", "all")] or None
    audit_only = requested == ["audit"]
    return HarvestRequest(
        layers=layers,
        do_reconcile=full or "reconcile" in requested,
        do_audit=full or "audit" in requested,
        audit_only=audit_only,
        no_harvest=audit_only or requested == ["reconcile"],
    )


def _parse_request(argv: list[str], layers_available: set[str]) -> HarvestRequest | int:
    """Parse CLI args into a :class:`HarvestRequest`, or an exit code if invalid."""
    requested = [a for a in argv if not a.startswith("-")]
    request = _request_from_tokens(requested)
    if request.layers:
        rejected = _reject_unknown_layers(request.layers, layers_available)
        if rejected is not None:
            return rejected
    return request


def _run_cross_cutting_passes(api, reports: dict, request: HarvestRequest) -> dict:
    """Run the reconcile/audit passes the request asks for; return their output."""
    out: dict = {}
    if request.do_reconcile and not request.audit_only:
        from egeria_mcp.reconcile import reconcile

        rec = reconcile(api)
        out["reconcile"] = rec.get("summary") or rec
    if request.do_audit:
        from egeria_mcp.audit import audit

        out["audit"] = audit(api)
    return out


def _any_layer_errored(reports: dict) -> bool:
    return any(
        r.get("summary", {}).get("errors")
        for r in reports.values()
        if isinstance(r, dict)
    )


def main() -> int:
    loaded = _load_env_file()

    from egeria_mcp.auth import get_client
    from egeria_mcp.harvest.runner import LAYERS, harvest_all

    api = get_client()

    request = _parse_request(sys.argv[1:], LAYERS)
    if isinstance(request, int):
        return request

    # Harvest + reconcile mutate Egeria; audit is read-only.
    if not request.audit_only and not api.enable_write:
        print("EGERIA_ENABLE_WRITE is not true — refusing to harvest.", file=sys.stderr)
        return 2

    reports = {} if request.no_harvest else harvest_all(api, request.layers)
    out: dict = {
        "env_file": loaded,
        "layers": {
            name: rep.get("summary")
            or {"skipped": rep.get("skipped") or rep.get("error")}
            for name, rep in reports.items()
        },
        "reports": reports,
    }
    out.update(_run_cross_cutting_passes(api, reports, request))
    print(json.dumps(out, indent=2))
    return 1 if _any_layer_errored(reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
