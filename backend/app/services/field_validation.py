import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"[\d\-\+\(\)\s]{6,20}")
CURRENCY_STRIP_RE = re.compile(r"[^\d.\-]")

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%B %d, %Y",
    "%d %B %Y",
    "%Y/%m/%d",
]

TRUE_VALUES = {"true", "yes", "y", "1"}
FALSE_VALUES = {"false", "no", "n", "0"}


class FieldValidationResult:
    def __init__(self, normalized_value, validation_status: str):
        self.normalized_value = normalized_value
        self.validation_status = validation_status


def validate_field_value(data_type: str, value) -> FieldValidationResult:
    if value is None:
        return FieldValidationResult(None, "NOT_FOUND")

    text = str(value).strip()
    data_type = data_type.lower()

    if data_type == "string":
        return FieldValidationResult(text, "VALID")

    if data_type == "integer":
        try:
            return FieldValidationResult(int(re.sub(r"[,\s]", "", text)), "VALID")
        except ValueError:
            return FieldValidationResult(None, "INVALID_FORMAT")

    if data_type in ("decimal", "currency"):
        try:
            cleaned = CURRENCY_STRIP_RE.sub("", text)
            return FieldValidationResult(float(cleaned), "VALID")
        except ValueError:
            return FieldValidationResult(None, "INVALID_FORMAT")

    if data_type == "date":
        for fmt in DATE_FORMATS:
            try:
                parsed = datetime.strptime(text, fmt)  # noqa: DTZ007 (date-only value, tz is irrelevant)
                return FieldValidationResult(parsed.date().isoformat(), "VALID")
            except ValueError:
                continue
        return FieldValidationResult(None, "INVALID_FORMAT")

    if data_type == "boolean":
        lowered = text.lower()
        if lowered in TRUE_VALUES:
            return FieldValidationResult(True, "VALID")
        if lowered in FALSE_VALUES:
            return FieldValidationResult(False, "VALID")
        return FieldValidationResult(None, "INVALID_FORMAT")

    if data_type == "email":
        if EMAIL_RE.match(text):
            return FieldValidationResult(text.lower(), "VALID")
        return FieldValidationResult(None, "INVALID_FORMAT")

    if data_type == "phone":
        if PHONE_RE.fullmatch(text):
            return FieldValidationResult(text, "VALID")
        return FieldValidationResult(None, "INVALID_FORMAT")

    return FieldValidationResult(text, "VALID")
