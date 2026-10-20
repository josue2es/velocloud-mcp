"""Tests for the API token: it must reach the Orchestrator and nowhere else."""

from velocloud_mcp.client.auth import auth_headers
from velocloud_mcp.config import Settings

TOKEN = "eyJhbGciOiJIUzI1NiJ9.pretend-this-is-real"


def build_settings() -> Settings:
    return Settings(host="vco99.example.net", token=TOKEN)


def test_token_is_hidden_from_repr_and_str():
    """repr ends up in tracebacks, logs and saved notebook outputs."""
    settings = build_settings()
    assert TOKEN not in repr(settings)
    assert TOKEN not in str(settings)


def test_auth_header_carries_the_real_token():
    """Masking the token must not mask it from the one place that needs it."""
    assert auth_headers(build_settings())["Authorization"] == f"Token {TOKEN}"
