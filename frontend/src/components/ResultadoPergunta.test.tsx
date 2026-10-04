import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ResultadoPergunta, type Pergunta } from './ResultadoPergunta'

const base: Pergunta = {
  id: 1,
  texto: 'Posso comprar um notebook?',
  modo: 'veredito',
  mensagem: null,
  criado_em: '2026-10-04T10:00:00Z',
  resposta: {
    veredito: 'sim_com_condicoes',
    razoes: ['Saldo mensal positivo'],
    numeros: [{ rotulo: 'Saldo mensal', valor: 2650, unidade: 'BRL' }],
    reflexao: 'Observe o impulso antes de comprar.',
    faltando: [],
    dados_consultados: [{ ferramenta: 'simular_compra', argumentos: { valor: 6000 } }],
  },
}

describe('ResultadoPergunta', () => {
  it('mostra veredito, razões, números, reflexão e dados consultados', () => {
    render(<ResultadoPergunta pergunta={base} />)
    expect(screen.getByRole('heading', { name: 'Sim, com condições' })).toBeInTheDocument()
    expect(screen.getByText('Saldo mensal positivo')).toBeInTheDocument()
    expect(screen.getByText(/2\.650,00/)).toBeInTheDocument()
    expect(screen.getByText('Reflexão')).toBeInTheDocument()
    expect(screen.getByText('Observe o impulso antes de comprar.')).toBeInTheDocument()
    expect(screen.getByText(/simular_compra/)).toBeInTheDocument()
  })

  it('lista o que falta cadastrar quando indeterminado', () => {
    const p = { ...base, resposta: { ...base.resposta!, veredito: 'indeterminado' as const, faltando: ['Cadastre suas despesas'] } }
    render(<ResultadoPergunta pergunta={p} />)
    expect(screen.getByRole('heading', { name: 'Indeterminado' })).toBeInTheDocument()
    expect(screen.getByText('Cadastre suas despesas')).toBeInTheDocument()
  })

  it('no modo acolhimento mostra só a mensagem', () => {
    const p: Pergunta = { ...base, modo: 'acolhimento', resposta: null, mensagem: 'Ligue 188 (CVV).' }
    render(<ResultadoPergunta pergunta={p} />)
    expect(screen.getByRole('note')).toHaveTextContent('Ligue 188')
    expect(screen.queryByText('Reflexão')).not.toBeInTheDocument()
  })
})
