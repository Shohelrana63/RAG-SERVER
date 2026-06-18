from datetime import datetime, timezone
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field


class Message(Document):
    conversation_id: PydanticObjectId
    role: str
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    token_usage: dict[str, int] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "messages"
