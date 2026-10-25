
import pytest

from backend.app.schemas import Action
from backend.app.validation import InvalidModelAction, validate_model_action
from backend.app.world import World


@pytest.fixture
def setup_world():
    world = World(seed=11)
    state = world.snapshot()
    agent = state.agents[0]
    return world, state, agent


def make_plan(state, agent, action="rest", **kwargs):
    return {
        "run_id": state.run_id,
        "agent_id": agent.id,
        "observation_revision": state.revision,
        "action": action,
        **kwargs,
    }


def test_valid_rest(setup_world):
    _, state, agent = setup_world
    result = validate_model_action(make_plan(state, agent), agent, state)
    assert result == Action(action="rest")


def test_unknown_action_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent, action="fly")
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_out_of_bounds_move_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent, action="move", x=-1, y=1)
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_non_adjacent_move_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent, action="move", x=8, y=8)
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_outdated_run_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent)
    plan["run_id"] = "old-run"
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_outdated_revision_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent)
    plan["observation_revision"] = state.revision + 1
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_wrong_agent_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent)
    plan["agent_id"] = "unknown-agent"
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_gather_without_resource_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(state, agent, action="gather")
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_eat_without_food_rejected(setup_world):
    _, state, agent = setup_world
    agent.food = 0
    plan = make_plan(state, agent, action="eat")
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_unknown_target_rejected(setup_world):
    _, state, agent = setup_world
    plan = make_plan(
        state, agent, action="move", x=agent.x + 1, y=agent.y,
        target="nonexistent-location",
    )
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)


def test_validation_does_not_mutate_world(setup_world):
    world, state, agent = setup_world
    before = world.snapshot().model_dump()

    plan = make_plan(state, agent, action="move", x=999, y=999)
    with pytest.raises(InvalidModelAction):
        validate_model_action(plan, agent, state)

    after = world.snapshot().model_dump()
    assert after == before


from backend.app.validation import safe_model_plan


def test_invalid_model_action_uses_safe_fallback(setup_world):
    world, state, agent = setup_world

    before = world.snapshot().model_dump()

    invalid_plan = {
        "run_id": state.run_id,
        "agent_id": agent.id,
        "observation_revision": state.revision,
        "action": "fly",
    }

    fallback = safe_model_plan(invalid_plan, agent, state)

    assert fallback == Action(action="move", x=2, y=1)

    # Selecting a fallback must not mutate authoritative state.
    after = world.snapshot().model_dump()
    assert after == before


from backend.app.validation import safe_model_plan
from backend.app.schemas import StepRequest


def test_world_step_replaces_invalid_model_actions():
    def invalid_model_planner(agent, state):
        invalid_plan = {
            "run_id": state.run_id,
            "agent_id": agent.id,
            "observation_revision": state.revision,
            "action": "fly",
        }
        return safe_model_plan(invalid_plan, agent, state)

    world = World(seed=11, planner=invalid_model_planner)
    before = world.snapshot()

    result = world.step(
        StepRequest(
            run_id=before.run_id,
            expected_revision=before.revision,
            request_id="invalid-model-test",
        )
    )

    assert result.tick == 1
    assert result.revision == 1
    assert len(result.events) == 5
    assert all(event.outcome == "accepted" for event in result.events)
    assert all(event.action != "fly" for event in result.events)
