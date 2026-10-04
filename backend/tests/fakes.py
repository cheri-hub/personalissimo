from app.agent.types import LLMResponse


class FakeProvider:
    """Scripted provider. `respostas` can be a list or an infinite iterator."""

    def __init__(self, respostas):
        self._it = iter(respostas)
        self.chamadas = []

    def generate(self, system, historico, tools):
        self.chamadas.append((system, list(historico)))
        return next(self._it)


def texto(conteudo: str) -> LLMResponse:
    return LLMResponse(text=conteudo)
