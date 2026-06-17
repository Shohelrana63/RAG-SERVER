from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import Field


class PdfDocument(Document):
    user_id: PydanticObjectId
    filename: str
    original_name: str
    size_bytes: int
    status: str = "processing"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "documents"
