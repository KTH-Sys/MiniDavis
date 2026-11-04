"""Re-execute recorded authoritative actions, never a model or provider."""

from .schemas import StepRequest


def reconstruct(trace):
    from .world import Conflict, World
    plans = {}
    world = World(seed=trace.seed, context_planner=lambda agent, state, memory: plans[agent.id])
    events = []
    expected_ids = [a.id for a in world.snapshot().agents]
    for index, operation in enumerate(trace.operations):
        state = world.snapshot()
        request = StepRequest(run_id=state.run_id, expected_revision=state.revision, request_id=f'replay-{index}')
        if operation.kind == 'step':
            if [row.agent_id for row in operation.actions] != expected_ids:
                raise Conflict('Trace must contain one action for each resident, in engine order.')
            plans = {row.agent_id: row.action for row in operation.actions}
            state = world.step(request)
            for row in operation.actions:
                decision = state.decisions[row.agent_id]
                event = next(e for e in state.events if e.event_id == decision.event_id)
                if event.outcome != row.outcome:
                    raise Conflict('Trace outcome differs from engine validation.')
            events.extend(e for e in state.events if e.tick == state.tick)
        else:
            if operation.actions:
                raise Conflict('Shortage trace operations cannot contain resident actions.')
            state = world.shortage(request)
            events.append(state.events[-1])
        if world._digest() != operation.digest:
            raise Conflict('Trace state checksum does not match deterministic replay.')
    for decision in world._state.decisions.values():
        decision.planner_mode = 'replay'
    return world, events
