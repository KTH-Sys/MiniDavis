import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ResidentInspector } from './ResidentInspector';
import { EventLog } from './EventLog';
import type { DecisionRecord, Resident, TownEvent } from '../types';

const agent: Resident = { id: 'ethan', name: 'Ethan', goal: 'Gather wood', x: 2, y: 2,
  food: 3, wood: 2, coins: 10, energy: 90, relationships: {} };
const event: TownEvent = { event_id: 'run-1:1:ethan', run_id: 'run-1', tick: 1,
  agent_id: 'ethan', action: 'gather', outcome: 'accepted', text: 'Ethan gathered 2 wood.' };
const decision: DecisionRecord = { tick: 2, observation_revision: 1, planner_mode: 'baseline',
  action: 'gather', explanation: 'Ethan gathered wood.', event_id: 'run-1:2:ethan',
  memory: { mode: 'lexical', query: 'wood', as_of_tick: 1, recent: [event], relevant: [event] } };

afterEach(cleanup);

describe('inspector evidence and event log', () => {
  it('shows actual source IDs and explicitly labels baseline and keyword retrieval', () => {
    render(<ResidentInspector agent={agent} decision={decision} />);
    expect(screen.getByRole('heading', { name: 'Ethan’s inspector' })).toBeTruthy();
    const recent = within(screen.getByRole('region', { name: 'Recent memories' }));
    expect(recent.getByText(event.text)).toBeTruthy();
    expect(recent.getByText(event.event_id)).toBeTruthy();
    expect(screen.getByText('Keyword search')).toBeTruthy();
    expect(screen.getByText('Baseline rules')).toBeTruthy();
    expect(screen.getByText(/baseline actions still follow fixed rules/)).toBeTruthy();
  });

  it('switches resident and removes old decision evidence after reset', () => {
    const view = render(<ResidentInspector agent={agent} decision={decision} />);
    view.rerender(<ResidentInspector agent={{ ...agent, id: 'gayatri', name: 'Gayatri' }} />);
    expect(screen.getByRole('heading', { name: 'Gayatri’s inspector' })).toBeTruthy();
    expect(screen.queryByText(event.event_id)).toBeNull();
    expect(screen.getByText('Advance a turn to see the first decision.')).toBeTruthy();
  });

  it('shows only the latest 20 event outcomes, without inventing accepted results', () => {
    const events = Array.from({ length: 25 }, (_, index) => ({ ...event, event_id: `event-${index}`, tick: index,
      outcome: 'rejected' as const, text: `Rejected ${index}` }));
    render(<EventLog events={events} />);
    expect(screen.getAllByRole('listitem')).toHaveLength(20);
    expect(screen.queryByText('Rejected 0')).toBeNull();
    expect(screen.getByText('Rejected 24')).toBeTruthy();
    expect(screen.getByText('Turn 24 · rejected')).toBeTruthy();
  });

  it('labels live, waiting, baseline and fallback runtime states separately from executed actions', () => {
    const view = render(<ResidentInspector agent={agent} decision={decision}
      runtime={{ status: 'waiting', detail: 'Waiting for the shared Groq queue', pending: true }} />);
    expect(screen.getByRole('status').textContent).toContain('WAITING');
    expect(screen.getByRole('status').textContent).toContain('request in progress');

    view.rerender(<ResidentInspector agent={agent} decision={{ ...decision, planner_mode: 'live',
      model_explanation: 'Wood supports my goal.', model_observation_revision: 1 }}
      runtime={{ status: 'live', detail: 'Cached Groq plan', pending: false }} />);
    expect(screen.getByRole('status').textContent).toContain('LIVE');
    expect(screen.getByText(/Model’s explanation: Wood supports my goal/)).toBeTruthy();
    expect(screen.getByText(/Model observed revision 1/)).toBeTruthy();

    view.rerender(<ResidentInspector agent={agent}
      runtime={{ status: 'fallback', detail: 'Missing server API key', pending: false }} />);
    expect(screen.getByRole('status').textContent).toContain('FALLBACK');
    expect(screen.queryByText(/Model’s explanation/)).toBeNull();

    view.rerender(<ResidentInspector agent={agent}
      runtime={{ status: 'baseline', detail: 'Baseline rules', pending: false }} />);
    expect(screen.getByRole('status').textContent).toContain('BASELINE');
  });

  it('displays the interaction label and confidence when memory events are labelled', () => {
    const labelledEvent: TownEvent = {
      ...event,
      event_id: 'coop-mem-1',
      interaction_label: 'cooperation',
      confidence: 0.92,
      text: 'Ethan helped Gayatri find the forest.',
    };
    const labelledDecision: DecisionRecord = {
      ...decision,
      memory: { ...decision.memory, recent: [labelledEvent], relevant: [labelledEvent] },
    };
    render(<ResidentInspector agent={agent} decision={labelledDecision} />);
    expect(screen.getAllByText(/Interaction label:/)).toHaveLength(2);
    expect(screen.getAllByText('cooperation')).toHaveLength(2);
    expect(screen.getAllByText(/92.0% confidence/)).toHaveLength(2);
  });
});
