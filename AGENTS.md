# egeria-mcp — AGENTS

> Claude Code loads this file via `CLAUDE.md` (`@AGENTS.md` import) — the two stay
> in sync. Edit **this** file, not `CLAUDE.md`.

## What this is

`egeria-mcp` is the **API + MCP server** for Apache Egeria (the OMAG open-metadata
platform), federated into the agent-utilities ecosystem as the
**metadata / governance / lineage system-of-record** alongside the epistemic-graph
Knowledge Graph (the cognition/orchestration plane).

Two hard invariants of the federation:
- **The KG never becomes the lineage store** — Egeria is system-of-record for data
  lineage, business glossary, and data-governance classifications.
- **Egeria never orchestrates** — `graph_orchestrate` / the policy router stay the
  orchestration brain; Egeria is the metadata oracle they *query* and write
  provenance back to.

## Project Structure
- `egeria_mcp/api/api_client_egeria.py` — `EgeriaApi`, a tolerant **raw-httpx REST**
  facade over the Egeria View Server (OMVS). Organized by OMVS service; every call
  degrades to `[]` / a clear error rather than raising.
- `egeria_mcp/mcp/mcp_egeria.py` — thin FastMCP tool wrappers (read, write-gated,
  harvest, governed-routing). No business logic — all API surface lives in `api/`.
- `egeria_mcp/governed_routing.py` — `governed_route()`: the federation delivering a
  policy-aware decision (proceed / review / require_approval) from Egeria
  governance + lineage.
- `egeria_mcp/harvest/` — bottom-up connectors that **populate** Egeria from the data
  estate (data stores first, then ERPNext/Camunda/GitLab). `topology.py` is the
  declared estate; `datastores.py` is the substrate/anchor harvest.
- `egeria_mcp/auth.py` — `get_client()` builds an `EgeriaApi` from the environment.

## Tech Stack
- Python 3.11+ (raw `httpx` REST — **no pyegeria runtime dependency**; pyegeria's
  sync wrappers call `asyncio.get_event_loop()`, which raises on Python 3.14).
- agent-utilities `[mcp]` (FastMCP, `create_mcp_server`).
- Apache Egeria 6.0 OMAG platform / View Server (OMVS) REST.

## Egeria REST contract (confirmed against Egeria 6.0)
- Token: `POST {platform}/api/token` `{userId,password}` → bearer JWT.
- Find: `POST {platform}/servers/{view_server}/api/open-metadata/{service}/{noun}/by-search-string`
  with `{"class":"SearchStringRequestBody","searchString": <term>}`. **Empty string =
  match-all**; `.*` matches nothing (it is a contains/regex match, not "any").
- Create: `POST .../{service}/{noun}` with a `NewElementRequestBody`
  (`properties.class` is the typed properties bean, e.g. `AssetProperties`).
- Read-back with classifications: `POST .../asset-maker/assets/{guid}/retrieve`
  `{"class":"AnyTimeRequestBody"}` → `element.elementHeader.<name>` (each
  classification is a *named* `ElementClassification`, not a list).
- Classify: `POST .../classification-explorer/elements/{guid}/{classification}`
  (the bean field is `confidentialityLevel`, **not** `levelIdentifier`).
- Lineage: `POST .../lineage-linker/from-elements/{a}/via/DataFlow/to-elements/{b}/attach`;
  read via `.../asset-catalog/assets/{guid}/as-lineage-graph` → edges in
  `element.lineageLinkage`.

## Commands
- `pytest` — run tests
- `pre-commit run --all-files` — lint
- `python -m egeria_mcp.harvest` — run the data-store harvest (needs
  `EGERIA_ENABLE_WRITE=true`)

## Configuration (environment)
`EGERIA_PLATFORM_URL`, `EGERIA_VIEW_SERVER`, `EGERIA_USER`, `EGERIA_USER_PASSWORD`,
`EGERIA_VERIFY_SSL` (default False — self-signed homelab), `EGERIA_ENABLE_WRITE`
(default False — gates every write/harvest tool), `EGERIATOOL` (default True).

## Conventions
- All write tools are gated by `EGERIA_ENABLE_WRITE`; never write unless enabled.
- MCP tool tags are strictly lowercase with hyphens (e.g. `tags={"governance"}`).
- Keep `api/` the single source of API surface; `mcp/` tools add no logic.
- Federation key: every Egeria-sourced KG node carries `externalToolId` (the Egeria
  GUID) + `domain="egeria"` (see the KG `egeria` extractor in agent-utilities).

## Concept Registry
Stable concept IDs (prefix `CONCEPT:EG-*`) trace the federation's core ideas across
`docs/concepts.md`, code docstrings, and pytest markers. Full descriptions live in
[`docs/concepts.md`](docs/concepts.md); keep both in sync.

<!-- CONCEPT:EA-KG.compute.egeria-metadata-federation-apache --> **EA-KG.compute.egeria-metadata-federation-apache** Egeria Metadata Federation — `egeria_mcp/__init__.py`
<!-- CONCEPT:EA-KG.compute.raw-rest-omvs-facade --> **EA-KG.compute.raw-rest-omvs-facade** Raw-REST OMVS Facade — `EgeriaApi` (`api/api_client_egeria.py`)
<!-- CONCEPT:EA-KG.compute.governed-routing-turns-egeria --> **EA-KG.compute.governed-routing-turns-egeria** Governed Routing — `governed_route()` (`governed_routing.py`)
<!-- CONCEPT:EA-KG.domains.bottom-up-harvest-data --> **EA-KG.domains.bottom-up-harvest-data** Bottom-Up Harvest — `harvest_datastores()` (`harvest/datastores.py`)
<!-- CONCEPT:EA-KG.maintenance.broad-omvs-coverage-action --> **EA-KG.maintenance.broad-omvs-coverage-action** Broad OMVS Coverage — `register_egeria_tools()` (`mcp/mcp_egeria.py`)
<!-- CONCEPT:EA-KG.compute.cross-reconciliation-weaves-independently --> **EA-KG.compute.cross-reconciliation-weaves-independently** Cross-Layer Reconciliation — `reconcile()` (`reconcile.py`)
<!-- CONCEPT:EA-KG.compute.bidirectional-kg-federation-powers --> **EA-KG.compute.bidirectional-kg-federation-powers** Bidirectional KG Federation — `EgeriaApi.list_data_flows()`
<!-- CONCEPT:EA-KG.compute.completeness-audit-reports-unlinked --> **EA-KG.compute.completeness-audit-reports-unlinked** Completeness Audit — `audit()` (`audit.py`)
<!-- CONCEPT:AU-KG.ingest.then-by-its-node --> **AU-KG.ingest.then-by-its-node** Vendor-Neutral Capability Tagging — `_capability_of()` (`reconcile.py`)

## ⛔ Keep the Repository Root Pristine
The repository ROOT must contain only canonical project files (packaging, config,
docs, lockfiles). Never write debug/migration/scratch scripts, data dumps, logs, or
build artifacts to the repo — scratch goes in `~/workspace/scratch/`, command output
in `~/workspace/reports/`, tests in `tests/` only. Run `git status` before finishing.

## Working Discipline — think, simplify, stay surgical, verify

These four habits cut the most common LLM coding mistakes. For trivial tasks, use
judgment; the bias here is correctness over speed.

- **Think before coding.** State your assumptions explicitly. If a request has more than
  one reasonable reading, surface the options instead of silently picking one. If a
  simpler approach exists, say so and push back when warranted. When something is
  genuinely unclear, stop and name what's confusing — ask, don't guess.
- **Simplicity first.** Write the minimum code that solves the stated problem — no
  speculative features, no abstraction for single-use code, no configurability that
  wasn't requested, no error handling for impossible states. If you wrote 200 lines and
  it could be 50, rewrite it. (Name code from its purpose, never `wave0`/`phase2`/`v2`.)
- **Stay surgical.** Every changed line should trace directly to the task. Don't refactor,
  reformat, or "improve" working code adjacent to your change; match the existing style
  even where you'd do it differently. Remove only the imports/symbols your own change
  orphaned; if you spot unrelated dead code, mention it rather than deleting it inline.
  *Exception — the Quality Bar below:* lint/format/type errors the pre-commit gate flags
  get fixed regardless of who introduced them. In short: **surgical on behavior, clean on
  lint.**
- **Verify against a goal.** Turn the task into a checkable outcome before you start:
  "fix the bug" → "write a failing test that reproduces it, then make it pass"; "add
  validation" → "tests for the invalid inputs pass". For multi-step work, state the short
  plan and the check for each step, then loop until the checks pass.

## Quality Bar — Leave the Codebase Clean (REQUIRED)

After completing any code change, run the project's pre-commit suite and drive it
**fully green** before committing:

```bash
pre-commit run --all-files
```

Resolve **every** issue it reports — failures, lint errors, type errors, and
warnings — **including problems that pre-date your change and were not caused by
your edits**. The standing goal is a clean, working codebase with **no errors and
no warnings**. Do not silence checks (`# noqa`, `# type: ignore`, `SKIP=`,
`--no-verify`) to force green unless the exception is already documented in this
file as a known, unavoidable limitation. Only commit once `pre-commit run
--all-files` passes cleanly; if a check legitimately cannot pass, stop and explain
why rather than bypassing it.

## Working with Git Worktrees (multi-session)

Multiple agents/sessions work the `agent-packages/*` repos concurrently. **Do not
edit the canonical checkout** (`/home/apps/workspace/agent-packages/<repo>`) — a
background `repository-manager` sync can reset its working tree and discard
uncommitted edits. Take your own git worktree on your own branch instead:

```bash
# preferred — repository-manager MCP:
rm_worktree add <repo> <your-branch>      # -> /home/apps/worktrees/<repo>/<your-branch>

# raw-git fallback:
git -C agent-packages/<repo> checkout main
git -C agent-packages/<repo> worktree add /home/apps/worktrees/<repo>/<branch> -b <branch>
```

Work in the worktree and **commit often** (commits survive a working-tree reset).
Each session must use a **distinct branch** — git allows a branch in only one
worktree, which is what keeps concurrent sessions from colliding. Worktrees live
under `/home/apps/worktrees/` (outside the workspace scan, so the sync leaves them
alone).

**Finishing work in a worktree** — run this sequence before calling it done:
1. **Pre-commit green** — `pre-commit run --all-files`; resolve every issue per the
   Quality Bar above (including pre-existing), no `--no-verify`.
2. **Commit** in the worktree.
3. **Merge to main locally** — `rm_worktree merge <repo> <branch> --into main`
   (or `git merge --no-ff`). Push only when the user asks.
4. **Clean up** — remove the worktree and delete the merged branch:
   `rm_worktree remove <repo> <branch> --delete-branch`; `rm_worktree prune` clears
   stale entries. (Raw-git: `git worktree remove <path> && git branch -d <branch>`.)

<!-- BEGIN concept-coordination (generated) -->
## Concept-ID Coordination (multi-session)

Working in parallel with other sessions/worktrees? **Reserve a concept id before you write its `CONCEPT:` marker** so two sessions never collide:

```bash
agent-utilities --json concept reserve --ns EG-KG.compute.backend   # or a package prefix, e.g. KEY
```

Full protocol (ledger, merge=union, reconcile, MCP/REST): <https://knuckles-team.github.io/agent-utilities/concept_coordination/>
<!-- END concept-coordination (generated) -->

## Version & lockfile drift edict (keep the version mirrors AND the lock in sync)

The two most common release-breakers in this fleet are **version drift** (the version in
`pyproject.toml`/`.bumpversion.cfg` advancing while `README.md`, `docker/Dockerfile`, and the
module `__version__`s lag) and a **stale `uv.lock`** (shipping known-vulnerable transitive deps).
A version mismatch makes the next `bump-my-version` throw `VersionNotFoundException`; a stale lock
is what Dependabot flags. Rules:

1. **Never hand-edit a version string.** Change the version ONLY via
   `bump-my-version bump {patch|minor|major}` (a.k.a. `bump2version`), which rewrites every file
   registered in `.bumpversion.cfg` in one atomic, tagged commit. If you edited the version in
   `pyproject.toml` by hand, you created drift — revert and use the bumper.
2. **Every version-bearing file must be registered in `.bumpversion.cfg`** — at minimum
   `pyproject.toml` AND `README.md`, plus `docker/Dockerfile` and any module `__version__`. Never
   add a file that embeds the version without a `[bumpversion:file:...]` entry for it.
3. **Re-lock on every dependency change.** After editing `pyproject.toml` deps/extras, run
   `uv lock` and commit `uv.lock` in the SAME change. The `uv-lock` pre-commit hook runs with
   `--locked` and fails on drift — never bypass it. The committed `uv.lock` is the
   Dependabot/security surface.
4. **Patch CVEs with a version floor at the source, then re-lock.** `uv` resolves one version
   graph-wide, so a lower-bound in the extra that pulls a dependency raises it for the whole lock.
