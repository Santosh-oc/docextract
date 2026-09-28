import json
import re

from pydantic import BaseModel, Field, ValidationError


class ExtractedFieldResponse(BaseModel):
    name: str
    value: str | float | int | bool | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    page: int | None = None
    evidence: str | None = None


class ExtractionResponse(BaseModel):
    fields: list[ExtractedFieldResponse]


class ResponseParseError(Exception):
    def __init__(self, message: str, raw_snippet: str):
        super().__init__(message)
        self.message = message
        self.raw_snippet = raw_snippet


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = _FENCE_RE.sub("", text).strip()
    return text


def parse_extraction_response(raw_text: str) -> ExtractionResponse:
    """Parse and validate the model's raw text into an ExtractionResponse.
    Attempts a markdown-fence cleanup before re-validating. Never silently
    accepts data that fails schema validation."""
    candidate = raw_text
    for attempt_text in (candidate, _strip_markdown_fence(candidate)):
        try:
            data = json.loads(attempt_text)
        except json.JSONDecodeError:
            continue
        try:
            return ExtractionResponse.model_validate(data)
        except ValidationError as exc:
            raise ResponseParseError(
                f"The Vision Model's JSON did not match the expected schema: {exc.errors()[:3]}",
                raw_snippet=_truncate(raw_text),
            ) from exc

    raise ResponseParseError(
        "The Vision Model did not return valid JSON.", raw_snippet=_truncate(raw_text)
    )


def _truncate(text: str, limit: int = 500) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "... [truncated]"
