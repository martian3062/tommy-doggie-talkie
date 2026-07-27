from litestar import Router, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import NamedDependency
from litestar.exceptions import HTTPException
from litestar.params import FromPath, MultipartBody
from litestar.status_codes import HTTP_200_OK
from sqlmodel import Session, select

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


def _owned_dog_or_404(session: Session, dog_id: str, owner_id: str) -> Dog:
    dog = session.get(Dog, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Dog not found")
    return dog


@post("/", status_code=HTTP_200_OK, sync_to_thread=True)
def create_dog(
    data: DogCreate,
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> DogRead:
    dog = Dog(owner_id=owner_id, **data.model_dump())
    session.add(dog)
    session.commit()
    session.refresh(dog)
    return DogRead.model_validate(dog, from_attributes=True)


@get("/", sync_to_thread=True)
def list_dogs(
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> list[DogRead]:
    dogs = session.exec(select(Dog).where(Dog.owner_id == owner_id)).all()
    return [DogRead.model_validate(dog, from_attributes=True) for dog in dogs]


@patch("/{dog_id:str}", sync_to_thread=True)
def update_dog(
    dog_id: FromPath[str],
    data: DogCreate,
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> DogRead:
    dog = _owned_dog_or_404(session, dog_id, owner_id)
    for key, value in data.model_dump().items():
        setattr(dog, key, value)
    session.add(dog)
    session.commit()
    session.refresh(dog)
    return DogRead.model_validate(dog, from_attributes=True)


@post("/{dog_id:str}/breed-detect", status_code=HTTP_200_OK)
async def detect_breed(
    dog_id: FromPath[str],
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
    data: MultipartBody[UploadFile],
) -> BreedDetectionRead:
    dog = _owned_dog_or_404(session, dog_id, owner_id)
    local_path = await StorageService().save_upload(data, owner_id=owner_id, dog_id=dog_id)
    predictions = detect_breed_from_media(local_path, original_filename=data.filename)
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


@get("/{dog_id:str}/habits", sync_to_thread=True)
def get_habits(
    dog_id: FromPath[str],
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> HabitSummaryRead:
    habit = session.exec(
        select(HabitSummary).where(HabitSummary.dog_id == dog_id, HabitSummary.owner_id == owner_id)
    ).first()
    if not habit:
        _owned_dog_or_404(session, dog_id, owner_id)
        habit = HabitSummary(dog_id=dog_id, owner_id=owner_id)
        session.add(habit)
        session.commit()
        session.refresh(habit)
    return HabitSummaryRead.model_validate(habit, from_attributes=True)


@post("/{dog_id:str}/personal-model/retrain", status_code=HTTP_200_OK, sync_to_thread=True)
def retrain_personal_model(
    dog_id: FromPath[str],
    session: NamedDependency[Session],
    owner_id: NamedDependency[str],
) -> RetrainResponse:
    _owned_dog_or_404(session, dog_id, owner_id)
    return RetrainResponse(
        dog_id=dog_id,
        queued=False,
        message="Need at least 30-50 corrected clips before per-dog retraining is useful.",
    )


@get("/", sync_to_thread=False)
def list_breeds() -> list[BreedProfileRead]:
    return [BreedProfileRead.model_validate(profile) for profile in list_breed_profiles()]


@get("/{breed_slug:str}/behavior-profile", sync_to_thread=False)
def get_breed_behavior_profile(breed_slug: FromPath[str]) -> BreedProfileRead:
    return BreedProfileRead.model_validate(get_breed_profile(breed_slug))


dogs_router = Router(
    path="/api/v1/dogs",
    tags=["dogs"],
    route_handlers=[
        create_dog,
        list_dogs,
        update_dog,
        detect_breed,
        get_habits,
        retrain_personal_model,
    ],
)

breeds_router = Router(
    path="/api/v1/breeds",
    tags=["breeds"],
    route_handlers=[list_breeds, get_breed_behavior_profile],
)
