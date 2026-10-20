import type { WorldState } from '../types';

const symbols: Record<string, string> = {
  forest: '♠', farm: '✿', market: '▤', 'town-hall': '⚑', 'house-west': '⌂', 'house-east': '⌂',
};

export function TownMap({ state }: { state: WorldState }) {
  return <div className="town-map" role="img" aria-label={`Town map, turn ${state.tick}, five residents`}>
    {Array.from({ length: state.map.width * state.map.height }, (_, index) => {
      const x = index % state.map.width;
      const y = Math.floor(index / state.map.width);
      const location = state.map.locations.find((place) => place.x === x && place.y === y);
      return <div key={index} className={`tile ${location?.id || ''} ${(x + y) % 2 ? 'alternate' : ''}`}
        title={location?.name}>
        {location && <span className="location-symbol">{symbols[location.id]}</span>}
      </div>;
    })}
    {state.agents.map((agent, index) => <div key={agent.id} className={`resident resident-${agent.id}`}
      data-agent={agent.id} data-x={agent.x} data-y={agent.y}
      title={`${agent.name} · (${agent.x}, ${agent.y})`}
      style={{ left: `${(agent.x + 0.5) / state.map.width * 100}%`, top: `${(agent.y + 0.5) / state.map.height * 100}%`,
        translate: `${(index % 3 - 1) * 4}px ${(index % 2) * 5 - 3}px` }}>
      <span>{agent.name[0]}</span><span className="resident-name">{agent.name}</span>
    </div>)}
  </div>;
}
