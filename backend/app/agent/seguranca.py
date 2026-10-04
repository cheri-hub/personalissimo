import re
import unicodedata

_SINAIS = tuple(
    re.compile(p)
    for p in (
        r"suicid",
        r"automutila",
        r"me (matar|cortar|ferir|machucar)",
        r"nao quero (mais )?viver",
        r"quer(o|ia) morrer",
        r"vou morrer",
        r"tirar (a )?(minha )?(propria )?vida",
        r"acabar com (a )?(minha )?(vida|tudo)",
        r"quero sumir",
        r"nao aguento mais",
        r"nao vale a pena viver",
        r"melhor sem mim",
    )
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def detecta_sofrimento(*textos: str) -> bool:
    """Heurística conservadora por palavras-chave (v1). Pode dar falso positivo; prefere errar para o lado do cuidado."""
    return any(sinal.search(n) for n in map(_normalizar, textos) for sinal in _SINAIS)
