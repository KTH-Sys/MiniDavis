"""Bounded social choices. The engine remains responsible for all transfers."""

from hashlib import sha256
from .schemas import Action

SOCIAL_ACTIONS = {'talk', 'offer_trade', 'accept_trade', 'reject_trade'}


def nearby(agent, state):
    return sorted((a for a in state.agents if a.id != agent.id
                   and abs(a.x-agent.x)+abs(a.y-agent.y) <= 1), key=lambda a: a.id)[:2]


def trade_terms(agent, other):
    if agent.id == 'saurya' and agent.food > 1:
        return ('food', 1, 'coins', 0)
    if agent.wood > 0 and other.food > 0:
        return ('wood', 1, 'food', 1)
    if agent.food > 1 and other.coins > 0:
        return ('food', 1, 'coins', 1)
    if agent.coins > 0 and other.food > 0:
        return ('coins', 1, 'food', 1)
    return None


def incoming(agent, state):
    return [o for o in state.trade_offers if o.recipient_id == agent.id
            and o.status == 'pending' and state.tick < o.expires_tick][:1]


def proposal_action(action, target, explanation, agent, state):
    if action == 'talk':
        return Action(action=action, recipient_id=target, message=explanation)
    if action == 'offer_trade':
        other = next((a for a in nearby(agent, state) if a.id == target), None)
        terms = trade_terms(agent, other) if other else None
        if not terms:
            raise ValueError('No legal nearby exchange')
        give, amount, receive, price = terms
        offer_id = 't:' + sha256(f'{state.run_id}:{state.revision}:{agent.id}'.encode()).hexdigest()[:12]
        return Action(action=action, recipient_id=target, offer_id=offer_id,
                      give_resource=give, give_amount=amount, receive_resource=receive, receive_amount=price)
    return Action(action=action, offer_id=target)


def validate_social(action, agent, state):
    if action.action in {'talk', 'offer_trade'}:
        other = next((a for a in state.agents if a.id == action.recipient_id), None)
        if other is None or other.id == agent.id or abs(agent.x-other.x)+abs(agent.y-other.y) > 1:
            raise ValueError('Social action requires a nearby resident')
        if action.action == 'talk':
            if not action.message or not action.message.strip():
                raise ValueError('Talk requires a message')
        else:
            if (not action.offer_id or action.give_resource is None or action.receive_resource is None
                    or action.give_amount is None or action.receive_amount is None
                    or action.give_amount <= 0 or action.receive_amount < 0
                    or getattr(agent, action.give_resource) < action.give_amount
                    or getattr(other, action.receive_resource) < action.receive_amount
                    or any(o.offer_id == action.offer_id for o in state.trade_offers)):
                raise ValueError('Invalid exchange terms')
    else:
        offer = next((o for o in state.trade_offers if o.offer_id == action.offer_id), None)
        if offer is None or offer.recipient_id != agent.id or offer.status != 'pending' or state.tick >= offer.expires_tick:
            raise ValueError('Offer is unavailable')
        if action.action == 'accept_trade':
            other = next(a for a in state.agents if a.id == offer.proposer_id)
            if (abs(agent.x-other.x)+abs(agent.y-other.y) > 1
                    or getattr(other, offer.give_resource) < offer.give_amount
                    or getattr(agent, offer.receive_resource) < offer.receive_amount):
                raise ValueError('Offer cannot be accepted here')
    return action
