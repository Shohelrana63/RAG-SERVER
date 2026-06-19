import os
import tempfile
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

# Configure test environment before importing the app.
_test_upload_dir = tempfile.mkdtemp(prefix="apdf_test_uploads_")
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/ai_pdf_assistant_test"
os.environ["STORAGE_LOCAL_PATH"] = _test_upload_dir
os.environ["JWT_ACCESS_SECRET"] = "test-secret"

from app.main import app  # noqa: E402
from app.models.conversation import Conversation  # noqa: E402
from app.models.document import PdfDocument  # noqa: E402
from app.models.message import Message  # noqa: E402
from app.models.user import User  # noqa: E402

API = "/api/v1"
SAMPLE_PDF = b"%PDF-1.4\n% test document\n"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        await Message.find_all().delete()
        await Conversation.find_all().delete()
        await PdfDocument.find_all().delete()
        await User.find_all().delete()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    email = f"test-{uuid.uuid4().hex}@example.com"
    response = await client.post(
        f"{API}/auth/register",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def uploaded_document(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    response = await client.post(
        f"{API}/documents",
        headers=auth_headers,
        files={"file": ("demo.pdf", SAMPLE_PDF, "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["data"]
