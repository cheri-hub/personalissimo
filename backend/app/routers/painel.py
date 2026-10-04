from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.tools import financas
from app.db import get_db
from app.deps import get_current_user
from app.models import Usuario

router = APIRouter(tags=["painel"])


@router.get("/painel")
def painel(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "fluxo": financas.obter_fluxo_de_caixa(db, user.id),
        "patrimonio": financas.obter_patrimonio(db, user.id),
        "metas": financas.listar_metas(db, user.id),
    }
