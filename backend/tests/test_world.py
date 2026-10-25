import pytest

from backend.app.agents import baseline_plan
from backend.app.schemas import Action, StepRequest
from backend.app.world import World


def advance(world,index):
    state=world.snapshot()
    return world.step(StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id=str(index)))


def test_all_five_baselines_follow_their_resource_destination():
    world=World(); state=world.snapshot()
    for agent in state.agents:
        target=state.resources[1] if agent.id in {'ethan','gayatri'} else state.resources[0]
        before=abs(agent.x-target.x)+abs(agent.y-target.y)
        action=baseline_plan(agent,state)
        assert action.action=='move'
        assert abs(action.x-target.x)+abs(action.y-target.y)==before-1
    actions=set()
    for turn in range(100):
        result=advance(world,turn)
        actions.update(d.action for d in result.decisions.values())
        assert all(event.outcome=='accepted' for event in result.events)
    assert actions=={'move','gather','eat','rest'}


def test_two_gatherers_cannot_duplicate_the_last_resource():
    world=World(planner=lambda *_:Action(action='gather'))
    world._state.resources[1].stock=1
    for agent in world._state.agents: agent.x,agent.y=2,2
    result=advance(world,0)
    assert sum(agent.wood for agent in result.agents)==1
    assert result.resources[1].stock==0
    assert sum(event.outcome=='accepted' for event in result.events)==1


@pytest.mark.parametrize('action',[Action(action='move',x=12,y=1),Action(action='move',x=3,y=1),Action(action='gather')])
def test_invalid_actions_preserve_every_inventory(action):
    world=World(planner=lambda *_:action)
    for agent in world._state.agents: agent.x,agent.y=1,1
    before=world.snapshot()
    after=advance(world,0)
    assert after.agents==before.agents and after.resources==before.resources
    assert all(event.outcome=='rejected' for event in after.events)


@pytest.mark.parametrize('action,energy,expected,food',[('eat',95,100,2),('rest',95,100,3),('eat',20,35,2),('rest',20,30,3)])
def test_eating_and_resting_have_exact_bounded_effects(action,energy,expected,food):
    world=World(planner=lambda *_:Action(action=action))
    for agent in world._state.agents: agent.energy=energy
    result=advance(world,0)
    assert all(agent.energy==expected and agent.food==food for agent in result.agents)
