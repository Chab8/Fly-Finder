"""Gemini vision adapter (google-genai SDK, Interactions API with JSON-schema output).

API usage verified against https://ai.google.dev/gemini-api/docs/structured-output and
https://ai.google.dev/gemini-api/docs/image-understanding on 2026-10-31.
"""

from __future__ import annotations

import base64
import copy
import logging
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.errors import ProviderResponseError, ProviderUnavailableError
from app.schemas.ai import FlyVisionResult, OrganismVisionResult
from app.services.ai.prompts import FLY_PROMPT, ORGANISM_PROMPT
from app.services.images.processing import ProcessedImage

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
_MAX_KNOWN_PATTERNS_IN_PROMPT = 150


def inline_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic JSON schema with $ref/$defs inlined, for maximum provider compatibility."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                target = copy.deepcopy(defs[node["$ref"].split("/")[-1]])
                extra = {k: v for k, v in node.items() if k != "$ref"}
                return resolve({**target, **extra})
            return {k: resolve(v) for k, v in node.items()}
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)


def _classify_failure(exc: Exception) -> ProviderUnavailableError:
    """Map SDK exceptions to app errors without importing private SDK modules."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if isinstance(exc, httpx.TimeoutException) or "Timeout" in type(exc).__name__:
        return ProviderUnavailableError("gemini", "The AI service took too long to respond.", code="ai_timeout")
    if status == 429:
        return ProviderUnavailableError("gemini", "The AI service quota or rate limit was reached.", code="ai_rate_limited")
    if status in (401, 403):
        return ProviderUnavailableError("gemini", "The AI service rejected the server credentials.", code="ai_auth_failed")
    return ProviderUnavailableError("gemini", "The AI service is unavailable.", code="ai_unavailable")


class GeminiVisionAnalyzer:
    provider = "gemini"

    def __init__(self, *, api_key: str, model: str, timeout_seconds: float, client: Any | None = None):
        if client is None:
            from google import genai

            client = genai.Client(api_key=api_key)
        self._client = client
        self.model = model
        self._timeout = timeout_seconds

    @property
    def available(self) -> bool:
        return True

    def _generate(self, prompt: str, image: ProcessedImage, schema: type[T]) -> T:
        try:
            interaction = self._client.interactions.create(
                model=self.model,
                input=[
                    {"type": "text", "text": prompt},
                    {"type": "image", "data": base64.b64encode(image.jpeg_bytes).decode("ascii"), "mime_type": image.mime_type},
                ],
                response_format={"type": "text", "mime_type": "application/json", "schema": inline_json_schema(schema)},
                timeout=self._timeout,
            )
        except Exception as exc:  # SDK raises several exception families; classify, never leak details
            error = _classify_failure(exc)
            logger.warning("Gemini call failed: %s (%s)", error.code, type(exc).__name__)
            raise error from exc

        text = getattr(interaction, "output_text", None)
        if not text:
            raise ProviderResponseError("gemini", "The AI service returned an empty response.")
        try:
            return schema.model_validate_json(text)
        except ValidationError as exc:
            logger.warning("Gemini response failed schema validation (%d errors)", exc.error_count())
            raise ProviderResponseError("gemini", "The AI response did not match the expected format.") from exc

    def analyze_organism(self, image: ProcessedImage) -> OrganismVisionResult:
        return self._generate(ORGANISM_PROMPT, image, OrganismVisionResult)

    def analyze_fly(self, image: ProcessedImage, known_patterns: list[str]) -> FlyVisionResult:
        names = ", ".join(known_patterns[:_MAX_KNOWN_PATTERNS_IN_PROMPT]) or "(catalog empty)"
        return self._generate(FLY_PROMPT.format(known_patterns=names), image, FlyVisionResult)
