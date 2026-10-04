def registrar_e_logar(client, email="a@example.com", senha="senha-segura-1") -> dict:
    client.post("/auth/registro", json={"email": email, "senha": senha})
    resposta = client.post("/auth/login", json={"email": email, "senha": senha})
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}
