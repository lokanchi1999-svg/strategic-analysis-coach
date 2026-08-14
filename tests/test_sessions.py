def test_free_and_guided_state_transitions(client):
    free = client.post("/api/sessions", json={"mode":"free","material":"行业材料"})
    assert free.json()["phase"] == "FRAMEWORK_SELECTION"
    turn = client.post(f"/api/sessions/{free.json()['session_id']}/messages", json={"content":"我选择 five_forces"})
    assert turn.status_code == 200 and turn.json()["session"]["phase"] == "ANALYSIS"
    guided = client.post("/api/sessions", json={"mode":"guided","case_code":"SAMPLE-CASE-01"})
    assert guided.json()["phase"] == "ANALYSIS" and guided.json()["active_skill"] == "five_forces"

def test_guided_exact_case_lookup(client):
    assert client.post("/api/sessions", json={"mode":"guided","case_code":"sample-case-01"}).status_code == 404
