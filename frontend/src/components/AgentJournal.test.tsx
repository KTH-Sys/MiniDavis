import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { AgentJournal, interactionsFor } from './AgentJournal';
import type { DecisionRecord, Resident, TownEvent } from '../types';

const agent: Resident = { id: 'ethan', name: 'Ethan', goal: 'Gather supplies', x: 2, y: 2,
  food: 3, wood: 2, coins: 10, energy: 90, relationships: {} };
const memory: TownEvent = { event_id: 'run-1:1:ethan', run_id: 'run-1', tick: 1,
  agent_id: 'ethan', action: 'gather', outcome: 'accepted', text: 'Ethan gathered 2 wood.' };
const decision: DecisionRecord = { tick: 2, observation_revision: 1, planner_mode: 'baseline',
  action: 'rest', explanation: 'Ethan rested and recovered energy.', event_id: 'run-1:2:ethan',
  memory: { mode: 'lexical', query: 'wood', as_of_tick: 1, recent: [memory], relevant: [memory] } };

afterEach(cleanup);

describe('resident journal', () => {
  it('shows the executed decision and the actual retrieved memory sources', () => {
    render(<AgentJournal agent={agent} decision={decision} events={[memory]} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Decision' }));
    expect(screen.getByText(decision.explanation)).toBeTruthy();
    fireEvent.click(screen.getByRole('tab', { name: /Memories/ }));
    expect(screen.getByRole('tabpanel').getAttribute('aria-labelledby')).toBe('tab-memory');
    expect(screen.getByText(/Retrieved with keyword search/)).toBeTruthy();
    expect(screen.getAllByText(memory.event_id)).toHaveLength(2);
    expect(screen.getAllByText(memory.text)).toHaveLength(2);
  });

  it('does not present movement or gathering as a conversation', () => {
    render(<AgentJournal agent={agent} decision={decision} events={[memory]} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Interactions' }));
    expect(screen.getByText('No interactions yet')).toBeTruthy();
    expect(screen.queryByText(memory.text)).toBeNull();
  });

  it('includes incoming and outgoing recorded interactions, excluding unrelated residents', () => {
    const social: TownEvent[] = [
      { ...memory, event_id: 'out', action: 'talk', text: 'Ethan spoke to Rylee.', target_agent_id: 'rylee' },
      { ...memory, event_id: 'in', agent_id: 'rylee', action: 'offer_trade', target_agent_id: 'ethan', text: 'Rylee offered wood to Ethan.' },
      { ...memory, event_id: 'group', agent_id: 'gayatri', action: 'talk', participants: ['ethan', 'gayatri'], text: 'Gayatri greeted Ethan.' },
      { ...memory, event_id: 'other', agent_id: 'aishani', action: 'talk', target_agent_id: 'saurya' },
    ];
    expect(interactionsFor([memory, ...social], 'ethan').map((event) => event.event_id)).toEqual(['group', 'in', 'out']);
    render(<AgentJournal agent={agent} events={social} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Interactions' }));
    expect(screen.getByText(/3 recorded/)).toBeTruthy();
    expect(screen.getByText('Rylee offered wood to Ethan.')).toBeTruthy();
  });

  it('opens to real town activity and supports keyboard navigation to the decision', () => {
    render(<AgentJournal agent={agent} decision={decision} events={[memory]} />);
    const feed = screen.getByRole('tab', { name: 'All activity' });
    expect(feed.getAttribute('aria-selected')).toBe('true');
    expect(screen.getAllByText(memory.text)).toHaveLength(2);
    fireEvent.keyDown(feed, { key: 'ArrowRight' });
    expect(screen.getByRole('tab', { name: 'Decision' }).getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(screen.getByRole('tab', { name: 'Decision' }));
    expect(screen.getByText(decision.explanation)).toBeTruthy();
  });

  it('clears decision and memory evidence when a new run has no decisions', () => {
    const view = render(<AgentJournal agent={agent} decision={decision} events={[memory]} />);
    fireEvent.click(screen.getByRole('tab', { name: /Memories/ }));
    view.rerender(<AgentJournal agent={{ ...agent, id: 'gayatri', name: 'Gayatri' }} events={[]} />);
    expect(screen.getByRole('heading', { name: 'Gayatri' })).toBeTruthy();
    expect(screen.queryByText(memory.event_id)).toBeNull();
    expect(screen.queryByText(memory.text)).toBeNull();
    fireEvent.click(screen.getByRole('tab', { name: 'Decision' }));
    expect(screen.queryByText(decision.explanation)).toBeNull();
    expect(screen.getByText(/Advance a turn to see my first action/)).toBeTruthy();
  });

  it('labels waiting, live and fallback states separately from executed actions', () => {
    const view = render(<AgentJournal agent={agent} decision={decision} events={[]}
      runtime={{ status: 'waiting', detail: 'Waiting for the shared Groq queue', pending: true }} />);
    expect(screen.getByRole('status').textContent).toContain('WAITING');
    view.rerender(<AgentJournal agent={agent} decision={{ ...decision, planner_mode: 'live',
      model_explanation: 'Wood supports my goal.', model_observation_revision: 1 }} events={[]}
      runtime={{ status: 'live', detail: 'Cached Groq plan', pending: false }} />);
    fireEvent.click(screen.getByRole('tab', { name: 'Decision' }));
    expect(screen.getByText(decision.explanation)).toBeTruthy();
    expect(screen.getByText(/Model’s explanation: Wood supports my goal/)).toBeTruthy();
    expect(screen.getByRole('status').textContent).toContain('LIVE');
    view.rerender(<AgentJournal agent={agent} events={[]}
      runtime={{ status: 'fallback', detail: 'Missing server API key', pending: false }} />);
    expect(screen.getByRole('status').textContent).toContain('FALLBACK');
    expect(screen.queryByText(/Model’s explanation/)).toBeNull();
  });
});
