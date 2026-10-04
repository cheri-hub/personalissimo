def test_registro_e_login(client):
    r = client.post("/auth/registro", json={"email": "A@Example.com", "senha": "senha-segura-1"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@example.com"
    r = client.post("/auth/login", json={"email": "a@example.com", "senha": "senha-segura-1"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_registro_duplicado_409(client):
    body = {"email": "a@example.com", "senha": "senha-segura-1"}
    assert client.post("/auth/registro", json=body).status_code == 201
    assert client.post("/auth/registro", json=body).status_code == 409


def test_registro_senha_curta_422(client):
    r = client.post("/auth/registro", json={"email": "a@example.com", "senha": "curta"})
    assert r.status_code == 422


def test_login_invalido_401(client):
    client.post("/auth/registro", json={"email": "a@example.com", "senha": "senha-segura-1"})
    r = client.post("/auth/login", json={"email": "a@example.com", "senha": "errada-errada"})
    assert r.status_code == 401
    r = client.post("/auth/login", json={"email": "x@example.com", "senha": "qualquer-coisa"})
    assert r.status_code == 401


def test_login_rate_limit_429(client):
    for _ in range(5):
        client.post("/auth/login", json={"email": "a@example.com", "senha": "errada-errada"})
    r = client.post("/auth/login", json={"email": "a@example.com", "senha": "errada-errada"})
    assert r.status_code == 429


def test_me_requer_token(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_me_e_config(client, auth):
    r = client.get("/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["lentes"] == []
    r = client.patch("/me/config", headers=auth, json={"lentes": ["estoicismo", "tcc"], "tom": "direto"})
    assert r.status_code == 200
    assert r.json()["lentes"] == ["estoicismo", "tcc"]
    assert r.json()["tom"] == "direto"


def test_config_lente_invalida_422(client, auth):
    r = client.patch("/me/config", headers=auth, json={"lentes": ["astrologia"]})
    assert r.status_code == 422


def test_lockout_de_um_cliente_nao_afeta_outro_ip(client):
    from fastapi.testclient import TestClient

    for _ in range(6):
        client.post("/auth/login", json={"email": "a@example.com", "senha": "errada-errada"})
    outro = TestClient(client.app, client=("9.9.9.9", 5000))
    r = outro.post("/auth/login", json={"email": "a@example.com", "senha": "errada-errada"})
    assert r.status_code == 401


def test_login_rate_limit_por_ip_429(client):
    for i in range(20):
        r = client.post("/auth/login", json={"email": f"u{i}@example.com", "senha": "errada-errada"})
        assert r.status_code == 401
    r = client.post("/auth/login", json={"email": "u99@example.com", "senha": "errada-errada"})
    assert r.status_code == 429


def test_registro_rate_limit_por_ip_429(client):
    for i in range(10):
        r = client.post("/auth/registro", json={"email": f"u{i}@example.com", "senha": "senha-segura-1"})
        assert r.status_code == 201
    r = client.post("/auth/registro", json={"email": "extra@example.com", "senha": "senha-segura-1"})
    assert r.status_code == 429
    assert r.json()["detail"] == "Muitas tentativas de cadastro. Tente mais tarde."


def test_registro_usa_limite_diario_configurado(client, monkeypatch):
    from app.config import Settings

    cfg = Settings(_env_file=None, database_url="sqlite://", jwt_secret="x" * 40, daily_question_limit=7)
    monkeypatch.setattr("app.routers.auth.get_settings", lambda: cfg)
    r = client.post("/auth/registro", json={"email": "a@example.com", "senha": "senha-segura-1"})
    assert r.status_code == 201
    assert r.json()["limite_diario"] == 7
