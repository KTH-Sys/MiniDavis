import { cleanup,fireEvent,render,screen,waitFor } from '@testing-library/react';
import { afterEach,beforeEach,expect,it,vi } from 'vitest';
import App from './App';
import { useTown } from './hooks/useTown';
import { loadSampleTrace } from './api';
vi.mock('./hooks/useTown',()=>({useTown:vi.fn()}));
vi.mock('./api',async(importOriginal)=>({...await importOriginal<typeof import('./api')>(),loadSampleTrace:vi.fn()}));
const resident={id:'ethan',name:'Ethan',goal:'Gather supplies',x:1,y:1,food:3,wood:0,coins:10,energy:100,relationships:{}};
let town:ReturnType<typeof useTown>;
beforeEach(()=>{
  town={state:{run_id:'r',tick:0,revision:0,seed:11,mode:'baseline',map:{width:12,height:12,locations:[]},agents:[resident],resources:[],events:[]},
    readiness:{classifier:'loaded',groq_configured:true,operator_protected:false,memory_requested:'semantic'},
    running:false,busy:false,replacing:false,error:null,play:vi.fn(),pause:vi.fn(),next:vi.fn(),reset:vi.fn(),shortage:vi.fn(),replay:vi.fn(),reconnect:vi.fn()};
  vi.mocked(useTown).mockReturnValue(town);
});
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('opens with a simple audience view and keeps technical setup out of the demo',()=>{
  render(<App/>);
  expect(screen.getByRole('button',{name:'Play'})).toBeTruthy();
  expect(screen.getByRole('button',{name:'Recorded example'})).toBeTruthy();
  expect(screen.queryByRole('tab',{name:'Memories'})).toBeNull();
  expect(screen.queryByLabelText('Seed')).toBeNull();
  expect(screen.queryByText('Try the trained classifier')).toBeNull();
  expect(screen.queryByLabelText('Operator key')).toBeNull();
  expect(screen.queryByText(/Groq calls/)).toBeNull();
});
it('reveals setup and inspectors only when the presenter opens the tools',()=>{
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Presenter tools'}));
  expect(screen.getByRole('tab',{name:'Memories'})).toBeTruthy();
  expect(screen.getByLabelText('Seed')).toBeTruthy();
  expect(screen.getByText('Try the trained classifier')).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Close tools'}));
  expect(screen.queryByRole('tab',{name:'Memories'})).toBeNull();
});
it('loads the recorded example through replay without fabricating a live AI decision',async()=>{
  const trace={version:1 as const,seed:11,source_run_id:'fixture',operations:[]};
  vi.mocked(loadSampleTrace).mockResolvedValue(trace);
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Recorded example'}));
  await waitFor(()=>expect(town.replay).toHaveBeenCalledWith(trace));
  expect(town.next).not.toHaveBeenCalled();
});
