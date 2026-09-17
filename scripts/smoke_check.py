"""Verify VCO reachability and token acceptance. Run before writing any client code.

Usage:
    export VCO_HOST=vco123-usca1.velocloud.net
    export VCO_TOKEN=...
    python scripts/smoke_check.py
"""

import sys

import httpx

from velocloud_mcp.client.auth import auth_headers
from velocloud_mcp.config import load_settings

# Ordered cheapest-first. Which of these answers depends on the token's role,
# so the script reports them all instead of assuming one.
PROBES: list[tuple[str, str, dict | None]] = [
    ("GET", "{api_base}/enterprises", None),
    ("POST", "/portal/rest/enterprise/getEnterprise", {}),
    ("POST", "/portal/rest/enterpriseProxy/getEnterpriseProxy", {}),
]


def probe(client: httpx.Client, method: str, path: str, body: dict | None) -> str:
    """Return a one-line verdict for a single probe."""
    try:
        response = client.request(method, path, json=body)
    except httpx.HTTPError as error:
        # No status code at all means the request never reached the Orchestrator.
        return f"{method} {path} -> transport failure: {type(error).__name__}: {error}"
    size = len(response.content)
    return f"{method} {path} -> HTTP {response.status_code} ({size} bytes)"


def main() -> int:
    settings = load_settings()
    base_url = f"https://{settings.host}"
    print(f"Orchestrator: {base_url}  verify_tls={settings.verify_tls}")

    with httpx.Client(
        base_url=base_url,
        headers=auth_headers(settings),
        verify=settings.verify_tls,
        timeout=settings.request_timeout,
    ) as client:
        for method, path, body in PROBES:
            print("  " + probe(client, method, path.format(api_base=settings.api_base), body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
