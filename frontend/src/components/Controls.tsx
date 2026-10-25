interface Props {
  running: boolean;
  busy: boolean;
  replacing: boolean;
  ready: boolean;
  seed: number;
  setSeed: (seed: number) => void;
  play: () => void;
  pause: () => void;
  next: () => void;
  reset: (seed: number) => void;
}

export function Controls({ running, busy, replacing, ready, seed, setSeed, play, pause, next, reset }: Props) {
  const validSeed = Number.isInteger(seed) && seed >= 0 && seed <= 2147483647;
  return <div className="controls" aria-label="Town controls">
    <button className="primary" onClick={running ? pause : play} disabled={!running && (!ready || busy)}>
      {running ? 'Pause' : 'Play'}
    </button>
    <button onClick={next} disabled={!ready || busy || running}>Next Turn</button>
    <span className="control-spacer" />
    <label className="seed-label">Seed
      <input aria-label="Seed" type="number" min="0" max="2147483647" step="1" value={Number.isNaN(seed) ? '' : seed}
        onChange={(event) => setSeed(event.target.valueAsNumber)} />
    </label>
    <button onClick={() => reset(seed)} disabled={!validSeed || replacing}>Reset</button>
  </div>;
}
