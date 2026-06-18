from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.conversation import CreateConversationRequest, SendMessageRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["conversations"])
chat_service = ChatService()


@router.post("")
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(get_current_user),
):
    try:
        conv = await chat_service.create_conversation(
            user, body.documentIds, body.title
        )
        return {"success": True, "data": conv.model_dump(by_alias=True)}
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"message": str(exc)}},
        )


@router.get("")
async def list_conversations(user: User = Depends(get_current_user)):
    items = await chat_service.list_conversations(user)
    return {"success": True, "data": {"items": [i.model_dump(by_alias=True) for i in items]}}


@router.get("/{conv_id}")
async def get_conversation(conv_id: str, user: User = Depends(get_current_user)):
    conv = await chat_service.get_conversation(user, conv_id)
    if not conv:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"message": "Conversation not found."}},
        )
    return {"success": True, "data": conv.model_dump(by_alias=True)}


@router.get("/{conv_id}/messages")
async def list_messages(conv_id: str, user: User = Depends(get_current_user)):
    messages = await chat_service.list_messages(user, conv_id)
    if messages is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"message": "Conversation not found."}},
        )
    return {"success": True, "data": {"items": [m.model_dump(by_alias=True) for m in messages]}}


@router.post("/{conv_id}/messages")
async def send_message(
    conv_id: str,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
):
    return StreamingResponse(
        chat_service.stream_message(user, conv_id, body.content),
        media_type="text/event-stream",
    )
