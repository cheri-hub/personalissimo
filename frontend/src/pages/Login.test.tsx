import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderComAuth } from '../test-utils'
import { Login } from './Login'

describe('Login', () => {
  it('faz login e guarda o token', async () => {
    const fetchMock = mockFetch(() => ({ access_token: 'abc', token_type: 'bearer' }))
    renderComAuth(<Login />, { token: null })
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'senha-segura-1')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(String(fetchMock.mock.calls[0][0])).toContain('/auth/login')
    await waitFor(() => expect(localStorage.getItem('personalissimo.token')).toBe('abc'))
  })

  it('mostra erro do servidor', async () => {
    mockFetch(() => ({ status: 401, body: { detail: 'Credenciais inválidas' } }))
    renderComAuth(<Login />, { token: null })
    await userEvent.type(screen.getByLabelText('Email'), 'a@example.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'errada-errada')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Credenciais inválidas')
  })

  it('alterna para cadastro e registra antes de logar', async () => {
    const fetchMock = mockFetch((url) =>
      url.includes('/auth/registro') ? { id: 1 } : { access_token: 'novo', token_type: 'bearer' },
    )
    renderComAuth(<Login />, { token: null })
    await userEvent.click(screen.getByRole('button', { name: 'Criar conta' }))
    await userEvent.type(screen.getByLabelText('Email'), 'b@example.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'senha-segura-1')
    await userEvent.click(screen.getByRole('button', { name: 'Cadastrar' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(String(fetchMock.mock.calls[0][0])).toContain('/auth/registro')
    expect(String(fetchMock.mock.calls[1][0])).toContain('/auth/login')
  })
})
