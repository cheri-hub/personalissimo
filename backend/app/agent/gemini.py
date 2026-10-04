import time
from collections.abc import Callable, Sequence
from typing import Any

from google import genai
from google.genai import errors, types

from app.agent.types import (
    LLMResponse,
    ProviderError,
    ProviderQuotaError,
    ToolCall,
    ToolSpec,
    Turn,
)

_ESPERA_429_SEGUNDOS = 2.0


def _declarar(tools: Sequence[ToolSpec]) -> types.Tool:
    declaracoes = [
        types.FunctionDeclaration(
            name=t.name,
            description=t.description,
            parameters_json_schema=t.parameters if t.parameters.get("properties") else None,
        )
        for t in tools
    ]
    return types.Tool(function_declarations=declaracoes)


def _para_contents(historico: Sequence[Turn]) -> list[Any]:
    contents: list[Any] = []
    for turno in historico:
        if turno.role == "user":
            contents.append(types.Content(role="user", parts=[types.Part(text=turno.text or "")]))
        elif turno.role == "model":
            if turno.raw is not None:
                contents.append(turno.raw)
            elif turno.text:
                contents.append(types.Content(role="model", parts=[types.Part(text=turno.text)]))
        else:
            partes = [types.Part.from_function_response(name=r.name, response=r.output) for r in turno.tool_results]
            contents.append(types.Content(role="user", parts=partes))
    return contents


class GeminiProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._client = client or genai.Client(api_key=api_key)
        self._model = model
        self._sleep = sleep

    def generate(self, system: str, historico: Sequence[Turn], tools: Sequence[ToolSpec]) -> LLMResponse:
        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=[_declarar(tools)] if tools else None,
            temperature=0.3,
        )
        resposta = self._chamar(_para_contents(historico), config)
        chamadas = tuple(
            ToolCall(name=fc.name, args=dict(fc.args or {}), id=getattr(fc, "id", None))
            for fc in (resposta.function_calls or [])
        )
        raw = resposta.candidates[0].content if resposta.candidates else None
        return LLMResponse(text=None if chamadas else resposta.text, tool_calls=chamadas, raw=raw)

    def _chamar(self, contents: list[Any], config: types.GenerateContentConfig) -> Any:
        for tentativa in range(2):
            try:
                return self._client.models.generate_content(model=self._model, contents=contents, config=config)
            except errors.APIError as exc:
                if exc.code != 429:
                    raise ProviderError(f"Erro do Gemini (código {exc.code})") from exc
                if tentativa == 0:
                    self._sleep(_ESPERA_429_SEGUNDOS)
            except Exception as exc:
                raise ProviderError("Falha de comunicação com o Gemini") from exc
        raise ProviderQuotaError("Cota do Gemini esgotada")
