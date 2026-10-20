"""Run from the repository root: python -m uvicorn backend.app.main:app --reload."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .schemas import ResetRequest, StepRequest, WorldState
from .world import Conflict, World


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    application = FastAPI(title="MiniDavis", version="0.1.0")
    application.state.world = World()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.get("/health")
    def health():
        return {"status": "ok", "mode": "baseline", "live_llm_enabled": False}

    @application.get("/state", response_model=WorldState)
    def state():
        return application.state.world.snapshot()

    @application.post("/reset", response_model=WorldState)
    def reset(request: ResetRequest):
        return application.state.world.reset(request.seed)

    @application.post("/step", response_model=WorldState)
    def step(request: StepRequest):
        try:
            return application.state.world.step(request)
        except Conflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return application


app = create_app()
