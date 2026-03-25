from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generate_team():
    test_request = {
        "project_description": "Proyecto web con React",
        "team_structure": {"frontend": 1},
        "budget": 5000,
    }

    response = client.post("/api/teams/generate", json=test_request)
    assert response.status_code == 200

    data = response.json()
    assert "equipo" in data
    assert len(data["equipo"]) == 1
    assert data["equipo"][0]["rol"] == "frontend"


def test_get_history():
    response = client.get("/api/teams/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_endpoint():
    response = client.post("/api/chat", json={"query": "Hola", "chat_history": []})
    assert response.status_code == 200
    assert "answer" in response.json()
