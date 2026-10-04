import { useEffect, useState, type FormEvent } from 'react'
import { useApi } from '../auth'

const LENTES = [
  ['estoicismo', 'Estoicismo'],
  ['epicurismo', 'Epicurismo'],
  ['tcc', 'TCC'],
  ['act', 'ACT'],
  ['mindfulness', 'Mindfulness'],
] as const

type Perfil = { lentes: string[]; tom: string; limite_diario?: number }

export function Config() {
  const request = useApi()
  const [lentes, setLentes] = useState<string[]>([])
  const [tom, setTom] = useState('acolhedor')
  const [limite, setLimite] = useState<number | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    request<Perfil>('/me')
      .then((p) => {
        setLentes(p.lentes)
        setTom(p.tom)
        setLimite(p.limite_diario ?? null)
      })
      .catch((e) => setErro(e instanceof Error ? e.message : 'Erro inesperado.'))
  }, [request])

  function alternar(chave: string) {
    setLentes(lentes.includes(chave) ? lentes.filter((l) => l !== chave) : [...lentes, chave])
  }

  async function salvar(e: FormEvent) {
    e.preventDefault()
    setMsg(null)
    setErro(null)
    try {
      await request<Perfil>('/me/config', { method: 'PATCH', body: { lentes, tom } })
      setMsg('Configurações salvas.')
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro inesperado.')
    }
  }

  return (
    <main>
      <form className="card" onSubmit={salvar}>
        <h2>Configurações</h2>
        <fieldset>
          <legend>Lentes de reflexão</legend>
          {LENTES.map(([chave, rotulo]) => (
            <label key={chave}>
              <input type="checkbox" checked={lentes.includes(chave)} onChange={() => alternar(chave)} />
              {rotulo}
            </label>
          ))}
        </fieldset>
        <label>
          Tom
          <select value={tom} onChange={(e) => setTom(e.target.value)}>
            <option value="direto">direto</option>
            <option value="acolhedor">acolhedor</option>
            <option value="provocador">provocador</option>
          </select>
        </label>
        {limite !== null && <p className="muted">Limite diário de perguntas: {limite}</p>}
        {erro && <p role="alert" className="erro">{erro}</p>}
        {msg && <p>{msg}</p>}
        <button type="submit">Salvar</button>
      </form>
    </main>
  )
}
