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


class WorldState(Contract):
    run_id: str
    tick: int = 0
    revision: int = 0
    seed: int
    mode: Literal["baseline"] = "baseline"
    map: TownMap
    agents: list[Resident]
    resources: list[Resource]
    events: list[Event] = Field(default_factory=list)


class Action(Contract):
    action: Literal["move", "gather", "eat", "rest"]
    x: int | None = None
    y: int | None = None


class StepRequest(Contract):
    run_id: str = Field(min_length=1, max_length=64)
    expected_revision: int = Field(ge=0, strict=True)
    request_id: str = Field(min_length=1, max_length=128)


class ResetRequest(Contract):
    seed: int = Field(default=11, ge=0, le=2**31 - 1, strict=True)
    mode: Literal["baseline"] = "baseline"
