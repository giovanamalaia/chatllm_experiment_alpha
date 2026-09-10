from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class SessionCreateResponse(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}


class SessionUpdateTitle(BaseModel):
    title: str = "Nova conversa"