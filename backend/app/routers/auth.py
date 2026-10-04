from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models import Usuario
from app.security import (
    create_token,
    hash_password,
    login_ip_limiter,
    login_limiter,
    register_ip_limiter,
    verify_password,
)

router = APIRouter(tags=["auth"])

Lente = Literal["estoicismo", "epicurismo", "tcc", "act", "mindfulness"]
Tom = Literal["direto", "acolhedor", "provocador"]

_DUMMY_HASH = hash_password("senha-fantasma")


class RegistroIn(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PerfilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    lentes: list[str]
    tom: str
    limite_diario: int


class ConfigIn(BaseModel):
    lentes: list[Lente] | None = None
    tom: Tom | None = None


@router.post("/auth/registro", response_model=PerfilOut, status_code=201)
def registrar(payload: RegistroIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if not register_ip_limiter.allow(ip):
        raise HTTPException(status_code=429, detail="Muitas tentativas de cadastro. Tente mais tarde.")
    user = Usuario(
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        limite_diario=get_settings().daily_question_limit,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email já cadastrado")
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower()
    ip = request.client.host if request.client else "unknown"
    if not login_ip_limiter.allow(ip) or not login_limiter.allow(f"{ip}:{email}"):
        raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde um minuto.")
    user = db.scalar(select(Usuario).where(Usuario.email == email))
    senha_ok = verify_password(user.senha_hash if user else _DUMMY_HASH, payload.senha)
    if user is None or not senha_ok:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return Token(access_token=create_token(user.id))


@router.get("/me", response_model=PerfilOut)
def me(user: Usuario = Depends(get_current_user)):
    return user


@router.patch("/me/config", response_model=PerfilOut)
def atualizar_config(
    payload: ConfigIn,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.lentes is not None:
        user.lentes = list(payload.lentes)
    if payload.tom is not None:
        user.tom = payload.tom
    db.commit()
    db.refresh(user)
    return user
