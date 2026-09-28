DEFAULT_INSTRUCTIONS = """Extract only information that is present in the document.

Do not guess or hallucinate values.

If a requested field cannot be found, return null.

Preserve the value as it appears in the document unless
normalization is explicitly requested."""


def build_extraction_prompt(fields: list[dict], instructions: str | None = None) -> str:
    """Build a dynamic extraction prompt for the given user-defined fields.

    Each field dict has: name, description, data_type, required.
    """
    instructions = instructions or DEFAULT_INSTRUCTIONS

    field_lines = []
    for f in fields:
        required = "required" if f.get("required") else "optional"
        field_lines.append(
            f"- name: \"{f['name']}\" | type: {f['data_type']} | {required} | "
            f"description: {f.get('description') or '(no description provided)'}"
        )
    fields_block = "\n".join(field_lines)

    return f"""You are a document data extraction assistant. You will be shown every page of a
PDF document, rendered as images in page order.

{instructions}

Extract exactly the following fields:
{fields_block}

For each field, return an object with:
- "name": the exact field name as given above
- "value": the extracted value as a string (or null if not found)
- "confidence": your confidence in the value, a number between 0 and 1
- "page": the 1-indexed page number where the value was found (or null)
- "evidence": a short verbatim quote from the document supporting the value (or null)

Respond with ONLY a single JSON object of this exact shape, no markdown fencing, no commentary:

{{
  "fields": [
    {{"name": "...", "value": "...", "confidence": 0.0, "page": 1, "evidence": "..."}}
  ]
}}
"""
