import { useState, type FormEvent } from 'react'
import { useApi } from '../auth'
import { ResultadoPergunta, type Pergunta } from '../components/ResultadoPergunta'

export function Perguntar() {
  const request = useApi()
  const [texto, setTexto] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [resultado, setResultado] = useState<Pergunta | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setCarregando(true)
    try {
      setResultado(await request<Pergunta>('/perguntas', { method: 'POST', body: { texto } }))
    } catch (err) {
      setResultado(null)
      setErro(err instanceof Error ? err.message : 'Erro inesperado.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <main>
      <form className="card" onSubmit={enviar}>
        <label>
          Sua pergunta
          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            minLength={3}
            maxLength={1000}
            required
            placeholder="Posso comprar um notebook de R$ 6.000?"
          />
        </label>
        <button type="submit" disabled={carregando}>{carregando ? 'Pensando…' : 'Perguntar'}</button>
      </form>
      {erro && <p role="alert" className="erro">{erro}</p>}
      {resultado && <ResultadoPergunta pergunta={resultado} />}
    </main>
  )
}
