import json

import pytest

from app.schemas.agent import AgentGenerateRequest, Subtopic, TaskDraft


def test_breakdown_endpoint(client, mock_llm, plan_for_agent):
    mock_llm.tasks_to_return = [
        Subtopic(name="React Hooks", description="Core hooks", suggested_hours=4.0),
        Subtopic(name="Context API", description="State management", suggested_hours=6.0),
    ]

    response = client.post(f"/plans/{plan_for_agent['id']}/agent/breakdown")

    assert response.status_code == 200
    data = response.json()
    assert len(data["subtopics"]) == 2
    assert data["subtopics"][0]["name"] == "React Hooks"
    assert data["subtopics"][0]["suggested_hours"] == 4.0
    assert data["subtopics"][1]["name"] == "Context API"
    assert "Master React 18" in mock_llm.last_prompt
    assert "practical exercises" in mock_llm.last_prompt


def test_breakdown_plan_not_found(client):
    response = client.post("/plans/999/agent/breakdown")
    assert response.status_code == 404


def test_generate_requires_subtopics(client, mock_llm, plan_for_agent):
    response = client.post(
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json={"approved_subtopics": []},
    )
    assert response.status_code == 422


def test_generate_plan_not_found(client, mock_llm):
    request = AgentGenerateRequest(
        approved_subtopics=[Subtopic(name="Test", description="Test", suggested_hours=1.0)]
    )
    response = client.post(
        "/plans/999/agent/generate",
        json=request.model_dump(),
    )
    assert response.status_code == 404


def _collect_sse_events(response) -> list[dict]:
    buffer = ""
    events = []
    for chunk in response.iter_text():
        buffer += chunk
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            event_type = None
            data = None
            for line in block.split("\n"):
                if line.startswith("event: "):
                    event_type = line[7:]
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
            if event_type and data is not None:
                events.append({"event": event_type, "data": data})
    return events


def test_graph_happy_path(client, mock_llm, plan_for_agent):
    call_count = [0]

    def side_effect(prompt, response_model):
        call_count[0] += 1
        if call_count[0] == 1:
            return [
                TaskDraft(title="React useState hook", estimated_hours=2.0),
                TaskDraft(title="React useEffect hook", estimated_hours=2.0),
            ]
        return [
            TaskDraft(title="React Context API basics", estimated_hours=3.0),
            TaskDraft(title="useContext pattern", estimated_hours=3.0),
        ]

    mock_llm.generate_tasks_fn = side_effect

    approved = [
        Subtopic(name="Hooks", description="React hooks", suggested_hours=4.0),
        Subtopic(name="Context", description="Context API", suggested_hours=6.0),
    ]

    with client.stream(
        "POST",
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json=AgentGenerateRequest(approved_subtopics=approved).model_dump(),
    ) as response:
        assert response.status_code == 200
        events = _collect_sse_events(response)

    event_types = [e["event"] for e in events]
    assert "planning_started" in event_types
    assert event_types.count("subtopic_started") == 2
    assert event_types.count("tasks_generated") == 2
    assert "planning_complete" in event_types
    assert "validation_retry" not in event_types
    assert "error" not in event_types

    assert events[0]["data"]["subtopic_count"] == 2
    assert events[1]["data"]["subtopic"] == "Hooks"
    assert events[3]["data"]["subtopic"] == "Context"

    tasks = client.get(f"/plans/{plan_for_agent['id']}/tasks").json()
    assert len(tasks) == 4
    task_titles = {t["title"] for t in tasks}
    assert "React useState hook" in task_titles
    assert "useContext pattern" in task_titles
    for t in tasks:
        assert t["plan_id"] == plan_for_agent["id"]

    subtopic_names = {t["subtopic"] for t in tasks}
    assert subtopic_names == {"Hooks", "Context"}


def test_graph_guardrail_retry(client, mock_llm, plan_for_agent):
    call_count = [0]

    def side_effect(prompt, response_model):
        call_count[0] += 1
        if call_count[0] == 1:
            return [TaskDraft(title="Overloaded task", estimated_hours=20.0)]
        return [
            TaskDraft(title="Adjusted task A", estimated_hours=3.0),
            TaskDraft(title="Adjusted task B", estimated_hours=2.0),
        ]

    mock_llm.generate_tasks_fn = side_effect

    approved = [
        Subtopic(name="SingleTopic", description="Test topic", suggested_hours=5.0),
    ]

    with client.stream(
        "POST",
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json=AgentGenerateRequest(approved_subtopics=approved).model_dump(),
    ) as response:
        assert response.status_code == 200
        events = _collect_sse_events(response)

    event_types = [e["event"] for e in events]
    assert "planning_started" in event_types
    assert event_types.count("subtopic_started") == 1
    assert event_types.count("tasks_generated") == 2
    assert "validation_retry" in event_types
    assert "planning_complete" in event_types
    assert "error" not in event_types

    retry_event = next(e for e in events if e["event"] == "validation_retry")
    assert "estimated_hours" in retry_event["data"]["feedback"].lower() or "hours" in retry_event["data"]["feedback"].lower()

    tasks = client.get(f"/plans/{plan_for_agent['id']}/tasks").json()
    assert len(tasks) == 2
    titles = {t["title"] for t in tasks}
    assert "Adjusted task A" in titles
    assert "Adjusted task B" in titles


def test_graph_max_retries_exhausted(client, mock_llm, plan_for_agent):
    def side_effect(prompt, response_model):
        return [TaskDraft(title="Always too big", estimated_hours=50.0)]

    mock_llm.generate_tasks_fn = side_effect

    approved = [
        Subtopic(name="Hopeless", description="Never fits", suggested_hours=5.0),
    ]

    with client.stream(
        "POST",
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json=AgentGenerateRequest(approved_subtopics=approved).model_dump(),
    ) as response:
        assert response.status_code == 200
        events = _collect_sse_events(response)

    event_types = [e["event"] for e in events]
    assert event_types.count("validation_retry") == 3
    assert "warning" in event_types
    assert "planning_complete" in event_types
    assert "error" not in event_types

    warning_events = [e for e in events if e["event"] == "warning"]
    assert any("Max retries" in w["data"]["message"] for w in warning_events)

    tasks = client.get(f"/plans/{plan_for_agent['id']}/tasks").json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Always too big"


def test_graph_no_tasks_generated(client, mock_llm, plan_for_agent):
    def side_effect(prompt, response_model):
        return []

    mock_llm.generate_tasks_fn = side_effect

    approved = [
        Subtopic(name="EmptyTopic", description="No tasks", suggested_hours=5.0),
    ]

    with client.stream(
        "POST",
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json=AgentGenerateRequest(approved_subtopics=approved).model_dump(),
    ) as response:
        assert response.status_code == 200
        events = _collect_sse_events(response)

    event_types = [e["event"] for e in events]
    assert "warning" in event_types
    warning_events = [e for e in events if e["event"] == "warning"]
    assert any("No tasks generated" in w["data"]["message"] for w in warning_events)
    assert "planning_complete" in event_types
    assert "error" not in event_types

    tasks = client.get(f"/plans/{plan_for_agent['id']}/tasks").json()
    assert len(tasks) == 0


def test_graph_tasks_persisted_with_correct_subtopic(client, mock_llm, plan_for_agent):
    call_count = [0]

    def side_effect(prompt, response_model):
        call_count[0] += 1
        if call_count[0] == 1:
            return [
                TaskDraft(title="Hooks task", estimated_hours=2.0),
                TaskDraft(title="More hooks", estimated_hours=2.0),
            ]
        return [
            TaskDraft(title="Context task", estimated_hours=3.0),
            TaskDraft(title="More context", estimated_hours=3.0),
        ]

    mock_llm.generate_tasks_fn = side_effect

    approved = [
        Subtopic(name="Hooks", description="React hooks", suggested_hours=4.0),
        Subtopic(name="Context", description="Context API", suggested_hours=6.0),
    ]

    with client.stream(
        "POST",
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json=AgentGenerateRequest(approved_subtopics=approved).model_dump(),
    ) as response:
        assert response.status_code == 200
        _collect_sse_events(response)

    tasks = client.get(f"/plans/{plan_for_agent['id']}/tasks").json()
    assert len(tasks) == 4
    for t in tasks:
        assert t["plan_id"] == plan_for_agent["id"]
        assert t["completed"] is False
        assert t["estimated_hours"] > 0

    subtopic_names = {t["subtopic"] for t in tasks}
    assert subtopic_names == {"Hooks", "Context"}


def test_sse_adapter_produces_correct_events(client, mock_llm, plan_for_agent):
    mock_llm.tasks_to_return = [
        TaskDraft(title="Task 1", estimated_hours=3.0),
        TaskDraft(title="Task 2", estimated_hours=2.0),
    ]

    approved = [
        Subtopic(name="Topic A", description="First", suggested_hours=5.0),
        Subtopic(name="Topic B", description="Second", suggested_hours=5.0),
    ]

    with client.stream(
        "POST",
        f"/plans/{plan_for_agent['id']}/agent/generate",
        json=AgentGenerateRequest(approved_subtopics=approved).model_dump(),
    ) as response:
        assert response.status_code == 200
        events = _collect_sse_events(response)

    assert events[0]["event"] == "planning_started"
    assert "subtopic_count" in events[0]["data"]
    assert events[0]["data"]["subtopic_count"] == 2

    assert events[1]["event"] == "subtopic_started"
    assert events[1]["data"]["subtopic"] == "Topic A"
    assert events[1]["data"]["index"] == 1
    assert events[1]["data"]["total"] == 2

    assert events[2]["event"] == "tasks_generated"
    assert events[2]["data"]["task_count"] == 2

    assert events[3]["event"] == "subtopic_started"
    assert events[3]["data"]["subtopic"] == "Topic B"
    assert events[3]["data"]["index"] == 2

    assert events[-1]["event"] == "planning_complete"
    assert events[-1]["data"]["status"] == "completed"

    for event in events:
        assert "event" in event
        assert "data" in event


def test_breakdown_uses_plan_constraints(client, mock_llm, plan_for_agent):
    mock_llm.tasks_to_return = [
        Subtopic(name="T1", description="d1", suggested_hours=5.0),
    ]

    client.post(f"/plans/{plan_for_agent['id']}/agent/breakdown")

    prompt = mock_llm.last_prompt
    assert "All tasks must include practical exercises" in prompt
    assert "Master React 18" in prompt
    assert "10.0" in prompt
