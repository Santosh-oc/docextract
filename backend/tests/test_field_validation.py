import pytest

from app.services.field_validation import validate_field_value


@pytest.mark.parametrize(
    "data_type,value,expected_normalized",
    [
        ("Integer", "1,234", 1234),
        ("Decimal", "$1,234.50", 1234.50),
        ("Currency", "USD 99.99", 99.99),
        ("Boolean", "yes", True),
        ("Boolean", "no", False),
        ("Email", "Person@Example.com", "person@example.com"),
        ("Date", "15/04/1980", "1980-04-15"),
    ],
)
def test_valid_values_normalize(data_type, value, expected_normalized):
    result = validate_field_value(data_type, value)
    assert result.validation_status == "VALID"
    assert result.normalized_value == expected_normalized


def test_none_value_is_not_found():
    result = validate_field_value("String", None)
    assert result.validation_status == "NOT_FOUND"
    assert result.normalized_value is None


@pytest.mark.parametrize(
    "data_type,value",
    [
        ("Integer", "not a number"),
        ("Date", "not a date"),
        ("Email", "not-an-email"),
        ("Boolean", "maybe"),
    ],
)
def test_invalid_values_flagged(data_type, value):
    result = validate_field_value(data_type, value)
    assert result.validation_status == "INVALID_FORMAT"
