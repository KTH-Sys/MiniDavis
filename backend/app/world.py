"""Authoritative in-memory baseline world and atomic reset/step operations."""

from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from uuid import uuid4

from .agents import baseline_plan, baseline_with_memory
from .memory import EventStore
from .schemas import (Action, AgentInspector, DecisionRecord, Event, Location,
                      MemoryContext, Resident, Resource, StepRequest, TownMap, WorldState)


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
ContextPlanner = Callable[[Resident, WorldState, MemoryContext], Action]


class World:
    def __init__(self, seed: int = 11, planner: Planner = baseline_plan, store: EventStore | None = None,
                 context_planner: ContextPlanner | None = None):
        self._lock = Lock()
        self._state = initial_state(seed)
        self._requests: OrderedDict[str, int] = OrderedDict()
        self._planner = planner
        self._store = store
        self._context_planner = context_planner or (baseline_with_memory if planner is baseline_plan else None)

    def _memory(self, agent: Resident, as_of_tick: int) -> MemoryContext:
        query = f"{agent.goal} food wood energy gather rejected"
        if self._store:
            return self._store.retrieve(self._state.run_id, agent.id, query, as_of_tick)
        recent = [event for event in self._state.events
                  if event.run_id == self._state.run_id and event.agent_id == agent.id and event.tick <= as_of_tick][-5:]
        return MemoryContext(mode="recent-only", query=query, as_of_tick=as_of_tick, recent=recent)

    def inspect(self, agent_id: str, run_id: str | None = None, revision: int | None = None) -> AgentInspector:
        with self._lock:
            state = self._state
            if (run_id is not None and run_id != state.run_id) or (revision is not None and revision != state.revision):
                raise Conflict("Town state changed. Refresh before inspecting again.")
            agent = next((item for item in state.agents if item.id == agent_id), None)
            if agent is None:
                raise KeyError(agent_id)
            decision = state.decisions.get(agent_id)
            return AgentInspector(run_id=state.run_id, revision=state.revision, tick=state.tick,
                                  agent=agent.model_copy(deep=True),
                                  decision=decision.model_copy(deep=True) if decision else None,
                                  retrieval=decision.memory.model_copy(deep=True) if decision else self._memory(agent, state.tick))

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

            before = state.model_copy(deep=True)
            try:
                return self._advance(request)
            except Exception:
                # A planner or storage error cannot leave a half-applied turn.
                self._state = before
                raise

    def _advance(self, request: StepRequest) -> WorldState:
        state = self._state
        state.tick += 1
        new_events = []
        for agent in state.agents:
            # Give a planner detached observations, never mutable world objects.
            memory = self._memory(agent, state.tick - 1)
            observation = state.model_copy(deep=True)
            observation.events = [event for event in observation.events
                                  if event.agent_id == agent.id and event.run_id == state.run_id
                                  and event.tick <= memory.as_of_tick]
            observation.decisions = {key: value for key, value in observation.decisions.items() if key == agent.id}
            if self._context_planner:
                action = self._context_planner(agent.model_copy(deep=True), observation, memory.model_copy(deep=True))
            else:
                action = self._planner(agent.model_copy(deep=True), observation)
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
            new_events.append(event)
            state.decisions[agent.id] = DecisionRecord(
                tick=state.tick, observation_revision=state.revision,
                planner_mode="baseline" if self._planner is baseline_plan and self._context_planner is baseline_with_memory else "custom",
                action=action.action, explanation=text, memory=memory, event_id=event.event_id,
            )
        if self._store:
            self._store.save_many(new_events)
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
