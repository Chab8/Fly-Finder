import base64
import json
from types import SimpleNamespace

import httpx
import pytest
from pydantic import ValidationError

from app.core.errors import ProviderResponseError, ProviderUnavailableError
from app.schemas.ai import FlyVisionResult, OrganismVisionResult
from app.services.ai.gemini import GeminiVisionAnalyzer, inline_json_schema
from app.services.images.processing import process_image
from tests.conftest import make_image_bytes

VALID_ORGANISM = {
    "subject_type": "real_organism",
    "image_quality": "good",
    "candidates": [{"scientific_name": "Baetis", "rank": "genus", "confidence": "moderate", "visual_evidence": "two tails"}],
    "life_stage": "nymph",
    "life_stage_confidence": "moderate",
}


class FakeInteractions:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.kwargs = text, error, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.text)


def analyzer(text=None, error=None):
    interactions = FakeInteractions(text, error)
    client = SimpleNamespace(interactions=interactions)
    return GeminiVisionAnalyzer(api_key="test", model="gemini-test", timeout_seconds=5, client=client), interactions


@pytest.fixture
def image():
    return process_image(make_image_bytes(), max_bytes=20 * 1024 * 1024)


def test_inline_schema_has_no_refs():
    text = json.dumps(inline_json_schema(FlyVisionResult))
    assert "$ref" not in text and "$defs" not in text
    assert "artificial_fly" in text


def test_valid_response_is_parsed_and_request_is_well_formed(image):
    gemini, calls = analyzer(json.dumps(VALID_ORGANISM))
    result = gemini.analyze_organism(image)
    assert result.candidates[0].scientific_name == "Baetis"
    assert calls.kwargs["model"] == "gemini-test"
    assert calls.kwargs["timeout"] == 5
    assert calls.kwargs["response_format"]["mime_type"] == "application/json"
    image_part = calls.kwargs["input"][1]
    assert image_part["mime_type"] == "image/jpeg"
    assert base64.b64decode(image_part["data"]) == image.jpeg_bytes


def test_known_patterns_are_given_to_the_model(image):
    gemini, calls = analyzer(json.dumps({"subject_type": "artificial_fly", "image_quality": "good"}))
    gemini.analyze_fly(image, ["Adams", "Zebra Midge"])
    assert "Adams, Zebra Midge" in calls.kwargs["input"][0]["text"]


@pytest.mark.parametrize("text", ["not json", json.dumps({"subject_type": "alien", "image_quality": "good"}), ""])
def test_invalid_or_empty_response_is_rejected(image, text):
    gemini, _ = analyzer(text)
    with pytest.raises(ProviderResponseError):
        gemini.analyze_organism(image)


def test_unknown_rank_or_too_many_candidates_rejected_by_schema():
    with pytest.raises(ValidationError):
        OrganismVisionResult.model_validate({**VALID_ORGANISM, "candidates": [{**VALID_ORGANISM["candidates"][0], "rank": "tribe-ish"}]})
    with pytest.raises(ValidationError):
        OrganismVisionResult.model_validate({**VALID_ORGANISM, "candidates": VALID_ORGANISM["candidates"] * 6})


def test_model_can_answer_that_it_does_not_know():
    result = OrganismVisionResult.model_validate(
        {"subject_type": "real_organism", "image_quality": "poor", "candidates": [], "cannot_identify_reason": "too blurry"}
    )
    assert result.candidates == [] and result.cannot_identify_reason


class StatusError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (httpx.ReadTimeout("slow"), "ai_timeout"),
        (StatusError(429), "ai_rate_limited"),
        (StatusError(403), "ai_auth_failed"),
        (StatusError(500), "ai_unavailable"),
        (ConnectionError("dns"), "ai_unavailable"),
    ],
)
def test_provider_failures_are_classified(image, error, code):
    gemini, _ = analyzer(error=error)
    with pytest.raises(ProviderUnavailableError) as exc:
        gemini.analyze_organism(image)
    assert exc.value.code == code
