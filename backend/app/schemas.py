from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=128)
    channel: Literal["web", "telegram"] = "web"


class ChatResponse(BaseModel):
    answer: str
    mode: Literal["facts", "analysis", "prediction", "help"]
    data: dict[str, Any] = Field(default_factory=dict)
    data_source: str = "mock"


class PredictionRequest(BaseModel):
    team_a: str = Field(min_length=2, max_length=80)
    team_b: str = Field(min_length=2, max_length=80)


class TelegramWebhookResponse(BaseModel):
    ok: bool
    detail: str = "accepted"
