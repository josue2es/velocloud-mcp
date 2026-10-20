"""Runtime configuration, read once from the environment at startup."""

import os
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, SecretStr, field_validator
from dotenv import load_dotenv

load_dotenv(override=False)  # read .env file if present

class Settings(BaseModel):
    """Everything the server needs to reach one Orchestrator."""

    model_config = ConfigDict(frozen=True)

    host: str                                   # e.g. "vco123-usca1.velocloud.net"
    token: SecretStr                            # API token (a JWT); masked in repr, str and errors
    verify_tls: bool = True
    api_base: str = "/api/sdwan/v2"             # "/sdwan" on Orchestrators older than 5.0.0.0
    request_timeout: PositiveFloat = 30.0      # 0 would make every socket non-blocking
    diag_timeout: Annotated[float, Field(gt=0, le=300)] = 30.0   # WebSocket idles out at ~300 s; tune from p95
    max_in_flight: Annotated[int, Field(ge=1, le=4)] = 3   # vendor asks for at most 4 in flight
    allowed_enterprises: frozenset[str] = frozenset()   # empty means "no restriction"

    @field_validator("host")
    @classmethod
    def require_bare_hostname(cls, host: str) -> str:
        """A scheme or path makes httpx dial a host named 'https' or prefix every request path."""
        if "/" in host:
            raise ValueError(f"must be a bare hostname such as vco99.example.net, got {host!r}")
        return host


class MissingSetting(RuntimeError):
    """Raised at startup when a required environment variable is absent."""


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingSetting(f"{name} is not set")
    return value


def _csv(name: str) -> frozenset[str]:
    raw = os.environ.get(name, "")
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


# Settings field -> environment variable, for every field that has a default in Settings.
_OPTIONAL_VARIABLES = {
    "verify_tls": "VCO_VERIFY_TLS",
    "api_base": "VCO_API_BASE",
    "request_timeout": "VCO_REQUEST_TIMEOUT",
    "diag_timeout": "VCO_DIAG_TIMEOUT",
    "max_in_flight": "VCO_MAX_IN_FLIGHT",
}


def _env_overrides(variables: dict[str, str]) -> dict[str, str]:
    """Raw strings for the variables that are set. Unset ones are omitted so the model default applies."""
    return {field: os.environ[name] for field, name in variables.items() if name in os.environ}


def load_settings() -> Settings:
    """Build Settings from the environment.

    Raises MissingSetting if a required variable is absent, and pydantic's
    ValidationError if any variable is set to a value that does not parse.
    """
    return Settings(
        host=_required("VCO_HOST"),
        token=_required("VCO_TOKEN"),
        allowed_enterprises=_csv("VCO_ALLOWED_ENTERPRISES"),
        **_env_overrides(_OPTIONAL_VARIABLES),
    )
