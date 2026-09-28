from app.vision.prompt import DEFAULT_INSTRUCTIONS, build_extraction_prompt


def test_prompt_includes_field_names_and_types():
    fields = [
        {"name": "policy_number", "description": "the policy number", "data_type": "String", "required": True},
        {"name": "amount", "description": "total amount", "data_type": "Currency", "required": False},
    ]
    prompt = build_extraction_prompt(fields)
    assert "policy_number" in prompt
    assert "String" in prompt
    assert "amount" in prompt
    assert "Currency" in prompt
    assert "required" in prompt
    assert "optional" in prompt


def test_prompt_uses_default_instructions_when_none_given():
    prompt = build_extraction_prompt([{"name": "x", "description": "", "data_type": "String", "required": False}])
    assert DEFAULT_INSTRUCTIONS in prompt


def test_prompt_uses_custom_instructions():
    custom = "Only extract values from the summary table."
    prompt = build_extraction_prompt(
        [{"name": "x", "description": "", "data_type": "String", "required": False}], instructions=custom
    )
    assert custom in prompt
    assert DEFAULT_INSTRUCTIONS not in prompt


def test_prompt_requests_json_shape():
    prompt = build_extraction_prompt([{"name": "x", "description": "", "data_type": "String", "required": False}])
    assert '"fields"' in prompt
    assert '"confidence"' in prompt
    assert '"evidence"' in prompt
