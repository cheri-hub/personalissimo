from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Usuario


ItemId = Annotated[int, Path(ge=1, le=2**31 - 1)]


def make_crud_router(prefix: str, model: type, in_schema: type[BaseModel], out_schema: type[BaseModel]) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[prefix.strip("/")])

    def _owned(db: Session, item_id: int, user: Usuario):
        obj = db.scalar(select(model).where(model.id == item_id, model.user_id == user.id))
        if obj is None:
            raise HTTPException(status_code=404, detail="Não encontrado")
        return obj

    @router.get("", response_model=list[out_schema])
    def listar(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
        return db.scalars(select(model).where(model.user_id == user.id).order_by(model.id)).all()

    @router.post("", response_model=out_schema, status_code=201)
    def criar(payload: in_schema, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
        obj = model(**payload.model_dump(), user_id=user.id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get("/{item_id}", response_model=out_schema)
    def obter(item_id: ItemId, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
        return _owned(db, item_id, user)

    @router.put("/{item_id}", response_model=out_schema)
    def atualizar(
        item_id: ItemId,
        payload: in_schema,
        user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        obj = _owned(db, item_id, user)
        for campo, valor in payload.model_dump().items():
            setattr(obj, campo, valor)
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=204)
    def remover(item_id: ItemId, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
        db.delete(_owned(db, item_id, user))
        db.commit()
        return Response(status_code=204)

    return router
