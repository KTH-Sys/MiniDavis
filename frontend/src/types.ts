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
  mode: 'baseline' | 'llm';
  decisions?: Record<string, DecisionRecord>;
  agent_runtime?: Record<string, AgentRuntime>;
  provider_usage?: { calls_run: number; calls_day: number; tokens_day: number; reserved_tokens_day: number; cooldown_seconds: number };
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
    target_agent_id?: string;
    participants?: string[];
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
  planner_mode: 'baseline' | 'custom' | 'live' | 'cached' | 'waiting' | 'fallback';
  action: string;
  explanation: string;
  memory: MemoryContext;
  event_id: string;
  model_explanation?: string | null;
  model_observation_revision?: number | null;
}

export interface AgentRuntime {
  status: 'baseline' | 'live' | 'waiting' | 'fallback';
  detail: string;
  pending: boolean;
  plan_target?: string | null;
}
