import re
import unicodedata

_SINAIS = tuple(
    re.compile(p)
    for p in (
        r"suicid",
        r"automutila",
        r"\bme (matar|cortar|ferir|machucar)\b",
        r"\bnao quero (mais )?viver\b",
        r"\bquer(o|ia) morrer\b",
        r"\bvou morrer\b",
        r"\btirar (a )?(minha )?(propria )?vida\b",
        r"\bacabar com (a )?(minha )?(vida|tudo)\b",
        r"\bquero sumir\b",
        r"\bnao aguento mais\b",
        r"\bnao vale a pena viver\b",
        r"\bmelhor sem mim\b",
    )
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def detecta_sofrimento(*textos: str) -> bool:
    """Heurística conservadora por palavras-chave (v1). Pode dar falso positivo; prefere errar para o lado do cuidado."""
    return any(sinal.search(n) for n in map(_normalizar, textos) for sinal in _SINAIS)
