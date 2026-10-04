import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderComAuth } from '../test-utils'
import { Config } from './Config'

describe('Config', () => {
  it('carrega e salva lentes e tom', async () => {
    const fetchMock = mockFetch((_url, init) =>
      init?.method === 'PATCH'
        ? { lentes: ['estoicismo', 'tcc'], tom: 'direto' }
        : { id: 1, email: 'a@example.com', lentes: ['estoicismo'], tom: 'acolhedor', limite_diario: 20 },
    )
    renderComAuth(<Config />)
    expect(await screen.findByLabelText('Estoicismo')).toBeChecked()
    await userEvent.click(screen.getByLabelText('TCC'))
    await userEvent.selectOptions(screen.getByLabelText('Tom'), 'direto')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar' }))
    await waitFor(() => {
      const patch = fetchMock.mock.calls.find(([, i]) => i?.method === 'PATCH')
      expect(JSON.parse(patch![1]!.body as string)).toEqual({ lentes: ['estoicismo', 'tcc'], tom: 'direto' })
    })
    expect(await screen.findByText('Configurações salvas.')).toBeInTheDocument()
  })

  it('mantém Salvar desabilitado e não envia PATCH enquanto /me carrega', async () => {
    let liberar: () => void = () => {}
    const espera = new Promise<void>((r) => (liberar = r))
    const perfil = { id: 1, email: 'a@example.com', lentes: ['estoicismo'], tom: 'acolhedor', limite_diario: 20 }
    const fetchMock = mockFetch(() => perfil)
    fetchMock.mockImplementationOnce(async () => {
      await espera
      return new Response(JSON.stringify(perfil), { status: 200, headers: { 'Content-Type': 'application/json' } })
    })
    renderComAuth(<Config />)
    const salvar = screen.getByRole('button', { name: 'Salvar' })
    expect(salvar).toBeDisabled()
    expect(screen.getByText('Carregando…')).toBeInTheDocument()
    await userEvent.click(salvar)
    expect(fetchMock.mock.calls.some(([, i]) => i?.method === 'PATCH')).toBe(false)
    liberar()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Salvar' })).toBeEnabled())
    expect(screen.getByLabelText('Estoicismo')).toBeChecked()
  })

  it('com falha em /me mostra erro, mantém Salvar desabilitado e nunca envia PATCH', async () => {
    const fetchMock = mockFetch(() => ({ status: 500, body: { detail: 'Falha' } }))
    renderComAuth(<Config />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Falha')
    const salvar = screen.getByRole('button', { name: 'Salvar' })
    expect(salvar).toBeDisabled()
    await userEvent.click(salvar)
    expect(fetchMock.mock.calls.some(([, i]) => i?.method === 'PATCH')).toBe(false)
  })
})
