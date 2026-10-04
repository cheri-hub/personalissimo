import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { Login } from './pages/Login'

function Rotas() {
  const { token } = useAuth()
  if (!token) return <Login />
  return <p>Autenticado</p>
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
