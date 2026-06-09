# Usage — API / CLI / MCP

`egeria-mcp` exposes the same capability three ways: as **MCP tools** an agent calls,
as a **Python API** (`EgeriaApi`) you import, and as a **harvest CLI**. The complete
tool surface and the verified Egeria 6.0 REST contract are in [Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server registers 21 tools. Reads work with no
configuration beyond the platform connection; writes require `EGERIA_ENABLE_WRITE=true`.

| Group | Tools |
|---|---|
| Granular reads | `egeria_asset_search`, `egeria_glossary_lookup`, `egeria_glossary_categories`, `egeria_lineage`, `egeria_governance_for`, `egeria_list_policies` |
| Broad action-dispatch reads | `egeria_catalog`, `egeria_data_design`, `egeria_collection`, `egeria_solution`, `egeria_governance_catalog`, `egeria_actors`, `egeria_metadata` |
| Routing | `egeria_governed_route` |
| Write-gated | `egeria_classify`, `egeria_create_term`, `egeria_assert_lineage`, `egeria_harvest` |

Example agent prompts that map onto these tools:

- *"Search the catalog for assets named like 'customer'"* → `egeria_asset_search`
- *"What is the downstream lineage impact of asset `<guid>`?"* → `egeria_lineage`
- *"Is it safe to act on asset `<guid>`?"* → `egeria_governed_route`

## As a Python API

`EgeriaApi` is a tolerant raw-`httpx` facade — every call degrades to `[]` / a clear
error rather than raising, so it is safe to use without a reachable platform.

```python
from egeria_mcp.api.api_client_egeria import EgeriaApi

api = EgeriaApi(
    platform_url="https://your-egeria:9443",
    view_server="qs-view-server",
    user_id="erinoverview",
    user_pwd="secret",
    verify_ssl=False,
)

# Reads
assets = api.asset_search("customer")          # flat records with GUIDs
terms = api.list_glossary_terms()
flows = api.list_data_flows()                  # DataFlow lineage edges
gov = api.governance_for(assets[0]["guid"])    # confidentiality, etc.

# The federation decision
from egeria_mcp.governed_routing import governed_route
decision = governed_route(api, assets[0]["guid"])
print(decision["decision"])                    # proceed | review | require_approval
```

Build a client straight from the environment:

```python
from egeria_mcp.auth import get_client
api = get_client()        # reads EGERIA_* from the environment / .env
```

### Writes

Writes are gated behind `enable_write` (env: `EGERIA_ENABLE_WRITE=true`):

```python
api = EgeriaApi(enable_write=True, ...)
api.create_term("Customer", "A party that purchases goods or services")
api.classify(guid, "Confidentiality", {"confidentialityLevel": 3})
api.assert_lineage(source_guid, target_guid, label="DataFlow")
```

## As a harvest CLI

The **bottom-up harvest** populates Egeria *from* your data estate (needs writes
enabled). Run a single layer or `all`:

```bash
EGERIA_PLATFORM_URL=https://your-egeria:9443 EGERIA_ENABLE_WRITE=true \
  python -m egeria_mcp.harvest datastores      # the anchor layer

# Cross-link the independently harvested layers into one graph
EGERIA_ENABLE_WRITE=true python -m egeria_mcp.harvest reconcile

# Coverage report (read-only): islands + per-layer lineage %
python -m egeria_mcp.harvest audit
```

Each connector reads its own credentials (see
[`.env.example`](https://github.com/Knuckles-Team/egeria-mcp/blob/main/.env.example))
and is a no-op when those are blank. The full source → Egeria-type → confidentiality
map for all 34 layers is in [Harvesters](harvesters.md).
