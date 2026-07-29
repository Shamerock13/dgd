import pytest
from pydantic import ValidationError

from app.fragrance_dna import FragranceDNAMetadata, FragranceDNAProfile, FragranceDNAValues


def test_accepts_partial_dna_profile():
    profile = FragranceDNAProfile(
        values=FragranceDNAValues(woody=8.5, smoky=6.0, earthy=7.0),
        metadata=FragranceDNAMetadata(
            source="RESEARCH",
            status="REVIEW_REQUIRED",
            source_count=3,
            confidence=0.72,
            disagreement=0.18,
        ),
    )

    assert profile.values.woody == 8.5
    assert profile.values.fresh is None
    assert profile.metadata.source_count == 3


def test_rejects_scores_outside_range():
    with pytest.raises(ValidationError):
        FragranceDNAValues(smoky=10.1)


def test_rejects_completely_empty_profile():
    with pytest.raises(ValidationError):
        FragranceDNAValues()


def test_rejects_unknown_dimensions():
    with pytest.raises(ValidationError):
        FragranceDNAValues(woody=5, metallic=7)


def test_rejects_invalid_metadata_ranges():
    with pytest.raises(ValidationError):
        FragranceDNAMetadata(source="MANUAL", confidence=1.2)


def test_rejects_unapproved_source_type():
    with pytest.raises(ValidationError):
        FragranceDNAMetadata(source="AI")
