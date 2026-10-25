import type { WorldState } from './types';

const base = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

export interface TownApi {
  state(signal: AbortSignal): Promise<WorldState>;
  step(state: WorldState, requestId: string, signal: AbortSignal): Promise<WorldState>;
  reset(seed: number, signal: AbortSignal): Promise<WorldState>;
}

async function request(path: string, signal: AbortSignal, body?: object): Promise<WorldState> {
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      signal,
      method: body ? 'POST' : 'GET',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new Error('Cannot reach the town. Start the backend, then reconnect.');
  }
  if (!response.ok) {
    throw new ApiError(response.status, response.status === 409
      ? 'The town changed in another window. Reconnect before continuing.'
      : `The town could not complete that request (${response.status}). Reconnect to check its state.`);
  }
  return response.json() as Promise<WorldState>;
}

export const townApi: TownApi = {
  state: (signal) => request('/state', signal),
  step: (state, requestId, signal) => request('/step', signal, {
    run_id: state.run_id,
    expected_revision: state.revision,
    request_id: requestId,
  }),
  reset: (seed, signal) => request('/reset', signal, { seed, mode: 'baseline' }),
};
