import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useApi } from '../auth'
import type { Campo, Recurso } from '../recursos'

type Item = Record<string, unknown> & { id: number }
type Formulario = Record<string, string | boolean>

function vazio(campos: Campo[]): Formulario {
  return Object.fromEntries(
    campos.map((c) => [c.nome, c.tipo === 'checkbox' ? false : c.tipo === 'select' ? (c.opcoes?.[0] ?? '') : '']),
  )
}

function doItem(item: Item, campos: Campo[]): Formulario {
  return Object.fromEntries(
    campos.map((c) => {
      const v = item[c.nome]
      if (c.tipo === 'checkbox') return [c.nome, Boolean(v)]
      if (c.tipo === 'tags') return [c.nome, Array.isArray(v) ? v.join(', ') : '']
      return [c.nome, v == null ? '' : String(v)]
    }),
  )
}

function paraPayload(campos: Campo[], form: Formulario): Record<string, unknown> {
  const payload: Record<string, unknown> = {}
  for (const c of campos) {
    const v = form[c.nome]
    if (c.tipo === 'checkbox') payload[c.nome] = Boolean(v)
    else if (c.tipo === 'tags') payload[c.nome] = String(v).split(',').map((t) => t.trim()).filter(Boolean)
    else if (v !== '') payload[c.nome] = v
  }
  return payload
}

function exibir(v: unknown): string {
  if (v == null || v === '') return '—'
  if (typeof v === 'boolean') return v ? 'Sim' : 'Não'
  if (Array.isArray(v)) return v.join(', ') || '—'
  return String(v)
}

export function ResourceManager({ path, titulo, campos }: Recurso) {
  const request = useApi()
  const [itens, setItens] = useState<Item[]>([])
  const [form, setForm] = useState<Formulario>(vazio(campos))
  const [editando, setEditando] = useState<number | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const carregar = useCallback(async () => {
    try {
      setItens(await request<Item[]>(path))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro inesperado.')
    }
  }, [request, path])

  useEffect(() => {
    setForm(vazio(campos))
    setEditando(null)
    void carregar()
  }, [carregar, campos])

  async function salvar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    try {
      const body = paraPayload(campos, form)
      if (editando === null) await request(path, { method: 'POST', body })
      else await request(`${path}/${editando}`, { method: 'PUT', body })
      setForm(vazio(campos))
      setEditando(null)
      await carregar()
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro inesperado.')
    }
  }

  async function excluir(id: number) {
    setErro(null)
    try {
      await request(`${path}/${id}`, { method: 'DELETE' })
      await carregar()
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro inesperado.')
    }
  }

  function atualizar(nome: string, valor: string | boolean) {
    setForm({ ...form, [nome]: valor })
  }

  return (
    <section className="card">
      <h2>{titulo}</h2>
      {erro && <p role="alert" className="erro">{erro}</p>}
      <form onSubmit={salvar}>
        {campos.map((c) => (
          <label key={c.nome}>
            {c.rotulo}
            {c.tipo === 'select' ? (
              <select value={String(form[c.nome])} onChange={(e) => atualizar(c.nome, e.target.value)}>
                {c.opcoes?.map((o) => <option key={o}>{o}</option>)}
              </select>
            ) : c.tipo === 'checkbox' ? (
              <input type="checkbox" checked={Boolean(form[c.nome])} onChange={(e) => atualizar(c.nome, e.target.checked)} />
            ) : c.tipo === 'textarea' ? (
              <textarea value={String(form[c.nome])} onChange={(e) => atualizar(c.nome, e.target.value)} required={c.obrigatorio} />
            ) : (
              <input
                type={c.tipo === 'number' ? 'number' : c.tipo === 'date' ? 'date' : 'text'}
                step={c.tipo === 'number' ? 'any' : undefined}
                value={String(form[c.nome])}
                onChange={(e) => atualizar(c.nome, e.target.value)}
                required={c.obrigatorio}
              />
            )}
          </label>
        ))}
        <div>
          <button type="submit">{editando === null ? 'Adicionar' : 'Salvar'}</button>{' '}
          {editando !== null && (
            <button type="button" className="sec" onClick={() => { setEditando(null); setForm(vazio(campos)) }}>
              Cancelar
            </button>
          )}
        </div>
      </form>
      <table>
        <thead>
          <tr>{campos.map((c) => <th key={c.nome}>{c.rotulo}</th>)}<th /></tr>
        </thead>
        <tbody>
          {itens.map((item) => (
            <tr key={item.id}>
              {campos.map((c) => <td key={c.nome}>{exibir(item[c.nome])}</td>)}
              <td>
                <button type="button" className="sec" onClick={() => { setEditando(item.id); setForm(doItem(item, campos)) }}>Editar</button>{' '}
                <button type="button" className="sec" onClick={() => void excluir(item.id)}>Excluir</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {itens.length === 0 && <p className="muted">Nada cadastrado ainda.</p>}
    </section>
  )
}
