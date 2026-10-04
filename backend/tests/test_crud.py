import pytest

from tests.helpers import registrar_e_logar

PAYLOADS = {
    "/rendas": {"descricao": "Salário", "valor": "5000.00", "frequencia": "mensal"},
    "/despesas": {"descricao": "Aluguel", "valor": "2000.00", "categoria": "moradia", "essencial": True},
    "/dividas": {"credor": "Banco", "saldo": "3000.00", "juros_mensal": "2.5", "parcela": "300.00"},
    "/patrimonio": {"tipo": "conta", "descricao": "Conta corrente", "valor": "8000.00"},
    "/metas": {"titulo": "Reserva", "valor_alvo": "10000.00", "acumulado": "4000.00", "prioridade": 1},
    "/notas": {"texto": "Valorizo segurança.", "tags": ["valores"]},
}
CAMPO_EDITAVEL = {
    "/rendas": ("descricao", "Salário líquido"),
    "/despesas": ("descricao", "Aluguel + condomínio"),
    "/dividas": ("credor", "Outro banco"),
    "/patrimonio": ("descricao", "Poupança"),
    "/metas": ("titulo", "Reserva de emergência"),
    "/notas": ("texto", "Valorizo segurança e liberdade."),
}


@pytest.mark.parametrize("path", PAYLOADS)
def test_crud_completo(client, auth, path):
    criado = client.post(path, headers=auth, json=PAYLOADS[path])
    assert criado.status_code == 201, criado.text
    item_id = criado.json()["id"]

    assert [i["id"] for i in client.get(path, headers=auth).json()] == [item_id]
    assert client.get(f"{path}/{item_id}", headers=auth).status_code == 200

    campo, novo = CAMPO_EDITAVEL[path]
    corpo = {**PAYLOADS[path], campo: novo}
    atualizado = client.put(f"{path}/{item_id}", headers=auth, json=corpo)
    assert atualizado.status_code == 200
    assert atualizado.json()[campo] == novo

    assert client.delete(f"{path}/{item_id}", headers=auth).status_code == 204
    assert client.get(f"{path}/{item_id}", headers=auth).status_code == 404


@pytest.mark.parametrize("path", PAYLOADS)
def test_requer_autenticacao(client, path):
    assert client.get(path).status_code == 401
    assert client.post(path, json=PAYLOADS[path]).status_code == 401


@pytest.mark.parametrize("path", PAYLOADS)
def test_isolamento_entre_usuarios(client, auth, path):
    item_id = client.post(path, headers=auth, json=PAYLOADS[path]).json()["id"]
    outro = registrar_e_logar(client, email="b@example.com")

    assert client.get(path, headers=outro).json() == []
    assert client.get(f"{path}/{item_id}", headers=outro).status_code == 404
    campo, novo = CAMPO_EDITAVEL[path]
    assert client.put(f"{path}/{item_id}", headers=outro, json={**PAYLOADS[path], campo: novo}).status_code == 404
    assert client.delete(f"{path}/{item_id}", headers=outro).status_code == 404
    assert client.get(f"{path}/{item_id}", headers=auth).status_code == 200


def test_validacao_valor_negativo_422(client, auth):
    r = client.post("/rendas", headers=auth, json={"descricao": "x", "valor": "-5"})
    assert r.status_code == 422


def test_frequencia_invalida_422(client, auth):
    r = client.post("/despesas", headers=auth, json={"descricao": "x", "valor": "5", "frequencia": "semanal"})
    assert r.status_code == 422
