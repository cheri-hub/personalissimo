from datetime import date
from decimal import Decimal

import pytest

from app.agent.tools import financas
from app.models import Renda
from tests.factories import criar_usuario, seed_basico

HOJE = date(2026, 10, 4)


@pytest.fixture
def user(db):
    u = criar_usuario(db)
    seed_basico(db, u.id)
    return u


def test_fluxo_mensal(db, user):
    r = financas.obter_fluxo_de_caixa(db, user.id, hoje=HOJE)
    assert r == {
        "periodo": "mensal",
        "renda": 5000.0,
        "despesas": 2050.0,
        "despesas_essenciais": 2000.0,
        "parcelas_dividas": 300.0,
        "saldo": 2650.0,
    }


def test_fluxo_anual(db, user):
    assert financas.obter_fluxo_de_caixa(db, user.id, periodo="anual", hoje=HOJE)["saldo"] == 31800.0


def test_fluxo_periodo_invalido(db, user):
    with pytest.raises(ValueError):
        financas.obter_fluxo_de_caixa(db, user.id, periodo="semanal")


def test_fluxo_ignora_renda_encerrada_e_unica(db, user):
    db.add_all(
        [
            Renda(user_id=user.id, descricao="Freela antigo", valor=Decimal("1000"), frequencia="mensal", fim=date(2026, 1, 1)),
            Renda(user_id=user.id, descricao="Bônus", valor=Decimal("9000"), frequencia="unica"),
            Renda(user_id=user.id, descricao="Futuro", valor=Decimal("500"), frequencia="mensal", inicio=date(2027, 1, 1)),
        ]
    )
    db.commit()
    assert financas.obter_fluxo_de_caixa(db, user.id, hoje=HOJE)["renda"] == 5000.0


def test_fluxo_usuario_sem_dados(db):
    u = criar_usuario(db, "vazio@example.com")
    r = financas.obter_fluxo_de_caixa(db, u.id, hoje=HOJE)
    assert r["saldo"] == 0.0


def test_listar_dividas(db, user):
    r = financas.listar_dividas(db, user.id)
    assert r["total_saldo"] == 3000.0
    assert r["total_parcelas"] == 300.0
    assert r["dividas"][0]["credor"] == "Banco"
    assert r["dividas"][0]["juros_mensal"] == 2.5


def test_listar_metas(db, user):
    meta = financas.listar_metas(db, user.id)["metas"][0]
    assert meta["falta"] == 6000.0
    assert meta["progresso_pct"] == 40.0


def test_obter_patrimonio(db, user):
    r = financas.obter_patrimonio(db, user.id)
    assert r["total"] == 38000.0
    assert r["liquido"] == 8000.0


def test_simular_a_vista(db, user):
    r = financas.simular_compra(db, user.id, valor=6000, hoje=HOJE)
    assert r["parcela_mensal"] == 6000.0
    assert r["saldo_mensal_antes"] == 2650.0
    assert r["saldo_mensal_depois"] == 2650.0
    assert r["patrimonio_liquido_antes"] == 8000.0
    assert r["patrimonio_liquido_depois"] == 2000.0
    assert r["metas"] == [{"titulo": "Reserva", "meses_antes": 3, "meses_depois": 5}]
    assert "observacao" in r


def test_simular_parcelado_sem_juros(db, user):
    r = financas.simular_compra(db, user.id, valor=6000, parcelas=10, hoje=HOJE)
    assert r["parcela_mensal"] == 600.0
    assert r["custo_total"] == 6000.0
    assert r["saldo_mensal_depois"] == 2050.0
    assert r["patrimonio_liquido_depois"] == 8000.0
    assert r["metas"][0]["meses_depois"] == 3


def test_simular_parcelado_com_juros(db, user):
    r = financas.simular_compra(db, user.id, valor=6000, parcelas=10, juros_mensal_pct=2.0, hoje=HOJE)
    assert r["parcela_mensal"] == pytest.approx(667.96, abs=0.02)
    assert r["custo_total"] > 6000.0


def test_simular_meta_inalcancavel_com_saldo_negativo(db, user):
    r = financas.simular_compra(db, user.id, valor=30000, parcelas=10, hoje=HOJE)
    assert r["saldo_mensal_depois"] < 0
    assert r["metas"][0]["meses_depois"] is None


@pytest.mark.parametrize("kwargs", [{"valor": 0}, {"valor": -1}, {"valor": 10, "parcelas": 0}, {"valor": 10, "parcelas": 2.5}])
def test_simular_entradas_invalidas(db, user, kwargs):
    with pytest.raises(ValueError):
        financas.simular_compra(db, user.id, **kwargs)


def test_simular_rejeita_nao_finitos_e_bool(db, user):
    for args in (
        {"valor": float("nan")},
        {"valor": float("inf")},
        {"valor": 100, "parcelas": float("inf")},
        {"valor": 100, "parcelas": float("nan")},
        {"valor": 100, "juros_mensal_pct": float("nan")},
        {"valor": 100, "juros_mensal_pct": float("inf")},
        {"valor": True},
        {"valor": 100, "parcelas": True},
        {"valor": 100, "juros_mensal_pct": True},
    ):
        with pytest.raises(ValueError, match="números finitos"):
            financas.simular_compra(db, user.id, hoje=HOJE, **args)


def test_ferramentas_isoladas_entre_usuarios(db, user):
    outro = criar_usuario(db, email="outro@example.com")
    assert financas.obter_fluxo_de_caixa(db, outro.id, hoje=HOJE) == {
        "periodo": "mensal",
        "renda": 0.0,
        "despesas": 0.0,
        "despesas_essenciais": 0.0,
        "parcelas_dividas": 0.0,
        "saldo": 0.0,
    }
    assert financas.listar_dividas(db, outro.id) == {"dividas": [], "total_saldo": 0.0, "total_parcelas": 0.0}
    assert financas.listar_metas(db, outro.id) == {"metas": []}
    assert financas.obter_patrimonio(db, outro.id) == {"itens": [], "total": 0.0, "liquido": 0.0}
    r = financas.simular_compra(db, outro.id, valor=1000, hoje=HOJE)
    assert r["saldo_mensal_antes"] == 0.0
    assert r["patrimonio_liquido_antes"] == 0.0
    assert r["metas"] == []
