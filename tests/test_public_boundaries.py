FORBIDDEN={"teacher_annotations","hidden_analysis","expected_reasoning","teacher_reference","api_key","credentials","authorization"}
def assert_public(value):
    if isinstance(value,dict):
        assert not ({key.lower() for key in value}&FORBIDDEN)
        for item in value.values(): assert_public(item)
    elif isinstance(value,list):
        for item in value: assert_public(item)

def test_all_public_session_and_case_responses_are_recursively_safe(client,caplog):
    secret="unique-secret-api-key"
    case=client.get("/api/cases/SAMPLE-CASE-01"); assert case.status_code==200; assert_public(case.json())
    created=client.post("/api/sessions",json={"mode":"guided","case_code":"SAMPLE-CASE-01","model_profile":{"adapter":"mock","models":{"default":"mock-model"}},"credentials":{"api_key":secret}})
    assert created.status_code==201; assert_public(created.json())
    session_id=created.json()["session_id"]
    fetched=client.get(f"/api/sessions/{session_id}"); assert_public(fetched.json())
    turn=client.post(f"/api/sessions/{session_id}/messages",json={"content":"my claim"}); assert turn.status_code==200; assert_public(turn.json())
    all_text=case.text+created.text+fetched.text+turn.text+caplog.text
    assert secret not in all_text
