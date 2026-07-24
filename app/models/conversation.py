from __future__ import annotations
from enum import StrEnum
from pydantic import BaseModel, Field

class ConversationAction(StrEnum):
    ANSWERED = "answered"
    CLARIFY = "clarify"
    HANDOFF = "handoff"
    EXIT = "exit"

class ConversationResponse(BaseModel):
    action: ConversationAction
    message: str
    matched_skus: list[str] = Field(default_factory=list)
    handoff_reason: str | None = None
