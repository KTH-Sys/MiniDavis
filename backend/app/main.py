"""Run from the repository root: python -m uvicorn backend.app.main:app --reload."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .memory import EventStore
from .schemas import AgentInspector, ResetRequest, StepRequest, WorldState
from .world import Conflict, World


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    store = EventStore(settings.memory_db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            store.close()

    application = FastAPI(title="MiniDavis", version="0.2.0", lifespan=lifespan)
    application.state.world = World(store=store)
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

    @application.get("/agents/{agent_id}", response_model=AgentInspector)
    def inspect(agent_id: str, run_id: str | None = None, revision: int | None = None):
        try:
            return application.state.world.inspect(agent_id, run_id, revision)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown resident.") from error
        except Conflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

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
