# Model Subtasks

| Subtask | Baseline | Advanced path | Implementation status |
|---|---|---|---|
| Dog detection | Ultralytics YOLO pretrained detect model | Fine-tune YOLO on app frames | Optional YOLO adapter with fallback rules |
| Dog tracking | YOLO detections + tracker | Per-dog embeddings for multi-dog scenes | Planned |
| Pose/keypoints | `mwmathis/DeepLabCutModelZoo-SuperAnimal-Quadruped` | Fine-tune with app-labeled frames | Declared, license-gated |
| Bark detection | `rmarcosg/bark-detection-model` | Fine-tuned dog-only audio model | Planned |
| Animal sound | `ardneebwar/wav2vec2-animal-sounds-finetuned-hubert-finetuned-animals` | Bark/whine/growl/howl/pant/noise classifier | Planned |
| Dog emotion image | `Dewa/dog_emotion_v2` | App-frame classifier | Planned, weak signal only |
| Video behavior | Rules from context/audio/pose | VideoMAE or SlowFast fine-tuning | MVP rules implemented |
| Canine reasoning | Pawgaze | Evaluation taxonomy and prompts | Planned evaluation dataset |
| Personal dog learning | Feedback counts + simple patterns | Per-dog classifier after 30-50 clips | Habit feedback implemented |
| Breed intelligence | Breed profile priors + optional `djhua0103/dog-breed-resnet50` | Fine-tuned breed classifier on clear owner photos, phone videos, and mixed-breed labels | Breed APIs, mobile UI, and behavior-score adjustments implemented |

## Validation Rule

Choose the "best" model by app-specific validation, not by popularity:

- Dog visible: precision/recall over phone clips.
- Bark/no-bark: F1 over quiet/noisy clips.
- Behavior labels: agreement with owner correction.
- Personal learning: improvement after feedback compared with baseline result.
- Breed layer: top-3 breed prediction quality on clear photos, mixed-breed honesty, and whether breed priors improve owner-corrected behavior labels.
