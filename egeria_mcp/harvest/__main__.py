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

from agent_utilities.core.config import setting

DEFAULT_ENV = os.path.expanduser("~/.config/agent-utilities/egeria-harvest.env")


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


def main() -> int:
    loaded = _load_env_file()

    from egeria_mcp.auth import get_client
    from egeria_mcp.harvest.runner import LAYERS, harvest_all

    api = get_client()

    requested = [a for a in sys.argv[1:] if not a.startswith("-")]
    # 'reconcile' and 'audit' are cross-cutting passes, not harvest layers.
    # A full run (no args, or 'all') does harvest → reconcile → audit.
    full = not requested or requested == ["all"]
    do_reconcile = full or "reconcile" in requested
    do_audit = full or "audit" in requested
    audit_only = requested == ["audit"]
    layers = [a for a in requested if a not in ("reconcile", "audit", "all")] or None
    if layers:
        unknown = [name for name in layers if name not in LAYERS]
        if unknown:
            print(
                f"unknown layer(s): {unknown}; valid: {sorted(LAYERS)} (+ 'reconcile', 'audit')",
                file=sys.stderr,
            )
            return 2

    # Harvest + reconcile mutate Egeria; audit is read-only.
    if not audit_only and not api.enable_write:
        print("EGERIA_ENABLE_WRITE is not true — refusing to harvest.", file=sys.stderr)
        return 2

    no_harvest = audit_only or requested == ["reconcile"]
    reports = {} if no_harvest else harvest_all(api, layers)
    out: dict = {
        "env_file": loaded,
        "layers": {
            name: rep.get("summary")
            or {"skipped": rep.get("skipped") or rep.get("error")}
            for name, rep in reports.items()
        },
        "reports": reports,
    }
    if do_reconcile and not audit_only:
        from egeria_mcp.reconcile import reconcile

        rec = reconcile(api)
        out["reconcile"] = rec.get("summary") or rec
    if do_audit:
        from egeria_mcp.audit import audit

        out["audit"] = audit(api)
    print(json.dumps(out, indent=2))
    any_err = any(
        r.get("summary", {}).get("errors")
        for r in reports.values()
        if isinstance(r, dict)
    )
    return 1 if any_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
