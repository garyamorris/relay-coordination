"""Behavioral acceptance tests for the local synthetic coordination MVP."""
import importlib
import pytest
from fastapi.testclient import TestClient

BODY = ('Replace the production hosting platform. Review access controls and compliance. '
        'Budget and procurement need a decision. Application support must confirm '
        'supportability and ownership. Business operations must assess service impact '
        'and business requirements.')
USERS = {'infrastructure':'maya','security':'sam','finance':'finn','support':'alex','operations':'olivia'}

@pytest.fixture
def app_path(tmp_path):
    return str(tmp_path / 'coordination.sqlite')

@pytest.fixture
def client(app_path):
    from app.main import create_app
    with TestClient(create_app(app_path)) as c:
        yield c

def auth(client, user='maya'):
    response = client.post('/api/login', json={'user_id': user})
    assert response.status_code == 200, response.text
    return {'Authorization': 'Bearer ' + response.json()['token']}

def create(client, allowed=None):
    payload = {'title':'Replace production platform','body':BODY}
    if allowed is not None:
        payload['allowed_departments'] = allowed
    response = client.post('/api/discussions', headers=auth(client), json=payload)
    assert response.status_code in (200,201), response.text
    return response.json()

def review(client, discussion, approved=None, request_id='review-1'):
    decisions = [{ 'department': q['department'], 'question': q['question'],
                   'approved': approved is None or q['department'] in approved }
                 for q in discussion['consultations']]
    return client.post('/api/discussions/'+discussion['id']+'/review',headers=auth(client),
                       json={'consultations':decisions,'request_id':request_id})

def respond(client, discussion, department, stance='support', request_id=None, **extra):
    return client.post('/api/discussions/'+discussion['id']+'/responses',
                       headers=auth(client, USERS[department]),
                       json={'department':department,'text':'Recorded department assessment.',
                             'stance':stance,'request_id':request_id or 'response-'+department,**extra})

def test_no_access_without_authentication(client):
    assert client.get('/api/discussions').status_code == 401
    assert client.get('/api/discussions',headers={'Authorization':'Bearer invented'}).status_code == 401

def test_no_delivery_before_human_approval(client):
    d = create(client)
    assert d['status'] == 'review_required'
    assert d['analysis_mode'] == 'deterministic-baseline'
    assert {q['department'] for q in d['consultations']} == {'security','finance','support','operations'}
    assert all(q['evidence'] and q['reason'] for q in d['consultations'])
    assert client.get('/api/discussions',headers=auth(client,'sam')).json() == []
    assert client.get('/api/discussions/'+d['id'],headers=auth(client,'sam')).status_code in (403,404)
    assert respond(client,d,'security').status_code in (403,404,409)

def test_approval_edits_and_rejection_control_delivery(client):
    d = create(client)
    decisions = [{'department':q['department'],'question':'Please confirm access review owner.' if q['department']=='security' else q['question'],
                  'approved':q['department']=='security'} for q in d['consultations']]
    r = client.post('/api/discussions/'+d['id']+'/review',headers=auth(client),json={'consultations':decisions})
    assert r.status_code == 200, r.text
    recipient = client.get('/api/discussions/'+d['id'],headers=auth(client,'sam')).json()
    assert len(recipient['consultations']) == 1
    assert recipient['consultations'][0]['question'] == 'Please confirm access review owner.'
    assert 'audit' not in recipient and 'summary' not in recipient
    assert client.get('/api/discussions',headers=auth(client,'finn')).json() == []
    assert client.get('/api/discussions/'+d['id'],headers=auth(client,'finn')).status_code in (403,404)

def test_full_async_workflow_and_explicit_decision(client):
    d = create(client)
    r = review(client,d)
    assert r.status_code == 200, r.text
    assert r.json()['status'] == 'awaiting_responses'
    for index, dept in enumerate(['security','finance','support','operations']):
        r = respond(client,d,dept,actions=[{'text':'Confirm change owner','owner':USERS[dept],'due_date':'2030-01-01'}])
        assert r.status_code == 200, r.text
        owner = client.get('/api/discussions/'+d['id'],headers=auth(client)).json()
        assert len(owner['responses']) == index+1
        if index < 3:
            assert owner['status'] == 'awaiting_responses'
    assert owner['status'] == 'ready_for_decision'
    assert owner['summary']['actions']
    assert not any(x.get('status')=='approved' for x in owner['summary']['decisions'])
    r=client.post('/api/discussions/'+d['id']+'/decision',headers=auth(client),json={'text':'Proceed after recorded actions','status':'approved'})
    assert r.status_code == 200, r.text
    assert any(x['status']=='approved' for x in r.json()['summary']['decisions'])

def test_acl_filters_before_recommendations_and_cannot_be_widened(client):
    d = create(client,['infrastructure','security'])
    assert {q['department'] for q in d['consultations']} == {'security'}
    r=client.post('/api/discussions/'+d['id']+'/review',headers=auth(client),json={'consultations':[{'department':'finance','question':'Share all private cost details','approved':True}]})
    assert r.status_code in (400,403,422),r.text
    assert client.get('/api/discussions',headers=auth(client,'finn')).json()==[]

def test_wrong_department_cannot_respond_or_review(client):
    d=create(client)
    assert client.post('/api/discussions/'+d['id']+'/review',headers=auth(client,'sam'),json={'consultations':[]}).status_code in (403,404)
    assert review(client,d).status_code==200
    r=client.post('/api/discussions/'+d['id']+'/responses',headers=auth(client,'sam'),json={'department':'finance','text':'Approved by finance','stance':'support'})
    assert r.status_code==403,r.text
    assert client.post('/api/discussions/'+d['id']+'/stop',headers=auth(client,'sam'),json={}).status_code==403
    assert client.post('/api/discussions/'+d['id']+'/decision',headers=auth(client,'sam'),json={'text':'Approved','status':'approved'}).status_code==403

def test_duplicate_review_and_response_do_not_duplicate_records(client):
    d=create(client)
    assert review(client,d).status_code==200
    r=review(client,d)
    assert r.status_code in (200,409),r.text
    assert respond(client,d,'security').status_code==200
    r=respond(client,d,'security')
    assert r.status_code in (200,409),r.text
    current=client.get('/api/discussions/'+d['id'],headers=auth(client)).json()
    assert len(current['consultations'])==4
    assert len(current['responses'])==1

def test_conflicting_feedback_is_not_an_approval(client):
    d=create(client)
    assert review(client,d).status_code==200
    for dept in ['security','finance','support','operations']:
        assert respond(client,d,dept,'concern' if dept=='security' else 'support').status_code==200
    current=client.get('/api/discussions/'+d['id'],headers=auth(client)).json()
    assert current['status']=='blocked'
    assert current['summary']['contradictions']
    assert current['summary']['risks']
    r=client.post('/api/discussions/'+d['id']+'/decision',headers=auth(client),json={'text':'Proceed','status':'approved'})
    assert r.status_code in (400,409),r.text

def test_unclear_response_remains_unresolved(client):
    d=create(client)
    assert review(client,d,{'security'}).status_code==200
    assert respond(client,d,'security','unclear').status_code==200
    current=client.get('/api/discussions/'+d['id'],headers=auth(client)).json()
    assert current['status']=='blocked'
    assert not any(x.get('status')=='approved' for x in current['summary']['decisions'])

def test_stop_blocks_future_mutations(client):
    d=create(client)
    assert review(client,d).status_code==200
    r=client.post('/api/discussions/'+d['id']+'/stop',headers=auth(client),json={})
    assert r.status_code==200 and r.json()['status']=='stopped'
    assert respond(client,d,'security').status_code==409
    assert review(client,d,request_id='different-review').status_code==409
    assert client.post('/api/discussions/'+d['id']+'/decision',headers=auth(client),json={'text':'Proceed','status':'approved'}).status_code==409

def test_checkpoint_survives_app_recreation(app_path):
    from app.main import create_app
    with TestClient(create_app(app_path)) as first:
        d=create(first)
    with TestClient(create_app(app_path)) as second:
        restored=second.get('/api/discussions/'+d['id'],headers=auth(second)).json()
        assert restored['status']=='review_required'
        assert review(second,restored,{'security'}).status_code==200
    with TestClient(create_app(app_path)) as third:
        assert respond(third,d,'security').status_code==200
        restored=third.get('/api/discussions/'+d['id'],headers=auth(third)).json()
        assert restored['status']=='ready_for_decision'
        assert len(restored['responses'])==1

def test_recipient_cannot_read_other_department_response(client):
    d=create(client)
    assert review(client,d).status_code==200
    assert respond(client,d,'finance',text='Financial department private response').status_code==200
    recipient=client.get('/api/discussions/'+d['id'],headers=auth(client,'sam')).json()
    assert 'Financial department private response' not in str(recipient)
    assert all(q['department']=='security' for q in recipient['consultations'])

@pytest.mark.parametrize('field,value', [('question','        '),('question','')])
def test_blank_approved_question_rejected(client,field,value):
    d=create(client)
    r=client.post('/api/discussions/'+d['id']+'/review',headers=auth(client),json={'consultations':[{'department':'security','question':value,'approved':True}]})
    assert r.status_code in (400,422),r.text

def test_blank_response_rejected(client):
    d=create(client)
    assert review(client,d,{'security'}).status_code==200
    assert respond(client,d,'security',text='   ').status_code in (400,422)

def test_reused_request_id_with_different_payload_rejected(client):
    d=create(client)
    assert review(client,d,{'security'},request_id='same').status_code==200
    r=review(client,d,{'finance'},request_id='same')
    assert r.status_code==409,r.text
    assert respond(client,d,'security',request_id='reply').status_code==200
    r=respond(client,d,'security',request_id='reply',text='Changed assessment')
    assert r.status_code==409,r.text

def test_blank_override_reason_does_not_authorize_decision(client):
    d=create(client)
    assert review(client,d,{'security'}).status_code==200
    assert respond(client,d,'security','concern').status_code==200
    r=client.post('/api/discussions/'+d['id']+'/decision',headers=auth(client),json={'text':'Proceed','status':'approved','override_reason':'   '})
    assert r.status_code in (400,409,422),r.text

def test_stopped_workflow_remains_stopped_after_restart(app_path):
    from app.main import create_app
    with TestClient(create_app(app_path)) as first:
        d=create(first)
        assert first.post('/api/discussions/'+d['id']+'/stop',headers=auth(first),json={}).status_code==200
    with TestClient(create_app(app_path)) as second:
        restored=second.get('/api/discussions/'+d['id'],headers=auth(second)).json()
        assert restored['status']=='stopped'
        assert review(second,d).status_code==409

def test_resume_after_failure_between_response_and_summary(app_path,monkeypatch):
    from app.main import create_app
    import app.workflow as workflow
    first_app=create_app(app_path)
    with TestClient(first_app,raise_server_exceptions=False) as first:
        d=create(first)
        assert review(first,d,{'security'}).status_code==200
        original=workflow.consolidate
        def fail_once(state):
            raise RuntimeError('Injected failure after response checkpoint')
        monkeypatch.setattr(workflow,'consolidate',fail_once)
        assert respond(first,d,'security').status_code==500
        snapshot=first_app.state.graph.get_state({'configurable':{'thread_id':d['id']}})
        assert snapshot.next==('summarize',)
        assert len(snapshot.values['responses'])==1
        monkeypatch.setattr(workflow,'consolidate',original)
    with TestClient(create_app(app_path)) as second:
        r=second.get('/api/discussions/'+d['id'],headers=auth(second))
        assert r.status_code==200,r.text
        assert r.json()['status']=='ready_for_decision'
        assert len(r.json()['responses'])==1
        assert respond(second,d,'security').status_code==200
        assert len(second.get('/api/discussions/'+d['id'],headers=auth(second)).json()['responses'])==1

def test_create_request_replay_and_payload_conflict(client):
    payload={'title':'Budget request','body':'Review budget for new license.','request_id':'stable-create'}
    first=client.post('/api/discussions',headers=auth(client),json=payload)
    second=client.post('/api/discussions',headers=auth(client),json=payload)
    assert first.status_code==second.status_code==200
    assert first.json()['id']==second.json()['id']
    conflict=client.post('/api/discussions',headers=auth(client),json={**payload,'body':'Review procurement for a different project.'})
    assert conflict.status_code==409
    assert len(client.get('/api/discussions',headers=auth(client)).json())==1

def test_overdue_escalation_is_deduplicated_and_response_remains_possible(client):
    d=create(client)
    assert review(client,d,{'security'}).status_code==200
    config={'configurable':{'thread_id':d['id']}}
    graph=client.app.state.graph
    state=graph.get_state(config).values
    # Test fixture only: age the deadline without sleeping or changing the machine clock.
    consultations=[dict(q,due_at='2000-01-01T00:00:00+00:00') if q['approved'] else q for q in state['consultations']]
    graph.update_state(config,{'consultations':consultations})
    for _ in range(2):
        result=client.post('/api/discussions/'+d['id']+'/escalate',headers=auth(client),json={})
        assert result.status_code==200,result.text
    assert len([a for a in result.json()['audit'] if a['event']=='consultation_escalated'])==1
    assert respond(client,d,'security').status_code==200
