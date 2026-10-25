"""Small deterministic integration policy, to be extended by the agents owner.

This is baseline logic, not an LLM or a trained policy. The engine owns mutations.
"""

from dataclasses import dataclass

from .schemas import Action, MemoryContext, Resident, WorldState


@dataclass
class PlannedStep:
    action: Action
    mode: str
    memory: MemoryContext
    model_explanation: str | None = None
    model_observation_revision: int | None = None


def baseline_with_memory(agent: Resident, state: WorldState, memory: MemoryContext) -> Action:
    """Integration boundary for the future Groq planner.

    This baseline receives retrieved evidence but still chooses by fixed rules.
    Do not describe it as a live LLM or a measured memory-driven policy.
    """
    return baseline_plan(agent, state)


def baseline_plan(agent: Resident, state: WorldState) -> Action:
    if agent.energy <= 75 and agent.food:
        return Action(action="eat")
    if agent.energy < 10:
        return Action(action="rest")

    available = [resource for resource in state.resources if resource.stock > 0]
    if not available:
        return Action(action="rest")

    preferred = "wood" if agent.id in {"ethan", "gayatri"} else "food"
    candidates = [resource for resource in available if resource.kind == preferred]
    if not candidates:
        candidates = available
    target = min(candidates, key=lambda item: abs(item.x - agent.x) + abs(item.y - agent.y))
    if (agent.x, agent.y) == (target.x, target.y):
        return Action(action="gather")

    # No obstacles in the fixed starter map: an orthogonal Manhattan route is shortest.
    if agent.x != target.x:
        return Action(action="move", x=agent.x + (1 if target.x > agent.x else -1), y=agent.y)
    return Action(action="move", x=agent.x, y=agent.y + (1 if target.y > agent.y else -1))
