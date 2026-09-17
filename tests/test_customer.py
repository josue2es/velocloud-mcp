"""Tests for the customer projection, against recorded fixtures."""

import json
from pathlib import Path

import pytest

from velocloud_mcp.domain.customer import project_customer
from velocloud_mcp.domain.roster import CustomerRoster

FIXTURE = Path(__file__).parent / "fixtures" / "enterprises.json"


@pytest.fixture
def raw_enterprises() -> list[dict]:
    return json.loads(FIXTURE.read_text())


def test_projection_keeps_only_the_four_fields(raw_enterprises):
    """The projection is the privacy boundary: nothing else may survive it."""
    customer = project_customer(raw_enterprises[0])
    assert set(customer.model_dump()) == {"logical_id", "name", "account_number", "city"}


def test_projection_drops_unlisted_fields():
    """A field the Orchestrator adds later must not leak through."""
    customer = project_customer(
        {
            "logicalId": "abc",
            "name": "Acme",
            "contactEmail": "someone@example.com",
            "streetAddress": "1 Main St",
        }
    )
    assert "someone@example.com" not in customer.model_dump_json()
    assert "1 Main St" not in customer.model_dump_json()


def test_empty_strings_become_none():
    """Two spellings of 'absent' is one too many for a resolver downstream."""
    customer = project_customer({"logicalId": "abc", "name": "Acme", "city": ""})
    assert customer.city is None


@pytest.mark.asyncio
async def test_roster_fetches_once_for_concurrent_callers(raw_enterprises):
    """Ten callers, one fetch: the stampede guard holds."""
    import asyncio

    calls = 0

    async def fetch() -> list[dict]:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)          # a real fetch always yields
        return raw_enterprises

    roster = CustomerRoster(fetch)
    await asyncio.gather(*(roster.customers() for _ in range(10)))
    assert calls == 1