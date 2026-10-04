# Personalissimo

Agente pessoal: você pergunta "posso fazer X?" e ele responde com um veredito racional (números calculados por código)
e uma reflexão filosófica/terapêutica, usando os dados que você cadastrou.

> **Atenção:** enquanto usar o plano gratuito do Gemini, cadastre **somente dados fictícios**. O Google pode usar e
> revisar o conteúdo enviado nesse plano. Antes de ter usuários reais: plano pago, LGPD, 2FA e migrações (Alembic).

## Rodando localmente

1. `docker compose up -d` (Postgres)
2. Backend: `cd backend`, `python -m venv .venv`, `.venv/Scripts/python -m pip install -e ".[dev]"`,
   copie `.env.example` para `.env` e preencha `JWT_SECRET` (32+ caracteres) e `GEMINI_API_KEY`
   (Google AI Studio), depois `.venv/Scripts/python -m uvicorn app.main:app --reload`
3. Frontend: `cd frontend`, `npm install`, `npm run dev` (http://localhost:5173)

## Testes

- Backend: `.venv/Scripts/python -m pytest --cov=app --cov-fail-under=80`
- Teste real do Gemini: `.venv/Scripts/python -m pytest -m integration`
- Frontend: `npm test`

## Produção

Termine HTTPS no host (proxy/PaaS), use segredos via variáveis de ambiente e troque `create_all` por migrações.
