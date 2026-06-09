from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import OwnerDep, SessionDep
from app.models import Dog, HabitSummary
from app.schemas import DogCreate, DogRead, HabitSummaryRead, RetrainResponse

router = APIRouter(prefix="/dogs", tags=["dogs"])


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
