def test_case_never_exposes_teacher_annotations(client):
    response = client.get("/api/cases/SAMPLE-CASE-01")
    assert response.status_code == 200
    body = response.text.lower()
    assert "teacher_annotations" not in body and "fact_ids" not in body

def test_api_key_not_serialized(client):
    created = client.post("/api/sessions", json={"mode":"guided","case_code":"SAMPLE-CASE-01","model_profile":{"adapter":"mock","models":{"default":"mock-model"}},"credentials":{"api_key":"super-secret-key"}})
    assert "super-secret-key" not in created.text
    fetched = client.get(f"/api/sessions/{created.json()['session_id']}")
    assert "super-secret-key" not in fetched.text and "api_key" not in fetched.text
