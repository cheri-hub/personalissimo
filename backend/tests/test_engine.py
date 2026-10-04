import itertools
import json

import pytest

from app.agent.engine import MAX_RODADAS, MotorErro, responder
from app.agent.types import LLMResponse, ToolCall
from app.models import Nota, Pergunta
from tests.fakes import FakeProvider, texto
from tests.factories import criar_usuario, seed_basico

VEREDITO_OK = json.dumps(
    {
        "veredito": "sim_com_condicoes",
        "razoes": ["Saldo mensal positivo"],
        "numeros": [{"rotulo": "Saldo mensal", "valor": 2650.0, "unidade": "BRL"}],
        "reflexao": "Observe o impulso antes de comprar.",
        "faltando": [],
    }
)


@pytest.fixture
def user(db):
    u = criar_usuario(db)
    seed_basico(db, u.id)
    return u


def test_resposta_direta(db, user):
    fake = FakeProvider([texto(VEREDITO_OK)])
    p = responder(db, user, "Posso comprar um notebook?", fake)
    assert p.modo == "veredito"
    assert p.resposta["veredito"] == "sim_com_condicoes"
    assert p.resposta["dados_consultados"] == []
    assert p.consultas == []
    assert db.get(Pergunta, p.id).texto == "Posso comprar um notebook?"


def test_loop_com_ferramenta_registra_consultas(db, user):
    chamada = ToolCall(name="listar_metas", args={})
    fake = FakeProvider([LLMResponse(tool_calls=(chamada,), raw="RAW"), texto(VEREDITO_OK)])
    p = responder(db, user, "Posso gastar?", fake)
    assert p.resposta["dados_consultados"] == [{"ferramenta": "listar_metas", "argumentos": {}}]
    assert p.consultas == [{"ferramenta": "listar_metas", "argumentos": {}}]
    _, historico = fake.chamadas[1]
    assert [t.role for t in historico] == ["user", "model", "tool"]
    assert historico[1].raw == "RAW"
    assert historico[2].tool_results[0].output["metas"][0]["titulo"] == "Reserva"


def test_ferramenta_com_erro_volta_ao_modelo(db, user):
    chamada = ToolCall(name="simular_compra", args={"valor": -1})
    fake = FakeProvider([LLMResponse(tool_calls=(chamada,)), texto(VEREDITO_OK)])
    responder(db, user, "Posso gastar?", fake)
    assert "erro" in fake.chamadas[1][1][2].tool_results[0].output


def test_json_invalido_uma_correcao(db, user):
    fake = FakeProvider([texto("não é json"), texto(VEREDITO_OK)])
    p = responder(db, user, "Posso?", fake)
    assert p.modo == "veredito"
    assert len(fake.chamadas) == 2
    assert "inválida" in fake.chamadas[1][1][-1].text


def test_json_invalido_duas_vezes_levanta_erro(db, user):
    fake = FakeProvider([texto("lixo"), texto("lixo de novo")])
    with pytest.raises(MotorErro):
        responder(db, user, "Posso?", fake)
    assert db.query(Pergunta).count() == 0


def test_limite_de_rodadas(db, user):
    chamada = LLMResponse(tool_calls=(ToolCall(name="listar_metas", args={}),))
    fake = FakeProvider(itertools.repeat(chamada))
    with pytest.raises(MotorErro):
        responder(db, user, "Posso?", fake)
    assert len(fake.chamadas) == MAX_RODADAS


def test_sofrimento_na_pergunta_ativa_acolhimento_sem_chamar_llm(db, user):
    fake = FakeProvider([])
    p = responder(db, user, "não quero mais viver", fake)
    assert fake.chamadas == []
    assert p.modo == "acolhimento"
    assert p.resposta is None
    assert "188" in p.mensagem


def test_sofrimento_em_nota_recente_ativa_acolhimento(db, user):
    db.add(Nota(user_id=user.id, texto="ando pensando em suicídio", tags=[]))
    db.commit()
    fake = FakeProvider([])
    p = responder(db, user, "Posso comprar um notebook?", fake)
    assert p.modo == "acolhimento"
    assert fake.chamadas == []


def test_prompt_usa_lentes_e_tom_do_usuario(db, user):
    user.lentes = ["estoicismo"]
    user.tom = "direto"
    db.commit()
    fake = FakeProvider([texto(VEREDITO_OK)])
    responder(db, user, "Posso?", fake)
    system, _ = fake.chamadas[0]
    assert "Estoicismo" in system and "direto" in system.lower()


def test_nota_antiga_de_sofrimento_nao_ativa_acolhimento(db, user):
    from datetime import datetime, timedelta, timezone

    antiga = datetime.now(timezone.utc) - timedelta(days=8)
    db.add(Nota(user_id=user.id, texto="ando pensando em suicídio", tags=[], criado_em=antiga))
    db.commit()
    p = responder(db, user, "Posso comprar um notebook?", FakeProvider([texto(VEREDITO_OK)]))
    assert p.modo == "veredito"


def test_nota_de_ontem_com_sofrimento_ativa_acolhimento(db, user):
    from datetime import datetime, timedelta, timezone

    ontem = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(Nota(user_id=user.id, texto="ando pensando em suicídio", tags=[], criado_em=ontem))
    db.commit()
    p = responder(db, user, "Posso comprar um notebook?", FakeProvider([]))
    assert p.modo == "acolhimento"
