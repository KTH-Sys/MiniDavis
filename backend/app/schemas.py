"""The shared Day 1–2 HTTP contract. Coordinates are (x, y)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Location(Contract):
    id: str
    name: str
    x: int
    y: int


class TownMap(Contract):
    width: int = 12
    height: int = 12
    locations: list[Location]


class Resident(Contract):
    id: str
    name: str
    goal: str
    x: int
    y: int
    food: int = 3
    wood: int = 0
    coins: int
    energy: int = 100
    relationships: dict[str, int] = Field(default_factory=dict)


class Resource(Contract):
    id: str
    kind: Literal["food", "wood"]
    x: int
    y: int
    stock: int


class Event(Contract):
    event_id: str
    run_id: str
    tick: int
    agent_id: str
    action: str
    outcome: Literal["accepted", "rejected"]
    text: str
    target_agent_id: str | None = None
    interaction_id: str | None = None
    interaction_label: Literal['cooperation', 'conflict', 'trade', 'neutral'] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class MemoryContext(Contract):
    mode: Literal["semantic", "lexical", "recent-only"] = "lexical"
    query: str
    as_of_tick: int
    recent: list[Event] = Field(default_factory=list)
    relevant: list[Event] = Field(default_factory=list)


class DecisionRecord(Contract):
    tick: int
    observation_revision: int
    planner_mode: Literal["baseline", "custom", "live", "cached", "waiting", "fallback", "replay"]
    action: str
    explanation: str
    memory: MemoryContext
    event_id: str
    model_explanation: str | None = None
    model_observation_revision: int | None = None


class AgentRuntime(Contract):
    status: Literal["baseline", "live", "waiting", "fallback", "replay"] = "baseline"
    detail: str = "Baseline rules"
    pending: bool = False
    plan_target: str | None = None


class ProviderUsage(Contract):
    calls_run: int = 0
    calls_day: int = 0
    tokens_day: int = 0
    reserved_tokens_day: int = 0
    cooldown_seconds: int = 0

class TradeOffer(Contract):
    offer_id: str
    proposer_id: str
    recipient_id: str
    give_resource: Literal["food", "wood", "coins"]
    give_amount: int = Field(gt=0)
    receive_resource: Literal["food", "wood", "coins"]
    receive_amount: int = Field(ge=0)
    created_tick: int = 0
    expires_tick: int = 5
    status: Literal["pending", "accepted", "rejected", "expired"] = "pending"

class WorldState(Contract):
    run_id: str
    tick: int = 0
    revision: int = 0
    seed: int
    mode: Literal["baseline", "llm", "replay"] = "baseline"
    map: TownMap
    agents: list[Resident]
    resources: list[Resource]
    events: list[Event] = Field(default_factory=list)
    trade_offers: list[TradeOffer] = Field(default_factory=list)
    decisions: dict[str, DecisionRecord] = Field(default_factory=dict)
    agent_runtime: dict[str, AgentRuntime] = Field(default_factory=dict)
    provider_usage: ProviderUsage = Field(default_factory=ProviderUsage)


class Action(Contract):
    action: Literal["move", "gather", "eat", "rest", "talk", "offer_trade", "accept_trade", "reject_trade"]
    x: int | None = Field(default=None, strict=True)
    y: int | None = Field(default=None, strict=True)
    offer_id: str | None = None
    recipient_id: str | None = None
    give_resource: Literal["food", "wood", "coins"] | None = None
    give_amount: int | None = Field(default=None, strict=True)
    receive_resource: Literal["food", "wood", "coins"] | None = None
    receive_amount: int | None = Field(default=None, strict=True)
    message: str | None = Field(default=None, max_length=240)


class StepRequest(Contract):
    run_id: str = Field(min_length=1, max_length=64)
    expected_revision: int = Field(ge=0, strict=True)
    request_id: str = Field(min_length=1, max_length=128)


class ResetRequest(Contract):
    seed: int = Field(default=11, ge=0, le=2**31 - 1, strict=True)
    mode: Literal["baseline", "llm"] | None = None


class AgentInspector(Contract):
    run_id: str
    revision: int
    tick: int
    agent: Resident
    decision: DecisionRecord | None
    retrieval: MemoryContext


class RecordedAction(Contract):
    agent_id: str
    action: Action
    outcome: Literal['accepted', 'rejected']


class TraceOperation(Contract):
    kind: Literal['step', 'shortage']
    actions: list[RecordedAction] = Field(default_factory=list, max_length=5)
    digest: str = Field(min_length=64, max_length=64)


class RunTrace(Contract):
    version: Literal[1] = 1
    seed: int = Field(ge=0, le=2**31 - 1, strict=True)
    source_run_id: str
    operations: list[TraceOperation] = Field(default_factory=list, max_length=2000)


class ReplayRequest(StepRequest):
    trace: RunTrace
