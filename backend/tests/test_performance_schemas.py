from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import FragranceCreate


def fragrance_payload(**overrides):
    payload = {
        "name": "Testduft",
        "brand_id": uuid4(),
    }
    payload.update(overrides)
    return payload


def test_accepts_empty_performance_values():
    fragrance = FragranceCreate(**fragrance_payload())

    assert fragrance.longevity_min_hours is None
    assert fragrance.performance_status == "OPEN"


def test_accepts_valid_performance_range_and_boundaries():
    fragrance = FragranceCreate(
        **fragrance_payload(
            longevity_min_hours=0,
            longevity_max_hours=72,
            longevity_score=10,
            projection=0,
            sillage=10,
            performance_score=8.4,
            performance_source_count=0,
            performance_confidence=100,
            performance_disagreement=0,
            performance_status="VERIFIED",
        )
    )

    assert fragrance.longevity_min_hours == 0
    assert fragrance.longevity_max_hours == 72
    assert fragrance.performance_confidence == 100


def test_rejects_longevity_minimum_above_maximum():
    with pytest.raises(ValidationError, match="longevity_min_hours"):
        FragranceCreate(
            **fragrance_payload(
                longevity_min_hours=9,
                longevity_max_hours=7,
            )
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("longevity_score", -0.1),
        ("projection_first_hour", 10.1),
        ("sillage", 11),
        ("performance_confidence", 100.1),
        ("performance_disagreement", -1),
        ("performance_source_count", -1),
        ("personal_longevity_hours", 72.1),
    ],
)
def test_rejects_values_outside_allowed_range(field, value):
    with pytest.raises(ValidationError):
        FragranceCreate(**fragrance_payload(**{field: value}))


def test_rejects_unknown_performance_status():
    with pytest.raises(ValidationError):
        FragranceCreate(
            **fragrance_payload(performance_status="AUTO_APPROVED")
        )
