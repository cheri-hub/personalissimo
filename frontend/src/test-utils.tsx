import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { AuthProvider } from './auth'

export function renderComAuth(ui: ReactElement, { token = 'tok' }: { token?: string | null } = {}) {
  return render(
    <AuthProvider initialToken={token}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>{ui}</MemoryRouter>
    </AuthProvider>,
  )
}

type Resposta = unknown | { status: number; body: unknown }

export function mockFetch(handler: (url: string, init?: RequestInit) => Resposta) {
  const fn = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const r = handler(String(url), init) as { status?: number; body?: unknown }
    const comStatus = r && typeof r === 'object' && 'status' in r && 'body' in r
    const status = comStatus ? (r.status as number) : 200
    const body = comStatus ? r.body : r
    return new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}
