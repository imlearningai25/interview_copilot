"""
Backend tests for /api/sessions endpoints.
Run from backend/:  pytest
"""

_JOB = {"role": "Principal Engineer", "company": "Acme Corp"}


def _job(client, **kw):
    r = client.post("/api/jobs", json={**_JOB, **kw})
    assert r.status_code == 201
    return r.json()


def _session(client, job_id):
    r = client.post("/api/sessions", json={"job_id": job_id})
    assert r.status_code == 201
    return r.json()


def _entry(client, session_id, q="Tell me about yourself.", a="I have 17 years…"):
    r = client.post(f"/api/sessions/{session_id}/entries",
                    json={"question": q, "answer": a})
    assert r.status_code == 201
    return r.json()


# ── create ────────────────────────────────────────────────────────────────────

def test_create_session(client):
    job = _job(client)
    r = client.post("/api/sessions", json={"job_id": job["id"]})
    assert r.status_code == 201
    body = r.json()
    assert body["job_id"] == job["id"]
    assert body["ended_at"] is None
    assert body["entries"] == []


def test_create_session_unknown_job_404(client):
    r = client.post("/api/sessions", json={"job_id": 9999})
    assert r.status_code == 404


# ── list ─────────────────────────────────────────────────────────────────────

def test_list_sessions_for_job(client):
    job = _job(client)
    _session(client, job["id"])
    _session(client, job["id"])
    r = client.get(f"/api/sessions?job_id={job['id']}")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_sessions_filters_by_job(client):
    job_a = _job(client, role="Job A")
    job_b = _job(client, role="Job B")
    _session(client, job_a["id"])
    _session(client, job_b["id"])
    r = client.get(f"/api/sessions?job_id={job_a['id']}")
    assert len(r.json()) == 1


def test_list_sessions_includes_entry_count(client):
    job = _job(client)
    s = _session(client, job["id"])
    _entry(client, s["id"])
    _entry(client, s["id"])
    r = client.get(f"/api/sessions?job_id={job['id']}")
    assert r.json()[0]["entry_count"] == 2


# ── get ───────────────────────────────────────────────────────────────────────

def test_get_session_with_entries(client):
    job = _job(client)
    s = _session(client, job["id"])
    _entry(client, s["id"], q="Q1", a="A1")
    r = client.get(f"/api/sessions/{s['id']}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["entries"]) == 1
    assert body["entries"][0]["question"] == "Q1"


def test_get_session_not_found(client):
    assert client.get("/api/sessions/9999").status_code == 404


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_session(client):
    job = _job(client)
    s = _session(client, job["id"])
    assert client.delete(f"/api/sessions/{s['id']}").status_code == 204
    assert client.get(f"/api/sessions/{s['id']}").status_code == 404


def test_delete_session_not_found(client):
    assert client.delete("/api/sessions/9999").status_code == 404


def test_bulk_delete_sessions(client):
    job = _job(client)
    s1 = _session(client, job["id"])
    s2 = _session(client, job["id"])
    r = client.delete("/api/sessions", json={"ids": [s1["id"], s2["id"]]})
    assert r.status_code == 204
    assert client.get(f"/api/sessions/{s1['id']}").status_code == 404
    assert client.get(f"/api/sessions/{s2['id']}").status_code == 404


# ── entries ───────────────────────────────────────────────────────────────────

def test_add_entry(client):
    job = _job(client)
    s = _session(client, job["id"])
    e = _entry(client, s["id"], q="How do you work?", a="I collaborate well.")
    assert e["question"] == "How do you work?"
    assert e["session_id"] == s["id"]


def test_add_entry_unknown_session_404(client):
    r = client.post("/api/sessions/9999/entries",
                    json={"question": "Q", "answer": "A"})
    assert r.status_code == 404


def test_delete_cascades_to_entries(client):
    """Deleting a session must also delete its entries."""
    job = _job(client)
    s = _session(client, job["id"])
    _entry(client, s["id"])
    client.delete(f"/api/sessions/{s['id']}")
    # Session gone; entries gone with it (cascade)
    assert client.get(f"/api/sessions/{s['id']}").status_code == 404


# ── end session ───────────────────────────────────────────────────────────────

def test_end_session_sets_ended_at(client):
    job = _job(client)
    s = _session(client, job["id"])
    assert s["ended_at"] is None
    r = client.patch(f"/api/sessions/{s['id']}/end")
    assert r.status_code == 200
    assert r.json()["ended_at"] is not None
