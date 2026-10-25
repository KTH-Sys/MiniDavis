import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TownMap } from './TownMap';
import type { WorldState } from '../types';

const state: WorldState = { run_id: 'run-1', tick: 0, revision: 0, seed: 11, mode: 'baseline',
  map: { width: 12, height: 12, locations: [] }, resources: [], events: [],
  agents: [{ id: 'ethan', name: 'Ethan', x: 1, y: 1, goal: 'Gather supplies',
    food: 3, wood: 0, coins: 10, energy: 100, relationships: {} }] };

afterEach(() => { cleanup(); vi.useRealTimers(); });

describe('animated town map', () => {
  it('animates a real coordinate change, settles, and resets without animating from the old run', () => {
    vi.useFakeTimers();
    const view = render(<TownMap state={state} />);
    expect(screen.getByRole('button', { name: 'Inspect Ethan' }).dataset.walking).toBe('false');
    const moved = { ...state, tick: 1, agents: [{ ...state.agents[0], x: 2 }] };
    view.rerender(<TownMap state={moved} />);
    const sprite = screen.getByRole('button', { name: 'Inspect Ethan' });
    expect(sprite.dataset.x).toBe('2');
    expect(sprite.dataset.walking).toBe('true');
    act(() => vi.advanceTimersByTime(580));
    expect(sprite.dataset.walking).toBe('false');
    view.rerender(<TownMap state={{ ...state, run_id: 'run-2' }} />);
    expect(screen.getByRole('button', { name: 'Inspect Ethan' }).dataset.walking).toBe('false');
    expect(screen.getByRole('button', { name: 'Inspect Ethan' }).dataset.x).toBe('1');
  });

  it('lets the user select a resident through the map', () => {
    const select = vi.fn();
    render(<TownMap state={state} onSelect={select} selectedId="ethan" />);
    fireEvent.click(screen.getByRole('button', { name: 'Inspect Ethan' }));
    expect(select).toHaveBeenCalledWith('ethan');
    expect(screen.getByRole('button', { name: 'Inspect Ethan' }).getAttribute('aria-pressed')).toBe('true');
  });
});
