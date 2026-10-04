import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { ApiError, api } from './api'

const CHAVE = 'personalissimo.token'

function lerToken(): string | null {
  try {
    return localStorage.getItem(CHAVE)
  } catch {
    return null
  }
}

function gravarToken(token: string | null) {
  try {
    if (token) localStorage.setItem(CHAVE, token)
    else localStorage.removeItem(CHAVE)
  } catch {
    /* storage indisponível: o token vale só nesta sessão */
  }
}

type Contexto = { token: string | null; entrar: (t: string) => void; sair: () => void }

const AuthContext = createContext<Contexto>({ token: null, entrar: () => {}, sair: () => {} })

export function AuthProvider({ children, initialToken }: { children: ReactNode; initialToken?: string | null }) {
  const [token, setToken] = useState<string | null>(initialToken !== undefined ? initialToken : lerToken())
  const entrar = useCallback((t: string) => {
    gravarToken(t)
    setToken(t)
  }, [])
  const sair = useCallback(() => {
    gravarToken(null)
    setToken(null)
  }, [])
  const valor = useMemo(() => ({ token, entrar, sair }), [token, entrar, sair])
  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)

export function useApi() {
  const { token, sair } = useAuth()
  return useCallback(
    async <T,>(path: string, opcoes: { method?: string; body?: unknown } = {}): Promise<T> => {
      try {
        return await api<T>(path, { ...opcoes, token })
      } catch (erro) {
        if (erro instanceof ApiError && erro.status === 401) sair()
        throw erro
      }
    },
    [token, sair],
  )
}
