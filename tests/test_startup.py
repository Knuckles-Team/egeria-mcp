"""Smoke tests: import-safety, client tolerance, and MCP tool registration."""

import pytest


def test_api_client_import_safe_without_pyegeria(monkeypatch):
    """EgeriaApi constructs and degrades to [] without pyegeria / a platform.

    CONCEPT:EA-KG.compute.raw-rest-omvs-facade — Raw-REST OMVS Facade. CONCEPT:EA-KG.compute.bidirectional-kg-federation-powers — Bidirectional KG
    Federation (``list_data_flows``).
    """
    from egeria_mcp.api_client import EgeriaApi

    def unavailable_http(self):
        raise RuntimeError("offline test transport")

    monkeypatch.setattr(EgeriaApi, "_http", unavailable_http)
    api = EgeriaApi(
        platform_url="https://unreachable.invalid:9443",
        user_id="test-user",
        user_pwd="test-password",
    )
    # No network, no pyegeria required: list methods return empty, not raise.
    assert api.list_assets() == []
    assert api.list_glossary_terms() == []
    assert api.list_data_flows() == []
    assert api.lineage("guid-x").get("guid") == "guid-x"


@pytest.mark.parametrize(
    "user_id,user_pwd", [(None, None), ("test-user", None), (None, "test-password")]
)
def test_missing_credentials_fail_closed(user_id, user_pwd):
    from egeria_mcp.api_client import EgeriaApi

    with pytest.raises(ValueError, match="credentials are required"):
        EgeriaApi(user_id=user_id, user_pwd=user_pwd)


def test_write_disabled_by_default():
    """Write tools are gated unless EGERIA_ENABLE_WRITE is set.

    CONCEPT:EA-KG.compute.raw-rest-omvs-facade — Raw-REST OMVS Facade (write gating). CONCEPT:EA-KG.domains.bottom-up-harvest-data —
    Bottom-Up Harvest (gated behind write-enable).
    """
    from egeria_mcp.api.api_client_egeria import EgeriaApi, EgeriaWriteDisabled

    api = EgeriaApi(user_id="test-user", user_pwd="test-password", enable_write=False)
    try:
        api.classify("g", "Confidentiality", {})
        raise AssertionError("expected EgeriaWriteDisabled")
    except EgeriaWriteDisabled:
        pass


def test_get_client_from_settings(monkeypatch):
    """get_client() builds the federated EgeriaApi from the environment.

    CONCEPT:EA-KG.compute.egeria-metadata-federation-apache — Egeria Metadata Federation.
    """
    settings = {
        "EGERIA_VIEW_SERVER": "qs-view-server",
        "EGERIA_USER": "test-user",
        "EGERIA_USER_PASSWORD": "test-password",
    }
    monkeypatch.setattr(
        "egeria_mcp.auth.setting",
        lambda name, default=None: settings.get(name, default),
    )
    from egeria_mcp.auth import get_client

    api = get_client()
    assert api.view_server == "qs-view-server"
    assert api.user_id == "test-user"
    assert api.user_pwd == "test-password"
    assert api.enable_write is False
