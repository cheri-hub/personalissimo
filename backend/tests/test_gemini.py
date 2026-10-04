from types import SimpleNamespace

import pytest
from google.genai import errors

from app.agent.gemini import GeminiProvider, _declarar, _para_contents
from app.agent.tools.registry import TOOL_SPECS
from app.agent.types import ProviderError, ProviderQuotaError, ToolCall, ToolResult, Turn


def _resposta(text=None, calls=(), content="RAW"):
    return SimpleNamespace(
        text=text,
        function_calls=[SimpleNamespace(name=n, args=a, id=None) for n, a in calls] or None,
        candidates=[SimpleNamespace(content=content)],
    )


class _Models:
    def __init__(self, passos):
        self._passos = list(passos)
        self.chamadas = []

    def generate_content(self, model, contents, config):
        self.chamadas.append((model, contents, config))
        passo = self._passos.pop(0)
        if isinstance(passo, Exception):
            raise passo
        return passo


def _provider(passos, dormidas=None):
    cliente = SimpleNamespace(models=_Models(passos))
    dormidas = dormidas if dormidas is not None else []
    return GeminiProvider("k", "modelo-x", client=cliente, sleep=dormidas.append), cliente, dormidas


def _erro(code):
    return errors.APIError(code, {"error": {"message": "x", "status": "X"}})


def test_texto_simples():
    p, cliente, _ = _provider([_resposta(text='{"ok": true}')])
    r = p.generate("sys", [Turn(role="user", text="oi")], TOOL_SPECS)
    assert r.text == '{"ok": true}' and r.tool_calls == ()
    assert cliente.models.chamadas[0][0] == "modelo-x"


def test_chamada_de_ferramenta_preserva_raw():
    p, _, _ = _provider([_resposta(calls=[("simular_compra", {"valor": 10})], content="CONTEUDO")])
    r = p.generate("sys", [Turn(role="user", text="oi")], TOOL_SPECS)
    assert r.tool_calls == (ToolCall(name="simular_compra", args={"valor": 10}),)
    assert r.text is None and r.raw == "CONTEUDO"


def test_429_tenta_de_novo_e_funciona():
    p, _, dormidas = _provider([_erro(429), _resposta(text="ok")])
    assert p.generate("s", [Turn(role="user", text="oi")], []).text == "ok"
    assert dormidas == [2.0]


def test_429_duas_vezes_levanta_quota():
    p, _, _ = _provider([_erro(429), _erro(429)])
    with pytest.raises(ProviderQuotaError):
        p.generate("s", [Turn(role="user", text="oi")], [])


def test_outro_erro_levanta_provider_error():
    p, _, dormidas = _provider([_erro(500)])
    with pytest.raises(ProviderError):
        p.generate("s", [Turn(role="user", text="oi")], [])
    assert dormidas == []


def test_erro_de_rede_levanta_provider_error():
    p, _, dormidas = _provider([TimeoutError("segredo")])
    with pytest.raises(ProviderError, match="Falha de comunicação com o Gemini") as info:
        p.generate("s", [Turn(role="user", text="oi")], [])
    assert isinstance(info.value.__cause__, TimeoutError)
    assert dormidas == []


def test_para_contents_traduz_turnos():
    historico = [
        Turn(role="user", text="pergunta"),
        Turn(role="model", tool_calls=(ToolCall(name="listar_metas", args={}),), raw="RAW-MODELO"),
        Turn(role="tool", tool_results=(ToolResult(name="listar_metas", output={"metas": []}),)),
        Turn(role="model", text="texto do modelo"),
    ]
    contents = _para_contents(historico)
    assert contents[0].role == "user" and contents[0].parts[0].text == "pergunta"
    assert contents[1] == "RAW-MODELO"
    assert contents[2].role == "user"
    assert contents[2].parts[0].function_response.name == "listar_metas"
    assert contents[2].parts[0].function_response.response == {"metas": []}
    assert contents[3].role == "model" and contents[3].parts[0].text == "texto do modelo"


def test_declarar_cobre_todas_as_ferramentas():
    declaracoes = _declarar(TOOL_SPECS).function_declarations
    assert {d.name for d in declaracoes} == {s.name for s in TOOL_SPECS}
