"""Authoritative in-memory baseline world and atomic reset/step operations."""

from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from uuid import uuid4
import hashlib
import json

from .agents import PlannedStep, baseline_plan, baseline_with_memory
from .memory import EventStore
from .schemas import (Action, AgentInspector, DecisionRecord, Event, Location,
                      MemoryContext, Resident, Resource, StepRequest, TownMap,
                      AgentRuntime, RunTrace, TraceOperation, RecordedAction, TradeOffer, WorldState)


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
                 context_planner: ContextPlanner | None = None, live_planner=None, mode: str = "baseline",
                 classifier=None):
        self._lock = Lock()
        self._state = initial_state(seed)
        self._state.mode = mode
        self._resume_mode = mode
        self._classifier = classifier
        self._trace_operations = []
        self._last_replay_request = None
        self.live_planner = live_planner
        if live_planner:
            live_planner.reset(self._state.run_id)
        self._requests: OrderedDict[str, tuple[int, str]] = OrderedDict()
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
            return self._snapshot()

    def _snapshot(self):
        result = self._state.model_copy(deep=True)
        if result.mode == 'replay':
            result.agent_runtime = {a.id: AgentRuntime(status='replay', detail='Recorded actions; no model calls') for a in result.agents}
        elif self.live_planner:
            result.agent_runtime = self.live_planner.statuses(result)
            result.provider_usage = self.live_planner.budget.usage(result.run_id)
        return result

    def planning_observation(self):
        with self._lock:
            return self._state.model_copy(deep=True), {
                agent.id: self._memory(agent, self._state.tick) for agent in self._state.agents}

    def install_live(self, plan, run_id, agent_id, revision, memory):
        with self._lock:
            state = self._state
            if state.mode != "llm" or state.run_id != run_id or state.revision != revision:
                return False
            agent = next(agent for agent in state.agents if agent.id == agent_id)
            self.live_planner.install(plan, state, agent, memory, revision)
            return True

    def reset(self, seed: int, mode: str | None = None) -> WorldState:
        with self._lock:
            current_mode = mode or (self._resume_mode if self._state.mode == 'replay' else self._state.mode)
            self._state = initial_state(seed)
            self._state.mode = current_mode
            self._resume_mode = current_mode
            self._trace_operations.clear()
            self._last_replay_request = None
            if self.live_planner:
                self.live_planner.reset(self._state.run_id)
            self._requests.clear()
            return self._snapshot()

    def step(self, request: StepRequest) -> WorldState:
        with self._lock:
            state = self._state
            if state.mode == 'replay':
                raise Conflict('Reset before advancing a replay.')
            if self._check_request(request, 'step'):
                return self._snapshot()

            before = state.model_copy(deep=True)
            try:
                self._advance(request)
            except Exception:
                # A planner or storage error cannot leave a half-applied turn.
                self._state = before
                raise
        if self.live_planner:
            self.live_planner.kick(self)
        return self.snapshot()

    def _advance(self, request: StepRequest) -> WorldState:
        state = self._state
        state.tick += 1
        for offer in state.trade_offers:
            if offer.status == 'pending' and state.tick >= offer.expires_tick:
                offer.status = 'expired'
        new_events = []
        recorded = []
        for agent in state.agents:
            # Give a planner detached observations, never mutable world objects.
            memory = self._memory(agent, state.tick - 1)
            observation = state.model_copy(deep=True)
            observation.events = [event for event in observation.events
                                  if event.agent_id == agent.id and event.run_id == state.run_id
                                  and event.tick <= memory.as_of_tick]
            observation.decisions = {key: value for key, value in observation.decisions.items() if key == agent.id}
            if self.live_planner and state.mode == "llm":
                action = self.live_planner.choose(agent.model_copy(deep=True), observation, memory.model_copy(deep=True))
            elif self._context_planner:
                action = self._context_planner(agent.model_copy(deep=True), observation, memory.model_copy(deep=True))
            else:
                action = self._planner(agent.model_copy(deep=True), observation)
            planned = action if isinstance(action, PlannedStep) else None
            if planned:
                action, memory = planned.action, planned.memory
            outcome, text = self._execute(agent, action)
            recorded.append(RecordedAction(agent_id=agent.id, action=action.model_copy(deep=True), outcome=outcome))
            target = action.recipient_id
            if action.action in {'accept_trade', 'reject_trade'}:
                offer = next((o for o in state.trade_offers if o.offer_id == action.offer_id), None)
                target = offer.proposer_id if offer else None
            event = Event(
                event_id=f"{state.run_id}:{state.tick}:{agent.id}",
                run_id=state.run_id,
                tick=state.tick,
                agent_id=agent.id,
                action=action.action,
                outcome=outcome,
                text=text,
                target_agent_id=target,
                interaction_id=f'{state.run_id}:{state.tick}:{agent.id}' if action.action in {'talk','offer_trade','accept_trade','reject_trade'} else None,
            )
            if self._classifier and outcome == 'accepted' and event.interaction_id:
                try:
                    prediction = self._classifier.predict(event.text)
                    event = Event(**{**event.model_dump(), 'interaction_label': prediction['label'],
                                     'confidence': prediction['confidence']})
                except Exception:
                    pass  # inference never controls or rolls back world accounting
            state.events.append(event)
            new_events.append(event)
            if action.action == "accept_trade" and outcome == "accepted":
                # The proposer acted earlier, so record the completed trade in their history too.
                offer = next(o for o in state.trade_offers if o.offer_id == action.offer_id)
                partner_event = event.model_copy(update={
                    "event_id": f"{event.event_id}:partner",
                    "agent_id": offer.proposer_id,
                    "action": "trade_completed",
                    "target_agent_id": agent.id,
                })
                state.events.append(partner_event)
                new_events.append(partner_event)
            elif outcome == 'accepted' and target and action.action in {'talk', 'offer_trade', 'reject_trade'}:
                partner_event = event.model_copy(update={'event_id': f'{event.event_id}:partner',
                                                         'agent_id': target, 'target_agent_id': agent.id})
                state.events.append(partner_event)
                new_events.append(partner_event)
            state.decisions[agent.id] = DecisionRecord(
                tick=state.tick, observation_revision=state.revision,
                planner_mode=planned.mode if planned else ("baseline" if self._planner is baseline_plan and self._context_planner is baseline_with_memory else "custom"),
                action=action.action, explanation=text, memory=memory, event_id=event.event_id,
                model_explanation=planned.model_explanation if planned else None,
                model_observation_revision=planned.model_observation_revision if planned else None,
            )
        if self._store:
            self._store.save_many(new_events)
        state.events = state.events[-200:]
        state.revision += 1
        self._trace_operations.append(TraceOperation(kind='step', actions=recorded, digest=self._digest()))
        self._requests[request.request_id] = (request.expected_revision, 'step')
        if len(self._requests) > 256:
            self._requests.popitem(last=False)
        return state.model_copy(deep=True)

    def _check_request(self, request, kind):
        if request.run_id != self._state.run_id:
            raise Conflict('This run was reset. Refresh the town state.')
        if request.request_id in self._requests:
            if self._requests[request.request_id] != (request.expected_revision, kind):
                raise Conflict('Request ID was already used for another operation or revision.')
            return True
        if request.expected_revision != self._state.revision:
            raise Conflict('Town state changed. Refresh before changing it.')
        if len(self._trace_operations) >= 2000:
            raise Conflict('Trace limit reached. Export and reset this run.')
        return False

    def _digest(self):
        state = self._state
        factual = {'tick': state.tick, 'revision': state.revision,
                   'agents': [a.model_dump() for a in state.agents],
                   'resources': [r.model_dump() for r in state.resources],
                   'trade_offers': [o.model_dump() for o in state.trade_offers]}
        return hashlib.sha256(json.dumps(factual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def trace(self):
        with self._lock:
            return RunTrace(seed=self._state.seed, source_run_id=self._state.run_id,
                            operations=[op.model_copy(deep=True) for op in self._trace_operations])

    def shortage(self, request):
        with self._lock:
            if self._state.mode == 'replay':
                raise Conflict('Reset before changing a replay.')
            if self._check_request(request, 'shortage'):
                return self._snapshot()
            before = self._state.model_copy(deep=True)
            state = self._state
            farm = next(r for r in state.resources if r.id == 'farm')
            previous = farm.stock
            farm.stock = min(farm.stock, 5)
            state.revision += 1
            event = Event(event_id=f'{state.run_id}:shortage:{state.revision}', run_id=state.run_id,
                          tick=state.tick, agent_id='operator', action='shortage', outcome='accepted',
                          text=f'Farm food shortage: stock changed from {previous} to {farm.stock}.')
            try:
                if self._store:
                    self._store.save(event)
            except Exception:
                self._state = before
                raise
            state.events = (state.events + [event])[-200:]
            self._trace_operations.append(TraceOperation(kind='shortage', digest=self._digest()))
            self._requests[request.request_id] = (request.expected_revision, 'shortage')
            if len(self._requests) > 256:
                self._requests.popitem(last=False)
            return self._snapshot()

    def replay(self, request):
        from .replay import reconstruct
        with self._lock:
            if self._last_replay_request == request.model_dump_json():
                return self._snapshot()
            if self._check_request(request, 'replay'):
                return self._snapshot()
            rebuilt, events = reconstruct(request.trace)
            if self._store:
                self._store.save_many(events)
            if self._state.mode != 'replay':
                self._resume_mode = self._state.mode
            self._state = rebuilt._state
            self._state.mode = 'replay'
            self._trace_operations = rebuilt._trace_operations
            self._requests.clear()
            self._last_replay_request = request.model_dump_json()
            if self.live_planner:
                self.live_planner.reset(self._state.run_id)
            return self._snapshot()

    @staticmethod
    def _adjust_relationship(agent: Resident, other_id: str, change: int) -> None:
        agent.relationships[other_id] = max(-100, min(100, agent.relationships.get(other_id, 0) + change))

    def _execute(self, agent: Resident, action: Action) -> tuple[str, str]:
        if action.action == 'talk':
            recipient = next((a for a in self._state.agents if a.id == action.recipient_id), None)
            if (recipient is None or recipient.id == agent.id or not action.message or not action.message.strip()
                    or abs(agent.x-recipient.x)+abs(agent.y-recipient.y) > 1):
                return 'rejected', f'{agent.name} could not speak to that resident.'
            return 'accepted', f'{agent.name} told {recipient.name}: {action.message.strip()}'
        if action.action == 'reject_trade':
            offer = next((o for o in self._state.trade_offers if o.offer_id == action.offer_id), None)
            if offer is None or offer.status != 'pending' or offer.recipient_id != agent.id or self._state.tick >= offer.expires_tick:
                return 'rejected', f'{agent.name} cannot reject this trade.'
            offer.status = 'rejected'
            return 'accepted', f'{agent.name} declined trade {offer.offer_id}.'
        if action.action == "offer_trade":
            recipient = next(
                (r for r in self._state.agents if r.id == action.recipient_id),
                None
            )

            if (
                recipient is None
                or recipient.id == agent.id
                or abs(agent.x-recipient.x)+abs(agent.y-recipient.y) > 1
                or not action.offer_id
                or action.give_resource is None
                or action.receive_resource is None
                or action.give_amount is None
                or action.receive_amount is None
                or action.give_amount <= 0
                or action.receive_amount < 0  # zero price makes the offer a gift
                or any(o.offer_id == action.offer_id for o in self._state.trade_offers)
                or getattr(agent, action.give_resource) < action.give_amount
                or getattr(recipient, action.receive_resource) < action.receive_amount
            ):
                return "rejected", f"{agent.name}'s trade offer was rejected."

            offer = TradeOffer(
                offer_id=action.offer_id,
                proposer_id=agent.id,
                recipient_id=recipient.id,
                give_resource=action.give_resource,
                give_amount=action.give_amount,
                receive_resource=action.receive_resource,
                receive_amount=action.receive_amount,
                created_tick=self._state.tick,
                expires_tick=self._state.tick + 5,
            )

            self._state.trade_offers.append(offer)

            return 'accepted', (f'{agent.name} offered {offer.give_amount} {offer.give_resource} '
                                f'for {offer.receive_amount} {offer.receive_resource} to {recipient.name}.')
        if action.action == "accept_trade":
            offer = next(
                (o for o in self._state.trade_offers
                 if o.offer_id == action.offer_id),
                None
            )

            if (
                offer is None
                or offer.status != "pending"
                or offer.recipient_id != agent.id
                or self._state.tick >= offer.expires_tick
            ):
                return "rejected", f"{agent.name} cannot accept this trade."

            proposer = next(
                (r for r in self._state.agents
                 if r.id == offer.proposer_id),
                None
            )

            if (
                proposer is None
                or abs(agent.x-proposer.x)+abs(agent.y-proposer.y) > 1
                or getattr(proposer, offer.give_resource) < offer.give_amount
                or getattr(agent, offer.receive_resource) < offer.receive_amount
            ):
                return "rejected", "Trade cannot be completed: insufficient resources."

            setattr(
                proposer, offer.give_resource,
                getattr(proposer, offer.give_resource) - offer.give_amount
            )
            setattr(
                agent, offer.give_resource,
                getattr(agent, offer.give_resource) + offer.give_amount
            )

            setattr(
                agent, offer.receive_resource,
                getattr(agent, offer.receive_resource) - offer.receive_amount
            )
            setattr(
                proposer, offer.receive_resource,
                getattr(proposer, offer.receive_resource) + offer.receive_amount
            )

            offer.status = "accepted"

            gave = f"{proposer.name} gave {offer.give_amount} {offer.give_resource}"
            if offer.receive_amount == 0:
                self._adjust_relationship(agent, proposer.id, 5)
                return "accepted", f"{agent.name} accepted gift {offer.offer_id}: {gave}."
            self._adjust_relationship(agent, proposer.id, 2)
            self._adjust_relationship(proposer, agent.id, 2)
            return "accepted", (f"{agent.name} accepted trade {offer.offer_id}: {gave}, "
                                f"{agent.name} gave {offer.receive_amount} {offer.receive_resource}.")

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
