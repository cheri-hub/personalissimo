import { useEffect, useState } from 'react'
import { useApi } from '../auth'
import { ResultadoPergunta, type Pergunta } from '../components/ResultadoPergunta'

export function Historico() {
  const request = useApi()
  const [itens, setItens] = useState<Pergunta[]>([])
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    request<Pergunta[]>('/perguntas')
      .then(setItens)
      .catch((e) => setErro(e instanceof Error ? e.message : 'Erro inesperado.'))
  }, [request])

  return (
    <main>
      <h2>Histórico</h2>
      {erro && <p role="alert" className="erro">{erro}</p>}
      {itens.length === 0 && !erro && <p className="muted">Nenhuma pergunta ainda.</p>}
      {itens.map((p) => (
        <details key={p.id} className="card">
          <summary>{p.texto} <span className="muted">({new Date(p.criado_em).toLocaleDateString('pt-BR')})</span></summary>
          <ResultadoPergunta pergunta={p} />
        </details>
      ))}
    </main>
  )
}
