"""Record live Orchestrator responses as test fixtures, projected before writing."""

import asyncio
import json
from pathlib import Path

from velocloud_mcp.client.rest import VcoClient
from velocloud_mcp.config import load_settings

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"

# Only these keys survive into a fixture. An allowlist, not a denylist: a field
# added by a future Orchestrator release is excluded by default rather than
# included until someone notices it carries personal data.
ENTERPRISE_KEYS = ("logicalId", "name", "accountNumber", "city")


def redact_enterprise(raw: dict, index: int) -> dict:
    """Keep only the allowlisted keys, and replace every identifying value."""
    return {
        "logicalId": f"00000000-0000-4000-8000-{index:012d}",
        "name": f"Test Customer {index:03d}",
        "accountNumber": None if raw.get("accountNumber") is None else f"ACCT-{index:05d}",
        "city": raw.get("city"),
    }


async def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    client = VcoClient(load_settings())
    try:
        # Ten records is enough to exercise projection and resolution.
        sample = [
            redact_enterprise(raw, index)
            for index, raw in enumerate((await client.enterprises())[:10])
        ]
        path = FIXTURES / "enterprises.json"
        path.write_text(json.dumps(sample, indent=2) + "\n")
        print(f"wrote {len(sample)} redacted records to {path}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())