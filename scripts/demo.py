#!/usr/bin/env python3
"""Run a synthetic, human-approved coordination journey against the local API."""
import argparse
import json
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def run(base_url):
    base_url = base_url.rstrip('/')

    def api(method, path, body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = Request(base_url + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except HTTPError as exc:
            # Never print request headers, which contain the session token.
            raise RuntimeError(f'{method} {path}: HTTP {exc.code}: {exc.read().decode()}') from exc

    tokens = {user: api('POST', '/api/login', {'user_id': user})['token'] for user in ['maya', 'sam', 'finn', 'alex', 'olivia']}
    owner = tokens['maya']
    discussion = api('POST', '/api/discussions', {
        'title': 'Replace the production order system — synthetic demonstration',
        'body': 'We propose replacing the production system and migrating customer data. Access controls need review. The vendor contract and budget need confirmation. Support runbooks and on-call ownership need agreement. A planned outage may affect business hours.',
        'allowed_departments': ['infrastructure', 'security', 'finance', 'support', 'operations'],
    }, owner)
    path = '/api/discussions/' + discussion['id']
    expected = {'security', 'finance', 'support', 'operations'}
    assert discussion['status'] == 'review_required', discussion['status']
    assert {c['department'] for c in discussion['consultations']} == expected
    assert not any(c['approved'] for c in discussion['consultations'])
    print(f"Created {discussion['id']}: four evidence-based suggestions; none dispatched.")

    review = {
        'request_id': 'demo-review-' + uuid.uuid4().hex,
        'consultations': [
            {'department': c['department'], 'question': c['question'], 'approved': True}
            for c in discussion['consultations']
        ],
    }
    approved = api('POST', path + '/review', review, owner)
    assert approved['status'] == 'awaiting_responses'
    replay = api('POST', path + '/review', review, owner)
    assert len(replay['consultations']) == len(approved['consultations']) == 4
    print('Owner approved four consultations. Replayed approval did not duplicate them.')

    responses = [
        ('sam', 'security', 'concern', 'Access-control evidence is incomplete. Security cannot support readiness yet.', 'Provide an access-control test report.', 'sam'),
        ('finn', 'finance', 'support', 'The proposed budget appears feasible. This is advisory support, not expenditure approval.', 'Confirm the procurement approver.', 'finn'),
        ('alex', 'support', 'support', 'Support can prepare for the change; the runbook still needs a rehearsal.', 'Rehearse the support runbook.', 'alex'),
        ('olivia', 'operations', 'support', 'Operations supports planning an outage outside business hours.', 'Agree an outage window with service owners.', 'olivia'),
    ]
    for user, department, stance, text, action, action_owner in responses:
        inbox = api('GET', path, token=tokens[user])
        assert 'audit' not in inbox and 'summary' not in inbox, 'Recipient received owner-only detail'
        assert all(c['department'] == department for c in inbox['consultations'])
        payload = {'department': department, 'text': text, 'stance': stance,
                   'actions': [{'text': action, 'owner': action_owner}],
                   'request_id': 'demo-response-' + uuid.uuid4().hex}
        api('POST', path + '/responses', payload, tokens[user])
        api('POST', path + '/responses', payload, tokens[user])
    final = api('GET', path, token=owner)
    assert final['status'] == 'blocked', final['status']
    assert len(final['responses']) == 4, 'Replayed responses were duplicated'
    summary = final['summary']
    assert not summary['outstanding']
    assert len(summary['risks']) == 1
    assert len(summary['actions']) == 4
    assert summary['contradictions'], 'Expected readiness disagreement signal'
    assert not summary['decisions'], 'Consultation must not create formal approval'
    print('Four asynchronous department responses recorded; duplicate replays suppressed.')
    print('Consolidated: 1 concern, 4 actions, 0 unanswered consultations, readiness disagreement.')
    print('Status: blocked for human resolution. No formal approval has been inferred.')
    print('Analysis: deterministic baseline; this run does not validate model accuracy or business impact.')
    print('Open the app as Maya to inspect the discussion and audit trail: ' + base_url)
    return final['id']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    try:
        run(args.base_url)
    except (RuntimeError, URLError, AssertionError, KeyError) as exc:
        print('Demo failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
