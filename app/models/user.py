from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    name: str
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    role: str = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
