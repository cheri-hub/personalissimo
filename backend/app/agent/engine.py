from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.prompts import ACOLHIMENTO, build_system_prompt
from app.agent.schema import Consulta, RespostaAgente, parse_veredito
from app.agent.seguranca import detecta_sofrimento
from app.agent.tools.registry import TOOL_SPECS, build_executor
from app.agent.types import LLMProvider, ToolResult, Turn
from app.models import Nota, Pergunta, Usuario

MAX_RODADAS = 6
NOTAS_VERIFICADAS = 3
NOTAS_JANELA_DIAS = 7


class MotorErro(Exception):
    pass


def _notas_recentes(db: Session, user_id: int) -> list[str]:
    limite = datetime.now(timezone.utc) - timedelta(days=NOTAS_JANELA_DIAS)
    consulta = (
        select(Nota.texto)
        .where(Nota.user_id == user_id, Nota.criado_em >= limite)
        .order_by(Nota.criado_em.desc(), Nota.id.desc())
        .limit(NOTAS_VERIFICADAS)
    )
    return list(db.scalars(consulta))


def _rodar_agente(db: Session, user: Usuario, pergunta: str, provider: LLMProvider) -> RespostaAgente:
    system = build_system_prompt(user.lentes, user.tom)
    executar = build_executor(db, user.id)
    historico = [Turn(role="user", text=pergunta)]
    consultas: list[Consulta] = []
    ja_corrigiu = False

    for _ in range(MAX_RODADAS):
        resposta = provider.generate(system, historico, TOOL_SPECS)

        if resposta.tool_calls:
            resultados = tuple(ToolResult(name=c.name, output=executar(c.name, c.args)) for c in resposta.tool_calls)
            consultas = [*consultas, *(Consulta(ferramenta=c.name, argumentos=c.args) for c in resposta.tool_calls)]
            historico = [
                *historico,
                Turn(role="model", tool_calls=resposta.tool_calls, raw=resposta.raw),
                Turn(role="tool", tool_results=resultados),
            ]
            continue

        try:
            veredito = parse_veredito(resposta.text or "")
        except ValueError as exc:
            if ja_corrigiu:
                raise MotorErro("A resposta do modelo não pôde ser validada") from exc
            ja_corrigiu = True
            historico = [
                *historico,
                Turn(role="model", text=resposta.text or "", raw=resposta.raw),
                Turn(
                    role="user",
                    text=f"Resposta inválida ({exc}). Responda novamente apenas com o JSON no formato pedido.",
                ),
            ]
            continue

        return RespostaAgente(**veredito.model_dump(), dados_consultados=consultas)

    raise MotorErro("Limite de rodadas do agente atingido")


def _salvar(db: Session, user_id: int, texto: str, resposta: RespostaAgente | None, mensagem: str | None) -> Pergunta:
    registro = Pergunta(
        user_id=user_id,
        texto=texto,
        modo="veredito" if resposta else "acolhimento",
        resposta=resposta.model_dump(mode="json") if resposta else None,
        mensagem=mensagem,
        consultas=[c.model_dump(mode="json") for c in resposta.dados_consultados] if resposta else [],
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def responder(db: Session, user: Usuario, pergunta: str, provider: LLMProvider) -> Pergunta:
    if detecta_sofrimento(pergunta, *_notas_recentes(db, user.id)):
        return _salvar(db, user.id, pergunta, None, ACOLHIMENTO)
    return _salvar(db, user.id, pergunta, _rodar_agente(db, user, pergunta, provider), None)
