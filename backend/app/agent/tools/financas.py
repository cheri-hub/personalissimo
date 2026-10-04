import math
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Despesa, Divida, Meta, Patrimonio, Renda

LIQUIDOS = ("conta", "investimento")
OBSERVACAO = (
    "Estimativa simplificada: considera o saldo mensal reduzido pela parcela "
    "durante todo o período e não projeta juros sobre as metas."
)


def _f(valor: Decimal) -> float:
    return round(float(valor), 2)


def _data(d: date | None) -> str | None:
    return d.isoformat() if d else None


def _mensal(valor: Decimal, frequencia: str) -> Decimal:
    if frequencia == "mensal":
        return valor
    if frequencia == "anual":
        return valor / Decimal(12)
    return Decimal(0)


def _renda_ativa(renda: Renda, hoje: date) -> bool:
    return (renda.inicio is None or renda.inicio <= hoje) and (renda.fim is None or renda.fim >= hoje)


def _componentes_fluxo(db: Session, user_id: int, hoje: date) -> dict[str, Decimal]:
    rendas = db.scalars(select(Renda).where(Renda.user_id == user_id)).all()
    despesas = db.scalars(select(Despesa).where(Despesa.user_id == user_id)).all()
    dividas = db.scalars(select(Divida).where(Divida.user_id == user_id)).all()
    renda = sum((_mensal(r.valor, r.frequencia) for r in rendas if _renda_ativa(r, hoje)), Decimal(0))
    gastos = sum((_mensal(d.valor, d.frequencia) for d in despesas), Decimal(0))
    essenciais = sum((_mensal(d.valor, d.frequencia) for d in despesas if d.essencial), Decimal(0))
    parcelas = sum((d.parcela for d in dividas), Decimal(0))
    return {
        "renda": renda,
        "despesas": gastos,
        "despesas_essenciais": essenciais,
        "parcelas_dividas": parcelas,
        "saldo": renda - gastos - parcelas,
    }


def obter_fluxo_de_caixa(db: Session, user_id: int, periodo: str = "mensal", hoje: date | None = None) -> dict:
    if periodo not in ("mensal", "anual"):
        raise ValueError("periodo deve ser 'mensal' ou 'anual'")
    fator = Decimal(12 if periodo == "anual" else 1)
    componentes = _componentes_fluxo(db, user_id, hoje or date.today())
    return {"periodo": periodo, **{k: _f(v * fator) for k, v in componentes.items()}}


def listar_dividas(db: Session, user_id: int) -> dict:
    dividas = db.scalars(select(Divida).where(Divida.user_id == user_id).order_by(Divida.id)).all()
    return {
        "dividas": [
            {
                "credor": d.credor,
                "saldo": _f(d.saldo),
                "juros_mensal": float(d.juros_mensal),
                "parcela": _f(d.parcela),
                "vencimento": _data(d.vencimento),
            }
            for d in dividas
        ],
        "total_saldo": _f(sum((d.saldo for d in dividas), Decimal(0))),
        "total_parcelas": _f(sum((d.parcela for d in dividas), Decimal(0))),
    }


def listar_metas(db: Session, user_id: int) -> dict:
    metas = db.scalars(select(Meta).where(Meta.user_id == user_id).order_by(Meta.prioridade, Meta.id)).all()
    return {
        "metas": [
            {
                "titulo": m.titulo,
                "valor_alvo": _f(m.valor_alvo),
                "acumulado": _f(m.acumulado),
                "falta": _f(max(m.valor_alvo - m.acumulado, Decimal(0))),
                "progresso_pct": round(float(m.acumulado / m.valor_alvo * 100), 1),
                "prazo": _data(m.prazo),
                "prioridade": m.prioridade,
            }
            for m in metas
        ]
    }


def _total_e_liquido(db: Session, user_id: int) -> tuple[Decimal, Decimal, list[Patrimonio]]:
    itens = db.scalars(select(Patrimonio).where(Patrimonio.user_id == user_id).order_by(Patrimonio.id)).all()
    total = sum((i.valor for i in itens), Decimal(0))
    liquido = sum((i.valor for i in itens if i.tipo in LIQUIDOS), Decimal(0))
    return total, liquido, itens


def obter_patrimonio(db: Session, user_id: int) -> dict:
    total, liquido, itens = _total_e_liquido(db, user_id)
    return {
        "itens": [{"tipo": i.tipo, "descricao": i.descricao, "valor": _f(i.valor)} for i in itens],
        "total": _f(total),
        "liquido": _f(liquido),
    }


def _parcela(valor: Decimal, parcelas: int, juros_pct: Decimal) -> Decimal:
    if parcelas == 1 or juros_pct == 0:
        return valor / parcelas
    i = juros_pct / 100
    return valor * i / (1 - (1 + i) ** -parcelas)


def _meses(falta: Decimal, saldo: Decimal) -> int | None:
    if falta <= 0:
        return 0
    if saldo <= 0:
        return None
    return math.ceil(falta / saldo)


def simular_compra(
    db: Session,
    user_id: int,
    valor: float,
    parcelas: float = 1,
    juros_mensal_pct: float = 0.0,
    hoje: date | None = None,
) -> dict:
    if valor <= 0:
        raise ValueError("valor deve ser maior que zero")
    if parcelas < 1 or parcelas != int(parcelas):
        raise ValueError("parcelas deve ser um inteiro >= 1")
    if juros_mensal_pct < 0:
        raise ValueError("juros_mensal_pct não pode ser negativo")
    n = int(parcelas)
    preco = Decimal(str(valor))
    parcela = _parcela(preco, n, Decimal(str(juros_mensal_pct)))
    saldo = _componentes_fluxo(db, user_id, hoje or date.today())["saldo"]
    _, liquido, _ = _total_e_liquido(db, user_id)
    a_vista = n == 1
    saldo_depois = saldo if a_vista else saldo - parcela
    liquido_depois = liquido - preco if a_vista else liquido
    extra = preco if a_vista else Decimal(0)
    metas = db.scalars(select(Meta).where(Meta.user_id == user_id).order_by(Meta.prioridade, Meta.id)).all()
    impacto = []
    for m in metas:
        falta = max(m.valor_alvo - m.acumulado, Decimal(0))
        impacto.append(
            {"titulo": m.titulo, "meses_antes": _meses(falta, saldo), "meses_depois": _meses(falta + extra, saldo_depois)}
        )
    return {
        "valor": _f(preco),
        "parcelas": n,
        "parcela_mensal": _f(parcela),
        "custo_total": _f(parcela * n),
        "saldo_mensal_antes": _f(saldo),
        "saldo_mensal_depois": _f(saldo_depois),
        "patrimonio_liquido_antes": _f(liquido),
        "patrimonio_liquido_depois": _f(liquido_depois),
        "metas": impacto,
        "observacao": OBSERVACAO,
    }
