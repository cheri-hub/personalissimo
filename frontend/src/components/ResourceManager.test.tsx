import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { RENDAS } from '../recursos'
import { mockFetch, renderComAuth } from '../test-utils'
import { ResourceManager } from './ResourceManager'

const SALARIO = { id: 1, descricao: 'Salário', valor: '5000.00', frequencia: 'mensal', inicio: null, fim: null }

function renderizar() {
  return renderComAuth(<ResourceManager {...RENDAS} />)
}

describe('ResourceManager', () => {
  it('lista os itens do servidor', async () => {
    mockFetch(() => [SALARIO])
    renderizar()
    expect(await screen.findByText('Salário')).toBeInTheDocument()
    expect(screen.getByText('5000.00')).toBeInTheDocument()
  })

  it('cria um item e recarrega a lista', async () => {
    const fetchMock = mockFetch((_url, init) => (init?.method === 'POST' ? { id: 2 } : [SALARIO]))
    renderizar()
    await screen.findByText('Salário')
    await userEvent.type(screen.getByLabelText('Descrição'), 'Freela')
    await userEvent.type(screen.getByLabelText('Valor'), '800')
    await userEvent.click(screen.getByRole('button', { name: 'Adicionar' }))
    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')
      expect(post).toBeTruthy()
      expect(JSON.parse(post![1]!.body as string)).toEqual({ descricao: 'Freela', valor: '800', frequencia: 'mensal' })
    })
  })

  it('edita um item com PUT', async () => {
    const fetchMock = mockFetch(() => [SALARIO])
    renderizar()
    const linha = (await screen.findByText('Salário')).closest('tr')!
    await userEvent.click(within(linha).getByRole('button', { name: 'Editar' }))
    const campo = screen.getByLabelText('Descrição')
    await userEvent.clear(campo)
    await userEvent.type(campo, 'Salário líquido')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar' }))
    await waitFor(() => {
      const put = fetchMock.mock.calls.find(([, init]) => init?.method === 'PUT')
      expect(String(put![0])).toContain('/rendas/1')
      expect(JSON.parse(put![1]!.body as string).descricao).toBe('Salário líquido')
    })
  })

  it('remove um item com DELETE', async () => {
    const fetchMock = mockFetch((_u, init) => (init?.method === 'DELETE' ? { status: 204, body: null } : [SALARIO]))
    renderizar()
    const linha = (await screen.findByText('Salário')).closest('tr')!
    await userEvent.click(within(linha).getByRole('button', { name: 'Excluir' }))
    await waitFor(() => expect(fetchMock.mock.calls.some(([, i]) => i?.method === 'DELETE')).toBe(true))
  })

  it('mostra erro de validação do servidor', async () => {
    mockFetch((_u, init) => (init?.method === 'POST' ? { status: 422, body: { detail: [{ msg: 'x' }] } } : []))
    renderizar()
    await userEvent.type(await screen.findByLabelText('Descrição'), 'X')
    await userEvent.type(screen.getByLabelText('Valor'), '-1')
    await userEvent.click(screen.getByRole('button', { name: 'Adicionar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Dados inválidos')
  })
})
