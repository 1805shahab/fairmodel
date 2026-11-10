import importlib.util
from pathlib import Path
import pytest
from decimal import Decimal
from sqlalchemy import select, func
from app.db import License, Asset, Royalty, Invoice, PaymentEvent, OverlapReview, Audit, get_session
from app.main import app


def test_three_first_party_scenarios_are_repeatable_and_preserve_existing_data(client, artist):
    source = Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py"
    if not (source.parents[1] / "backend" / "fixtures" / "scenarios.json").is_file():
        pytest.skip("Generate the first-party scenarios with scripts/create-scenarios.ps1.")
    spec = importlib.util.spec_from_file_location("readiness_seed", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    existing = client.post(
        "/api/licenses",
        headers=artist,
        json={"title": "Existing owner record must remain untouched", "studio_id": "studio_demo"},
    ).json()

    def counts():
        generator = app.dependency_overrides[get_session]()
        db = next(generator)
        try:
            return {
                model.__tablename__: db.scalar(select(func.count()).select_from(model))
                for model in (License, Asset, Royalty, Invoice, PaymentEvent, OverlapReview, Audit)
            }
        finally:
            generator.close()

    first = module.seed_scenarios(client)
    before = counts()
    second = module.seed_scenarios(client)
    assert first == second and counts() == before
    assert client.get(f"/api/licenses/{existing['id']}", headers=artist).json()["status"] == "DRAFT"
    assert [case["status"] for case in first["scenarios"]] == [
        "COMPLIANT",
        "ADDITIONAL_ROYALTY_DUE",
        "RESTRICTED_USAGE",
    ]
    assert first["scenarios"][0]["additional_royalty"] == "0.00" and not first["scenarios"][0]["invoice_id"]
    expected = ((Decimal(first["scenarios"][1]["spoken_seconds"]) - Decimal("30")) * Decimal("2")).quantize(
        Decimal("0.01")
    )
    assert (
        first["scenarios"][1]["additional_royalty"] == str(expected) and first["scenarios"][1]["invoice_id"]
    )
    assert not first["scenarios"][2]["invoice_id"]
    assert before["invoices"] == 1 and before["payment_events"] == 1
    for case in first["scenarios"]:
        detail = client.get(f"/api/assets/{case['asset_id']}", headers=artist).json()
        assert detail["processing_state"] == "ANALYZED"
        assert detail["report"]["result"]["assessment_fixture"]
        assert detail["analysis"]["result"]["demo_fixture"]
        assert detail["analysis"]["result"]["provider"] == "demo_fixture (not Groq)"
