from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.models.user import User
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
document_service = DocumentService()


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    try:
        doc = await document_service.upload(user, file)
        return {"success": True, "data": doc.model_dump()}
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"message": str(exc)}},
        )


@router.get("")
async def list_documents(user: User = Depends(get_current_user)):
    items = await document_service.list_by_user(user)
    return {"success": True, "data": {"items": [d.model_dump() for d in items]}}


@router.get("/{doc_id}")
async def get_document(doc_id: str, user: User = Depends(get_current_user)):
    doc = await document_service.get_by_user(user, doc_id)
    if not doc:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"message": "Document not found."}},
        )
    return {"success": True, "data": doc.model_dump()}


@router.get("/{doc_id}/status")
async def get_document_status(doc_id: str, user: User = Depends(get_current_user)):
    doc = await document_service.get_by_user(user, doc_id)
    if not doc:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"message": "Document not found."}},
        )
    return {"success": True, "data": {"status": doc.status}}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user: User = Depends(get_current_user)):
    deleted = await document_service.delete_by_user(user, doc_id)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"message": "Document not found."}},
        )
    return {"success": True, "data": None}
