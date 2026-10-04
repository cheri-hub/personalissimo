import { useState, type FormEvent } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'

export function Login() {
  const { entrar } = useAuth()
  const [cadastro, setCadastro] = useState(false)
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      if (cadastro) await api('/auth/registro', { method: 'POST', body: { email, senha } })
      const { access_token } = await api<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: { email, senha },
      })
      entrar(access_token)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro inesperado.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="card login">
      <h1>Personalissimo</h1>
      <form onSubmit={enviar}>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            minLength={cadastro ? 8 : undefined}
            required
          />
        </label>
        {erro && <p role="alert" className="erro">{erro}</p>}
        <button type="submit" disabled={enviando}>{cadastro ? 'Cadastrar' : 'Entrar'}</button>
      </form>
      <button type="button" className="link" onClick={() => setCadastro(!cadastro)}>
        {cadastro ? 'Já tenho conta' : 'Criar conta'}
      </button>
    </main>
  )
}
