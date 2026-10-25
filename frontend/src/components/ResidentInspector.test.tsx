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
    expect(screen.getByText(/Live AI and semantic embeddings are pending/)).toBeTruthy();
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
});
