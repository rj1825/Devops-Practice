import pytest
from fastapi.testclient import TestClient
from main import app, in_memory_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    # Clear in-memory DB before each test
    in_memory_db.clear()
    yield
    # Clean up after tests
    in_memory_db.clear()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_task():
    task_data = {
        "title": "Build CI/CD Pipeline",
        "description": "Set up Jenkinsfile with linting and Docker build",
        "status": "todo",
        "priority": "high"
    }
    response = client.post("/api/tasks", json=task_data)
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["title"] == task_data["title"]
    assert res_json["description"] == task_data["description"]
    assert res_json["id"] is not None


def test_get_tasks():
    # Create two tasks
    client.post("/api/tasks", json={"title": "Task 1", "status": "todo"})
    client.post("/api/tasks", json={"title": "Task 2", "status": "in-progress"})

    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2
    assert tasks[0]["title"] == "Task 1"
    assert tasks[1]["title"] == "Task 2"


def test_update_task():
    # Create a task
    create_response = client.post("/api/tasks", json={"title": "Original Task", "status": "todo"})
    task_id = create_response.json()["id"]

    updated_data = {
        "title": "Updated Task",
        "description": "New description",
        "status": "done",
        "priority": "low"
    }
    response = client.put(f"/api/tasks/{task_id}", json=updated_data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["title"] == "Updated Task"
    assert res_json["status"] == "done"
    assert res_json["priority"] == "low"


def test_delete_task():
    # Create a task
    create_response = client.post("/api/tasks", json={"title": "Task to Delete", "status": "todo"})
    task_id = create_response.json()["id"]

    # Delete task
    delete_response = client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 204

    # Verify task is deleted
    get_response = client.get("/api/tasks")
    assert len(get_response.json()) == 0


def test_update_nonexistent_task():
    updated_data = {
        "title": "Ghost Task",
        "status": "done"
    }
    response = client.put("/api/tasks/999", json=updated_data)
    assert response.status_code == 404


def test_delete_nonexistent_task():
    response = client.delete("/api/tasks/999")
    assert response.status_code == 404
