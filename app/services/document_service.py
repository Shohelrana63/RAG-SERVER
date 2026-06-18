import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.models.document import PdfDocument
from app.models.user import User
from app.schemas.document import DocumentOut

PDF_MAGIC = b"%PDF"
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


class DocumentService:
    def __init__(self) -> None:
        self.storage_root = Path(settings.storage_local_path)

    def _to_out(self, doc: PdfDocument) -> DocumentOut:
        return DocumentOut(
            id=str(doc.id),
            title=doc.original_name,
            sizeBytes=doc.size_bytes,
            pageCount=None,
            status=doc.status,
            createdAt=doc.created_at,
        )

    async def _validate_pdf(self, file: UploadFile, data: bytes) -> None:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Only PDF files are supported.")
        if not data.startswith(PDF_MAGIC):
            raise ValueError("Invalid PDF file.")
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(data) > max_bytes:
            raise ValueError(f"File exceeds the {settings.max_upload_mb} MB limit.")

    async def upload(self, user: User, file: UploadFile) -> DocumentOut:
        if not file.filename:
            raise ValueError("Filename is required.")

        data = await file.read()
        await self._validate_pdf(file, data)

        stored_name = f"{uuid.uuid4().hex}.pdf"
        user_dir = self.storage_root / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_dir / stored_name
        file_path.write_bytes(data)

        doc = PdfDocument(
            user_id=user.id,
            filename=stored_name,
            original_name=file.filename,
            size_bytes=len(data),
            status="ready",  # TODO: set "processing" once ingestion pipeline is implemented
        )
        await doc.insert()
        return self._to_out(doc)

    async def list_by_user(self, user: User) -> list[DocumentOut]:
        docs = await PdfDocument.find(PdfDocument.user_id == user.id).sort(
            -PdfDocument.created_at
        ).to_list()
        return [self._to_out(d) for d in docs]

    async def get_by_user(self, user: User, doc_id: str) -> DocumentOut | None:
        doc = await PdfDocument.get(doc_id)
        if not doc or doc.user_id != user.id:
            return None
        return self._to_out(doc)

    async def delete_by_user(self, user: User, doc_id: str) -> bool:
        doc = await PdfDocument.get(doc_id)
        if not doc or doc.user_id != user.id:
            return False
        file_path = self.storage_root / str(user.id) / doc.filename
        if file_path.exists():
            file_path.unlink()
        await doc.delete()
        return True
