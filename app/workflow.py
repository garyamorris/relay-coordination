from typing import TypedDict
from datetime import datetime, timezone, timedelta
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from app.analysis import recommend, consolidate


def now():
    return datetime.now(timezone.utc).isoformat()


def event(kind, actor, detail):
    return {'at': now(), 'event': kind, 'actor': actor, 'detail': detail}


class State(TypedDict, total=False):
    id: str
    title: str
    body: str
    owner_id: str
    author_department: str
    allowed_departments: list
    created_at: str
    consultations: list
    responses: list
    decisions: list
    summary: dict
    audit: list
    processed_ids: list
    status: str
    analysis_mode: str
    escalation_hours: int


def build_graph(checkpointer):
    graph = StateGraph(State)
    def discover(state):
        consultations = recommend(state['body'], state['allowed_departments'], state['author_department'])
        return {'consultations': consultations, 'status': 'review_required', 'audit': state['audit'] + [event('recommendations_generated', 'baseline', f'{len(consultations)} evidence-based recommendation(s); no messages sent.')]}
    def review(state):
        command = interrupt({'kind': 'review_consultations', 'discussion_id': state['id']})
        if command['kind'] == 'stop':
            return {'status': 'stopped', 'audit': state['audit'] + [event('workflow_stopped', command['actor'], 'No further consultations permitted.')]}
        consultations = command['consultations']
        for c in consultations:
            c['status'] = 'sent' if c['approved'] else 'rejected'
            c['due_at'] = (datetime.now(timezone.utc) + timedelta(hours=state['escalation_hours'])).isoformat() if c['approved'] else None
        return {'consultations': consultations, 'status': 'awaiting_responses' if any(c['approved'] for c in consultations) else 'ready_for_decision', 'processed_ids': state['processed_ids'] + [command['request_id']], 'audit': state['audit'] + [event('consultations_reviewed', command['actor'], f"{sum(c['approved'] for c in consultations)} approved; local inbox delivery only.")]}
    def receive(state):
        command = interrupt({'kind': 'await_response', 'discussion_id': state['id']})
        if command['kind'] == 'stop':
            return {'status': 'stopped', 'audit': state['audit'] + [event('workflow_stopped', command['actor'], 'No further consultations permitted.')]}
        response = command['response']
        consultations = [dict(c, status='answered') if c['department'] == response['department'] else c for c in state['consultations']]
        return {'responses': state['responses'] + [response], 'consultations': consultations, 'processed_ids': state['processed_ids'] + [command['request_id']], 'audit': state['audit'] + [event('response_received', command['actor'], 'Response recorded from ' + response['department'])]}
    def summarize(state):
        summary = consolidate(state)
        status = 'awaiting_responses' if summary['outstanding'] else ('blocked' if any(r['stance'] in ['concern', 'unclear'] for r in state['responses']) else 'ready_for_decision')
        return {'summary': summary, 'status': status}
    graph.add_node('discover', discover)
    graph.add_node('review', review)
    graph.add_node('receive', receive)
    graph.add_node('summarize', summarize)
    graph.add_edge(START, 'discover')
    graph.add_edge('discover', 'review')
    graph.add_conditional_edges('review', lambda s: END if s['status'] == 'stopped' else 'summarize')
    graph.add_conditional_edges('receive', lambda s: END if s['status'] == 'stopped' else 'summarize')
    graph.add_conditional_edges('summarize', lambda s: 'receive' if s['status'] == 'awaiting_responses' else END)
    return graph.compile(checkpointer=checkpointer)
