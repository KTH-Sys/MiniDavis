/**
 * Controls Component
 *
 * Renders the simulation buttons: Next Turn, Play, Pause, and Reset.
 * Disables buttons based on playback state and active network requests.
 */
function Controls({ onNextTurn, onPlay, onPause, onReset, isPlaying, isLoading }) {
  return (
    <div className="controls-container">
      {/* 1. Next Turn: Advance simulation by a single tick */}
      <button
        type="button"
        className="control-btn"
        onClick={onNextTurn}
        disabled={isPlaying || isLoading}
        title="Advance one tick"
      >
        Next Turn
      </button>

      {/* 2. Play: Continuously advance turns on a timed interval */}
      <button
        type="button"
        className="control-btn play-btn"
        onClick={onPlay}
        disabled={isPlaying || isLoading}
        title="Start auto-playing turns"
      >
        Play
      </button>

      {/* 3. Pause: Stop continuous turn playback */}
      <button
        type="button"
        className="control-btn pause-btn"
        onClick={onPause}
        disabled={!isPlaying || isLoading}
        title="Pause auto-play"
      >
        Pause
      </button>

      {/* 4. Reset: Call /reset to return the town to its seeded starting state */}
      <button
        type="button"
        className="control-btn reset-btn"
        onClick={onReset}
        disabled={isLoading}
        title="Reset town to initial state"
      >
        Reset
      </button>
    </div>
  );
}

export default Controls;
