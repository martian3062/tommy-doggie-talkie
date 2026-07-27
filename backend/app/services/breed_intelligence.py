import json
from functools import lru_cache
from pathlib import Path
from typing import Any

LOCAL_BREED_MODEL_SOURCE = "tommy-breed-resnet50-kaggle"


def _slug(value: str) -> str:
    return value.lower().replace("_", " ").replace("-", " ").strip()


BREED_PROFILES: dict[str, dict[str, Any]] = {
    "german shepherd": {
        "display_name": "German Shepherd",
        "group": "herding/working",
        "energy_level": "high",
        "behavior_biases": {"alert/guarding": 0.16, "anxious": 0.04},
        "common_patterns": ["watching doors/windows", "protective barking", "task-seeking focus"],
        "health_watch": ["hip or joint discomfort", "repeated pacing under stress"],
        "interpretation_notes": ["Guarding-like cues need visitor/noise context before calling anxiety."],
    },
    "siberian husky": {
        "display_name": "Siberian Husky",
        "group": "working/spitz",
        "energy_level": "very high",
        "behavior_biases": {"attention seeking": 0.14, "playful": 0.1, "anxious": 0.04},
        "common_patterns": ["high vocalization", "escape-seeking boredom", "playful dramatic response"],
        "health_watch": ["heat stress", "restlessness from under-exercise"],
        "interpretation_notes": ["Frequent vocalization is not automatically distress for this breed."],
    },
    "border collie": {
        "display_name": "Border Collie",
        "group": "herding",
        "energy_level": "very high",
        "behavior_biases": {"playful": 0.12, "attention seeking": 0.08, "anxious": 0.06},
        "common_patterns": ["staring/fixating", "herding motion", "task-seeking behavior"],
        "health_watch": ["compulsive fixation", "stress from low mental stimulation"],
        "interpretation_notes": ["Staring and circling can be herding drive, not only anxiety."],
    },
    "labrador retriever": {
        "display_name": "Labrador Retriever",
        "group": "sporting/retriever",
        "energy_level": "medium-high",
        "behavior_biases": {"hungry": 0.14, "playful": 0.12, "attention seeking": 0.05},
        "common_patterns": ["food-seeking", "retrieving play", "social attention seeking"],
        "health_watch": ["joint discomfort", "overfeeding/weight gain"],
        "interpretation_notes": ["Food context should strongly influence begging and kitchen behavior."],
    },
    "golden retriever": {
        "display_name": "Golden Retriever",
        "group": "sporting/retriever",
        "energy_level": "medium-high",
        "behavior_biases": {"playful": 0.12, "attention seeking": 0.08, "hungry": 0.06},
        "common_patterns": ["social approach", "retrieving play", "owner-oriented behavior"],
        "health_watch": ["joint discomfort", "skin/itch discomfort cues"],
        "interpretation_notes": ["Close owner-following often reflects social drive."],
    },
    "beagle": {
        "display_name": "Beagle",
        "group": "hound",
        "energy_level": "medium-high",
        "behavior_biases": {"alert/guarding": 0.1, "hungry": 0.1, "attention seeking": 0.06},
        "common_patterns": ["scent tracking", "bay/howl vocalization", "food-seeking"],
        "health_watch": ["ear discomfort", "weight gain"],
        "interpretation_notes": ["Nose-down scanning often means scent interest rather than avoidance."],
    },
    "bulldog": {
        "display_name": "Bulldog",
        "group": "companion/non-sporting",
        "energy_level": "low-medium",
        "behavior_biases": {"resting": 0.14, "pain/discomfort possible": 0.06},
        "common_patterns": ["short play bursts", "resting after exertion", "close-contact affection"],
        "health_watch": ["breathing distress", "heat stress", "skin fold irritation"],
        "interpretation_notes": ["Panting after mild activity deserves more caution than in athletic breeds."],
    },
    "pug": {
        "display_name": "Pug",
        "group": "toy/companion",
        "energy_level": "low-medium",
        "behavior_biases": {"attention seeking": 0.1, "resting": 0.1, "pain/discomfort possible": 0.06},
        "common_patterns": ["owner proximity", "attention seeking", "short activity bursts"],
        "health_watch": ["breathing distress", "heat stress", "eye discomfort"],
        "interpretation_notes": ["Noisy breathing plus restlessness should be surfaced as caution."],
    },
    "dachshund": {
        "display_name": "Dachshund",
        "group": "hound",
        "energy_level": "medium",
        "behavior_biases": {"alert/guarding": 0.09, "pain/discomfort possible": 0.08},
        "common_patterns": ["digging", "burrowing", "alert barking"],
        "health_watch": ["back/spine discomfort", "reluctance to jump or climb"],
        "interpretation_notes": ["Hunched posture or jump refusal should raise discomfort caution."],
    },
    "indie": {
        "display_name": "Indian Pariah / Indie",
        "group": "landrace/mixed",
        "energy_level": "medium-high",
        "behavior_biases": {"alert/guarding": 0.08, "playful": 0.06},
        "common_patterns": ["environment scanning", "adaptive routine learning", "territorial alerting"],
        "health_watch": ["injury or limp changes", "heat stress"],
        "interpretation_notes": ["Use personal baseline heavily because variation is broad."],
    },
    "mixed": {
        "display_name": "Mixed Breed",
        "group": "mixed",
        "energy_level": "varies",
        "behavior_biases": {},
        "common_patterns": ["breed signals may be blended", "personal history matters most"],
        "health_watch": ["repeated changes from personal baseline"],
        "interpretation_notes": ["Prefer top breed predictions plus owner corrections over hard labels."],
    },
    "unknown": {
        "display_name": "Unknown Breed",
        "group": "unknown",
        "energy_level": "unknown",
        "behavior_biases": {},
        "common_patterns": ["insufficient breed evidence"],
        "health_watch": ["repeated discomfort or unusual behavior"],
        "interpretation_notes": ["Do not apply breed priors until user or model gives a reliable breed."],
    },
}


ALIASES = {
    "gsd": "german shepherd",
    "german_shepherd": "german shepherd",
    "husky": "siberian husky",
    "siberian_husky": "siberian husky",
    "lab": "labrador retriever",
    "labrador": "labrador retriever",
    "golden": "golden retriever",
    "golden_retriever": "golden retriever",
    "indian pariah": "indie",
    "indian pariah dog": "indie",
    "indian_pariah": "indie",
}


def normalize_breed(value: str | None) -> str:
    if not value:
        return "unknown"
    key = _slug(value)
    return ALIASES.get(key, key)


def get_breed_profile(breed: str | None) -> dict[str, Any]:
    key = normalize_breed(breed)
    profile = BREED_PROFILES.get(key, BREED_PROFILES["unknown"])
    return {"slug": key if key in BREED_PROFILES else "unknown", **profile}


def list_breed_profiles() -> list[dict[str, Any]]:
    return [{"slug": slug, **profile} for slug, profile in sorted(BREED_PROFILES.items())]


def profile_for_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    if not predictions:
        return get_breed_profile("unknown")
    return get_breed_profile(predictions[0].get("breed"))


def heuristic_breed_predictions(
    filename: str | None,
    context_tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    text = " ".join([filename or "", *(context_tags or [])]).lower()
    matches: list[dict[str, Any]] = []
    for slug, profile in BREED_PROFILES.items():
        if slug != "unknown" and slug in text:
            matches.append({"breed": profile["display_name"], "confidence": 0.72, "source": "heuristic"})
    if matches:
        return matches[:3]
    return [
        {"breed": "Mixed Breed", "confidence": 0.34, "source": "fallback"},
        {"breed": "Indian Pariah / Indie", "confidence": 0.22, "source": "fallback"},
        {"breed": "Unknown Breed", "confidence": 0.18, "source": "fallback"},
    ]


@lru_cache(maxsize=2)
def _cached_torchscript_model(model_path: str, labels_path: str) -> tuple[Any, list[str]] | None:
    try:
        import torch

        labels = [str(label) for label in json.loads(Path(labels_path).read_text(encoding="utf-8"))]
        model = torch.jit.load(model_path, map_location="cpu")
        model.eval()
        return model, labels
    except Exception:
        return None


def _local_breed_model() -> tuple[Any, list[str]] | None:
    from app.core.config import get_settings

    model_dir = get_settings().breed_model_dir
    model_path = model_dir / "breed_model.torchscript.pt"
    labels_path = model_dir / "labels.json"
    if not model_path.exists() or not labels_path.exists():
        return None
    return _cached_torchscript_model(str(model_path), str(labels_path))


def _image_tensor(media_path: str, image_size: int = 224) -> Any:
    import numpy as np
    import torch
    from PIL import Image

    image = Image.open(media_path).convert("RGB")
    scale = (image_size * 256 / 224) / min(image.size)
    image = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.BILINEAR,
    )
    left = (image.width - image_size) // 2
    top = (image.height - image_size) // 2
    image = image.crop((left, top, left + image_size, top + image_size))
    array = np.asarray(image, dtype="float32") / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype="float32")
    std = np.array([0.229, 0.224, 0.225], dtype="float32")
    array = (array - mean) / std
    return torch.from_numpy(array.transpose(2, 0, 1)).unsqueeze(0)


def _local_breed_predictions(media_path: str) -> list[dict[str, Any]] | None:
    loaded = _local_breed_model()
    if not loaded:
        return None
    model, labels = loaded
    try:
        import torch

        with torch.inference_mode():
            logits = model(_image_tensor(media_path))
            probabilities = torch.softmax(logits[0], dim=0)
            top = torch.topk(probabilities, k=min(3, len(labels)))
        return [
            {
                "breed": labels[index],
                "confidence": round(float(score), 3),
                "source": LOCAL_BREED_MODEL_SOURCE,
            }
            for score, index in zip(top.values.tolist(), top.indices.tolist())
        ]
    except Exception:
        return None


def detect_breed_from_media(
    media_path: str | None,
    original_filename: str | None = None,
) -> list[dict[str, Any]]:
    if not media_path or not Path(media_path).exists():
        return heuristic_breed_predictions(original_filename or media_path)
    local_predictions = _local_breed_predictions(media_path)
    if local_predictions:
        return local_predictions
    try:
        from transformers import pipeline

        classifier = pipeline("image-classification", model="djhua0103/dog-breed-resnet50")
        raw_predictions = classifier(media_path, top_k=3)
        predictions = []
        for item in raw_predictions:
            label = str(item["label"]).replace("_", " ").title()
            predictions.append(
                {
                    "breed": label,
                    "confidence": round(float(item["score"]), 3),
                    "source": "djhua0103/dog-breed-resnet50",
                }
            )
        return predictions
    except Exception:
        return heuristic_breed_predictions(original_filename or Path(media_path).name)


def breed_adjustments_for(breed: str | None) -> tuple[dict[str, float], list[str], list[str]]:
    profile = get_breed_profile(breed)
    return (
        dict(profile.get("behavior_biases", {})),
        list(profile.get("interpretation_notes", [])),
        list(profile.get("health_watch", [])),
    )
