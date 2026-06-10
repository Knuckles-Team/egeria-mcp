"""Smoke tests: import-safety, client tolerance, and MCP tool registration."""

import os


def test_api_client_import_safe_without_pyegeria():
    """EgeriaApi constructs and degrades to [] without pyegeria / a platform.

    CONCEPT:EG-002 — Raw-REST OMVS Facade. CONCEPT:EG-007 — Bidirectional KG
    Federation (``list_data_flows``).
    """
    from egeria_mcp.api_client import EgeriaApi

    api = EgeriaApi(platform_url="https://unreachable.invalid:9443")
    # No network, no pyegeria required: list methods return empty, not raise.
    assert api.list_assets() == []
    assert api.list_glossary_terms() == []
    assert api.list_data_flows() == []
    assert api.lineage("guid-x").get("guid") == "guid-x"


def test_write_disabled_by_default():
    """Write tools are gated unless EGERIA_ENABLE_WRITE is set.

    CONCEPT:EG-002 — Raw-REST OMVS Facade (write gating). CONCEPT:EG-004 —
    Bottom-Up Harvest (gated behind write-enable).
    """
    from egeria_mcp.api.api_client_egeria import EgeriaApi, EgeriaWriteDisabled

    api = EgeriaApi(enable_write=False)
    try:
        api.classify("g", "Confidentiality", {})
        raise AssertionError("expected EgeriaWriteDisabled")
    except EgeriaWriteDisabled:
        pass


def test_get_client_from_env():
    """get_client() builds the federated EgeriaApi from the environment.

    CONCEPT:EG-001 — Egeria Metadata Federation.
    """
    os.environ["EGERIA_VIEW_SERVER"] = "qs-view-server"
    from egeria_mcp.auth import get_client

    api = get_client()
    assert api.view_server == "qs-view-server"
    assert api.enable_write is False


def test_mcp_tools_register():
    """The MCP server builds and registers the expected tool surface.

    CONCEPT:EG-005 — Broad OMVS Coverage.
    """
    import asyncio
    import inspect

    from egeria_mcp.mcp_server import get_mcp_instance

    # command_args=[] so the server's CLI parser doesn't consume pytest's argv
    # (e.g. `-p`/`--port`), which previously aborted this test with SystemExit.
    mcp, _args, _mw = get_mcp_instance(command_args=[])
    res = mcp.list_tools() if hasattr(mcp, "list_tools") else mcp.get_tools()
    if inspect.isawaitable(res):
        res = asyncio.new_event_loop().run_until_complete(res)
    names = (
        set(res.keys())
        if isinstance(res, dict)
        else {getattr(t, "name", t) for t in res}
    )
    expected = {
        "egeria_asset_search",
        "egeria_glossary_lookup",
        "egeria_glossary_categories",
        "egeria_lineage",
        "egeria_governance_for",
        "egeria_list_policies",
        "egeria_classify",
        "egeria_create_term",
        "egeria_assert_lineage",
    }
    assert expected.issubset(names), f"missing tools; got {sorted(names)}"
