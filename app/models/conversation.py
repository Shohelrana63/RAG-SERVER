from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import Field


class Conversation(Document):
    user_id: PydanticObjectId
    title: str
    document_ids: list[PydanticObjectId] = Field(default_factory=list)
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversations"
