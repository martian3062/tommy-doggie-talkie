from pathlib import Path
from typing import Any

import numpy as np

from app.services.breed_intelligence import breed_adjustments_for, get_breed_profile


MODEL_REGISTRY: dict[str, dict[str, str]] = {
    "dog_detection": {
        "baseline": "Ultralytics YOLO pretrained detect model",
        "advanced": "Fine-tuned YOLO on app dog frames",
        "status": "implemented as optional adapter with heuristic fallback",
    },
    "pose_keypoints": {
        "baseline": "mwmathis/DeepLabCutModelZoo-SuperAnimal-Quadruped",
        "advanced": "Fine-tune with 100-300 app-labeled frames",
        "status": "declared; license-gated before commercial use",
    },
    "bark_detection": {
        "baseline": "rmarcosg/bark-detection-model",
        "advanced": "Fine-tuned dog-only Wav2Vec2/HuBERT",
        "status": "declared; optional transformers integration",
    },
    "animal_sound": {
        "baseline": "ardneebwar/wav2vec2-animal-sounds-finetuned-hubert-finetuned-animals",
        "advanced": "Custom bark/whine/growl/howl/pant/noise classifier",
        "status": "declared; optional transformers integration",
    },
    "dog_emotion_image": {
        "baseline": "Dewa/dog_emotion_v2",
        "advanced": "Fine-tuned app-frame classifier",
        "status": "declared; weak signal only",
    },
    "video_behavior": {
        "baseline": "Rules from pose/audio/context features",
        "advanced": "VideoMAE or PyTorchVideo SlowFast fine-tuning",
        "status": "rules implemented for MVP",
    },
    "breed_detection": {
        "baseline": "djhua0103/dog-breed-resnet50 / Stanford Dogs style classifiers",
        "advanced": "Fine-tuned breed classifier on local phone-video frames and mixed-breed labels",
        "status": "implemented as optional image-classification adapter with fallback",
    },
}


def _try_yolo_detection(media_path: str | None) -> dict[str, Any]:
    if not media_path or not Path(media_path).exists():
        return {"available": False, "dog_frames": 0, "avg_confidence": 0.0, "reason": "no media"}
    try:
        from ultralytics import YOLO

        model = YOLO("yolo11n.pt")
        results = model(media_path, stream=True, verbose=False)
        dog_frames = 0
        confidences: list[float] = []
        sampled = 0
        for result in results:
            sampled += 1
            names = result.names
            for box in result.boxes:
                label = names[int(box.cls.item())]
                if label == "dog":
                    dog_frames += 1
                    confidences.append(float(box.conf.item()))
            if sampled >= 24:
                break
        return {
            "available": True,
            "dog_frames": dog_frames,
            "sampled_frames": sampled,
            "avg_confidence": float(np.mean(confidences)) if confidences else 0.0,
        }
    except Exception as exc:
        return {
            "available": False,
            "dog_frames": 0,
            "avg_confidence": 0.0,
            "reason": f"YOLO unavailable: {exc.__class__.__name__}",
        }


def _heuristic_audio_signals(media_path: str | None) -> dict[str, Any]:
    if not media_path or not Path(media_path).exists():
        return {"available": False, "bark_likelihood": 0.0, "reason": "no media"}
    size_mb = Path(media_path).stat().st_size / (1024 * 1024)
    return {
        "available": False,
        "bark_likelihood": min(0.65, 0.2 + size_mb / 50),
        "reason": "audio model not loaded; using media-size placeholder signal",
    }


def _context_label_boost(context_tags: list[str]) -> dict[str, float]:
    normalized = {tag.lower().strip() for tag in context_tags}
    boosts = {
        "playful": 0.0,
        "hungry": 0.0,
        "attention seeking": 0.0,
        "anxious": 0.0,
        "alert/guarding": 0.0,
        "resting": 0.0,
        "pain/discomfort possible": 0.0,
        "unknown": 0.0,
    }
    if {"toy", "park", "play", "excited"} & normalized:
        boosts["playful"] += 0.18
    if {"food", "meal", "kitchen", "treat"} & normalized:
        boosts["hungry"] += 0.22
    if {"door", "visitor", "noise", "outside"} & normalized:
        boosts["alert/guarding"] += 0.18
    if {"alone", "crate", "storm", "fireworks"} & normalized:
        boosts["anxious"] += 0.2
    if {"sleep", "bed", "calm"} & normalized:
        boosts["resting"] += 0.22
    if {"limp", "pain", "vet", "injury"} & normalized:
        boosts["pain/discomfort possible"] += 0.3
    return boosts


def analyze_media(
    media_path: str | None,
    context_tags: list[str],
    dog_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detection = _try_yolo_detection(media_path)
    audio = _heuristic_audio_signals(media_path)
    boosts = _context_label_boost(context_tags)
    dog_profile = dog_profile or {}
    breed = dog_profile.get("breed")
    breed_profile = get_breed_profile(breed)
    breed_biases, breed_notes, health_watch = breed_adjustments_for(breed)

    dog_seen = detection.get("dog_frames", 0) > 0
    detection_conf = float(detection.get("avg_confidence", 0.0))
    bark_likelihood = float(audio.get("bark_likelihood", 0.0))

    scores = {
        "playful": 0.34 + boosts["playful"] + max(detection_conf - 0.4, 0) * 0.2,
        "hungry": 0.22 + boosts["hungry"],
        "attention seeking": 0.28 + bark_likelihood * 0.2 + boosts["attention seeking"],
        "anxious": 0.2 + bark_likelihood * 0.24 + boosts["anxious"],
        "alert/guarding": 0.2 + bark_likelihood * 0.28 + boosts["alert/guarding"],
        "resting": 0.18 + boosts["resting"],
        "pain/discomfort possible": 0.08 + boosts["pain/discomfort possible"],
        "unknown": 0.15 if dog_seen else 0.55,
    }
    for label, boost in breed_biases.items():
        if label in scores:
            scores[label] += boost
    if health_watch and any(tag.lower() in {"limp", "pain", "panting", "heat", "injury"} for tag in context_tags):
        scores["pain/discomfort possible"] += 0.12

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    top_predictions = [
        {
            "label": label,
            "confidence": round(min(score, 0.92), 2),
            "evidence": _evidence_for(label, detection, audio, context_tags, breed_profile),
        }
        for label, score in ordered
    ]

    uncertainty = []
    if not detection.get("available"):
        uncertainty.append(detection.get("reason", "dog detector did not run"))
    if not audio.get("available"):
        uncertainty.append(audio.get("reason", "audio detector did not run"))
    if not dog_seen:
        uncertainty.append("dog not confidently detected in sampled frames")

    return {
        "top_predictions": top_predictions,
        "uncertainty_reason": "; ".join(uncertainty) if uncertainty else None,
        "needs_feedback": True,
        "evidence_timeline": [
            {"time_sec": 0, "event": "media_received", "detail": media_path or "storage-only job"},
            {"time_sec": 1, "event": "dog_detection", "detail": detection},
            {"time_sec": 2, "event": "audio_signal", "detail": audio},
            {"time_sec": 3, "event": "breed_adjustment", "detail": breed_profile},
        ],
        "raw_signals": {
            "model_registry": MODEL_REGISTRY,
            "dog_detection": detection,
            "audio": audio,
            "context_tags": context_tags,
            "breed_profile": breed_profile,
            "breed_notes": breed_notes,
            "health_watch": health_watch,
        },
    }


def _evidence_for(
    label: str,
    detection: dict[str, Any],
    audio: dict[str, Any],
    context_tags: list[str],
    breed_profile: dict[str, Any],
) -> list[str]:
    evidence = []
    if detection.get("dog_frames", 0) > 0:
        evidence.append(f"dog detected in {detection.get('dog_frames')} sampled frame(s)")
    if audio.get("bark_likelihood", 0) > 0.3:
        evidence.append("audio activity suggests possible vocalization")
    if context_tags:
        evidence.append(f"context tags: {', '.join(context_tags)}")
    if breed_profile.get("slug") != "unknown":
        evidence.append(f"breed profile: {breed_profile.get('display_name')}")
    if label == "unknown":
        evidence.append("not enough validated model evidence for a stronger label")
    return evidence or ["baseline rules only; user feedback needed"]
