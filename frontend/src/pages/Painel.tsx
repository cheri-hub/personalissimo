import { useEffect, useState } from 'react'
import { useApi } from '../auth'

type PainelDados = {
  fluxo: { renda: number; despesas: number; parcelas_dividas: number; saldo: number }
  patrimonio: { total: number; liquido: number }
  metas: { metas: { titulo: string; progresso_pct: number; falta: number }[] }
}

const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export function Painel() {
  const request = useApi()
  const [dados, setDados] = useState<PainelDados | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    request<PainelDados>('/painel')
      .then(setDados)
      .catch((e) => setErro(e instanceof Error ? e.message : 'Erro inesperado.'))
  }, [request])

  if (erro) return <main><p role="alert" className="erro">{erro}</p></main>
  if (!dados) return <main><p className="muted">Carregando…</p></main>

  return (
    <main>
      <div className="grid">
        <div className="card"><span className="muted">Saldo mensal</span><div className="numero">{brl(dados.fluxo.saldo)}</div></div>
        <div className="card"><span className="muted">Patrimônio líquido</span><div className="numero">{brl(dados.patrimonio.liquido)}</div></div>
        <div className="card"><span className="muted">Patrimônio total</span><div className="numero">{brl(dados.patrimonio.total)}</div></div>
      </div>
      <section className="card">
        <h2>Metas</h2>
        {dados.metas.metas.length === 0 && <p className="muted">Nenhuma meta cadastrada.</p>}
        {dados.metas.metas.map((m) => (
          <div key={m.titulo}>
            <p>{m.titulo} — {m.progresso_pct}% (faltam {brl(m.falta)})</p>
            <div className="barra"><div style={{ width: `${Math.min(m.progresso_pct, 100)}%` }} /></div>
          </div>
        ))}
      </section>
    </main>
  )
}
