import pytest
from fastapi.testclient import TestClient

from archagent.agent.session import ArchitectSession
from archagent.agent.testing import install_scripted_llm
from archagent.server import create_app
from archagent.server.config import Settings
from tests.support import scenarios as sc


@pytest.fixture
def client(tmp_path):
    def factory(ws):
        s = ArchitectSession(ws, model="gpt-4o")
        install_scripted_llm(s.coder, [sc.REPLY_3BHK])
        return s
    return TestClient(create_app(Settings(workspace=tmp_path / "w"), session_factory=factory))


def test_health_and_no_implicit_project(client):
    assert client.get("/api/health").json()["ok"] is True
    assert client.get("/api/projects/p_deadbeef").status_code == 404           # never creates projects implicitly
    assert client.post("/api/projects/p_deadbeef/messages", json={"message": "hi"}).status_code == 404


def test_create_project_chat_and_fetch_every_artifact(client):
    pid = client.post("/api/projects").json()["project_id"]
    assert client.get("/api/projects").json()["projects"] == [pid]
    r = client.post(f"/api/projects/{pid}/messages", json={"message": sc.PROMPT_3BHK}).json()
    assert r["valid"] and r["state"]["project_id"] == pid and r["state"]["phase"] == "ready"
    assert client.get(f"/api/projects/{pid}/floorplan").headers["content-type"].startswith("image/svg")
    assert client.get(f"/api/projects/{pid}/model3d").content[:4] == b"glTF"
    assert client.get(f"/api/projects/{pid}/ifc").content.startswith(b"ISO-10303-21")
    assert client.get(f"/api/projects/{pid}/model").json()["site"]["width"] == 20
    assert client.get(f"/api/projects/{pid}/floorplan?floor=nope").status_code == 404


def test_projects_are_isolated(client):
    a = client.post("/api/projects").json()["project_id"]
    b = client.post("/api/projects").json()["project_id"]
    client.post(f"/api/projects/{a}/messages", json={"message": sc.PROMPT_3BHK})
    assert client.get(f"/api/projects/{a}").json()["status"]["valid"] is True
    assert client.get(f"/api/projects/{b}").json()["status"]["valid"] is False
    assert client.get(f"/api/projects/{b}/model3d").status_code == 404


def test_path_traversal_and_bad_ids_are_rejected(client):
    pid = client.post("/api/projects").json()["project_id"]
    assert client.get(f"/api/projects/{pid}/files/../design.py").status_code in (404,)
    assert client.get(f"/api/projects/{pid}/files/%2e%2e/design.py").status_code == 404
    assert client.get("/api/projects/..%2fx").status_code == 404
    assert client.post(f"/api/projects/{pid}/messages", json={"message": ""}).status_code == 422


def test_llm_failure_is_reported_as_json_and_state_is_kept(tmp_path):
    def factory(ws):
        s = ArchitectSession(ws, model="gpt-4o")
        def boom(*a, **k):
            raise RuntimeError("no API key")
        s.coder.run = boom
        return s
    c = TestClient(create_app(Settings(workspace=tmp_path / "w"), session_factory=factory))
    pid = c.post("/api/projects").json()["project_id"]
    r = c.post(f"/api/projects/{pid}/messages", json={"message": "hello"})
    assert r.status_code == 502 and "no API key" in r.json()["error"] and r.json()["state"]["phase"] == "failed"


def test_project_survives_server_restart_because_model_is_on_disk(tmp_path):
    def factory(ws):
        s = ArchitectSession(ws, model="gpt-4o")
        install_scripted_llm(s.coder, [sc.REPLY_3BHK])
        return s
    st = Settings(workspace=tmp_path / "w")
    c1 = TestClient(create_app(st, session_factory=factory))
    pid = c1.post("/api/projects").json()["project_id"]
    c1.post(f"/api/projects/{pid}/messages", json={"message": sc.PROMPT_3BHK})
    c2 = TestClient(create_app(st, session_factory=factory))                      # "restart"
    s = c2.get(f"/api/projects/{pid}").json()
    assert s["status"]["valid"] and s["model"]["site"]["depth"] == 30


def test_phases_are_reported_in_order(tmp_path):
    seen = []
    s = ArchitectSession(str(tmp_path / "w"), model="gpt-4o")
    orig = s._set_phase
    def spy(name):
        seen.append(name); orig(name)
    s.coder._on_phase = spy
    install_scripted_llm(s.coder, [sc.REPLY_3BHK])
    s.chat(sc.PROMPT_3BHK)
    order = [p for i, p in enumerate(seen) if i == 0 or p != seen[i - 1]]
    assert order[:5] == ["understanding", "generating", "validating", "rendering", "ready"]
