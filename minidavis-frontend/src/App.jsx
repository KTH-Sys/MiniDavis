import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import TownMap from './TownMap';
import Controls from './Controls';
import { getState, nextTurn, reset, BASE_URL } from './api';
import { residents as defaultResidents, RESIDENT_COLORS } from './data';
import './App.css';

// Default interval between turns in Play mode (1000 milliseconds)
const PLAY_INTERVAL_MS = 1000;

function App() {
  // Authoritative simulation state from backend: { run_id, tick, revision, agents, ... }
  const [worldState, setWorldState] = useState(null);

  // Status indicator: "Connected" | "Playing" | "Paused" | "Backend unreachable"
  const [status, setStatus] = useState('Connecting...');

  // Flag indicating if we are using fallback mock data from src/data.js
  const [isOffline, setIsOffline] = useState(false);

  // Playback & request activity states
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Error message state to display to the user without crashing
  const [errorMessage, setErrorMessage] = useState(null);

  // Refs to avoid stale closures in timeouts and async loops
  const isPlayingRef = useRef(false);
  const isBusyRef = useRef(false);
  const timerRef = useRef(null);
  const worldStateRef = useRef(null);
  const scheduleNextTurnRef = useRef(null);

  // Keep worldStateRef synchronized with latest worldState
  useEffect(() => {
    worldStateRef.current = worldState;
  }, [worldState]);

  // Execute a single tick step against the backend
  const executeStep = useCallback(async () => {
    // Prevent firing a new request while the previous one is still in flight
    if (isBusyRef.current) {
      return false;
    }

    isBusyRef.current = true;
    setIsLoading(true);

    try {
      const currentState = worldStateRef.current;
      let nextState;

      // If we don't have an active backend state yet, attempt /state to connect
      if (!currentState || !currentState.run_id) {
        nextState = await getState();
      } else {
        nextState = await nextTurn(currentState);
      }

      setWorldState(nextState);
      worldStateRef.current = nextState;
      setIsOffline(false);
      setErrorMessage(null);
      return true;
    } catch (error) {
      // On failure: stop Play, display error message, and do not crash
      const msg = error.message || 'Failed to communicate with backend.';
      setErrorMessage(msg);
      setStatus('Backend unreachable');

      setIsPlaying(false);
      isPlayingRef.current = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return false;
    } finally {
      isBusyRef.current = false;
      setIsLoading(false);
    }
  }, []);

  // Chained setTimeout loop: ensures a new request only fires AFTER the previous one completes
  const scheduleNextTurn = useCallback(() => {
    if (!isPlayingRef.current) return;

    timerRef.current = setTimeout(async () => {
      // Re-verify that user didn't pause while waiting
      if (!isPlayingRef.current) return;

      const success = await executeStep();

      // Chain the next turn only if the current step succeeded and play wasn't paused
      if (success && isPlayingRef.current) {
        scheduleNextTurnRef.current?.();
      }
    }, PLAY_INTERVAL_MS);
  }, [executeStep]);

  // Keep ref up to date with scheduleNextTurn callback
  useEffect(() => {
    scheduleNextTurnRef.current = scheduleNextTurn;
  }, [scheduleNextTurn]);

  // 1. Initial connection: fetch /state on mount
  useEffect(() => {
    let isMounted = true;

    async function loadInitial() {
      setIsLoading(true);
      try {
        const state = await getState();
        if (isMounted) {
          setWorldState(state);
          worldStateRef.current = state;
          setIsOffline(false);
          setStatus('Connected');
          setErrorMessage(null);
        }
      } catch (error) {
        if (isMounted) {
          // Backend is unreachable: fallback to mock data and label clearly
          console.warn('Initial backend fetch failed, using fallback data:', error);
          setIsOffline(true);
          setStatus('Backend unreachable');
          setErrorMessage(`Backend unreachable at ${BASE_URL}. Using offline / mock data.`);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadInitial();

    // Clean up timer on unmount
    return () => {
      isMounted = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  // 2. Next Turn handler
  const handleNextTurn = useCallback(async () => {
    if (isPlaying || isLoading) return;
    const success = await executeStep();
    if (success) {
      setStatus((prev) => (prev === 'Playing' ? 'Playing' : 'Connected'));
    }
  }, [isPlaying, isLoading, executeStep]);

  // 3. Play handler: start recurring turns using chained setTimeout
  const handlePlay = useCallback(() => {
    if (isPlaying || isLoading) return;
    setIsPlaying(true);
    isPlayingRef.current = true;
    setStatus('Playing');
    setErrorMessage(null);

    // Schedule the next turn
    scheduleNextTurn();
  }, [isPlaying, isLoading, scheduleNextTurn]);

  // 4. Pause handler: clear any pending timer and update status
  const handlePause = useCallback(() => {
    setIsPlaying(false);
    isPlayingRef.current = false;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setStatus('Paused');
  }, []);

  // 5. Reset handler: reset town via /reset, stop Play, and refresh state
  const handleReset = useCallback(async () => {
    // Stop Play when Reset is triggered
    setIsPlaying(false);
    isPlayingRef.current = false;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    if (isBusyRef.current) return;
    isBusyRef.current = true;
    setIsLoading(true);

    try {
      const resetState = await reset();
      setWorldState(resetState);
      worldStateRef.current = resetState;
      setIsOffline(false);
      setStatus('Connected');
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error.message || 'Failed to reset town simulation.');
      setStatus('Backend unreachable');
    } finally {
      isBusyRef.current = false;
      setIsLoading(false);
    }
  }, []);

  // Compute residents to display: use backend agents with assigned colors if available,
  // otherwise fallback to the hardcoded residents in src/data.js
  const displayedResidents = useMemo(() => {
    if (worldState && Array.isArray(worldState.agents) && worldState.agents.length > 0) {
      return worldState.agents.map((agent) => ({
        id: agent.id,
        name: agent.name,
        x: agent.x,
        y: agent.y,
        color: agent.color || RESIDENT_COLORS[agent.id] || '#457b9d',
      }));
    }
    return defaultResidents;
  }, [worldState]);

  // Current tick number from authoritative backend state or 0 for mock
  const currentTick = worldState ? worldState.tick : 0;

  return (
    <div className="app">
      <h1>MiniDavis</h1>

      {/* Status Bar: shows Current Tick, Status Line, and Offline/Mock label */}
      <div className="status-bar">
        <div className="status-item">
          <span className="status-title">Tick:</span>
          <span className="tick-number">{currentTick}</span>
        </div>

        <div className="status-item">
          <span className="status-title">Status:</span>
          <span className={`status-pill status-${status.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}>
            {status}
          </span>
          {isOffline && <span className="mock-badge">offline / mock</span>}
        </div>
      </div>

      {/* Error message banner (if any network or backend error occurs) */}
      {errorMessage && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Controls: Next Turn, Play, Pause, Reset */}
      <Controls
        onNextTurn={handleNextTurn}
        onPlay={handlePlay}
        onPause={handlePause}
        onReset={handleReset}
        isPlaying={isPlaying}
        isLoading={isLoading}
      />

      {/* Town Map Grid */}
      <TownMap residents={displayedResidents} />
    </div>
  );
}

export default App;
