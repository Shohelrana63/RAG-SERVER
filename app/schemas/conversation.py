from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateConversationRequest(BaseModel):
    documentIds: list[str] = Field(min_length=1)
    title: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class SourceOut(BaseModel):
    chunkId: str
    documentId: str
    title: str | None = None
    page: int | None = None
    score: float | None = None
    snippet: str | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    role: str
    content: str
    sources: list[SourceOut] | None = None
    createdAt: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    title: str
    documentIds: list[str]
    lastMessageAt: datetime | None = None
    updatedAt: datetime | None = None
    createdAt: datetime | None = None
    messages: list[MessageOut] | None = None
