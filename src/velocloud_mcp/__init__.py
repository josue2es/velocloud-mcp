"""MCP server for the Arista VeloCloud SD-WAN Orchestrator.

Read-only inventory and health, plus safe Edge diagnostics
(ping, traceroute, route table, paths, interfaces, active flows).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    # Single source of truth: the version declared in pyproject.toml,
    # read back from the installed package metadata.
    __version__ = version("velocloud-mcp")
except PackageNotFoundError:
    # Importable but never installed — a source checkout on PYTHONPATH.
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
