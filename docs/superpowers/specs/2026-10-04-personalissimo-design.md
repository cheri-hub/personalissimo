# Personalissimo — Design (Etapa 1)

Data: 2026-10-04
Status: aguardando revisão do usuário

## 1. Visão

Agente pessoal web. O usuário pergunta se pode fazer algo ("posso comprar um notebook de R$ 6.000?"). O agente consulta os dados que tem sobre a pessoa (finanças, metas, notas pessoais) e devolve:

1. um **veredito racional** estruturado, com números calculados por código, e
2. uma **reflexão** filosófica e terapêutica, separada, baseada nas lentes que o usuário escolheu.

O produto é **público** (multiusuário, isolamento total de dados), **sem cobrança** por enquanto.

## 2. Escopo

### Dentro da Etapa 1
- Contas: cadastro e login por email e senha (hash argon2). **Sem 2FA** (item futuro).
- Entrada **manual** de dados por telas: rendas, despesas, dívidas, patrimônio, metas e notas livres.
- Motor do agente com tool use, veredito estruturado, reflexão com lentes configuráveis.
- Checagem de sinais de sofrimento (modo acolhimento).
- Limite diário de perguntas por usuário.
- Histórico de perguntas com log do que foi consultado.
- Provedor de LLM trocável; implementação inicial com **Gemini 3 Flash (plano gratuito)**.

### Fora da Etapa 1 (roadmap)
- Etapa 2: importação de arquivos (extratos CSV/OFX/PDF, planilhas).
- Etapa 3: conectores automáticos (Open Finance, Gmail, Calendar), um por vez.
- Cobrança e planos (descartado por enquanto).
- 2FA.
- Conformidade LGPD completa (consentimento, exportação e exclusão de dados, política de privacidade).

### Premissa de dados
Enquanto o plano gratuito do Gemini for usado, **somente dados fictícios**. Nos termos do Gemini API (plano gratuito), o Google usa o conteúdo enviado para melhorar produtos e revisores humanos podem lê-lo; o Brasil não tem a exceção válida para EEE, Suíça e Reino Unido. **Antes de qualquer usuário real**: migrar para plano pago (ou outro provedor) e fechar os itens de LGPD acima.

## 3. Stack

- Backend: Python, FastAPI, Pydantic.
- Frontend: React.
- Banco: PostgreSQL.
- LLM: Gemini 3 Flash (gratuito, dev) atrás de uma interface de provedor trocável.

## 4. Arquitetura

### Componentes
- **Frontend (React):** login, cadastro de dados, painel, tela de perguntas, histórico, configurações.
- **API (FastAPI):** autenticação, CRUD dos dados, endpoint `POST /perguntas`.
- **Banco (Postgres):** todas as tabelas de dados têm `user_id`; toda consulta filtra por ele. Row-level security pode reforçar depois.
- **Motor do agente:** orquestra o loop com a LLM e as ferramentas.
- **Ferramentas:** funções Python puras e determinísticas. A LLM não faz aritmética.
- **Camada de provedor de LLM:** interface única `gerar(mensagens, ferramentas)`. Implementação inicial: Gemini. Outras (Claude, Groq, OpenRouter) são novas classes.

### Princípio central
O Gemini decide e explica; **os números vêm sempre das ferramentas**. A reflexão **nunca altera** os números do veredito.

## 5. Modelo de dados

Todas as tabelas, exceto `usuarios`, têm `user_id`.

| Tabela | Campos principais |
|---|---|
| `usuarios` | email, senha (hash), `lentes` (lista), `tom` (direto, acolhedor, provocador), limite diário |
| `rendas` | descrição, valor, frequência, data de início e fim |
| `despesas` | descrição, valor, categoria, frequência, essencial (bool) |
| `dividas` | credor, saldo, juros, parcela, vencimento |
| `patrimonio` | tipo (conta, investimento, bem), descrição, valor, data |
| `metas` | título, valor-alvo, prazo, prioridade, valor acumulado |
| `notas` | texto livre, data, tags (valores, rotina, saúde geral, família) |
| `perguntas` | texto, veredito (JSON), reflexão, `consultas` (log das ferramentas), data |

## 6. Telas

1. Login e cadastro.
2. Painel: saldo mensal, patrimônio, progresso das metas.
3. Finanças: abas Rendas, Despesas, Dívidas, Patrimônio (lista e formulário).
4. Metas: lista com barra de progresso.
5. Notas: editor livre com tags e busca.
6. Perguntar: campo de pergunta; resultado em duas partes — **Veredito racional** (decisão, razões, números, "dados consultados" expansível) e **Reflexão** (bloco recolhível).
7. Histórico.
8. Configurações: lentes (Estoicismo, Epicurismo, TCC, ACT, Mindfulness etc.), tom, limite de uso.

## 7. Motor do agente

Fluxo de `POST /perguntas`:

1. **Pré-checagens:** login válido, limite diário, checagem de sofrimento.
2. **Modo acolhimento:** se a checagem disparar (pergunta ou notas recentes), pula veredito e ferramentas; responde com acolhimento e indicação de apoio profissional (CVV, 188).
3. **Loop de ferramentas:** Gemini recebe pergunta, lentes e tom; pode chamar ferramentas; **máximo de 6 rodadas**.
4. **Resposta final:** JSON validado por schema Pydantic: `veredito` (`sim`, `nao`, `sim_com_condicoes`, `indeterminado`), `razoes`, `numeros`, `reflexao`, `dados_consultados`.
5. **Persistência:** pergunta, resposta e log das ferramentas em `perguntas`.

### Ferramentas
- `obter_fluxo_de_caixa(periodo)`
- `listar_dividas()`
- `listar_metas()`
- `obter_patrimonio()`
- `simular_compra(valor, parcelas, juros)` — impacto no saldo mensal, nas metas e no prazo de cada meta
- `buscar_notas(termo)`
- `obter_notas_relevantes()`

O `user_id` vem do token e **nunca** da LLM, o que impede acesso cruzado entre usuários.

### Tratamento de erros
- **JSON inválido:** uma nova tentativa com o erro do schema; se falhar de novo, erro claro, sem resposta inventada.
- **Dados insuficientes:** veredito `indeterminado` listando o que falta cadastrar.
- **Cota esgotada (429):** tentativa automática curta e depois mensagem amigável.
- **Falha de ferramenta:** o erro volta ao Gemini, que registra a limitação; sem valores chutados.
- **Prompt injection via notas:** o conteúdo das notas entra marcado como dado do usuário; o prompt de sistema o trata como informação, nunca como instrução.

## 8. Segurança (Etapa 1)

- Senhas com argon2; HTTPS; segredos (chave do Gemini, segredo JWT) em variáveis de ambiente, validados no startup.
- Validação de entrada em todos os endpoints (Pydantic).
- Rate limiting por usuário e no login.
- Mensagens de erro sem vazar dados sensíveis.
- Isolamento por `user_id` em toda consulta, com testes específicos de acesso cruzado.

## 9. Testes

- Ferramentas: unitários com dados fictícios (cálculos).
- Motor: testes com **LLM falso** (respostas fixas) para loop, limite de rodadas, schema, modo acolhimento.
- Provedor Gemini: poucos testes de integração, marcados à parte.
- API: integração incluindo isolamento entre usuários.
- Frontend: formulários e fluxo de pergunta.
- Meta: cobertura mínima de 80%.

## 10. Decisões registradas

| Decisão | Escolha |
|---|---|
| Entrada de dados | Manual com telas, importação depois, conectores depois |
| Hospedagem | Nuvem, produto público |
| Stack | Python (FastAPI) + React + Postgres |
| Abordagem do agente | Tool use com cálculos determinísticos |
| Formato da resposta | Veredito estruturado + Reflexão separada |
| Camada filosófica/terapêutica | Bloco separado; lentes configuráveis pelo usuário |
| LLM inicial | Gemini 3 Flash gratuito, só com dados fictícios |
| Cobrança | Fora de escopo |
| 2FA e LGPD | Adiados para antes de usuários reais |
