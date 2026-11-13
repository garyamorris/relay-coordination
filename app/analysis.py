"""Transparent deterministic baseline: evidence rules, not model-generated reasoning."""
import re

DEPARTMENTS = {
    'infrastructure': {'name': 'Infrastructure', 'responsibility': 'Hosting, capacity and operational readiness', 'terms': ['hosting', 'capacity', 'server', 'migration', 'production system', 'production database'], 'question': 'What hosting capacity, migration and rollback requirements must be resolved before this proposal can proceed?'},
    'security': {'name': 'Security', 'responsibility': 'Access, compliance and risk', 'terms': ['access', 'customer data', 'personal data', 'security', 'compliance', 'authentication', 'encryption'], 'question': 'What access controls or data protection risks require review, and what evidence would support a security decision?'},
    'finance': {'name': 'Finance', 'responsibility': 'Budget and procurement', 'terms': ['budget', 'cost', 'procurement', 'purchase', 'license', 'licence', 'vendor contract'], 'question': 'What budget, procurement or cost information is needed, and who can authorize the expenditure?'},
    'support': {'name': 'Application Support', 'responsibility': 'Supportability, runbooks and service ownership', 'terms': ['support', 'on-call', 'runbook', 'service owner', 'supportability'], 'question': 'Who will own support, and which runbooks, training or on-call arrangements must be confirmed?'},
    'operations': {'name': 'Business Operations', 'responsibility': 'Service impacts and business requirements', 'terms': ['downtime', 'business impact', 'service impact', 'business requirements', 'outage', 'business hours'], 'question': 'What service impact or interruption is acceptable, and which business requirements or timing constraints must be confirmed?'},
}


def recommend(body: str, allowed_departments: list[str], author_department: str) -> list[dict]:
    results = []
    sentences = re.split(r'(?<=[.!?])\s+|\n', body)
    for department, meta in DEPARTMENTS.items():
        if department not in allowed_departments or department == author_department:
            continue
        evidence = []
        for sentence in sentences:
            lower = sentence.lower()
            for term in meta['terms']:
                if re.search(r'\b' + re.escape(term) + r'\b', lower):
                    # Conservative suppression of explicit negation near the routing term.
                    if re.search(r'\b(no|without|not|unchanged)\b.{0,35}\b' + re.escape(term) + r'\b', lower):
                        continue
                    evidence.append(sentence.strip())
                    break
        if evidence:
            results.append({'department': department, 'department_name': meta['name'], 'reason': 'Proposal contains evidence relevant to ' + meta['responsibility'].lower() + '.', 'evidence': evidence[:3], 'question': 'Proposal states: “' + evidence[0][:500] + '”\n' + meta['question'], 'approved': False, 'status': 'suggested', 'due_at': None})
    return results


def consolidate(state: dict) -> dict:
    responses = state.get('responses', [])
    outstanding = [c['department'] for c in state['consultations'] if c.get('approved') and not any(r['department'] == c['department'] for r in responses)]
    concerns = [r for r in responses if r['stance'] == 'concern']
    supports = [r for r in responses if r['stance'] == 'support']
    unclear = [r for r in responses if r['stance'] == 'unclear']
    contradictions = []
    if concerns and supports:
        contradictions.append({'type': 'readiness_disagreement', 'text': 'Departments disagree on proposal readiness. This is a review signal, not proof of a factual contradiction.', 'response_ids': [r['id'] for r in concerns + supports]})
    return {'text': f'{len(responses)} department response(s) recorded; {len(outstanding)} outstanding. ' + ('Human resolution required.' if concerns or unclear else 'Responses are advisory; formal approval is separate.'), 'risks': [{'text': r['text'], 'department': r['department'], 'response_id': r['id']} for r in concerns], 'actions': [dict(a, response_id=r['id'], department=r['department']) for r in responses for a in r.get('actions', [])], 'contradictions': contradictions, 'outstanding': outstanding, 'decisions': state.get('decisions', []), 'assumptions': [{'text': 'Department ownership is a synthetic demo directory; confirm before real use.', 'status': 'unvalidated'}], 'dependencies': [{'department': c['department'], 'question': c['question'], 'status': c['status']} for c in state['consultations'] if c.get('approved')]}
