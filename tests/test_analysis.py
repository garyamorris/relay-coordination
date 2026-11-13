import json
from pathlib import Path
import pytest
from app.analysis import recommend, consolidate

DEPARTMENTS=['infrastructure','security','finance','support','operations']
SCENARIOS=json.loads((Path(__file__).parent/'scenarios.json').read_text())

@pytest.mark.parametrize('scenario',[s for s in SCENARIOS if s['kind']!='challenge'],ids=lambda s:s['id'])
def test_supported_routing_contract(scenario):
    suggestions=recommend(scenario['body'],DEPARTMENTS,'')
    assert {q['department'] for q in suggestions}==set(scenario['expected'])
    for suggestion in suggestions:
        assert all(evidence in scenario['body'] for evidence in suggestion['evidence'])
        assert suggestion['question'].endswith('?')
        assert suggestion['approved'] is False
        assert suggestion['status']=='suggested'

def test_source_acl_precedes_analysis_and_author_not_notified():
    body=SCENARIOS[0]['body']
    assert recommend(body,[],'')==[]
    assert recommend(body,['security'],'security')==[]
    assert {q['department'] for q in recommend(body,['security'],'infrastructure')}=={'security'}

def test_ambiguous_text_is_not_formal_approval():
    summary=consolidate({'consultations':[{'department':'security','approved':True,'question':'Review?','status':'answered'}],
                         'responses':[{'id':'r1','department':'security','text':'Looks good, probably','stance':'unclear','actions':[]}],
                         'decisions':[]})
    assert summary['decisions']==[]
    assert summary['contradictions']==[]
