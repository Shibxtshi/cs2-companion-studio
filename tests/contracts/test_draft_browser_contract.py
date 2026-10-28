"""Keep the browser's generated model and semantic corpus aligned with P3."""
import copy
import json
from pathlib import Path

import pytest
from companion.profile_contracts import ContractError, Profile, validate_contract
from scripts.generate_profile_schema import generated_source

ROOT = Path(__file__).resolve().parents[2]
CORPUS = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))
CORPUS['draft'] = {**CORPUS['draftMetadata'], 'name': CORPUS['profile']['name'],
                   'configuration': copy.deepcopy(CORPUS['profile']['configuration'])}


def test_generated_browser_schema_is_current():
    assert (ROOT / 'static/js/draft-schema.js').read_text('utf-8') == generated_source()


@pytest.mark.parametrize('case', CORPUS['cases'], ids=lambda case: case['name'])
def test_browser_semantic_corpus_matches_authoritative_validation(case):
    value = copy.deepcopy(CORPUS[case['kind']])
    for change in case['changes']:
        parent = value
        for key in change['path'][:-1]:
            parent = parent[key]
        if change.get('remove'):
            del parent[change['path'][-1]]
        elif change.get('repeatWidget'):
            widget = CORPUS['profile']['configuration']['layout']['widgets'][0]
            parent[change['path'][-1]] = [{**widget, 'id': 'w' + str(index)}
                                        for index in range(change['repeatWidget'])]
        else:
            parent[change['path'][-1]] = change['value']
    def validate():
        if case['kind'] == 'profile':
            Profile.model_validate(value)
        else:
            validate_contract(value, case['kind'])
    if case['valid']:
        validate()
    else:
        with pytest.raises((ContractError, ValueError)):
            validate()
