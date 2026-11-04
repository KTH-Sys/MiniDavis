import { useCallback, useEffect, useRef, useState } from 'react';
import { townApi, type TownApi } from '../api';
import type { Readiness, RunTrace, WorldState } from '../types';

/** Exactly one request at a time. Reset invalidates every earlier response. */
export function useTown(api: TownApi = townApi, intervalMs = 700) {
  const [state, setState] = useState<WorldState | null>(null);
  const [running, setRunning] = useState(false);
  const [busy, setBusy] = useState(false);
  const [replacing, setReplacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const snapshot = useRef<WorldState | null>(null);
  const active = useRef(false);
  const replacingRef = useRef(false);
  const runningRef = useRef(false);
  const epoch = useRef(0);
  const controller = useRef<AbortController | null>(null);

  const pause = useCallback(() => {
    runningRef.current = false;
    setRunning(false);
  }, []);

  const apply = useCallback((next: WorldState) => {
    snapshot.current = next;
    setState(next);
  }, []);

  const replace = useCallback(async (seed?: number, trace?: RunTrace, mode?: 'baseline' | 'llm') => {
    if (replacingRef.current) return;
    replacingRef.current = true;
    setReplacing(true);
    pause();
    const generation = ++epoch.current;
    controller.current?.abort();
    const abort = new AbortController();
    controller.current = abort;
    active.current = true;
    setBusy(true);
    setError(null);
    try {
      let next: WorldState;
      if (trace) {
        if (!api.replay || !snapshot.current) throw new Error('Connect to the town before replaying.');
        next = await api.replay(snapshot.current, trace, crypto.randomUUID(), abort.signal);
      } else next = seed === undefined ? await api.state(abort.signal)
        : mode ? await api.reset(seed, abort.signal, mode) : await api.reset(seed, abort.signal);
      if (generation === epoch.current) apply(next);
      if (api.ready) {
        const ready = await api.ready(abort.signal).catch(() => null);
        if (generation === epoch.current) setReadiness(ready);
      }
    } catch (problem) {
      if (generation === epoch.current && !abort.signal.aborted) {
        setError(problem instanceof Error ? problem.message : 'Could not connect to the town.');
      }
    } finally {
      if (generation === epoch.current) {
        replacingRef.current = false;
        setReplacing(false);
        active.current = false;
        setBusy(false);
      }
    }
  }, [api, apply, pause]);

  const step = useCallback(async (operation: 'step' | 'shortage' = 'step') => {
    const previous = snapshot.current;
    if (active.current || !previous) return;
    if (operation === 'step' && previous.mode === 'llm'
        && Object.values(previous.agent_runtime ?? {}).some((agent) => agent.pending)) return;
    active.current = true;
    setBusy(true);
    const generation = epoch.current;
    const abort = new AbortController();
    controller.current = abort;
    try {
      const mutation = operation === 'shortage' ? api.shortage : api.step;
      if (!mutation) throw new Error('This town does not support that action.');
      const next = await mutation(previous, crypto.randomUUID(), abort.signal);
      if (generation === epoch.current && next.run_id === previous.run_id
          && next.revision >= previous.revision) {
        apply(next);
        setError(null);
      }
    } catch (problem) {
      if (generation === epoch.current && !abort.signal.aborted) {
        pause();
        setError(problem instanceof Error ? problem.message : 'The town could not advance.');
      }
    } finally {
      if (generation === epoch.current) {
        active.current = false;
        setBusy(false);
      }
    }
  }, [api, apply, pause]);

  const play = useCallback(() => {
    if (!snapshot.current || snapshot.current.mode === 'replay' || active.current || error) return;
    runningRef.current = true;
    setRunning(true);
  }, [error]);

  const refreshPlanning = useCallback(async () => {
    if (active.current) return;
    active.current = true;
    setBusy(true);
    const generation = epoch.current;
    const abort = new AbortController();
    controller.current = abort;
    try {
      const next = await api.state(abort.signal);
      if (generation === epoch.current) apply(next);
    } catch (problem) {
      if (generation === epoch.current && !abort.signal.aborted) {
        setError(problem instanceof Error ? problem.message : 'Could not refresh planning status.');
      }
    } finally {
      if (generation === epoch.current) { active.current = false; setBusy(false); }
    }
  }, [api, apply]);

  useEffect(() => {
    void replace();
    return () => {
      ++epoch.current;
      runningRef.current = false;
      replacingRef.current = false;
      controller.current?.abort();
    };
  }, [replace]);

  // Schedule the next turn only after the previous response has finished.
  useEffect(() => {
    if (!running || busy || error) return;
    // Let an in-flight model reply arrive before changing its observed world.
    // Baseline stays fast; live mode also respects the shared four/minute pace.
    const pending = state?.mode === 'llm' && Object.values(state.agent_runtime ?? {}).some((agent) => agent.pending);
    const timer = window.setTimeout(() => {
      if (runningRef.current) {
        if (pending) void refreshPlanning();
        else void step();
      }
    }, pending ? 1000 : state?.mode === 'llm' ? Math.max(intervalMs, 15_000) : intervalMs);
    return () => window.clearTimeout(timer);
  }, [running, busy, error, state, step, intervalMs, refreshPlanning]);

  // Paused viewers follow the same server town without advancing it. Pending
  // plans refresh faster. GET /state never schedules a provider call.
  useEffect(() => {
    if (running || busy || error || !state) return;
    const pending = Object.values(state.agent_runtime ?? {}).some((agent) => agent.pending);
    const timer = window.setTimeout(() => void refreshPlanning(), pending ? 1000 : 2000);
    return () => window.clearTimeout(timer);
  }, [running, busy, error, state, refreshPlanning]);

  return {
    state, readiness, running, busy, replacing, error, play, pause,
    next: () => { pause(); void step(); },
    reset: (seed: number, mode?: 'baseline' | 'llm') => void replace(seed, undefined, mode),
    shortage: () => { pause(); void step('shortage'); },
    replay: (trace: RunTrace) => void replace(undefined, trace),
    reconnect: () => void replace(),
  };
}
