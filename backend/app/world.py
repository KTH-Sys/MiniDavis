"""Authoritative in-memory baseline world and atomic reset/step operations."""

from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from uuid import uuid4

from .agents import baseline_plan
from .memory import EventStore
from .schemas import Action, Event, Location, Resident, Resource, StepRequest, TownMap, WorldState


class Conflict(Exception):
    """The caller must fetch state before retrying a stale mutation."""


def initial_state(seed: int) -> WorldState:
    people = [
        ("ethan", "Ethan", "Gather supplies and grow wealth", 1, 1, 10),
        ("gayatri", "Gayatri", "Collect supplies for shelter", 8, 3, 5),
        ("aishani", "Aishani", "Collect food for future trades", 5, 4, 15),
        ("rylee", "Rylee", "Build cooperation in town", 8, 9, 8),
        ("saurya", "Saurya", "Gather food to help neighbors", 2, 8, 6),
    ]
    agents = [Resident(id=i, name=n, goal=g, x=x, y=y, coins=c) for i, n, g, x, y, c in people]
    for agent in agents:
        agent.relationships = {other.id: 0 for other in agents if other.id != agent.id}
    return WorldState(
        run_id=str(uuid4()),
        seed=seed,
        map=TownMap(locations=[
            Location(id="forest", name="Forest", x=2, y=2),
            Location(id="farm", name="Farm", x=9, y=3),
            Location(id="market", name="Market", x=5, y=5),
            Location(id="town-hall", name="Town hall", x=6, y=5),
            Location(id="house-west", name="West house", x=2, y=9),
            Location(id="house-east", name="East house", x=9, y=9),
        ]),
        agents=agents,
        resources=[
            Resource(id="farm", kind="food", x=9, y=3, stock=30),
            Resource(id="forest", kind="wood", x=2, y=2, stock=40),
        ],
    )


Planner = Callable[[Resident, WorldState], Action]


class World:
    def __init__(self, seed: int = 11, planner: Planner = baseline_plan, store: EventStore | None = None):
        self._lock = Lock()
        self._state = initial_state(seed)
        self._requests: OrderedDict[str, int] = OrderedDict()
        self._planner = planner
        self._store = store

    def snapshot(self) -> WorldState:
        with self._lock:
            return self._state.model_copy(deep=True)

    def reset(self, seed: int) -> WorldState:
        with self._lock:
            self._state = initial_state(seed)
            self._requests.clear()
            return self._state.model_copy(deep=True)

    def step(self, request: StepRequest) -> WorldState:
        with self._lock:
            state = self._state
            if request.run_id != state.run_id:
                raise Conflict("This run was reset. Refresh the town state.")
            if request.request_id in self._requests:
                if self._requests[request.request_id] != request.expected_revision:
                    raise Conflict("Request ID was already used for a different revision.")
                # Return the latest state, so a late retry cannot move the UI backwards.
                return state.model_copy(deep=True)
            if request.expected_revision != state.revision:
                raise Conflict("Town state changed. Refresh before stepping again.")

            state.tick += 1
            for agent in state.agents:
                # Give a planner detached observations, never mutable world objects.
                action = self._planner(agent.model_copy(deep=True), state.model_copy(deep=True))
                outcome, text = self._execute(agent, action)
                event = Event(
                    event_id=f"{state.run_id}:{state.tick}:{agent.id}",
                    run_id=state.run_id,
                    tick=state.tick,
                    agent_id=agent.id,
                    action=action.action,
                    outcome=outcome,
                    text=text,
                )
                state.events.append(event)
                if self._store:
                    self._store.save(event)
            state.events = state.events[-200:]
            state.revision += 1
            self._requests[request.request_id] = request.expected_revision
            if len(self._requests) > 256:
                self._requests.popitem(last=False)
            return state.model_copy(deep=True)

    def _execute(self, agent: Resident, action: Action) -> tuple[str, str]:
        if action.action == "move":
            x, y = action.x, action.y
            if (x is None or y is None or not (0 <= x < 12 and 0 <= y < 12)
                    or abs(x - agent.x) + abs(y - agent.y) != 1 or agent.energy < 1):
                return "rejected", f"{agent.name}'s move was rejected."
            agent.x, agent.y = x, y
            agent.energy -= 1
            return "accepted", f"{agent.name} moved to ({x}, {y})."
        if action.action == "gather":
            resource = next((r for r in self._state.resources if (r.x, r.y) == (agent.x, agent.y)), None)
            if resource is None or resource.stock <= 0 or agent.energy < 5:
                return "rejected", f"{agent.name} could not gather here."
            amount = min(2, resource.stock)
            resource.stock -= amount
            if resource.kind == "food":
                agent.food += amount
            else:
                agent.wood += amount
            agent.energy -= 5
            return "accepted", f"{agent.name} gathered {amount} {resource.kind}."
        if action.action == "eat":
            if not agent.food:
                return "rejected", f"{agent.name} has no food to eat."
            agent.food -= 1
            agent.energy = min(100, agent.energy + 15)
            return "accepted", f"{agent.name} ate and recovered energy."
        agent.energy = min(100, agent.energy + 10)
        return "accepted", f"{agent.name} rested."
