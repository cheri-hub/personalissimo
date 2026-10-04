import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class Numero(BaseModel):
    rotulo: str
    valor: float
    unidade: Literal["BRL", "meses", "%", "parcelas"]


class VereditoLLM(BaseModel):
    veredito: Literal["sim", "nao", "sim_com_condicoes", "indeterminado"]
    razoes: Annotated[list[str], Field(min_length=1)]
    numeros: list[Numero] = []
    reflexao: Annotated[str, Field(min_length=1)]
    faltando: list[str] = []

    @model_validator(mode="after")
    def _indeterminado_exige_faltando(self) -> "VereditoLLM":
        if self.veredito == "indeterminado" and not self.faltando:
            raise ValueError("veredito indeterminado exige a lista 'faltando'")
        return self


class Consulta(BaseModel):
    ferramenta: str
    argumentos: dict


class RespostaAgente(VereditoLLM):
    dados_consultados: list[Consulta]


_CERCA = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def parse_veredito(texto: str) -> VereditoLLM:
    limpo = texto.strip()
    cerca = _CERCA.match(limpo)
    if cerca:
        limpo = cerca.group(1)
    return VereditoLLM.model_validate(json.loads(limpo))
