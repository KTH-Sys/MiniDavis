import type { Readiness, RunTrace, WorldState } from './types';

let operatorKey = '';
export function setOperatorKey(value: string) { operatorKey = value; }

export async function loadSampleTrace(): Promise<RunTrace> {
  const response = await fetch('/demo/sample-run.json');
  if (!response.ok) throw new Error('The recorded example is unavailable. Open Presenter tools to load a saved run.');
  const trace = await response.json();
  if (trace?.version !== 1 || !Array.isArray(trace.operations)) throw new Error('The recorded example is not a valid town run.');
  return trace as RunTrace;
}

// Accept the original frontend setting while keeping the shared setting primary.
const base = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

export interface TownApi {
  state(signal: AbortSignal): Promise<WorldState>;
  step(state: WorldState, requestId: string, signal: AbortSignal): Promise<WorldState>;
  reset(seed: number, signal: AbortSignal, mode?: 'baseline' | 'llm'): Promise<WorldState>;
  ready?(signal: AbortSignal): Promise<Readiness>;
  classify?(text: string, signal: AbortSignal): Promise<{label: string; confidence: number}>;
  shortage?(state: WorldState, requestId: string, signal: AbortSignal): Promise<WorldState>;
  replay?(state: WorldState, trace: RunTrace, requestId: string, signal: AbortSignal): Promise<WorldState>;
  trace?(signal: AbortSignal): Promise<RunTrace>;
}

async function request<T = WorldState>(path: string, signal: AbortSignal, body?: object): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      signal,
      method: body ? 'POST' : 'GET',
      headers: body ? { 'Content-Type': 'application/json', ...(operatorKey ? { 'X-Operator-Token': operatorKey } : {}) } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new Error('Cannot reach the town. Start the backend, then reconnect.');
  }
  if (!response.ok) {
    throw new ApiError(response.status, response.status === 401 ? 'Operator access required. Enter the operator key below the town.' : response.status === 409
      ? 'The town changed in another window. Reconnect before continuing.'
      : `The town could not complete that request (${response.status}). Reconnect to check its state.`);
  }
  return response.json() as Promise<T>;
}

export const townApi: TownApi = {
  state: (signal) => request('/state', signal),
  step: (state, requestId, signal) => request('/step', signal, {
    run_id: state.run_id,
    expected_revision: state.revision,
    request_id: requestId,
  }),
  reset: (seed, signal, mode) => request('/reset', signal, { seed, ...(mode ? {mode} : {}) }),
  ready: (signal) => request<Readiness>('/ready', signal),
  classify: (text, signal) => request<{label: string; confidence: number}>('/classify', signal, {text}),
  shortage: (state, requestId, signal) => request('/scenario/shortage', signal, {
    run_id: state.run_id, expected_revision: state.revision, request_id: requestId,
  }),
  trace: (signal) => request<RunTrace>('/trace', signal),
  replay: (state, trace, requestId, signal) => request('/replay', signal, {
    run_id: state.run_id, expected_revision: state.revision, request_id: requestId, trace,
  }),
};
