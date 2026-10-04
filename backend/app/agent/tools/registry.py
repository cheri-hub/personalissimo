from collections.abc import Callable
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.agent.tools import financas, notas
from app.agent.types import ToolSpec

_SEM_PARAMETROS = {"type": "object", "properties": {}}

TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "obter_fluxo_de_caixa",
        "Renda, despesas, despesas essenciais, parcelas de dívidas e saldo (renda - despesas - parcelas) do usuário. "
        "As despesas NÃO incluem as parcelas das dívidas cadastradas.",
        {"type": "object", "properties": {"periodo": {"type": "string", "enum": ["mensal", "anual"]}}},
    ),
    ToolSpec("listar_dividas", "Lista as dívidas do usuário com saldo, juros e parcela.", _SEM_PARAMETROS),
    ToolSpec("listar_metas", "Lista as metas do usuário com valor-alvo, acumulado, falta e progresso.", _SEM_PARAMETROS),
    ToolSpec("obter_patrimonio", "Patrimônio do usuário: itens, total e total líquido (contas e investimentos).", _SEM_PARAMETROS),
    ToolSpec(
        "simular_compra",
        "Simula uma compra: parcela, custo total, saldo mensal e patrimônio líquido antes/depois, "
        "e meses para atingir cada meta antes/depois. Use SEMPRE esta ferramenta para números de compras.",
        {
            "type": "object",
            "properties": {
                "valor": {"type": "number", "description": "Preço total em reais"},
                "parcelas": {"type": "integer", "description": "Número de parcelas (1 = à vista)"},
                "juros_mensal_pct": {"type": "number", "description": "Juros mensais em % (0 se não houver)"},
            },
            "required": ["valor"],
        },
    ),
    ToolSpec(
        "buscar_notas",
        "Busca nas notas pessoais do usuário por um termo (valores, rotina, contexto).",
        {"type": "object", "properties": {"termo": {"type": "string"}}, "required": ["termo"]},
    ),
    ToolSpec("obter_notas_relevantes", "Retorna as notas pessoais mais recentes do usuário.", _SEM_PARAMETROS),
)


def build_executor(db: Session, user_id: int, hoje: date | None = None) -> Callable[[str, dict[str, Any]], dict]:
    hoje = hoje or date.today()
    funcoes: dict[str, Callable[..., dict]] = {
        "obter_fluxo_de_caixa": lambda **kw: financas.obter_fluxo_de_caixa(db, user_id, hoje=hoje, **kw),
        "listar_dividas": lambda **kw: financas.listar_dividas(db, user_id, **kw),
        "listar_metas": lambda **kw: financas.listar_metas(db, user_id, **kw),
        "obter_patrimonio": lambda **kw: financas.obter_patrimonio(db, user_id, **kw),
        "simular_compra": lambda **kw: financas.simular_compra(db, user_id, hoje=hoje, **kw),
        "buscar_notas": lambda **kw: notas.buscar_notas(db, user_id, **kw),
        "obter_notas_relevantes": lambda **kw: notas.obter_notas_relevantes(db, user_id, **kw),
    }

    def executar(nome: str, args: dict[str, Any]) -> dict:
        funcao = funcoes.get(nome)
        if funcao is None:
            return {"erro": f"ferramenta desconhecida: {nome}"}
        try:
            return funcao(**(args or {}))
        except (TypeError, ValueError) as exc:
            return {"erro": str(exc)}

    return executar
