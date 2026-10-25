export interface Resident {
  id: string;
  name: string;
  goal: string;
  x: number;
  y: number;
  food: number;
  wood: number;
  coins: number;
  energy: number;
  relationships: Record<string, number>;
}

export interface WorldState {
  run_id: string;
  tick: number;
  revision: number;
  seed: number;
  mode: 'baseline';
  decisions?: Record<string, DecisionRecord>;
  map: {
    width: number;
    height: number;
    locations: { id: string; name: string; x: number; y: number }[];
  };
  agents: Resident[];
  resources: { id: string; kind: 'food' | 'wood'; x: number; y: number; stock: number }[];
  events: {
    event_id: string;
    run_id: string;
    tick: number;
    agent_id: string;
    action: string;
    outcome: 'accepted' | 'rejected';
    text: string;
  }[];
}

export type TownEvent = WorldState['events'][number];

export interface MemoryContext {
  mode: 'lexical' | 'recent-only';
  query: string;
  as_of_tick: number;
  recent: TownEvent[];
  relevant: TownEvent[];
}

export interface DecisionRecord {
  tick: number;
  observation_revision: number;
  planner_mode: 'baseline' | 'custom';
  action: string;
  explanation: string;
  memory: MemoryContext;
  event_id: string;
}
