import { describe, expect, it } from 'vitest'
import { ApiError, api } from './api'
import { mockFetch } from './test-utils'

describe('api', () => {
  it('envia token e corpo JSON', async () => {
    const fetchMock = mockFetch(() => ({ ok: true }))
    await api('/x', { method: 'POST', body: { a: 1 }, token: 'tok' })
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/x')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ a: 1 })
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('usa detail como mensagem de erro', async () => {
    mockFetch(() => ({ status: 401, body: { detail: 'Credenciais inválidas' } }))
    await expect(api('/x')).rejects.toMatchObject({ status: 401, message: 'Credenciais inválidas' })
  })

  it('resume erros de validação', async () => {
    mockFetch(() => ({ status: 422, body: { detail: [{ msg: 'x' }] } }))
    await expect(api('/x')).rejects.toBeInstanceOf(ApiError)
    await expect(api('/x')).rejects.toHaveProperty('message', 'Dados inválidos. Revise os campos.')
  })

  it('retorna undefined em 204', async () => {
    mockFetch(() => ({ status: 204, body: null }))
    expect(await api('/x', { method: 'DELETE' })).toBeUndefined()
  })
})
