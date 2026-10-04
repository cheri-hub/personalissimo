from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.db import Base

Dinheiro = Numeric(14, 2)


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    lentes: Mapped[list[str]] = mapped_column(JSON, default=list)
    tom: Mapped[str] = mapped_column(String(20), default="acolhedor")
    limite_diario: Mapped[int] = mapped_column(default=20)


class DonoMixin:
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("usuarios.id"), index=True)


class Renda(DonoMixin, Base):
    __tablename__ = "rendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(200))
    valor: Mapped[Decimal] = mapped_column(Dinheiro)
    frequencia: Mapped[str] = mapped_column(String(10), default="mensal")
    inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fim: Mapped[date | None] = mapped_column(Date, nullable=True)


class Despesa(DonoMixin, Base):
    __tablename__ = "despesas"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(200))
    valor: Mapped[Decimal] = mapped_column(Dinheiro)
    categoria: Mapped[str] = mapped_column(String(50), default="outros")
    frequencia: Mapped[str] = mapped_column(String(10), default="mensal")
    essencial: Mapped[bool] = mapped_column(Boolean, default=False)


class Divida(DonoMixin, Base):
    __tablename__ = "dividas"

    id: Mapped[int] = mapped_column(primary_key=True)
    credor: Mapped[str] = mapped_column(String(200))
    saldo: Mapped[Decimal] = mapped_column(Dinheiro)
    juros_mensal: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=Decimal("0"))
    parcela: Mapped[Decimal] = mapped_column(Dinheiro, default=Decimal("0"))
    vencimento: Mapped[date | None] = mapped_column(Date, nullable=True)


class Patrimonio(DonoMixin, Base):
    __tablename__ = "patrimonio"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))
    descricao: Mapped[str] = mapped_column(String(200))
    valor: Mapped[Decimal] = mapped_column(Dinheiro)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)


class Meta(DonoMixin, Base):
    __tablename__ = "metas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    valor_alvo: Mapped[Decimal] = mapped_column(Dinheiro)
    acumulado: Mapped[Decimal] = mapped_column(Dinheiro, default=Decimal("0"))
    prazo: Mapped[date | None] = mapped_column(Date, nullable=True)
    prioridade: Mapped[int] = mapped_column(default=3)


class Nota(DonoMixin, Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True)
    texto: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Pergunta(DonoMixin, Base):
    __tablename__ = "perguntas"

    id: Mapped[int] = mapped_column(primary_key=True)
    texto: Mapped[str] = mapped_column(Text)
    modo: Mapped[str] = mapped_column(String(12))
    resposta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultas: Mapped[list[dict]] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
