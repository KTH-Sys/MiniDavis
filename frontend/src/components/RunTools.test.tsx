import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { RunTools } from './RunTools';
import { setOperatorKey } from '../api';

vi.mock('../api', async (importOriginal) => ({...await importOriginal<typeof import('../api')>(),setOperatorKey:vi.fn(),townApi:{trace:vi.fn()}}));
afterEach(()=>{cleanup();vi.clearAllMocks();});

it('sets a tab-only operator key and clears the visible input',()=>{
  const reconnect=vi.fn();
  render(<RunTools disabled={false} replaying={false} shortage={vi.fn()} replay={vi.fn()} reconnect={reconnect}/>);
  const input=screen.getByLabelText('Operator key') as HTMLInputElement;
  fireEvent.change(input,{target:{value:'operator-fixture'}});
  fireEvent.submit(input.closest('form')!);
  expect(setOperatorKey).toHaveBeenCalledWith('operator-fixture');
  expect(input.value).toBe('');
  expect(reconnect).toHaveBeenCalledOnce();
});

it('loads a saved run rather than advancing the live simulation',async()=>{
  const replay=vi.fn();
  render(<RunTools disabled={false} replaying={false} shortage={vi.fn()} replay={replay} reconnect={vi.fn()}/>);
  const trace={version:1,seed:11,source_run_id:'r',operations:[]};
  const file=new File([JSON.stringify(trace)],'run.json',{type:'application/json'});
  Object.defineProperty(file,'text',{value:async()=>JSON.stringify(trace)});
  fireEvent.change(screen.getByLabelText('Replay saved run'),{target:{files:[file]}});
  await waitFor(()=>expect(replay).toHaveBeenCalledWith(trace));
});

it('hides operator access locally and makes a live-mode reset explicit',()=>{
  const startMode=vi.fn();
  render(<RunTools disabled={false} replaying={false} shortage={vi.fn()} replay={vi.fn()} reconnect={vi.fn()}
    mode="baseline" readiness={{classifier:'loaded',groq_configured:true,operator_protected:false,memory_requested:'semantic'}} startMode={startMode}/>);
  expect(screen.queryByLabelText('Operator key')).toBeNull();
  fireEvent.change(screen.getByLabelText('Town mode'),{target:{value:'llm'}});
  fireEvent.click(screen.getByText('Start new town'));
  expect(startMode).toHaveBeenCalledWith('llm');
});

it('loads the clearly labelled sample trace without advancing the town',async()=>{
  const trace={version:1,seed:11,source_run_id:'sample',operations:[]};
  const replay=vi.fn();
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>trace}));
  try {
    render(<RunTools disabled={false} replaying={false} shortage={vi.fn()} replay={replay} reconnect={vi.fn()}/>);
    fireEvent.click(screen.getByText('Load sample run'));
    await waitFor(()=>expect(replay).toHaveBeenCalledWith(trace));
    expect(screen.getByRole('status').textContent).toContain('scripted actions');
  } finally {vi.unstubAllGlobals();}
});
