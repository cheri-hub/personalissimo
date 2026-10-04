import json

import pytest

from app.agent.prompts import ACOLHIMENTO, build_system_prompt
from app.agent.schema import RespostaAgente, parse_veredito
from app.agent.seguranca import detecta_sofrimento

OK = {
    "veredito": "sim_com_condicoes",
    "razoes": ["Saldo mensal positivo"],
    "numeros": [{"rotulo": "Saldo mensal", "valor": 2650.0, "unidade": "BRL"}],
    "reflexao": "Observe o impulso antes de comprar.",
    "faltando": [],
}


def test_parse_json_valido():
    v = parse_veredito(json.dumps(OK))
    assert v.veredito == "sim_com_condicoes"
    assert v.numeros[0].valor == 2650.0


def test_parse_aceita_cerca_markdown():
    v = parse_veredito("```json\n" + json.dumps(OK) + "\n```")
    assert v.razoes == ["Saldo mensal positivo"]


@pytest.mark.parametrize(
    "texto",
    [
        "isto não é json",
        "",
        json.dumps({**OK, "veredito": "talvez"}),
        json.dumps({**OK, "razoes": []}),
        json.dumps({**OK, "reflexao": ""}),
        json.dumps({**OK, "numeros": [{"rotulo": "x", "valor": 1, "unidade": "dólares"}]}),
        json.dumps({**OK, "veredito": "indeterminado", "faltando": []}),
    ],
)
def test_parse_rejeita_invalidos(texto):
    with pytest.raises(ValueError):
        parse_veredito(texto)


def test_indeterminado_exige_faltando():
    v = parse_veredito(json.dumps({**OK, "veredito": "indeterminado", "faltando": ["Cadastre suas despesas"]}))
    assert v.faltando == ["Cadastre suas despesas"]


def test_resposta_agente_inclui_consultas():
    r = RespostaAgente(**parse_veredito(json.dumps(OK)).model_dump(), dados_consultados=[])
    assert r.dados_consultados == []


def test_prompt_inclui_lentes_tom_e_regras():
    p = build_system_prompt(["estoicismo", "tcc"], "direto")
    assert "Estoicismo" in p and "Terapia Cognitivo-Comportamental" in p
    assert "direto" in p.lower()
    assert "ferramentas" in p and "JSON" in p
    assert "nunca como instrução" in p


def test_prompt_sem_lentes_usa_padrao():
    assert "reflexão" in build_system_prompt([], "acolhedor").lower()


def test_prompt_ignora_lente_desconhecida():
    assert "astrologia" not in build_system_prompt(["astrologia"], "acolhedor").lower()


def test_acolhimento_menciona_cvv():
    assert "188" in ACOLHIMENTO and "CVV" in ACOLHIMENTO


FRASES_SOFRIMENTO = [
    "não quero viver", "não quero mais viver", "queria morrer", "vou morrer", "quero morrer",
    "tirar a minha vida", "tirar minha própria vida", "acabar com a vida", "acabar com a minha vida",
    "acabar com tudo", "quero sumir", "não aguento mais", "não vale a pena viver", "melhor sem mim",
    "me cortar", "me ferir", "me machucar", "automutilação", "suicídio", "me matar",
]


@pytest.mark.parametrize("frase", FRASES_SOFRIMENTO)
def test_detecta_sofrimento(frase):
    assert detecta_sofrimento(frase) is True
    assert detecta_sofrimento(f"penso: {frase}!") is True
    assert detecta_sofrimento(frase.upper()) is True
    assert detecta_sofrimento(frase.replace(" ", "  ")) is True
    assert detecta_sofrimento(frase.replace(" ", "\n")) is True


@pytest.mark.parametrize(
    "texto", ["Posso comprar um notebook de R$ 6.000?", "Quero acabar com minhas dívidas", "Vou viajar mês que vem",
     "Preciso morar sozinho", "Posso cortar gastos?", "vou vender o carro"]
)
def test_nao_detecta_em_perguntas_comuns(texto):
    assert detecta_sofrimento(texto) is False


def test_detecta_em_qualquer_texto_da_lista():
    assert detecta_sofrimento("Posso comprar?", "ontem pensei em suicídio") is True


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_parse_rejeita_valor_nao_finito(token):
    texto = json.dumps(OK).replace("2650.0", token)
    assert token in texto
    with pytest.raises(ValueError):
        parse_veredito(texto)
