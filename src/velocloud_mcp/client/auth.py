"""Authentication headers for the VeloCloud Orchestrator API."""

from velocloud_mcp.config import Settings


def auth_headers(settings: Settings) -> dict[str, str]:
    """Token auth: the Orchestrator expects the API token in an Authorization header."""
    return {
        "Authorization": f"Token {settings.token}",
        "Content-Type": "application/json",
    }
