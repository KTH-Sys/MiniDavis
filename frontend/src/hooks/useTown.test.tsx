import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { TownApi } from '../api';
import type { WorldState } from '../types';
import { useTown } from './useTown';

const initial = (run_id = 'run-1', tick = 0): WorldState => ({
  run_id, tick, revision: tick, seed: 11, mode: 'baseline',
  map: { width: 12, height: 12, locations: [] }, agents: [], resources: [], events: [],
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function apiMock(): TownApi {
  return {
    state: vi.fn().mockResolvedValue(initial()),
    step: vi.fn().mockImplementation(async (state: WorldState) => initial(state.run_id, state.tick + 1)),
    reset: vi.fn().mockResolvedValue(initial('run-2')),
  };
}

const flush = () => act(async () => { await Promise.resolve(); });
const advance = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

describe('town controls', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => { cleanup(); vi.useRealTimers(); });

  it('Next Turn advances once; Play schedules more turns and Pause stops scheduling', async () => {
    const api = apiMock();
    const { result } = renderHook(() => useTown(api, 20));
    await flush();
    act(() => result.current.next());
    await flush();
    expect(result.current.state?.tick).toBe(1);
    await advance(100);
    expect(api.step).toHaveBeenCalledTimes(1);
    act(() => result.current.play());
    await advance(20);
    expect(result.current.state?.tick).toBe(2);
    await advance(20);
    expect(result.current.state?.tick).toBe(3);
    act(() => result.current.pause());
    await advance(100);
    expect(api.step).toHaveBeenCalledTimes(3);
  });

  it('never overlaps requests, and Pause permits only the already in-flight turn', async () => {
    const api = apiMock();
    const pending = deferred<WorldState>();
    vi.mocked(api.step).mockReturnValue(pending.promise);
    const { result } = renderHook(() => useTown(api, 20));
    await flush();
    act(() => result.current.play());
    await advance(20);
    await advance(200);
    act(() => result.current.next());
    expect(api.step).toHaveBeenCalledTimes(1);
    act(() => result.current.pause());
    await act(async () => pending.resolve(initial('run-1', 1)));
    await advance(100);
    expect(result.current.state?.tick).toBe(1);
    expect(api.step).toHaveBeenCalledTimes(1);
    expect(result.current.running).toBe(false);
  });

  it('Reset aborts a pending step and ignores its late response', async () => {
    const api = apiMock();
    const pending = deferred<WorldState>();
    vi.mocked(api.step).mockReturnValue(pending.promise);
    const { result } = renderHook(() => useTown(api, 20));
    await flush();
    act(() => result.current.next());
    const signal = vi.mocked(api.step).mock.calls[0][2];
    act(() => result.current.reset(22));
    await flush();
    expect(signal.aborted).toBe(true);
    expect(api.reset).toHaveBeenCalledWith(22, expect.any(AbortSignal));
    expect(result.current.state?.run_id).toBe('run-2');
    await act(async () => pending.resolve(initial('run-1', 99)));
    expect(result.current.state?.run_id).toBe('run-2');
    expect(result.current.state?.tick).toBe(0);
    expect(result.current.running).toBe(false);
  });

  it('stops after a failed request and requires reconnecting before Play', async () => {
    const api = apiMock();
    vi.mocked(api.step).mockRejectedValue(new Error('The town changed in another window.'));
    const { result } = renderHook(() => useTown(api, 20));
    await flush();
    act(() => result.current.play());
    await advance(20);
    expect(result.current.error).toContain('another window');
    expect(result.current.running).toBe(false);
    act(() => result.current.play());
    await advance(100);
    expect(api.step).toHaveBeenCalledTimes(1);
    act(() => result.current.reconnect());
    await flush();
    expect(result.current.error).toBeNull();
  });

  it('does not submit overlapping resets', async () => {
    const api = apiMock();
    const pending = deferred<WorldState>();
    vi.mocked(api.reset).mockReturnValue(pending.promise);
    const { result } = renderHook(() => useTown(api, 20));
    await flush();
    act(() => result.current.reset(11));
    act(() => result.current.reset(22));
    expect(api.reset).toHaveBeenCalledTimes(1);
    expect(result.current.replacing).toBe(true);
    await act(async () => pending.resolve(initial('run-2')));
    expect(result.current.replacing).toBe(false);
  });

  it('aborts an active request and cannot schedule turns after unmount', async () => {
    const api = apiMock();
    const pending = deferred<WorldState>();
    vi.mocked(api.step).mockReturnValue(pending.promise);
    const { result, unmount } = renderHook(() => useTown(api, 20));
    await flush();
    act(() => result.current.play());
    await advance(20);
    const signal = vi.mocked(api.step).mock.calls[0][2];
    unmount();
    expect(signal.aborted).toBe(true);
    await act(async () => pending.resolve(initial('run-1', 1)));
    await advance(100);
    expect(api.step).toHaveBeenCalledTimes(1);
  });

  it('refreshes a pending plan while paused without advancing the town', async () => {
    const api = apiMock();
    const pending: WorldState = { ...initial(), mode: 'llm', agent_runtime: {
      ethan: { status: 'waiting', detail: 'Waiting for Groq', pending: true } } };
    const ready: WorldState = { ...pending, agent_runtime: {
      ethan: { status: 'live', detail: 'Cached Groq plan', pending: false } } };
    vi.mocked(api.state).mockResolvedValueOnce(pending).mockResolvedValue(ready);
    const { result } = renderHook(() => useTown(api, 20));
    await flush();
    await advance(1000);
    expect(result.current.state?.agent_runtime?.ethan.status).toBe('live');
    expect(api.step).not.toHaveBeenCalled();
    await advance(5000);
    expect(api.state).toHaveBeenCalledTimes(2);
  });
});
