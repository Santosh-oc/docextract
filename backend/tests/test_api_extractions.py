import json

import httpx
import pytest
import respx

from tests.fixtures.pdf_fixtures import make_pdf

CHAT_URL = "http://mock-vision.test/v1/chat/completions"


def _mock_chat_response(fields: list[dict]):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"fields": fields})}}]})


async def _upload(client, num_pages=1):
    resp = await client.post(
        "/api/documents/upload", files={"file": ("test.pdf", make_pdf(num_pages=num_pages), "application/pdf")}
    )
    return resp.json()["document"]["id"]


FIELDS_PAYLOAD = [
    {
        "name": "policy_number",
        "display_name": "Policy Number",
        "description": "the policy number",
        "data_type": "String",
        "required": True,
    },
    {
        "name": "phone",
        "display_name": "Phone",
        "description": "phone number",
        "data_type": "Phone",
        "required": False,
    },
]


@pytest.mark.asyncio
@respx.mock
async def test_create_extraction_success(client):
    document_id = await _upload(client)
    respx.post(CHAT_URL).mock(
        return_value=_mock_chat_response(
            [
                {"name": "policy_number", "value": "POL-1", "confidence": 0.9, "page": 1, "evidence": "e"},
                {"name": "phone", "value": None},
            ]
        )
    )
    resp = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["fields_extracted"] == 1
    assert body["fields_not_found"] == 1


@pytest.mark.asyncio
async def test_create_extraction_missing_document_returns_404(client):
    resp = await client.post(
        "/api/extractions",
        json={"document_id": "00000000-0000-0000-0000-000000000000", "fields": FIELDS_PAYLOAD},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_extraction_without_fields_returns_error(client):
    document_id = await _upload(client)
    resp = await client.post("/api/extractions", json={"document_id": document_id, "fields": []})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_extraction_model_not_configured(client):
    await client.put(
        "/api/settings/model",
        json={"provider": "openai_compatible", "api_base_url": "", "api_key": "", "model_name": ""},
    )
    document_id = await _upload(client)
    resp = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    assert resp.status_code == 400
    # restore configuration for subsequent tests
    await client.put(
        "/api/settings/model",
        json={
            "provider": "openai_compatible",
            "api_base_url": "http://mock-vision.test/v1",
            "api_key": "test-key",
            "model_name": "mock-vision-model",
        },
    )


@pytest.mark.asyncio
@respx.mock
async def test_create_extraction_malformed_model_response_marks_failed(client):
    document_id = await _upload(client)
    respx.post(CHAT_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]}))
    resp = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    assert resp.status_code == 502
    assert "error" in resp.json()


@pytest.mark.asyncio
@respx.mock
async def test_get_extraction_result_orders_by_field_sort_order(client):
    document_id = await _upload(client)
    respx.post(CHAT_URL).mock(
        return_value=_mock_chat_response(
            [{"name": "policy_number", "value": "POL-1"}, {"name": "phone", "value": "555-1234"}]
        )
    )
    create = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    extraction_id = create.json()["id"]
    resp = await client.get(f"/api/extractions/{extraction_id}/result")
    assert resp.status_code == 200
    names = [r["field_name"] for r in resp.json()["results"]]
    assert names == ["policy_number", "phone"]


@pytest.mark.asyncio
@respx.mock
async def test_extract_again_creates_new_extraction_without_overwriting(client):
    document_id = await _upload(client)
    respx.post(CHAT_URL).mock(
        return_value=_mock_chat_response([{"name": "policy_number", "value": "POL-1"}, {"name": "phone", "value": None}])
    )
    first = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    second = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    assert first.json()["id"] != second.json()["id"]

    first_result = await client.get(f"/api/extractions/{first.json()['id']}/result")
    assert first_result.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_download_json_and_csv(client):
    document_id = await _upload(client)
    respx.post(CHAT_URL).mock(return_value=_mock_chat_response([{"name": "policy_number", "value": "POL-1"}]))
    create = await client.post("/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD})
    extraction_id = create.json()["id"]

    json_resp = await client.get(f"/api/extractions/{extraction_id}/download/json")
    assert json_resp.status_code == 200
    payload = json.loads(json_resp.content)
    assert payload["extraction_id"] == extraction_id

    csv_resp = await client.get(f"/api/extractions/{extraction_id}/download/csv")
    assert csv_resp.status_code == 200
    assert b"field_name" in csv_resp.content
