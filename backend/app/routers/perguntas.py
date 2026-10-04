from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agent.engine import MotorErro, responder
from app.agent.gemini import GeminiProvider
from app.agent.types import LLMProvider, ProviderError, ProviderQuotaError
from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models import Pergunta, Usuario

router = APIRouter(prefix="/perguntas", tags=["perguntas"])


class PerguntaIn(BaseModel):
    texto: str = Field(min_length=3, max_length=1000)


class PerguntaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    modo: str
    resposta: dict | None
    mensagem: str | None
    criado_em: datetime


def get_provider() -> LLMProvider:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Provedor de IA não configurado")
    return GeminiProvider(settings.gemini_api_key, settings.gemini_model)


def _perguntas_hoje(db: Session, user_id: int) -> int:
    inicio = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    consulta = select(func.count()).select_from(Pergunta).where(
        Pergunta.user_id == user_id, Pergunta.criado_em >= inicio
    )
    return db.scalar(consulta) or 0


@router.post("", response_model=PerguntaOut, status_code=201)
def perguntar(
    payload: PerguntaIn,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_provider),
):
    if _perguntas_hoje(db, user.id) >= user.limite_diario:
        raise HTTPException(status_code=429, detail="Limite diário de perguntas atingido. Volte amanhã.")
    try:
        return responder(db, user, payload.texto, provider)
    except ProviderQuotaError:
        raise HTTPException(status_code=503, detail="O serviço de IA está sobrecarregado. Tente novamente em alguns minutos.")
    except (MotorErro, ProviderError):
        raise HTTPException(status_code=502, detail="Não consegui gerar uma resposta confiável. Tente novamente.")


@router.get("", response_model=list[PerguntaOut])
def historico(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    consulta = (
        select(Pergunta)
        .where(Pergunta.user_id == user.id)
        .order_by(Pergunta.criado_em.desc(), Pergunta.id.desc())
        .limit(50)
    )
    return db.scalars(consulta).all()
