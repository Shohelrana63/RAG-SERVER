import pytest
from httpx import AsyncClient

API = "/api/v1"
SAMPLE_PDF = b"%PDF-1.4\n% test document\n"


@pytest.mark.asyncio
async def test_upload_document_requires_auth(client: AsyncClient):
    response = await client.post(
        f"{API}/documents",
        files={"file": ("demo.pdf", SAMPLE_PDF, "application/pdf")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_document_rejects_non_pdf(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        f"{API}/documents",
        headers=auth_headers,
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "PDF" in body["error"]["message"]


@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        f"{API}/documents",
        headers=auth_headers,
        files={"file": ("demo.pdf", SAMPLE_PDF, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["_id"]
    assert data["title"] == "demo.pdf"
    assert data["sizeBytes"] == len(SAMPLE_PDF)
    assert data["status"] == "ready"
    assert data["createdAt"]


@pytest.mark.asyncio
async def test_list_documents_requires_auth(client: AsyncClient):
    response = await client.get(f"{API}/documents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_documents_returns_user_documents(
    client: AsyncClient, auth_headers: dict, uploaded_document: dict
):
    response = await client.get(f"{API}/documents", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) == 1
    assert items[0]["_id"] == uploaded_document["_id"]
    assert items[0]["title"] == "demo.pdf"


@pytest.mark.asyncio
async def test_get_document_success(
    client: AsyncClient, auth_headers: dict, uploaded_document: dict
):
    doc_id = uploaded_document["_id"]
    response = await client.get(f"{API}/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["_id"] == doc_id


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        f"{API}/documents/507f1f77bcf86cd799439011",
        headers=auth_headers,
    )
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["message"] == "Document not found."


@pytest.mark.asyncio
async def test_get_document_status_success(
    client: AsyncClient, auth_headers: dict, uploaded_document: dict
):
    doc_id = uploaded_document["_id"]
    response = await client.get(
        f"{API}/documents/{doc_id}/status",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ready"


@pytest.mark.asyncio
async def test_delete_document_success(
    client: AsyncClient, auth_headers: dict, uploaded_document: dict
):
    doc_id = uploaded_document["_id"]
    response = await client.delete(f"{API}/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is None

    get_response = await client.get(f"{API}/documents/{doc_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.delete(
        f"{API}/documents/507f1f77bcf86cd799439011",
        headers=auth_headers,
    )
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["message"] == "Document not found."
