import pytest

from app.schemas.task_generation import FailedGeneration, GeneratedTask


@pytest.fixture
def plan_with_date(client):
    user = client.post("/users", json={"name": "Alice"}).json()
    return client.post(
        "/plans",
        json={
            "user_id": user["id"],
            "goal": "Learn Python",
            "hours_per_week": 10.0,
            "target_date": "2026-09-01",
        },
    ).json()


@pytest.fixture
def plan_without_date(client):
    user = client.post("/users", json={"name": "Bob"}).json()
    return client.post(
        "/plans",
        json={
            "user_id": user["id"],
            "goal": "Learn Rust",
            "hours_per_week": 5.0,
        },
    ).json()


@pytest.fixture
def plan_with_zero_hours(client):
    user = client.post("/users", json={"name": "Carol"}).json()
    return client.post(
        "/plans",
        json={
            "user_id": user["id"],
            "goal": "Zero hour plan",
            "hours_per_week": 0.0,
            "target_date": "2026-12-01",
        },
    ).json()


def test_generate_tasks_success(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Read chapter 1", estimated_hours=2.0),
        GeneratedTask(title="Complete exercises", estimated_hours=3.0),
        GeneratedTask(title="Build a project", estimated_hours=5.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 3
    assert data["tasks"][0]["title"] == "Read chapter 1"
    assert data["tasks"][0]["plan_id"] == plan_with_date["id"]
    assert data["tasks"][0]["completed"] is False
    assert data["total_estimated_hours"] == 10.0
    assert data["hours_match"] is True
    assert data["warning"] is None
    assert data["failed_generations"] == []


def test_generate_tasks_saves_to_db(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Task A", estimated_hours=1.5),
    ]

    # Act
    client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )
    tasks_response = client.get(f"/plans/{plan_with_date['id']}/tasks")

    # Assert
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Task A"


def test_generate_tasks_complementary_to_existing(client, mock_llm, plan_with_date):
    # Arrange
    client.post(
        f"/plans/{plan_with_date['id']}/tasks",
        json={"title": "Existing task", "estimated_hours": 2.0},
    )
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Next chapter", estimated_hours=3.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1

    all_tasks = client.get(f"/plans/{plan_with_date['id']}/tasks").json()
    titles = {t["title"] for t in all_tasks}
    assert titles == {"Existing task", "Next chapter"}


def test_generate_tasks_no_target_date(client, mock_llm, plan_without_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Task 1", estimated_hours=2.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_without_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 422
    assert "target_date" in response.json()["detail"].lower()


def test_generate_tasks_plan_not_found(client):
    # Act
    response = client.post("/plans/999/generate-tasks", json={})

    # Assert
    assert response.status_code == 404


def test_generate_tasks_filters_invalid(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Valid task", estimated_hours=2.0),
        GeneratedTask(title="", estimated_hours=1.0),
        GeneratedTask(title="Negative hours", estimated_hours=-3.0),
        GeneratedTask(title="Zero hours", estimated_hours=0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Valid task"
    assert len(data["failed_generations"]) == 3
    reasons = [f["reason"] for f in data["failed_generations"]]
    assert any("Empty title" in r for r in reasons)
    assert any("hours must be positive" in r for r in reasons)


def test_generate_tasks_empty_response(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = []

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"] == []
    assert data["total_estimated_hours"] == 0
    assert data["hours_match"] is False
    assert data["failed_generations"] == []


def test_generate_tasks_hours_mismatch_exceeds_warning(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Huge task", estimated_hours=14.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["hours_match"] is False
    assert data["warning"] is not None
    assert "exceeds" in data["warning"].lower()


def test_generate_tasks_hours_mismatch_under_warning(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Tiny task", estimated_hours=1.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["hours_match"] is False
    assert data["warning"] is not None
    assert "under" in data["warning"].lower()


def test_generate_tasks_zero_hours_per_week(client, mock_llm, plan_with_zero_hours):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Zero hour task", estimated_hours=1.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_zero_hours['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["hours_match"] is True
    assert data["warning"] is not None
    assert "hours_per_week=0" in data["warning"]


def test_generate_tasks_respects_max_tasks_param(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="Task 1", estimated_hours=2.0),
        GeneratedTask(title="Task 2", estimated_hours=2.0),
        GeneratedTask(title="Task 3", estimated_hours=2.0),
    ]

    # Act
    client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks",
        json={"max_tasks": 2},
    )

    # Assert: verify the prompt passed to the LLM includes the max_tasks instruction
    assert mock_llm.last_prompt is not None
    assert "Generate at most 2 tasks" in mock_llm.last_prompt


def test_generate_tasks_response_uses_failed_generation_model(client, mock_llm, plan_with_date):
    # Arrange
    mock_llm.tasks_to_return = [
        GeneratedTask(title="", estimated_hours=1.0),
    ]

    # Act
    response = client.post(
        f"/plans/{plan_with_date['id']}/generate-tasks", json={}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["failed_generations"]) == 1
    failed = data["failed_generations"][0]
    assert "title" in failed
    assert "estimated_hours" in failed
    assert "reason" in failed
    assert failed["reason"] == "Empty title"
