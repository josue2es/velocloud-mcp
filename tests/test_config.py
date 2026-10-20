"""Tests for configuration loading: bad values must fail loudly, never fall back silently."""

import pytest
from pydantic import ValidationError

from velocloud_mcp.config import Settings, load_settings


@pytest.fixture(autouse=True)
def required_settings(monkeypatch):
    """Every test starts with the two required variables set and the optional ones under test unset."""
    monkeypatch.setenv("VCO_HOST", "vco99.example.net")
    monkeypatch.setenv("VCO_TOKEN", "test-token")
    monkeypatch.delenv("VCO_VERIFY_TLS", raising=False)
    monkeypatch.delenv("VCO_MAX_IN_FLIGHT", raising=False)
    monkeypatch.delenv("VCO_REQUEST_TIMEOUT", raising=False)
    monkeypatch.delenv("VCO_DIAG_TIMEOUT", raising=False)


def test_verify_tls_defaults_to_true_when_unset():
    assert load_settings().verify_tls is True


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("true", True), ("yes", True), ("on", True), ("1", True),
     ("false", False), ("no", False), ("off", False), ("0", False)],
)
def test_verify_tls_accepts_known_spellings(monkeypatch, raw, expected):
    monkeypatch.setenv("VCO_VERIFY_TLS", raw)
    assert load_settings().verify_tls is expected


@pytest.mark.parametrize("raw", ["treu", "flase", ""])
def test_verify_tls_rejects_unknown_spellings(monkeypatch, raw):
    """A typo must stop startup. Falling back to False would silently disable certificate checks."""
    monkeypatch.setenv("VCO_VERIFY_TLS", raw)
    with pytest.raises(ValidationError, match="verify_tls"):
        load_settings()


@pytest.mark.parametrize("raw", ["1", "3", "4"])
def test_max_in_flight_accepts_the_vendor_range(monkeypatch, raw):
    monkeypatch.setenv("VCO_MAX_IN_FLIGHT", raw)
    assert load_settings().max_in_flight == int(raw)


@pytest.mark.parametrize("raw", ["0", "-1", "5"])
def test_max_in_flight_rejects_values_outside_the_vendor_range(monkeypatch, raw):
    """0 hangs every call forever; above 4 exceeds what the Orchestrator asks for."""
    monkeypatch.setenv("VCO_MAX_IN_FLIGHT", raw)
    with pytest.raises(ValidationError, match="max_in_flight"):
        load_settings()


@pytest.mark.parametrize("raw", ["0", "-1"])
def test_request_timeout_rejects_zero_and_negative(monkeypatch, raw):
    """At the socket level 0 means non-blocking: every request fails at once, blaming the network."""
    monkeypatch.setenv("VCO_REQUEST_TIMEOUT", raw)
    with pytest.raises(ValidationError, match="request_timeout"):
        load_settings()


@pytest.mark.parametrize("raw", ["0", "301"])
def test_diag_timeout_rejects_values_outside_the_websocket_window(monkeypatch, raw):
    """The diagnostics WebSocket idles out at ~300 s; a longer wait can never complete."""
    monkeypatch.setenv("VCO_DIAG_TIMEOUT", raw)
    with pytest.raises(ValidationError, match="diag_timeout"):
        load_settings()


def test_timeouts_accept_fractional_seconds(monkeypatch):
    monkeypatch.setenv("VCO_REQUEST_TIMEOUT", "0.5")
    monkeypatch.setenv("VCO_DIAG_TIMEOUT", "300")
    settings = load_settings()
    assert (settings.request_timeout, settings.diag_timeout) == (0.5, 300.0)


@pytest.mark.parametrize("raw", ["vco99.example.net", "vco99.example.net:8443"])
def test_host_accepts_a_bare_hostname(raw):
    assert Settings(host=raw, token="t").host == raw


@pytest.mark.parametrize("raw", ["https://vco99.example.net", "vco99.example.net/portal/"])
def test_host_rejects_schemes_and_paths(raw):
    """Entered once, so a clear error beats silent repair: the fix is one edit to .env."""
    with pytest.raises(ValidationError, match="host"):
        Settings(host=raw, token="t")
