import pytest

from tests.fixtures.pdf_fixtures import make_empty_pdf, make_invalid_pdf, make_pdf


async def _upload(client, data: bytes, filename: str = "test.pdf", content_type: str = "application/pdf"):
    return await client.post(
        "/api/documents/upload", files={"file": (filename, data, content_type)}
    )


@pytest.mark.asyncio
async def test_upload_valid_pdf_returns_document(client):
    resp = await _upload(client, make_pdf(num_pages=3))
    assert resp.status_code == 200
    doc = resp.json()["document"]
    assert doc["page_count"] == 3
    assert doc["status"] == "UPLOADED"
    assert doc["original_filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_upload_rejects_non_pdf_content_type(client):
    resp = await _upload(client, b"hello", filename="test.txt", content_type="text/plain")
    assert resp.status_code == 422
    assert "Only PDF documents are supported." in resp.json()["error"]


@pytest.mark.asyncio
async def test_upload_rejects_invalid_pdf_bytes(client):
    resp = await _upload(client, make_invalid_pdf())
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_rejects_empty_pdf(client):
    resp = await _upload(client, make_empty_pdf())
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_document_by_id(client):
    upload = await _upload(client, make_pdf(num_pages=1))
    document_id = upload.json()["document"]["id"]
    resp = await client.get(f"/api/documents/{document_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == document_id


@pytest.mark.asyncio
async def test_get_document_not_found(client):
    resp = await client.get("/api/documents/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_page_image_returns_png(client):
    upload = await _upload(client, make_pdf(num_pages=2))
    document_id = upload.json()["document"]["id"]
    resp = await client.get(f"/api/documents/{document_id}/pages/1")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_get_page_image_out_of_range(client):
    upload = await _upload(client, make_pdf(num_pages=1))
    document_id = upload.json()["document"]["id"]
    resp = await client.get(f"/api/documents/{document_id}/pages/5")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_download_document_returns_original_bytes(client):
    data = make_pdf(num_pages=1)
    upload = await _upload(client, data)
    document_id = upload.json()["document"]["id"]
    resp = await client.get(f"/api/documents/{document_id}/download")
    assert resp.status_code == 200
    assert resp.content == data


@pytest.mark.asyncio
async def test_delete_document_removes_it(client):
    upload = await _upload(client, make_pdf(num_pages=1))
    document_id = upload.json()["document"]["id"]
    resp = await client.delete(f"/api/documents/{document_id}")
    assert resp.status_code == 200
    follow_up = await client.get(f"/api/documents/{document_id}")
    assert follow_up.status_code == 404
