import { useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import type { Resident, WorldState } from '../types';
import { PixelResident } from './PixelResident';

function MovingResident({ agent, state, selected, onSelect }: {
  agent: Resident; state: WorldState; selected: boolean; onSelect?: (id: string) => void;
}) {
  const previous = useRef({ x: agent.x, y: agent.y, run: state.run_id });
  const [walking, setWalking] = useState(false);
  useEffect(() => {
    const moved = previous.current.run === state.run_id && (previous.current.x !== agent.x || previous.current.y !== agent.y);
    previous.current = { x: agent.x, y: agent.y, run: state.run_id };
    setWalking(moved);
    if (moved) {
      const timer = window.setTimeout(() => setWalking(false), 580);
      return () => window.clearTimeout(timer);
    }
  }, [agent.x, agent.y, state.run_id]);
  const others = state.agents.filter((item) => item.x === agent.x && item.y === agent.y);
  // Keep each sprite's center clickable when residents share a logical tile.
  const offset = (others.findIndex((item) => item.id === agent.id) - (others.length - 1) / 2) * 40;
  const action = state.decisions?.[agent.id]?.action;
  return <button className={`resident resident-${agent.id} ${walking ? 'is-walking' : ''} ${selected ? 'is-selected' : ''}`}
    aria-label={`Inspect ${agent.name}`} aria-pressed={selected} onClick={() => onSelect?.(agent.id)}
    data-agent={agent.id} data-x={agent.x} data-y={agent.y} data-walking={walking}
    title={`${agent.name} · (${agent.x}, ${agent.y})`}
    style={{ left: `${(agent.x + .5) / state.map.width * 100}%`, top: `${(agent.y + .5) / state.map.height * 100}%`,
      marginLeft: offset, zIndex: 20 + agent.y + (selected ? 20 : 0) }}>
    {selected && <span className="selection-arrow">▼</span>}
    <PixelResident id={agent.id} walking={walking} action={walking ? undefined : action} />
    <span className="resident-name">{agent.name}</span>
  </button>;
}

export function TownMap({ state, selectedId, onSelect, running = false, showGrid = true }: {
  state: WorldState; selectedId?: string; onSelect?: (id: string) => void; running?: boolean; showGrid?: boolean;
}) {
  return <div className={`town-map ${running ? 'is-running' : ''}`} role="group"
    aria-label={`Town map, turn ${state.tick}, five residents`}
    style={{ '--grid-width': `${100 / state.map.width}%`, '--grid-height': `${100 / state.map.height}%` } as CSSProperties}>
    <img className="town-art" src="/art/minidavis-town.png" alt="" draggable="false" />
    {showGrid && <div className="tile-grid" aria-hidden="true" />}
    <div className="ambient smoke smoke-west" aria-hidden="true" />
    <div className="ambient smoke smoke-east" aria-hidden="true" />
    <div className="ambient water-sparkle sparkle-one" aria-hidden="true">✦</div>
    <div className="ambient water-sparkle sparkle-two" aria-hidden="true">✦</div>
    {state.map.locations.map((location) => <span key={location.id} className={`location-marker marker-${location.id}`}
      style={{ left: `${(location.x + .5) / state.map.width * 100}%`, top: `${(location.y + .5) / state.map.height * 100}%` }}>
      {location.name}
    </span>)}
    {state.agents.map((agent) => <MovingResident key={`${state.run_id}:${agent.id}`} agent={agent} state={state}
      selected={selectedId === agent.id} onSelect={onSelect} />)}
  </div>;
}
