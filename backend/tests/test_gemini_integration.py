import os

import pytest

from app.agent.gemini import GeminiProvider
from app.agent.tools.registry import TOOL_SPECS
from app.agent.types import Turn


@pytest.mark.integration
def test_gemini_real_responde():
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        pytest.skip("GEMINI_API_KEY não definido")
    provider = GeminiProvider(chave, os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview"))
    r = provider.generate("Responda em uma palavra.", [Turn(role="user", text="Diga oi")], TOOL_SPECS)
    assert r.text or r.tool_calls
