import unicodedata

_SINAIS = (
    "suicid",
    "me matar",
    "quero morrer",
    "nao quero mais viver",
    "nao aguento mais viver",
    "acabar com tudo",
    "acabar com a minha vida",
    "tirar minha vida",
    "me machucar",
    "automutila",
)


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def detecta_sofrimento(*textos: str) -> bool:
    """Heurística conservadora por palavras-chave (v1). Pode dar falso positivo; prefere errar para o lado do cuidado."""
    return any(sinal in _normalizar(t) for t in textos for sinal in _SINAIS)
