"""Customer (enterprise) records, projected down from the Orchestrator's shape."""

from pydantic import BaseModel, Field

# Kept from GET /api/sdwan/v2/enterprises. The raw record carries contact names,
# phones and street addresses for every customer; none of it survives this function.
# Fill rates measured against 978 live customers: logicalId/name 100%,
# accountNumber 99%, city 82%. Dropped: prefix 0%, state 2%, description 0%.


class Customer(BaseModel):
    """One customer, as the rest of the server sees it."""

    logical_id: str = Field(description="UUID used by the v2 API for nested paths.")
    name: str = Field(description="Customer name as shown in the Orchestrator.")
    account_number: str | None = Field(
        default=None, description="Account number; how tickets identify a customer."
    )
    city: str | None = Field(default=None, description="Used only to disambiguate similar names.")


def project_customer(raw: dict) -> Customer:
    """Keep the few fields we use; drop the rest at the API boundary."""
    return Customer(
        logical_id=raw["logicalId"],
        name=raw["name"],
        account_number=raw.get("accountNumber") or None,
        city=raw.get("city") or None,
    )