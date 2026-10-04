export type Numero = { rotulo: string; valor: number; unidade: 'BRL' | 'meses' | '%' | 'parcelas' }

export type Resposta = {
  veredito: 'sim' | 'nao' | 'sim_com_condicoes' | 'indeterminado'
  razoes: string[]
  numeros: Numero[]
  reflexao: string
  faltando: string[]
  dados_consultados: { ferramenta: string; argumentos: Record<string, unknown> }[]
}

export type Pergunta = {
  id: number
  texto: string
  modo: 'veredito' | 'acolhimento'
  resposta: Resposta | null
  mensagem: string | null
  criado_em: string
}

const ROTULOS: Record<Resposta['veredito'], string> = {
  sim: 'Sim',
  nao: 'Não',
  sim_com_condicoes: 'Sim, com condições',
  indeterminado: 'Indeterminado',
}

function formatar({ valor, unidade }: Numero): string {
  if (unidade === 'BRL') return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  return `${valor.toLocaleString('pt-BR')} ${unidade === '%' ? '%' : unidade}`
}

export function ResultadoPergunta({ pergunta }: { pergunta: Pergunta }) {
  if (pergunta.modo === 'acolhimento' || !pergunta.resposta) {
    return <div role="note" className="acolhimento">{pergunta.mensagem}</div>
  }
  const r = pergunta.resposta
  return (
    <div className="card">
      <h3>{ROTULOS[r.veredito]}</h3>
      <ul>{r.razoes.map((x) => <li key={x}>{x}</li>)}</ul>
      {r.faltando.length > 0 && (
        <>
          <p className="muted">Para decidir melhor, cadastre:</p>
          <ul>{r.faltando.map((x) => <li key={x}>{x}</li>)}</ul>
        </>
      )}
      {r.numeros.length > 0 && (
        <table>
          <tbody>
            {r.numeros.map((n) => (
              <tr key={n.rotulo}><td>{n.rotulo}</td><td>{formatar(n)}</td></tr>
            ))}
          </tbody>
        </table>
      )}
      <details>
        <summary>Reflexão</summary>
        <p>{r.reflexao}</p>
      </details>
      <details>
        <summary>Dados consultados</summary>
        <ul>
          {r.dados_consultados.map((c, i) => (
            <li key={i}>{c.ferramenta} {JSON.stringify(c.argumentos)}</li>
          ))}
        </ul>
      </details>
    </div>
  )
}
