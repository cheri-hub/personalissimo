import { useState } from 'react'
import { ResourceManager } from '../components/ResourceManager'
import { DESPESAS, DIVIDAS, PATRIMONIO, RENDAS } from '../recursos'

const ABAS = [RENDAS, DESPESAS, DIVIDAS, PATRIMONIO]

export function Financas() {
  const [ativa, setAtiva] = useState(0)
  return (
    <main>
      <div role="tablist">
        {ABAS.map((a, i) => (
          <button
            key={a.path}
            role="tab"
            aria-selected={i === ativa}
            className={i === ativa ? '' : 'sec'}
            onClick={() => setAtiva(i)}
          >
            {a.titulo}
          </button>
        ))}
      </div>
      <ResourceManager key={ABAS[ativa].path} {...ABAS[ativa]} />
    </main>
  )
}
