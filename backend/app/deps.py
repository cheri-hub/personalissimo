from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Usuario
from app.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    user_id = decode_token(creds.credentials) if creds else None
    user = db.get(Usuario, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user
