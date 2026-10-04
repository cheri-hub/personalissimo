import json

import pytest

from app.agent.types import ProviderQuotaError
from app.models import Usuario
from app.routers.perguntas import get_provider
from tests.factories import seed_basico
from tests.fakes import FakeProvider, texto

VEREDITO_OK = json.dumps(
    {
        "veredito": "sim",
        "razoes": ["Cabe no orçamento"],
        "numeros": [],
        "reflexao": "Pergunte-se o que você realmente quer.",
        "faltando": [],
    }
)


def _usar(client, provider):
    client.app.dependency_overrides[get_provider] = lambda: provider


class _Quebrado:
    def __init__(self, erro):
        self._erro = erro

    def generate(self, *args, **kwargs):
        raise self._erro


def test_perguntar_retorna_veredito_e_historico(client, auth):
    _usar(client, FakeProvider([texto(VEREDITO_OK)]))
    r = client.post("/perguntas", headers=auth, json={"texto": "Posso comprar um notebook?"})
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["modo"] == "veredito"
    assert corpo["resposta"]["veredito"] == "sim"
    assert corpo["mensagem"] is None
    historico = client.get("/perguntas", headers=auth).json()
    assert [p["id"] for p in historico] == [corpo["id"]]


def test_acolhimento_via_api(client, auth):
    _usar(client, FakeProvider([]))
    r = client.post("/perguntas", headers=auth, json={"texto": "não quero mais viver"})
    assert r.status_code == 201
    assert r.json()["modo"] == "acolhimento"
    assert "188" in r.json()["mensagem"]


def test_requer_autenticacao(client):
    assert client.post("/perguntas", json={"texto": "Posso?"}).status_code == 401
    assert client.get("/perguntas").status_code == 401


def test_texto_curto_422(client, auth):
    _usar(client, FakeProvider([]))
    assert client.post("/perguntas", headers=auth, json={"texto": "a"}).status_code == 422


def test_limite_diario_429(client, auth, engine):
    from sqlalchemy.orm import Session

    with Session(engine) as s:
        u = s.query(Usuario).one()
        u.limite_diario = 1
        s.commit()
    _usar(client, FakeProvider([texto(VEREDITO_OK), texto(VEREDITO_OK)]))
    assert client.post("/perguntas", headers=auth, json={"texto": "Primeira?"}).status_code == 201
    assert client.post("/perguntas", headers=auth, json={"texto": "Segunda?"}).status_code == 429


def test_cota_do_provedor_503(client, auth):
    _usar(client, _Quebrado(ProviderQuotaError("x")))
    r = client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"})
    assert r.status_code == 503
    assert "tente novamente" in r.json()["detail"].lower()


def test_resposta_invalida_502_e_nao_consome_limite(client, auth):
    _usar(client, FakeProvider([texto("lixo"), texto("lixo")]))
    assert client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"}).status_code == 502
    assert client.get("/perguntas", headers=auth).json() == []


def test_sem_chave_do_gemini_503(client, auth, monkeypatch):
    from app.config import Settings

    sem_chave = Settings(
        _env_file=None, database_url="sqlite://", jwt_secret="x" * 40, gemini_api_key=None
    )
    monkeypatch.setattr("app.routers.perguntas.get_settings", lambda: sem_chave)
    r = client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"})
    assert r.status_code == 503


def test_historico_isolado_entre_usuarios(client, auth):
    from tests.helpers import registrar_e_logar

    _usar(client, FakeProvider([texto(VEREDITO_OK)]))
    client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"})
    outro = registrar_e_logar(client, email="b@example.com")
    assert client.get("/perguntas", headers=outro).json() == []


def test_painel(client, auth, engine):
    from sqlalchemy.orm import Session

    with Session(engine) as s:
        seed_basico(s, s.query(Usuario).one().id)
    r = client.get("/painel", headers=auth)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["fluxo"]["saldo"] == 2650.0
    assert corpo["patrimonio"]["liquido"] == 8000.0
    assert corpo["metas"]["metas"][0]["titulo"] == "Reserva"


def test_painel_requer_autenticacao(client):
    assert client.get("/painel").status_code == 401


def test_perguntas_rate_limit_429(client, auth):
    _usar(client, FakeProvider([texto(VEREDITO_OK)] * 6))
    for _ in range(6):
        assert client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"}).status_code == 201
    r = client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"})
    assert r.status_code == 429
    assert r.json()["detail"] == "Muitas perguntas seguidas. Aguarde um minuto."


def test_perguntas_rate_limit_conta_tentativas_com_falha(client, auth):
    _usar(client, _Quebrado(ProviderQuotaError("x")))
    for _ in range(6):
        assert client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"}).status_code == 503
    assert client.post("/perguntas", headers=auth, json={"texto": "Posso comprar?"}).status_code == 429


def test_falha_do_provedor_loga_tipo_e_mensagem(client, auth, caplog):
    import logging

    _usar(client, _Quebrado(ProviderQuotaError("cota-esgotada")))
    with caplog.at_level(logging.WARNING, logger="app.routers.perguntas"):
        client.post("/perguntas", headers=auth, json={"texto": "texto-secreto-da-pergunta"})
    assert "ProviderQuotaError" in caplog.text
    assert "cota-esgotada" in caplog.text
    assert "texto-secreto-da-pergunta" not in caplog.text
