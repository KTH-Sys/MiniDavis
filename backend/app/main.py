"""Run from the repository root: python -m uvicorn backend.app.main:app --reload."""
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from hmac import compare_digest
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .classifier import InteractionClassifier
from .memory import EventStore, minilm_embedder
from .groq_planner import LivePlanner
from .schemas import AgentInspector, ReplayRequest, ResetRequest, RunTrace, StepRequest, WorldState
from .world import Conflict, World


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.require_operator_token and not settings.operator_token.get_secret_value():
        raise ValueError('A server operator token is required for this deployment.')
    embedder = (minilm_embedder(settings.embedding_model, settings.embedding_cache_path, settings.embedding_revision)
                if settings.memory_retrieval_mode == 'semantic' else None)
    store = EventStore(settings.memory_db_path, embedder=embedder)
    planner = LivePlanner(settings)

    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            # Initialize optional models before accepting requests.
            store.warmup()

            classifier_path = Path(settings.classifier_model_path)
            application.state.classifier = None
            application.state.classifier_status = 'not_available'

            if classifier_path.is_dir():
                try:
                    application.state.classifier = InteractionClassifier(classifier_path).load()
                    application.state.classifier_status = 'loaded'
                except Exception:
                    application.state.classifier_status = 'unavailable'
            if settings.classifier_required and application.state.classifier is None:
                raise RuntimeError('Required classifier export is unavailable or invalid.')
            application.state.world._classifier = application.state.classifier

            yield

        finally:
            planner.close()
            store.close()

    application = FastAPI(title="MiniDavis", version="0.2.0", lifespan=lifespan)
    application.state.world = World(store=store, live_planner=planner, mode=settings.minidavis_mode)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Operator-Token"],
    )

    def operator_access(token: str | None = Header(default=None, alias='X-Operator-Token')):
        expected = settings.operator_token.get_secret_value()
        if expected and (token is None or not compare_digest(token.encode(), expected.encode())):
            raise HTTPException(status_code=401, detail='Operator access is required to control the town.')

    @application.get("/health")
    def health():
        mode = application.state.world.snapshot().mode
        return {"status": "ok", "mode": mode,
                "live_llm_enabled": mode == "llm" and bool(settings.llm_api_key.get_secret_value())}

    @application.get('/ready')
    def ready():
        return {'status': 'ok', 'classifier': application.state.classifier_status,
                'classifier_required': settings.classifier_required,
                'operator_protected': bool(settings.operator_token.get_secret_value()),
                'memory_requested': settings.memory_retrieval_mode,
                'restart_behavior': 'new town; old SQLite events remain isolated by run'}

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

    @application.post("/reset", response_model=WorldState, dependencies=[Depends(operator_access)])
    def reset(request: ResetRequest):
        return application.state.world.reset(request.seed, request.mode)

    @application.post("/step", response_model=WorldState, dependencies=[Depends(operator_access)])
    def step(request: StepRequest):
        try:
            return application.state.world.step(request)
        except Conflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @application.post('/scenario/shortage', response_model=WorldState, dependencies=[Depends(operator_access)])
    def shortage(request: StepRequest):
        try:
            return application.state.world.shortage(request)
        except Conflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @application.get('/trace', response_model=RunTrace)
    def trace():
        return application.state.world.trace()

    @application.post('/replay', response_model=WorldState, dependencies=[Depends(operator_access)])
    def replay(request: ReplayRequest):
        try:
            return application.state.world.replay(request)
        except Conflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return application


app = create_app()
