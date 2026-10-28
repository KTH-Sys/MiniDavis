"""Real CPU MiniLM API/evidence check; no Groq calls or API key required."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.app.config import Settings
from backend.app.main import create_app


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix='minidavis-day4-api-') as folder:
        config = Settings(_env_file=None, memory_db_path=str(Path(folder) / 'events.sqlite'),
                          llm_api_key='', minidavis_mode='baseline', memory_retrieval_mode='semantic',
                          embedding_cache_path=str(ROOT / 'data/model-cache'))
        with TestClient(create_app(config)) as client:
            state = client.get('/state').json()
            for index in range(3):
                response = client.post('/step', json={'run_id': state['run_id'],
                    'expected_revision': state['revision'], 'request_id': f'audit-{index}'})
                response.raise_for_status()
                state = response.json()
            for agent in state['agents']:
                response = client.get(f"/agents/{agent['id']}", params={
                    'run_id': state['run_id'], 'revision': state['revision']})
                response.raise_for_status()
                body = response.json()
                memory = body['retrieval']
                assert body['decision'] == state['decisions'][agent['id']]
                assert memory == body['decision']['memory']
                assert memory['mode'] == 'semantic'
                assert memory['recent']  # relevant can be empty when no score is positive
                assert len(memory['recent']) <= 5 and len(memory['relevant']) <= 3
                sources = memory['recent'] + memory['relevant']
                assert all(e['run_id'] == state['run_id'] and e['agent_id'] == agent['id']
                           and e['tick'] <= memory['as_of_tick'] < body['decision']['tick'] for e in sources)
                checks.append({'agent_id': agent['id'], 'mode': memory['mode'],
                               'recent_count': len(memory['recent']), 'relevant_count': len(memory['relevant']),
                               'source_ids': sorted({e['event_id'] for e in sources}), 'passed': True})
            old_run = state['run_id']
            reset = client.post('/reset', json={'seed': 11}).json()
            assert reset['run_id'] != old_run
            for agent in state['agents']:
                assert client.get(f"/agents/{agent['id']}").json()['retrieval']['recent'] == []
            assert reset['provider_usage']['calls_run'] == 0
    report = {'passed': True, 'retrieval': 'real MiniLM CPU', 'agents': checks,
              'reset_isolation': True, 'provider_calls': 0}
    path = ROOT / 'results/day0-day4/semantic-api.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
