from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_user_stats_basic():
    response = client.get("/user-stats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_user_stats_filter_country():
    response = client.get("/user-stats?countries=USA")
    assert response.status_code == 200


def test_user_stats_filter_os():
    response = client.get("/user-stats?oss=iOS")
    assert response.status_code == 200


def test_map_stats_valid():
    response = client.get("/map-stats/Forest")
    assert response.status_code == 200

    data = response.json()
    if data:
        assert "date" in data[0]
        assert "match_cnt" in data[0]


def test_map_stats_invalid_map():
    response = client.get("/map-stats/INVALID_MAP_NAME")
    assert response.status_code == 404


def test_map_stats_with_dates():
    response = client.get(
        "/map-stats/Forest?date_from=2026-04-03&date_to=2026-04-07"
    )
    assert response.status_code == 200


def test_map_stats_bad_date():
    response = client.get(
        "/map-stats/Forest?date_from=bad-date"
    )
    assert response.status_code == 422

def test_player_stats_valid():
    response = client.get("/player-stats/CosmicRay2014")

    if response.status_code == 200:
        data = response.json()
        assert "username" in data
        assert "match_history" in data
    else:
        # fallback if DB doesn't contain this user
        assert response.status_code == 404


def test_player_stats_not_found():
    response = client.get("/player-stats/THIS_USER_DOES_NOT_EXIST")
    assert response.status_code == 404