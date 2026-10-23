"""The governed HTTP client every Egeria harvest and OMVS call goes through."""

from __future__ import annotations

import httpx
from agent_connector_sdk.http.client import create_http_client
from agent_connector_sdk.http.options import HttpClientOptions
from agent_connector_sdk.tls.profile import ResolvedTLSProfile
from agent_connector_sdk.tls.resolve import resolve_tls_profile

__all__ = ["governed_client"]


def governed_client(
    base_url: str,
    *,
    timeout: float = 20.0,
    tls_profile: ResolvedTLSProfile | None = None,
) -> httpx.Client:
    """A governed client for one source; the TLS profile defaults to ``EGERIA``.

    Harvest sources sit on the internal network, so plaintext HTTP is allowed.
    """
    return create_http_client(
        HttpClientOptions(
            base_url=base_url,
            timeout=timeout,
            tls=tls_profile or resolve_tls_profile("EGERIA"),
            allow_plaintext=True,
        )
    )
