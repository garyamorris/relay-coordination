"""Local-only coordination demo. Run exactly one worker; demo identity is not enterprise authentication."""
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from app.analysis import DEPARTMENTS, consolidate
from app.workflow import build_graph, now, event

USERS = [
    {'id': 'maya', 'name': 'Maya Chen', 'department': 'infrastructure', 'role': 'Infrastructure Architect'},
    {'id': 'sam', 'name': 'Sam Rivera', 'department': 'security', 'role': 'Security Lead'},
    {'id': 'finn', 'name': 'Finn Patel', 'department': 'finance', 'role': 'Finance Partner'},
    {'id': 'alex', 'name': 'Alex Morgan', 'department': 'support', 'role': 'Application Support Lead'},
    {'id': 'olivia', 'name': 'Olivia James', 'department': 'operations', 'role': 'Business Operations Lead'},
]

class Model(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

class Login(Model):
    user_id: str
class Create(Model):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=10, max_length=20000)
    allowed_departments: list[str] = Field(default_factory=lambda: list(DEPARTMENTS))
    escalation_hours: int = Field(default=48, ge=1, le=720)
    request_id: str | None = Field(default=None, max_length=128)
class Consultation(Model):
    department: str
    question: str = Field(min_length=5, max_length=2000)
    approved: bool
class Review(Model):
    consultations: list[Consultation] = Field(max_length=5)
    request_id: str | None = Field(default=None, max_length=128)
class Action(Model):
    text: str = Field(min_length=1, max_length=1000)
    owner: str = Field(min_length=1, max_length=100)
    due_date: str | None = Field(default=None, max_length=30)
class Response(Model):
    department: str
    text: str = Field(min_length=1, max_length=10000)
    stance: Literal['support', 'concern', 'unclear']
    actions: list[Action] = Field(default_factory=list, max_length=20)
    request_id: str | None = Field(default=None, max_length=128)
class Decision(Model):
    text: str = Field(min_length=1, max_length=2000)
    status: Literal['proposed', 'approved']
    override_reason: str | None = Field(default=None, max_length=2000)
    request_id: str | None = Field(default=None, max_length=128)


def create_app(db_path=None):
    path = str(db_path or os.environ.get('COORDINATION_DB', 'data/coordination.sqlite'))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('CREATE TABLE IF NOT EXISTS discussions (id TEXT PRIMARY KEY)')
    conn.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL)')
    conn.commit()
    saver = SqliteSaver(conn)
    graph = build_graph(saver)
    lock = threading.RLock()
    app = FastAPI(title='Relay Coordination — Local Demo')
    app.state.graph = graph
    app.state.connection = conn
    app.state.lock = lock

    def auth(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(401, 'Sign in with a demo identity')
        digest = hashlib.sha256(authorization[7:].encode()).hexdigest()
        with lock:
            row = conn.execute('SELECT user_id FROM sessions WHERE token_hash=?', (digest,)).fetchone()
        user = next((u for u in USERS if row and u['id'] == row[0]), None)
        if not user:
            raise HTTPException(401, 'Invalid session')
        return user
    def config(did):
        return {'configurable': {'thread_id': did}}
    def read(did):
        snapshot = graph.get_state(config(did))
        if snapshot.next and not any(task.interrupts for task in snapshot.tasks):
            graph.invoke(None, config(did))
            snapshot = graph.get_state(config(did))
        state = dict(snapshot.values)
        if not state:
            raise HTTPException(404, 'Discussion not found')
        return state
    def owner(state, user):
        if state['owner_id'] != user['id']:
            raise HTTPException(403, 'Only the discussion owner may perform this action')
    def visible(state, user):
        return state['owner_id'] == user['id'] or (user['department'] in state['allowed_departments'] and any(c['department'] == user['department'] and c.get('approved') for c in state.get('consultations', [])))
    def project(state, user):
        if not visible(state, user):
            raise HTTPException(404, 'Discussion not found')
        if state['owner_id'] == user['id']:
            return state
        return {**{k: state[k] for k in ['id','title','body','owner_id','created_at','status','analysis_mode']}, 'consultations': [c for c in state['consultations'] if c['department'] == user['department'] and c['approved']], 'responses': [r for r in state['responses'] if r['department'] == user['department']]}
    def identity(state, user, operation, payload):
        data = payload.model_dump()
        rid = data.pop('request_id', None) or str(uuid.uuid4())
        prefix = user['id'] + ':' + operation + ':' + rid + ':'
        key = prefix + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        for seen in state.get('processed_ids', []):
            if seen.startswith(prefix):
                if seen != key:
                    raise HTTPException(409, 'Request ID was already used with a different payload')
                return key, True
        return key, False

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'mode': 'local-demo', 'analysis_mode': 'deterministic-baseline'}
    @app.get('/api/users')
    def users():
        return USERS
    @app.post('/api/login')
    def login(payload: Login):
        user = next((u for u in USERS if u['id'] == payload.user_id), None)
        if not user:
            raise HTTPException(400, 'Unknown demo user')
        token = secrets.token_urlsafe(32)
        with lock:
            conn.execute('INSERT INTO sessions VALUES (?,?)', (hashlib.sha256(token.encode()).hexdigest(), user['id']))
            conn.commit()
        return {'token': token, 'user': user}
    @app.get('/api/departments')
    def departments(user=Depends(auth)):
        return [{'id': k, 'name': v['name'], 'responsibility': v['responsibility']} for k,v in DEPARTMENTS.items()]
    @app.get('/api/discussions')
    def discussions(user=Depends(auth)):
        with lock:
            results = []
            for (did,) in conn.execute('SELECT id FROM discussions').fetchall():
                snapshot = graph.get_state(config(did))
                state = read(did) if snapshot.values else {}
                if state and visible(state, user):
                    results.append({k: state[k] for k in ['id','title','status','owner_id','created_at']})
            return sorted(results, key=lambda x: x['created_at'], reverse=True)
    @app.post('/api/discussions')
    def create(payload: Create, user=Depends(auth)):
        if set(payload.allowed_departments) - DEPARTMENTS.keys():
            raise HTTPException(400, 'Unknown department')
        did = str(uuid.uuid5(uuid.NAMESPACE_URL, user['id'] + ':' + payload.request_id)) if payload.request_id else str(uuid.uuid4())
        with lock:
            existing = dict(graph.get_state(config(did)).values)
            key, _ = identity(existing, user, 'create', payload)
            if existing:
                existing = read(did)
                if key not in existing['processed_ids']:
                    raise HTTPException(409, 'Request ID was already used with a different payload')
                return project(existing, user)
            # Catalog is written first, so interrupted initialization can be safely retried.
            conn.execute('INSERT OR IGNORE INTO discussions VALUES (?)', (did,))
            conn.commit()
            graph.invoke({'id': did, 'title': payload.title.strip(), 'body': payload.body, 'owner_id': user['id'], 'author_department': user['department'], 'allowed_departments': sorted(set(payload.allowed_departments)), 'created_at': now(), 'consultations': [], 'responses': [], 'decisions': [], 'summary': {}, 'audit': [event('discussion_created', user['id'], 'Owner is designated decision authority; source access explicitly configured.')], 'processed_ids': [key], 'status': 'review_required', 'analysis_mode': 'deterministic-baseline', 'escalation_hours': payload.escalation_hours}, config(did))
            return project(read(did), user)
    @app.get('/api/discussions/{did}')
    def detail(did: str, user=Depends(auth)):
        with lock:
            return project(read(did), user)
    @app.post('/api/discussions/{did}/review')
    def review(did: str, payload: Review, user=Depends(auth)):
        with lock:
            state = read(did); owner(state, user)
            key, duplicate = identity(state, user, 'review', payload)
            if duplicate: return project(state, user)
            if state['status'] != 'review_required': raise HTTPException(409, 'Consultation review is already complete')
            departments = [c.department for c in payload.consultations]
            if len(set(departments)) != len(departments): raise HTTPException(400, 'Duplicate department')
            original = {c['department']: c for c in state['consultations']}
            if not set(original).issubset(departments): raise HTTPException(400, 'Explicitly approve or reject every recommendation')
            consultations = []
            for c in payload.consultations:
                if c.department not in state['allowed_departments']: raise HTTPException(403, 'Source permission does not authorize this department')
                base = original.get(c.department, {'department_name': DEPARTMENTS[c.department]['name'], 'reason': 'Added by discussion owner', 'evidence': []})
                consultations.append({**base, **c.model_dump()})
            graph.invoke(Command(resume={'kind': 'review', 'actor': user['id'], 'consultations': consultations, 'request_id': key}), config(did))
            return project(read(did), user)
    @app.post('/api/discussions/{did}/responses')
    def response(did: str, payload: Response, user=Depends(auth)):
        with lock:
            state = read(did)
            if not visible(state, user): raise HTTPException(404, 'Discussion not found')
            if payload.department != user['department']: raise HTTPException(403, 'Cannot respond for another department')
            if not any(c['department'] == payload.department and c['approved'] for c in state['consultations']): raise HTTPException(403, 'No approved consultation for your department')
            key, duplicate = identity(state, user, 'response', payload)
            if duplicate: return project(state, user)
            if state['status'] != 'awaiting_responses': raise HTTPException(409, 'Workflow is not accepting responses')
            if any(r['department'] == payload.department for r in state['responses']): raise HTTPException(409, 'Department has already responded')
            record = {**payload.model_dump(exclude={'request_id'}), 'id': str(uuid.uuid4()), 'created_at': now(), 'user_id': user['id']}
            graph.invoke(Command(resume={'kind': 'response', 'actor': user['id'], 'response': record, 'request_id': key}), config(did))
            return project(read(did), user)
    @app.post('/api/discussions/{did}/stop')
    def stop(did: str, user=Depends(auth)):
        with lock:
            state = read(did); owner(state, user)
            if state['status'] in ['stopped', 'closed']: return project(state, user)
            if graph.get_state(config(did)).next:
                graph.invoke(Command(resume={'kind': 'stop', 'actor': user['id']}), config(did))
            else:
                graph.update_state(config(did), {'status': 'stopped', 'audit': state['audit'] + [event('workflow_stopped', user['id'], 'Stopped by owner')]})
            return project(read(did), user)
    @app.post('/api/discussions/{did}/decision')
    def decision(did: str, payload: Decision, user=Depends(auth)):
        with lock:
            state = read(did); owner(state, user)
            key, duplicate = identity(state, user, 'decision', payload)
            if duplicate: return project(state, user)
            if state['status'] in ['stopped', 'closed', 'review_required', 'awaiting_responses']: raise HTTPException(409, 'Complete consultations before recording a decision')
            if payload.status == 'approved' and state['status'] == 'blocked' and not (payload.override_reason or '').strip(): raise HTTPException(409, 'Unresolved concerns require an explicit override reason')
            record = {**payload.model_dump(exclude={'request_id'}), 'id': str(uuid.uuid4()), 'owner': user['id'], 'created_at': now()}
            decisions = state['decisions'] + [record]
            graph.update_state(config(did), {'decisions': decisions, 'summary': {**state['summary'], 'decisions': decisions}, 'status': 'closed' if payload.status == 'approved' else state['status'], 'processed_ids': state['processed_ids'] + [key], 'audit': state['audit'] + [event('decision_' + payload.status, user['id'], payload.text)]})
            return project(read(did), user)
    @app.post('/api/discussions/{did}/escalate')
    def escalate(did: str, user=Depends(auth)):
        with lock:
            state = read(did); owner(state, user)
            if state['status'] != 'awaiting_responses': raise HTTPException(409, 'No pending consultations')
            consultations = []
            events = []
            for c in state['consultations']:
                if c['status'] == 'sent' and datetime.fromisoformat(c['due_at']) <= datetime.now(timezone.utc):
                    c = {**c, 'status': 'escalated'}
                    events.append(event('consultation_escalated', user['id'], c['department'] + ': overdue; owner dashboard only'))
                consultations.append(c)
            graph.update_state(config(did), {'consultations': consultations, 'audit': state['audit'] + events})
            return project(read(did), user)
    static_dir = Path(__file__).resolve().parent.parent / 'static'
    app.mount('/static', StaticFiles(directory=static_dir), name='assets')
    app.mount('/', StaticFiles(directory=static_dir, html=True), name='static')
    return app

app = create_app()
