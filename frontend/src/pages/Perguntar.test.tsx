import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderComAuth } from '../test-utils'
import { Perguntar } from './Perguntar'

const RESPOSTA = {
  id: 7,
  texto: 'Posso comprar um notebook?',
  modo: 'veredito',
  mensagem: null,
  criado_em: '2026-10-04T10:00:00Z',
  resposta: {
    veredito: 'nao',
    razoes: ['Compromete a reserva'],
    numeros: [],
    reflexao: 'O que você busca com essa compra?',
    faltando: [],
    dados_consultados: [],
  },
}

describe('Perguntar', () => {
  it('envia a pergunta e mostra o resultado', async () => {
    const fetchMock = mockFetch(() => RESPOSTA)
    renderComAuth(<Perguntar />)
    await userEvent.type(screen.getByLabelText('Sua pergunta'), 'Posso comprar um notebook?')
    await userEvent.click(screen.getByRole('button', { name: 'Perguntar' }))
    expect(await screen.findByRole('heading', { name: 'Não' })).toBeInTheDocument()
    expect(screen.getByText('Compromete a reserva')).toBeInTheDocument()
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/perguntas')
    expect(JSON.parse(init!.body as string)).toEqual({ texto: 'Posso comprar um notebook?' })
  })

  it('mostra erro do servidor (ex.: limite diário)', async () => {
    mockFetch(() => ({ status: 429, body: { detail: 'Limite diário de perguntas atingido. Volte amanhã.' } }))
    renderComAuth(<Perguntar />)
    await userEvent.type(screen.getByLabelText('Sua pergunta'), 'Posso viajar?')
    await userEvent.click(screen.getByRole('button', { name: 'Perguntar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Limite diário')
  })

  it('desabilita o botão enquanto espera', async () => {
    let liberar: () => void = () => {}
    const espera = new Promise<void>((r) => (liberar = r))
    const fetchMock = mockFetch(() => RESPOSTA)
    fetchMock.mockImplementationOnce(async () => {
      await espera
      return new Response(JSON.stringify(RESPOSTA), { status: 200, headers: { 'Content-Type': 'application/json' } })
    })
    renderComAuth(<Perguntar />)
    await userEvent.type(screen.getByLabelText('Sua pergunta'), 'Posso viajar?')
    await userEvent.click(screen.getByRole('button', { name: 'Perguntar' }))
    expect(screen.getByRole('button', { name: 'Pensando…' })).toBeDisabled()
    liberar()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Perguntar' })).toBeEnabled())
  })
})
