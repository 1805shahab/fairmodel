"""Wire names from official Invoicing v2 schema, not the APIMatic SDK (no invoicing controller)."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class Wire(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class Money(Wire):
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    value: str = Field(pattern=r"^\d+(\.\d{1,2})?$")


class ProviderMoney(Money):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)


class Billing(Wire):
    email_address: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class Recipient(Wire):
    billing_info: Billing


class Item(Wire):
    name: str = Field(max_length=200)
    description: str = Field(max_length=1000)
    quantity: str = "1"
    unit_amount: Money


class Detail(Wire):
    invoice_number: str = Field(min_length=1, max_length=25)
    reference: str = Field(max_length=120)
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    invoice_date: str
    payment_term: dict = Field(default_factory=lambda: {"term_type": "DUE_ON_RECEIPT"})
    note: str = "PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY"


class DraftInvoice(Wire):
    detail: Detail
    primary_recipients: list[Recipient] = Field(min_length=1, max_length=1)
    items: list[Item] = Field(min_length=1, max_length=1)
    configuration: dict = Field(
        default_factory=lambda: {
            "auto_populate_invoicer": True,
            "allow_tip": False,
            "partial_payment": {"allow_partial_payment": False},
        }
    )


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)
    id: str = Field(pattern=r"^INV2-[A-Z0-9-]{4,64}$")
    status: str
    detail: dict
    invoicer: dict
    primary_recipients: list[dict]
    amount: ProviderMoney
    due_amount: ProviderMoney | None = None
    payments: dict = Field(default_factory=dict)
    refunds: dict = Field(default_factory=dict)


def money_value(value, currency):
    amount = Money.model_validate(value)
    number = Decimal(amount.value)
    if amount.currency_code != currency or not number.is_finite() or number < 0:
        raise ValueError("Invalid provider money")
    return number
