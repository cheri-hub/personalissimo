from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

ValorPositivo = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]
ValorNaoNegativo = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
Frequencia = Literal["mensal", "anual", "unica"]
Texto = Annotated[str, Field(min_length=1, max_length=200)]


class Saida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RendaIn(BaseModel):
    descricao: Texto
    valor: ValorPositivo
    frequencia: Frequencia = "mensal"
    inicio: date | None = None
    fim: date | None = None


class RendaOut(Saida, RendaIn):
    pass


class DespesaIn(BaseModel):
    descricao: Texto
    valor: ValorPositivo
    categoria: Annotated[str, Field(min_length=1, max_length=50)] = "outros"
    frequencia: Frequencia = "mensal"
    essencial: bool = False


class DespesaOut(Saida, DespesaIn):
    pass


class DividaIn(BaseModel):
    credor: Texto
    saldo: ValorNaoNegativo
    juros_mensal: Annotated[Decimal, Field(ge=0, le=100, max_digits=6, decimal_places=3)] = Decimal("0")
    parcela: ValorNaoNegativo = Decimal("0")
    vencimento: date | None = None


class DividaOut(Saida, DividaIn):
    pass


class PatrimonioIn(BaseModel):
    tipo: Literal["conta", "investimento", "bem"]
    descricao: Texto
    valor: ValorNaoNegativo
    data: date | None = None


class PatrimonioOut(Saida, PatrimonioIn):
    pass


class MetaIn(BaseModel):
    titulo: Texto
    valor_alvo: ValorPositivo
    acumulado: ValorNaoNegativo = Decimal("0")
    prazo: date | None = None
    prioridade: Annotated[int, Field(ge=1, le=5)] = 3


class MetaOut(Saida, MetaIn):
    pass


class NotaIn(BaseModel):
    texto: Annotated[str, Field(min_length=1, max_length=5000)]
    tags: list[Annotated[str, Field(min_length=1, max_length=30)]] = []


class NotaOut(Saida, NotaIn):
    pass
