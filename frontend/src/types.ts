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

export interface Readiness {
  classifier: 'loaded' | 'not_available' | 'unavailable';
  groq_configured: boolean;
  operator_protected: boolean;
  memory_requested: 'lexical' | 'semantic';
}

export interface WorldState {
  run_id: string;
  tick: number;
  revision: number;
  seed: number;
  mode: 'baseline' | 'llm' | 'replay';
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
  trade_offers?: TradeOffer[];
  events: {
    event_id: string;
    run_id: string;
    tick: number;
    agent_id: string;
    target_agent_id?: string | null;
    interaction_id?: string | null;
    participants?: string[];
    action: string;
    outcome: 'accepted' | 'rejected';
    text: string;
    interaction_label?: 'cooperation' | 'conflict' | 'trade' | 'neutral' | string | null;
    confidence?: number | null;
    label?: 'cooperation' | 'conflict' | 'trade' | 'neutral' | string;
    classification?: {
      label: 'cooperation' | 'conflict' | 'trade' | 'neutral' | string;
      confidence?: number;
    };
  }[];
}

export type TownEvent = WorldState['events'][number];

export interface MemoryContext {
  mode: 'semantic' | 'lexical' | 'recent-only';
  query: string;
  as_of_tick: number;
  recent: TownEvent[];
  relevant: TownEvent[];
}

export interface DecisionRecord {
  tick: number;
  observation_revision: number;
  planner_mode: 'baseline' | 'custom' | 'live' | 'cached' | 'waiting' | 'fallback' | 'replay';
  action: string;
  explanation: string;
  memory: MemoryContext;
  event_id: string;
  model_explanation?: string | null;
  model_observation_revision?: number | null;
}

export interface AgentRuntime {
  status: 'baseline' | 'live' | 'waiting' | 'fallback' | 'replay';
  detail: string;
  pending: boolean;
  plan_target?: string | null;
}

export interface TradeOffer {
  offer_id: string;
  proposer_id: string;
  recipient_id: string;
  give_resource: 'food' | 'wood' | 'coins';
  give_amount: number;
  receive_resource: 'food' | 'wood' | 'coins';
  receive_amount: number;
  status: 'pending' | 'accepted' | 'rejected' | 'expired';
}

export interface RunTrace {
  version: 1;
  seed: number;
  source_run_id: string;
  operations: unknown[];
}
