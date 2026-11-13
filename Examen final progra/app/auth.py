from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer token-"):
        raise HTTPException(status_code=401, detail="No autenticado.")
    try:
        user_id = int(authorization.removeprefix("Bearer token-"))
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    return user
