import pytest
from fastapi.testclient import TestClient
from database import Base, SessionLocal, engine, init_db, Customer, Product, Order
from main import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Initializes the database schema and seeds sample records once for the test module."""
    # Ensure tables are built and seeded
    init_db()
    yield


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_total_revenue():
    # Ask a question matching total revenue mock mapping
    response = client.post("/api/chat", json={"question": "What is the total revenue?"})
    assert response.status_code == 200
    
    res_json = response.json()
    assert "SELECT SUM(total_amount)" in res_json["sql_query"]
    assert "total_revenue" in res_json["columns"]
    assert len(res_json["results"]) == 1
    # Check that we have a numeric positive value in results
    assert res_json["results"][0]["total_revenue"] > 0
    assert "total_revenue" in res_json["answer"].lower() or "based on" in res_json["answer"].lower()


def test_chat_shoe_buyers():
    response = client.post("/api/chat", json={"question": "Who bought shoes?"})
    assert response.status_code == 200
    
    res_json = response.json()
    assert "name" in res_json["columns"]
    # Verify that at least Alice Johnson bought the Performance Running Shoes in mock seed data
    buyers = [row["name"] for row in res_json["results"]]
    assert "Alice Johnson" in buyers


def test_chat_list_products():
    response = client.post("/api/chat", json={"question": "List all products."})
    assert response.status_code == 200
    
    res_json = response.json()
    assert "name" in res_json["columns"]
    assert "price" in res_json["columns"]
    assert len(res_json["results"]) >= 5  # We seeded 5 items


def test_chat_empty_question():
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 400
