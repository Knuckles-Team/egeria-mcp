"""egeria-mcp: Apache Egeria open-metadata API + MCP Server.

Granular, typed Egeria tools (lineage / glossary / asset / governance) plus the
``EgeriaApi`` client used as the injected ``config["client"]`` for the KG
``egeria`` enrichment extractor.

CONCEPT:EA-KG.compute.egeria-metadata-federation-apache — Egeria Metadata Federation. Apache Egeria is the
metadata/governance/lineage system-of-record, federated with the epistemic-graph
KG. Two invariants: the KG is never the lineage store; Egeria never orchestrates.
"""

import importlib
import inspect
from typing import Any

__version__ = "2.1.0"
__all__: list[str] = []

CORE_MODULES = ["egeria_mcp.api_client"]
OPTIONAL_MODULES = {
    "egeria_mcp.mcp_server": "mcp",
}


def _expose_members(module):
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            globals()[name] = obj
            if name not in __all__:
                __all__.append(name)


for module_name in CORE_MODULES:
    module = importlib.import_module(module_name)
    _expose_members(module)

_loaded_optional_modules: dict[str, Any] = {}


def _import_module_safely(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


_UNRESOLVED = object()


def _mcp_available() -> bool:
    mcp_key = next((k for k in OPTIONAL_MODULES if "mcp_server" in k), None)
    return _import_module_safely(mcp_key) is not None if mcp_key else False


def _ensure_optional_module_loaded(module_name: str):
    """Import + expose ``module_name``'s members once; return it (or None)."""
    if module_name not in _loaded_optional_modules:
        module = _import_module_safely(module_name)
        if module is not None:
            _loaded_optional_modules[module_name] = module
            _expose_members(module)
    return _loaded_optional_modules.get(module_name)


def _resolve_optional_attr(name: str) -> Any:
    """``name`` from the first optional module that defines it, else ``_UNRESOLVED``."""
    for module_name in OPTIONAL_MODULES:
        module = _ensure_optional_module_loaded(module_name)
        if module is not None and hasattr(module, name):
            return getattr(module, name)
    return _UNRESOLVED


def __getattr__(name: str) -> Any:
    if name == "_MCP_AVAILABLE":
        return _mcp_available()

    resolved = _resolve_optional_attr(name)
    if resolved is not _UNRESOLVED:
        return resolved
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
