import { cleanup,fireEvent,render,screen,waitFor } from '@testing-library/react';
import { afterEach,expect,it,vi } from 'vitest';
import { ClassifierProbe } from './ClassifierProbe';
import { townApi } from '../api';
vi.mock('../api',()=>({townApi:{classify:vi.fn()}}));
afterEach(()=>{cleanup();vi.resetAllMocks();});
it('shows only the returned real prediction and clears it after the input changes',async()=>{
  vi.mocked(townApi.classify!).mockResolvedValue({label:'cooperation',confidence:.76});
  render(<ClassifierProbe/>);
  fireEvent.click(screen.getByText('Classify example'));
  await waitFor(()=>expect(screen.getByRole('status').textContent).toContain('cooperation'));
  expect(screen.getByRole('status').textContent).toContain('76.0%');
  fireEvent.change(screen.getByLabelText('Interaction text'),{target:{value:'A different example'}});
  expect(screen.queryByRole('status')).toBeNull();
});
it('reports a loading failure without inventing a label',async()=>{
  vi.mocked(townApi.classify!).mockRejectedValue(new Error('Classifier unavailable'));
  render(<ClassifierProbe/>);fireEvent.click(screen.getByText('Classify example'));
  await waitFor(()=>expect(screen.getByRole('alert').textContent).toBe('Classifier unavailable'));
  expect(screen.queryByRole('status')).toBeNull();
});
