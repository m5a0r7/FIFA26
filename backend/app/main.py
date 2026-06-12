from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.agents import WorldCupAgent
from backend.app.config import Settings, get_settings
from backend.app.data.cache import get_match_cache_status
from backend.app.schemas import ChatRequest, ChatResponse, PredictionRequest, TelegramWebhookResponse
from backend.app.telegram.webhook import TelegramWebhookHandler
from backend.app.tools import FootballTools


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    football_tools = FootballTools()
    agent = WorldCupAgent(football_tools)
    telegram_handler = TelegramWebhookHandler(settings, agent)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/data/freshness")
    async def data_freshness() -> dict[str, object]:
        return get_match_cache_status()

    @app.get("/matches")
    async def matches(team: str | None = None) -> list[dict[str, object]]:
        return football_tools.get_match_schedule(team)

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        return await agent.answer(request.message, session_id=request.session_id)

    @app.post("/predict")
    async def predict(request: PredictionRequest) -> dict[str, object]:
        try:
            return football_tools.predict_match(request.team_a, request.team_b)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/telegram/webhook", response_model=TelegramWebhookResponse)
    async def telegram_webhook(
        request: Request,
        settings_dependency: Settings = Depends(get_settings),
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> dict[str, object]:
        expected_secret = settings_dependency.telegram_webhook_secret
        if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
            raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret.")

        update = await request.json()
        return await telegram_handler.handle_update(update)

    return app


app = create_app()
