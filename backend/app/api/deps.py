from typing import Annotated

from fastapi import Depends, Header
from sqlmodel import Session

from app.core.database import get_session


SessionDep = Annotated[Session, Depends(get_session)]


def get_current_owner_id(x_user_id: Annotated[str | None, Header()] = None) -> str:
    # Supabase JWT verification can be added once project credentials are supplied.
    # Until then, this keeps local development and APK smoke tests simple.
    return x_user_id or "local-demo-user"


OwnerDep = Annotated[str, Depends(get_current_owner_id)]
