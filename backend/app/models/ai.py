from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization
from app.models.user import User

class AIChatConversation(Document):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    user_id: Link[User]
    title: str = "New Conversation"
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    # Each message: {"role": "user" | "assistant" | "system", "content": str, "timestamp": str, "sources": Optional[List[str]]}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_chat_conversations"
        indexes = [
            "conversation_id",
            "organization_id",
            "user_id"
        ]

class HRPolicyDocument(Document):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    title: str
    category: str = "General Policy"
    content: str
    chunks: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "hr_policy_documents"
        indexes = [
            "document_id",
            "organization_id",
            "title"
        ]
