from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import init_db
from app.main import app


init_db()
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dog_job_result_feedback_flow(tmp_path: Path) -> None:
    dog_response = client.post(
        "/api/v1/dogs",
        json={
            "name": "Milo",
            "breed": "Indie",
            "breed_source": "user_selected",
            "routines": {"walk": "morning"},
        },
    )
    assert dog_response.status_code == 200
    dog_id = dog_response.json()["id"]
    assert dog_response.json()["breed_source"] == "user_selected"

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake-video")
    with video.open("rb") as handle:
        job_response = client.post(
            "/api/v1/analysis-jobs",
            data={"dog_id": dog_id, "context_tags": '["play", "toy"]'},
            files={"file": ("clip.mp4", handle, "video/mp4")},
        )
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "done"

    result_response = client.get(f"/api/v1/analysis-jobs/{job['id']}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["top_predictions"]
    assert result["raw_signals"]["breed_profile"]["display_name"] == "Indian Pariah / Indie"

    feedback_response = client.post(
        f"/api/v1/analysis-jobs/{job['id']}/feedback",
        json={"selected_label": "playful", "is_correct": True, "note": "Tail wagging near toy"},
    )
    assert feedback_response.status_code == 200

    habits_response = client.get(f"/api/v1/dogs/{dog_id}/habits")
    assert habits_response.status_code == 200
    assert habits_response.json()["label_counts"]["playful"] >= 1


def test_breed_profiles_and_detection_fallback(tmp_path: Path) -> None:
    dog_response = client.post("/api/v1/dogs", json={"name": "Tommy"})
    assert dog_response.status_code == 200
    dog_id = dog_response.json()["id"]

    breeds_response = client.get("/api/v1/breeds")
    assert breeds_response.status_code == 200
    assert any(item["slug"] == "siberian husky" for item in breeds_response.json())

    profile_response = client.get("/api/v1/breeds/husky/behavior-profile")
    assert profile_response.status_code == 200
    assert profile_response.json()["display_name"] == "Siberian Husky"

    image = tmp_path / "siberian husky.jpg"
    image.write_bytes(b"fake-image")
    with image.open("rb") as handle:
        detect_response = client.post(
            f"/api/v1/dogs/{dog_id}/breed-detect",
            files={"file": ("siberian husky.jpg", handle, "image/jpeg")},
        )
    assert detect_response.status_code == 200
    payload = detect_response.json()
    assert payload["breed_predictions"]
    assert payload["behavior_profile"]["display_name"] == "Siberian Husky"
