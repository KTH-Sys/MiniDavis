
"""Validate model-generated actions before world execution."""

from typing import Any

from pydantic import ValidationError

from .schemas import Action, Resident, WorldState


class InvalidModelAction(ValueError):
    """The model proposed an invalid or outdated action."""


def validate_model_action(
    plan: dict[str, Any],
    agent: Resident,
    state: WorldState,
) -> Action:
    """Return a legal Action or reject the model's plan."""

    if not isinstance(plan, dict):
        raise InvalidModelAction("Plan must be a JSON object.")

    if plan.get("run_id") != state.run_id:
        raise InvalidModelAction("Outdated or incorrect run_id.")

    if plan.get("agent_id") != agent.id:
        raise InvalidModelAction("Incorrect agent_id.")

    revision = plan.get("observation_revision")
    if type(revision) is not int or revision != state.revision:
        raise InvalidModelAction("Outdated or invalid observation_revision.")

    # Only these fields belong to the model's structured plan.
    allowed_fields = {
        "run_id",
        "agent_id",
        "observation_revision",
        "action",
        "x",
        "y",
        "target",
        "explanation",
    }
    if set(plan) - allowed_fields:
        raise InvalidModelAction("Unexpected fields in model plan.")

    action_name = plan.get("action")
    if action_name not in ("move", "gather", "eat", "rest"):
        raise InvalidModelAction("Unknown action.")

    x, y = plan.get("x"), plan.get("y")
    target = plan.get("target")

    if action_name == "move":
        if type(x) is not int or type(y) is not int:
            raise InvalidModelAction("Move requires integer coordinates.")

        if not (0 <= x < state.map.width and 0 <= y < state.map.height):
            raise InvalidModelAction("Move is outside the map.")

        if abs(x - agent.x) + abs(y - agent.y) != 1:
            raise InvalidModelAction("Move must be exactly one tile.")

        if agent.energy < 1:
            raise InvalidModelAction("Not enough energy to move.")

        if target is not None and target not in {
            location.id for location in state.map.locations
        }:
            raise InvalidModelAction("Unknown target.")

    else:
        if x is not None or y is not None:
            raise InvalidModelAction("Coordinates are only valid for moves.")

        if action_name == "gather":
            resource = next(
                (
                    resource
                    for resource in state.resources
                    if resource.x == agent.x and resource.y == agent.y
                    and resource.stock > 0
                ),
                None,
            )
            if resource is None or agent.energy < 5:
                raise InvalidModelAction("No available resource or insufficient energy.")

            if target is not None and target != resource.id:
                raise InvalidModelAction("Gather target does not match resource.")

        elif target is not None:
            raise InvalidModelAction("This action cannot have a target.")

        if action_name == "eat" and agent.food < 1:
            raise InvalidModelAction("Resident has no food.")

    try:
        return Action(action=action_name, x=x, y=y)
    except ValidationError as exc:
        raise InvalidModelAction("Invalid action structure.") from exc

def safe_model_plan(
    plan: dict[str, Any] | None,
    agent: Resident,
    state: WorldState,
) -> Action:
    """Validate a model plan, falling back to baseline when invalid."""

    from .agents import baseline_plan

    try:
        return validate_model_action(plan, agent, state)
    except (InvalidModelAction, ValidationError, TypeError, ValueError):
        fallback = baseline_plan(agent, state)

        # Check the fallback against the same world rules.
        fallback_plan = {
            "run_id": state.run_id,
            "agent_id": agent.id,
            "observation_revision": state.revision,
            "action": fallback.action,
            "x": fallback.x,
            "y": fallback.y,
        }

        try:
            return validate_model_action(fallback_plan, agent, state)
        except InvalidModelAction:
            return Action(action="rest")
