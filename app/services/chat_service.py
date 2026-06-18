import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.models.conversation import Conversation
from app.models.document import PdfDocument
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ConversationOut, MessageOut, SourceOut

PLACEHOLDER_REPLY = (
    "Based on the selected documents, here is a placeholder answer. "
    "RAG retrieval will be connected in a later step."
)


class ChatService:
    def _message_out(self, msg: Message) -> MessageOut:
        sources = None
        if msg.sources:
            sources = [SourceOut(**s) for s in msg.sources]
        return MessageOut(
            id=str(msg.id),
            role=msg.role,
            content=msg.content,
            sources=sources,
            createdAt=msg.created_at,
        )

    def _conversation_out(
        self, conv: Conversation, messages: list[Message] | None = None
    ) -> ConversationOut:
        return ConversationOut(
            id=str(conv.id),
            title=conv.title,
            documentIds=[str(d) for d in conv.document_ids],
            lastMessageAt=conv.last_message_at,
            updatedAt=conv.updated_at,
            createdAt=conv.created_at,
            messages=[self._message_out(m) for m in messages] if messages is not None else None,
        )

    async def _validate_documents(self, user: User, document_ids: list[str]) -> list[PydanticObjectId]:
        ids = [PydanticObjectId(d) for d in document_ids]
        for doc_id in ids:
            doc = await PdfDocument.get(doc_id)
            if not doc or doc.user_id != user.id:
                raise ValueError("One or more documents were not found.")
            if doc.status != "ready":
                raise ValueError("All documents must be ready before starting a chat.")
        return ids

    async def create_conversation(
        self, user: User, document_ids: list[str], title: str | None
    ) -> ConversationOut:
        ids = await self._validate_documents(user, document_ids)
        now = datetime.now(timezone.utc)
        conv = Conversation(
            user_id=user.id,
            title=title or "New conversation",
            document_ids=ids,
            last_message_at=now,
            created_at=now,
            updated_at=now,
        )
        await conv.insert()
        return self._conversation_out(conv, messages=[])

    async def list_conversations(self, user: User) -> list[ConversationOut]:
        convs = await Conversation.find(Conversation.user_id == user.id).sort(
            -Conversation.last_message_at
        ).to_list()
        return [self._conversation_out(c) for c in convs]

    async def get_conversation(self, user: User, conv_id: str) -> ConversationOut | None:
        conv = await Conversation.get(conv_id)
        if not conv or conv.user_id != user.id:
            return None
        messages = await Message.find(Message.conversation_id == conv.id).sort(
            Message.created_at
        ).to_list()
        return self._conversation_out(conv, messages)

    async def list_messages(self, user: User, conv_id: str) -> list[MessageOut] | None:
        conv = await Conversation.get(conv_id)
        if not conv or conv.user_id != user.id:
            return None
        messages = await Message.find(Message.conversation_id == conv.id).sort(
            Message.created_at
        ).to_list()
        return [self._message_out(m) for m in messages]

    async def _build_sources(self, conv: Conversation) -> list[dict]:
        sources: list[dict] = []
        for i, doc_id in enumerate(conv.document_ids):
            doc = await PdfDocument.get(doc_id)
            if not doc:
                continue
            sources.append(
                {
                    "chunkId": f"placeholder_{doc_id}",
                    "documentId": str(doc_id),
                    "title": doc.original_name,
                    "page": i + 1,
                    "score": 0.9,
                    "snippet": "Placeholder source excerpt until RAG is enabled.",
                }
            )
        return sources

    async def stream_message(
        self, user: User, conv_id: str, content: str
    ) -> AsyncIterator[str]:
        conv = await Conversation.get(conv_id)
        if not conv or conv.user_id != user.id:
            yield f"data: {json.dumps({'type': 'error', 'value': 'Conversation not found.'})}\n\n"
            return

        user_msg = Message(conversation_id=conv.id, role="user", content=content)
        await user_msg.insert()

        full_reply = ""
        for word in PLACEHOLDER_REPLY.split():
            token = f"{word} "
            full_reply += token
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

        sources = await self._build_sources(conv)
        yield f"data: {json.dumps({'type': 'sources', 'value': sources})}\n\n"

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_reply.strip(),
            sources=sources,
        )
        await assistant_msg.insert()

        now = datetime.now(timezone.utc)
        conv.last_message_at = now
        conv.updated_at = now
        if conv.title == "New conversation":
            conv.title = content[:60]
        await conv.save()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        yield "data: [DONE]\n\n"
