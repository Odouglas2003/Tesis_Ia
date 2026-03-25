import pytest
import pandas as pd
from app.recommendation_engine import SoftwareTeamRecommender


@pytest.fixture
def sample_data():
    data = {
        "id": [1, 2, 3],
        "nombre": ["Alice", "Bob", "Charlie"],
        "perfil": ["Developer", "Developer", "DevOps"],
        "nivel": ["Senior", "Mid", "Senior"],
        "salario": [5000, 4000, 4500],
        "anos_experiencia": [5, 3, 4],
        "Python_exp": [0.8, 0.6, 0.3],
        "Python_proyectos": [5, 3, 1],
        "Python_principal": [1, 1, 0],
        "React_exp": [0.2, 0.7, 0.1],
        "React_proyectos": [1, 4, 0],
        "React_principal": [0, 1, 0],
        "Docker_exp": [0.3, 0.4, 0.9],
        "Docker_proyectos": [2, 3, 5],
        "Docker_principal": [0, 0, 1],
    }
    return pd.DataFrame(data)


def test_recommend_backend_team(sample_data):
    recommender = SoftwareTeamRecommender(sample_data)
    result = recommender.recommend_team(
        project_description="Proyecto backend en Python",
        team_structure={"backend": 2},
        budget=10000,
    )

    assert len(result["equipo"]) == 2
    assert result["equipo"][0]["nombre"] == "Alice"  # Mejor puntaje Python
    assert result["presupuesto_utilizado"] <= 10000


def test_recommend_with_criteria(sample_data):
    recommender = SoftwareTeamRecommender(sample_data)
    result = recommender.recommend_team(
        project_description="Proyecto DevOps",
        team_structure={"devops": 1},
        budget=5000,
        criteria={"devops": {"Docker_exp": 0.8}},
    )

    assert len(result["equipo"]) == 1
    assert result["equipo"][0]["nombre"] == "Charlie"  # Único con Docker_exp >= 0.8


def test_budget_constraint(sample_data):
    recommender = SoftwareTeamRecommender(sample_data)
    result = recommender.recommend_team(
        project_description="Proyecto pequeño",
        team_structure={"backend": 3},
        budget=9000,
    )

    # Solo debería poder contratar a Alice (5000) y Bob (4000) = 9000
    assert len(result["equipo"]) == 2
    assert result["presupuesto_utilizado"] == 9000
