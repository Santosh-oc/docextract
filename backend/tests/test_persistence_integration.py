import json

import httpx
import pytest
import respx

import app.storage.minio_storage as minio_storage_module
from tests.fixtures.pdf_fixtures import make_pdf

CHAT_URL = "http://mock-vision.test/v1/chat/completions"

FIELDS_PAYLOAD = [
    {"name": "policy_number", "display_name": "Policy Number", "description": "d", "data_type": "String", "required": True},
]


def _mock_chat_response(fields):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"fields": fields})}}]})


def _simulate_backend_restart():
    """Drop in-process caches that a real ``uvicorn --reload`` restart would
    also drop, so re-reading through the API proves data survived in
    PostgreSQL/MinIO rather than in Python-process memory."""
    minio_storage_module._storage = None


@pytest.mark.asyncio
@respx.mock
async def test_full_persistence_lifecycle_survives_restart(client):
    pdf_bytes = make_pdf(num_pages=1, texts=["Policy Number: POL-999"])

    # 1. Upload a PDF.
    upload = await client.post(
        "/api/documents/upload", files={"file": ("policy.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload.status_code == 200
    document_id = upload.json()["document"]["id"]

    # 2. Verify the original PDF exists in MinIO (S3-compatible storage).
    from app.config import get_settings
    from app.storage.minio_storage import get_object_storage

    storage = get_object_storage()
    settings = get_settings()
    assert storage.exists(settings.minio_bucket_documents, f"documents/{document_id}/original.pdf")

    # 3. Verify document metadata exists in PostgreSQL.
    doc_resp = await client.get(f"/api/documents/{document_id}")
    assert doc_resp.status_code == 200
    assert doc_resp.json()["status"] == "UPLOADED"

    # 4. Run extraction.
    respx.post(CHAT_URL).mock(
        return_value=_mock_chat_response([{"name": "policy_number", "value": "POL-999", "confidence": 0.9, "page": 1}])
    )
    extraction_resp = await client.post(
        "/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD}
    )
    assert extraction_resp.status_code == 200
    extraction_id = extraction_resp.json()["id"]

    # 5. Verify extraction, field definitions, and results exist in PostgreSQL.
    result_resp = await client.get(f"/api/extractions/{extraction_id}/result")
    assert result_resp.status_code == 200
    result_body = result_resp.json()
    assert result_body["extraction"]["status"] == "COMPLETED"
    assert len(result_body["results"]) == 1
    assert result_body["results"][0]["value"] == "POL-999"

    # 6. Restart the backend.
    _simulate_backend_restart()

    # 7. Retrieve the document and results again.
    doc_after = await client.get(f"/api/documents/{document_id}")
    result_after = await client.get(f"/api/extractions/{extraction_id}/result")

    # 8. Verify the PDF remains available from MinIO and structured data remains available.
    assert doc_after.status_code == 200
    download_after = await client.get(f"/api/documents/{document_id}/download")
    assert download_after.status_code == 200
    assert download_after.content == pdf_bytes
    assert result_after.status_code == 200
    assert result_after.json()["results"][0]["value"] == "POL-999"

    # 9. Run Extract Again and verify a new extraction run is created without
    # overwriting the previous run.
    respx.post(CHAT_URL).mock(
        return_value=_mock_chat_response([{"name": "policy_number", "value": "POL-999", "confidence": 0.95, "page": 1}])
    )
    second_extraction = await client.post(
        "/api/extractions", json={"document_id": document_id, "fields": FIELDS_PAYLOAD}
    )
    assert second_extraction.status_code == 200
    assert second_extraction.json()["id"] != extraction_id

    original_still_present = await client.get(f"/api/extractions/{extraction_id}/result")
    assert original_still_present.status_code == 200
    assert original_still_present.json()["extraction"]["id"] == extraction_id
