import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { renderComAuth } from '../test-utils'
import { Financas } from './Financas'

function resposta(corpo: unknown) {
  return new Response(JSON.stringify(corpo), { status: 200, headers: { 'Content-Type': 'application/json' } })
}

describe('Financas', () => {
  it('ignora resposta atrasada da aba anterior', async () => {
    let liberarRendas: (r: Response) => void = () => {}
    const rendasPendente = new Promise<Response>((res) => { liberarRendas = res })
    const fetchMock = vi.fn(async (url: RequestInfo | URL) => {
      const u = String(url)
      if (u.endsWith('/rendas')) return rendasPendente
      return resposta([{ id: 7, descricao: 'Aluguel', valor: '1000', categoria: 'moradia', frequencia: 'mensal', essencial: true }])
    })
    vi.stubGlobal('fetch', fetchMock)
    renderComAuth(<Financas />)
    await userEvent.click(screen.getByRole('tab', { name: 'Despesas' }))
    expect(await screen.findByText('Aluguel')).toBeInTheDocument()
    liberarRendas(resposta([{ id: 1, descricao: 'Salário', valor: '5000', frequencia: 'mensal' }]))
    await new Promise((r) => setTimeout(r, 20))
    expect(screen.queryByText('Salário')).not.toBeInTheDocument()
    expect(screen.getByText('Aluguel')).toBeInTheDocument()
  })

  it('Excluir após trocar de aba usa a URL do novo recurso', async () => {
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === 'DELETE') return new Response(null, { status: 204 })
      if (String(url).endsWith('/despesas'))
        return resposta([{ id: 7, descricao: 'Aluguel', valor: '1000', categoria: 'moradia', frequencia: 'mensal', essencial: true }])
      return resposta([{ id: 1, descricao: 'Salário', valor: '5000', frequencia: 'mensal' }])
    })
    vi.stubGlobal('fetch', fetchMock)
    renderComAuth(<Financas />)
    await screen.findByText('Salário')
    await userEvent.click(screen.getByRole('tab', { name: 'Despesas' }))
    const linha = (await screen.findByText('Aluguel')).closest('tr')!
    await userEvent.click(within(linha).getByRole('button', { name: 'Excluir' }))
    await waitFor(() => {
      const del = fetchMock.mock.calls.find(([, i]) => i?.method === 'DELETE')
      expect(String(del![0])).toMatch(/\/despesas\/7$/)
    })
  })
})
