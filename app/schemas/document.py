from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    _id: str
    title: str
    sizeBytes: int
    pageCount: int | None = None
    status: str
    createdAt: datetime
