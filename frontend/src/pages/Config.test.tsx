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
})
