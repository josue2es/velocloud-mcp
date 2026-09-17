"""Runtime configuration, read once from the environment at startup."""

import os

from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv

load_dotenv(override=False)  # read .env file if present

class Settings(BaseModel):
    """Everything the server needs to reach one Orchestrator."""

    model_config = ConfigDict(frozen=True)

    host: str                                   # e.g. "vco123-usca1.velocloud.net"
    token: str                                  # API token (a JWT) from the VCO UI
    verify_tls: bool = True
    api_base: str = "/api/sdwan/v2"             # "/sdwan" on Orchestrators older than 5.0.0.0
    request_timeout: float = 30.0
    diag_timeout: float = 30.0                  # tune from measured p95, not from feel
    max_in_flight: int = 3                      # vendor asks for 2-4 concurrent calls
    allowed_enterprises: frozenset[str] = frozenset()   # empty means "no restriction"


class MissingSetting(RuntimeError):
    """Raised at startup when a required environment variable is absent."""


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingSetting(f"{name} is not set")
    return value


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes"}


def _csv(name: str) -> frozenset[str]:
    raw = os.environ.get(name, "")
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def load_settings() -> Settings:
    """Build Settings from the environment. Raises MissingSetting if incomplete."""
    return Settings(
        host=_required("VCO_HOST").removeprefix("https://").rstrip("/"),
        token=_required("VCO_TOKEN"),
        verify_tls=_flag("VCO_VERIFY_TLS", True),
        api_base=os.environ.get("VCO_API_BASE", "/api/sdwan/v2"),
        request_timeout=float(os.environ.get("VCO_REQUEST_TIMEOUT", "30")),
        diag_timeout=float(os.environ.get("VCO_DIAG_TIMEOUT", "30")),
        max_in_flight=int(os.environ.get("VCO_MAX_IN_FLIGHT", "3")),
        allowed_enterprises=_csv("VCO_ALLOWED_ENTERPRISES"),
    )
