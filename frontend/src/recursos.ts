export type Campo = {
  nome: string
  rotulo: string
  tipo: 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea' | 'tags'
  opcoes?: string[]
  obrigatorio?: boolean
}

export type Recurso = { path: string; titulo: string; campos: Campo[] }

const FREQUENCIAS = ['mensal', 'anual', 'unica']

export const RENDAS: Recurso = {
  path: '/rendas',
  titulo: 'Rendas',
  campos: [
    { nome: 'descricao', rotulo: 'Descrição', tipo: 'text', obrigatorio: true },
    { nome: 'valor', rotulo: 'Valor', tipo: 'number', obrigatorio: true },
    { nome: 'frequencia', rotulo: 'Frequência', tipo: 'select', opcoes: FREQUENCIAS },
    { nome: 'inicio', rotulo: 'Início', tipo: 'date' },
    { nome: 'fim', rotulo: 'Fim', tipo: 'date' },
  ],
}

export const DESPESAS: Recurso = {
  path: '/despesas',
  titulo: 'Despesas',
  campos: [
    { nome: 'descricao', rotulo: 'Descrição', tipo: 'text', obrigatorio: true },
    { nome: 'valor', rotulo: 'Valor', tipo: 'number', obrigatorio: true },
    { nome: 'categoria', rotulo: 'Categoria', tipo: 'text' },
    { nome: 'frequencia', rotulo: 'Frequência', tipo: 'select', opcoes: FREQUENCIAS },
    { nome: 'essencial', rotulo: 'Essencial', tipo: 'checkbox' },
  ],
}

export const DIVIDAS: Recurso = {
  path: '/dividas',
  titulo: 'Dívidas',
  campos: [
    { nome: 'credor', rotulo: 'Credor', tipo: 'text', obrigatorio: true },
    { nome: 'saldo', rotulo: 'Saldo', tipo: 'number', obrigatorio: true },
    { nome: 'juros_mensal', rotulo: 'Juros mensais (%)', tipo: 'number' },
    { nome: 'parcela', rotulo: 'Parcela', tipo: 'number' },
    { nome: 'vencimento', rotulo: 'Vencimento', tipo: 'date' },
  ],
}

export const PATRIMONIO: Recurso = {
  path: '/patrimonio',
  titulo: 'Patrimônio',
  campos: [
    { nome: 'tipo', rotulo: 'Tipo', tipo: 'select', opcoes: ['conta', 'investimento', 'bem'] },
    { nome: 'descricao', rotulo: 'Descrição', tipo: 'text', obrigatorio: true },
    { nome: 'valor', rotulo: 'Valor', tipo: 'number', obrigatorio: true },
    { nome: 'data', rotulo: 'Data', tipo: 'date' },
  ],
}

export const METAS: Recurso = {
  path: '/metas',
  titulo: 'Metas',
  campos: [
    { nome: 'titulo', rotulo: 'Título', tipo: 'text', obrigatorio: true },
    { nome: 'valor_alvo', rotulo: 'Valor-alvo', tipo: 'number', obrigatorio: true },
    { nome: 'acumulado', rotulo: 'Acumulado', tipo: 'number' },
    { nome: 'prazo', rotulo: 'Prazo', tipo: 'date' },
    { nome: 'prioridade', rotulo: 'Prioridade (1-5)', tipo: 'number' },
  ],
}

export const NOTAS: Recurso = {
  path: '/notas',
  titulo: 'Notas',
  campos: [
    { nome: 'texto', rotulo: 'Texto', tipo: 'textarea', obrigatorio: true },
    { nome: 'tags', rotulo: 'Tags (separadas por vírgula)', tipo: 'tags' },
  ],
}
