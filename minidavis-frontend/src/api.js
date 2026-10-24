// Central backend API configuration and client calls

// 1. Base API URL configured via environment variable, defaulting to local FastAPI port 8000
export const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// 2. Centralized endpoint paths mapped to backend routes defined in README-TECHNICAL.md
export const ENDPOINTS = {
  HEALTH: '/health',
  STATE: '/state',
  RESET: '/reset',
  STEP: '/step', // Advance one tick
};

/**
 * Helper to process responses and extract error details from FastAPI
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (data && data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Response was not JSON
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

/**
 * GET /health
 * Checks readiness and mode of the backend service.
 */
export async function health() {
  const url = `${BASE_URL}${ENDPOINTS.HEALTH}`;
  const response = await fetch(url);
  return handleResponse(response);
}

/**
 * GET /state
 * Fetches the authoritative town snapshot (run_id, tick, revision, map, agents, resources, events).
 */
export async function getState() {
  const url = `${BASE_URL}${ENDPOINTS.STATE}`;
  const response = await fetch(url);
  return handleResponse(response);
}

/**
 * POST /step
 * Advances the simulation by exactly one tick.
 * Requires: { run_id, expected_revision, request_id }
 */
export async function nextTurn(params = {}) {
  const url = `${BASE_URL}${ENDPOINTS.STEP}`;

  // Accept a WorldState object directly, or an object with explicit fields
  const run_id = params.run_id;
  const expected_revision = params.expected_revision ?? params.revision ?? 0;
  const request_id =
    params.request_id || `req-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;

  const body = {
    run_id,
    expected_revision,
    request_id,
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  return handleResponse(response);
}

/**
 * POST /reset
 * Resets the town to its seeded initial state.
 * Accepts: { seed, mode }
 */
export async function reset(seed = 11, mode = 'baseline') {
  const url = `${BASE_URL}${ENDPOINTS.RESET}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ seed, mode }),
  });

  return handleResponse(response);
}
