const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

type Opcoes = { method?: string; body?: unknown; token?: string | null }

function mensagemDeErro(corpo: unknown, status: number): string {
  const detail = (corpo as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Dados inválidos. Revise os campos.'
  return `Erro inesperado (${status}).`
}

export async function api<T>(path: string, { method = 'GET', body, token }: Opcoes = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`
  const resposta = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (resposta.status === 204) return undefined as T
  const corpo = await resposta.json().catch(() => null)
  if (!resposta.ok) throw new ApiError(resposta.status, mensagemDeErro(corpo, resposta.status))
  return corpo as T
}
