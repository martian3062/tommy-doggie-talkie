from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlmodel import select

from app.api.deps import OwnerDep, SessionDep
from app.models import Dog, HabitSummary
from app.schemas import (
    BreedDetectionRead,
    BreedProfileRead,
    DogCreate,
    DogRead,
    HabitSummaryRead,
    RetrainResponse,
)
from app.services.breed_intelligence import (
    detect_breed_from_media,
    get_breed_profile,
    list_breed_profiles,
    profile_for_predictions,
)
from app.services.storage import StorageService

router = APIRouter(prefix="/dogs", tags=["dogs"])
breed_router = APIRouter(prefix="/breeds", tags=["breeds"])


@router.post("", response_model=DogRead)
def create_dog(payload: DogCreate, session: SessionDep, owner_id: OwnerDep) -> Dog:
    dog = Dog(owner_id=owner_id, **payload.model_dump())
    session.add(dog)
    session.commit()
    session.refresh(dog)
    return dog


@router.get("", response_model=list[DogRead])
def list_dogs(session: SessionDep, owner_id: OwnerDep) -> list[Dog]:
    return list(session.exec(select(Dog).where(Dog.owner_id == owner_id)).all())


@router.patch("/{dog_id}", response_model=DogRead)
def update_dog(dog_id: str, payload: DogCreate, session: SessionDep, owner_id: OwnerDep) -> Dog:
    dog = session.get(Dog, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")
    for key, value in payload.model_dump().items():
        setattr(dog, key, value)
    session.add(dog)
    session.commit()
    session.refresh(dog)
    return dog


@router.post("/{dog_id}/breed-detect", response_model=BreedDetectionRead)
async def detect_breed(
    dog_id: str,
    session: SessionDep,
    owner_id: OwnerDep,
    file: UploadFile = File(...),
) -> BreedDetectionRead:
    dog = session.get(Dog, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")
    local_path = await StorageService().save_upload(file, owner_id=owner_id, dog_id=dog_id)
    predictions = detect_breed_from_media(local_path, original_filename=file.filename)
    profile = profile_for_predictions(predictions)
    if predictions:
        top = predictions[0]
        dog.breed = top["breed"]
        dog.breed_source = top["source"]
        dog.breed_confidence = top["confidence"]
        dog.breed_predictions = predictions
        dog.breed_behavior_profile = profile
        session.add(dog)
        session.commit()
        session.refresh(dog)
    return BreedDetectionRead(
        dog_id=dog.id,
        breed_predictions=predictions,
        selected_breed=dog.breed,
        breed_source=dog.breed_source,
        behavior_profile=profile,
    )


@router.get("/{dog_id}/habits", response_model=HabitSummaryRead)
def get_habits(dog_id: str, session: SessionDep, owner_id: OwnerDep) -> HabitSummary:
    habit = session.exec(
        select(HabitSummary).where(HabitSummary.dog_id == dog_id, HabitSummary.owner_id == owner_id)
    ).first()
    if habit:
        return habit
    dog = session.get(Dog, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")
    habit = HabitSummary(dog_id=dog_id, owner_id=owner_id)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


@router.post("/{dog_id}/personal-model/retrain", response_model=RetrainResponse)
def retrain_personal_model(dog_id: str, session: SessionDep, owner_id: OwnerDep) -> RetrainResponse:
    dog = session.get(Dog, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")
    return RetrainResponse(
        dog_id=dog_id,
        queued=False,
        message="Need at least 30-50 corrected clips before per-dog retraining is useful.",
    )


@breed_router.get("", response_model=list[BreedProfileRead])
def list_breeds() -> list[dict]:
    return list_breed_profiles()


@breed_router.get("/{breed_slug}/behavior-profile", response_model=BreedProfileRead)
def get_breed_behavior_profile(breed_slug: str) -> dict:
    return get_breed_profile(breed_slug)
