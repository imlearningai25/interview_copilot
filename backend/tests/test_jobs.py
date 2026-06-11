"""
Backend tests for the /api/jobs endpoints.

Run from backend/:
    pip install -r requirements-test.txt
    pytest
"""

_JOB = {
    "role": "Principal Engineer",
    "company": "Acme Corp",
    "location": "Remote",
    "job_description": "Build awesome things.",
}


def _create(client, **overrides):
    r = client.post("/api/jobs", json={**_JOB, **overrides})
    assert r.status_code == 201
    return r.json()


# ── health ───────────────────────────────────────────────────────────────────


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ── list ─────────────────────────────────────────────────────────────────────


def test_list_empty(client):
    assert client.get("/api/jobs").json() == []


def test_list_returns_all_jobs(client):
    _create(client, role="Job A")
    _create(client, role="Job B")
    jobs = client.get("/api/jobs").json()
    assert len(jobs) == 2



# ── create ───────────────────────────────────────────────────────────────────


def test_create_returns_201(client):
    r = client.post("/api/jobs", json=_JOB)
    assert r.status_code == 201


def test_create_fields(client):
    body = _create(client)
    assert body["role"] == _JOB["role"]
    assert body["company"] == _JOB["company"]
    assert body["is_active"] is False
    assert "id" in body
    assert "created_at" in body


def test_create_optional_fields_default_null(client):
    r = client.post("/api/jobs", json={"role": "SWE", "company": "Acme"})
    assert r.status_code == 201
    body = r.json()
    assert body["location"] is None
    assert body["job_description"] is None


def test_create_missing_role_422(client):
    r = client.post("/api/jobs", json={"company": "Acme"})
    assert r.status_code == 422


def test_create_missing_company_422(client):
    r = client.post("/api/jobs", json={"role": "SWE"})
    assert r.status_code == 422


# ── get by id ────────────────────────────────────────────────────────────────


def test_get_job(client):
    job = _create(client)
    r = client.get(f"/api/jobs/{job['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == job["id"]


def test_get_job_not_found(client):
    assert client.get("/api/jobs/9999").status_code == 404


# ── active ───────────────────────────────────────────────────────────────────


def test_active_404_when_none(client):
    assert client.get("/api/jobs/active").status_code == 404


def test_active_returns_activated_job(client):
    job = _create(client)
    client.patch(f"/api/jobs/{job['id']}/activate")
    r = client.get("/api/jobs/active")
    assert r.status_code == 200
    assert r.json()["id"] == job["id"]
    assert r.json()["is_active"] is True


# ── update ───────────────────────────────────────────────────────────────────


def test_update_role(client):
    job = _create(client)
    r = client.put(f"/api/jobs/{job['id']}", json={"role": "Staff Engineer"})
    assert r.status_code == 200
    assert r.json()["role"] == "Staff Engineer"
    assert r.json()["company"] == _JOB["company"]   # unchanged


def test_update_preserves_unset_fields(client):
    job = _create(client)
    client.put(f"/api/jobs/{job['id']}", json={"company": "New Corp"})
    updated = client.get(f"/api/jobs/{job['id']}").json()
    assert updated["role"] == _JOB["role"]


def test_update_not_found(client):
    assert client.put("/api/jobs/9999", json={"role": "X"}).status_code == 404


# ── delete ───────────────────────────────────────────────────────────────────


def test_delete_job(client):
    job = _create(client)
    assert client.delete(f"/api/jobs/{job['id']}").status_code == 204
    assert client.get(f"/api/jobs/{job['id']}").status_code == 404


def test_delete_not_found(client):
    assert client.delete("/api/jobs/9999").status_code == 404


# ── activate ─────────────────────────────────────────────────────────────────


def test_activate_sets_flag(client):
    job = _create(client)
    r = client.patch(f"/api/jobs/{job['id']}/activate")
    assert r.status_code == 200
    assert r.json()["is_active"] is True


def test_activate_deactivates_previous(client):
    first = _create(client, role="Job A")
    second = _create(client, role="Job B")

    client.patch(f"/api/jobs/{first['id']}/activate")
    client.patch(f"/api/jobs/{second['id']}/activate")

    jobs = client.get("/api/jobs").json()
    active = [j for j in jobs if j["is_active"]]
    assert len(active) == 1
    assert active[0]["id"] == second["id"]


def test_activate_not_found(client):
    assert client.patch("/api/jobs/9999/activate").status_code == 404
