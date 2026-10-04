import { BrowserRouter, Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { Config } from './pages/Config'
import { Financas } from './pages/Financas'
import { Historico } from './pages/Historico'
import { Login } from './pages/Login'
import { Metas } from './pages/Metas'
import { Notas } from './pages/Notas'
import { Painel } from './pages/Painel'
import { Perguntar } from './pages/Perguntar'

const LINKS: [string, string][] = [
  ['/', 'Painel'],
  ['/perguntar', 'Perguntar'],
  ['/financas', 'Finanças'],
  ['/metas', 'Metas'],
  ['/notas', 'Notas'],
  ['/historico', 'Histórico'],
  ['/config', 'Configurações'],
]

function Rotas() {
  const { token, sair } = useAuth()
  if (!token) return <Login />
  return (
    <>
      <nav>
        {LINKS.map(([para, rotulo]) => (
          <NavLink key={para} to={para} end={para === '/'} className={({ isActive }) => (isActive ? 'ativo' : '')}>
            {rotulo}
          </NavLink>
        ))}
        <button type="button" className="link" onClick={sair}>Sair</button>
      </nav>
      <Routes>
        <Route path="/" element={<Painel />} />
        <Route path="/perguntar" element={<Perguntar />} />
        <Route path="/financas" element={<Financas />} />
        <Route path="/metas" element={<Metas />} />
        <Route path="/notas" element={<Notas />} />
        <Route path="/historico" element={<Historico />} />
        <Route path="/config" element={<Config />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Rotas />
      </BrowserRouter>
    </AuthProvider>
  )
}
