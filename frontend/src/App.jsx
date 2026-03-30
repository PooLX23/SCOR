import { useCallback, useEffect, useState } from 'react'
import { useCallback, useEffect, useState } from 'react'

import { useMsal } from '@azure/msal-react'
import { loginRequest } from './auth/msal'
import ApplicationForm from './components/ApplicationForm'
import { env } from './config/env'

export default function App() {
  const { instance, accounts } = useMsal()
  const [formType, setFormType] = useState('company')

  const account = accounts[0]


  const login = async () => {
    await instance.loginRedirect(loginRequest)
  }

  const logout = async () => {
    await instance.logoutRedirect({ postLogoutRedirectUri: window.location.origin })
  }

  const getAccessToken = useCallback(async () => {
    if (!account) return null
    try {
      const response = await instance.acquireTokenSilent({ ...loginRequest, account })
      return response.accessToken
    } catch (error) {
      const name = error?.name || ''
      if (name.includes('InteractionRequiredAuthError')) {
        await instance.acquireTokenRedirect({ ...loginRequest, account })
        return null
      }
      throw error
    }
  }, [instance, account])


  const loginBgStyle = env.loginBackgroundUrl
    ? { '--login-bg': `url(${env.loginBackgroundUrl})` }
    : {}

  if (!account) {
    return (
      <main className="page page--centered page--login" style={loginBgStyle}>
        <section className="glass-card glass-card--auth">
          <div className="brand-bar" />
          <p className="eyebrow">SCORING • SIXT</p>
          <h1>Panel składania wniosków</h1>
          <p className="muted">
            Zaloguj się kontem służbowym Entra ID, aby złożyć nowy wniosek klienta.
          </p>
          <button className="btn btn--primary" onClick={login}>Zaloguj przez Entra ID</button>
        </section>
      </main>
    )
  }

  return (
    <main className="page page--app">
      <section className="glass-card glass-card--header">
        <div className="header-top">
          <div>
            <div className="brand-bar" />
            <p className="eyebrow">SCORING • SIXT</p>
            <h1>Nowy wniosek scoringowy</h1>
            <p className="muted">Zalogowano jako: <strong>{account.username}</strong></p>
          </div>
          <div className="header-actions">
            {env.appLogoUrl && <img className="app-logo" src={env.appLogoUrl} alt="Logo aplikacji" />}
            <button className="btn btn--ghost" type="button" onClick={logout}>Wyloguj</button>
          </div>

        </div>

        <div className="type-switcher">
          <button
            className={`btn ${formType === 'company' ? 'btn--primary' : 'btn--ghost'}`}
            onClick={() => setFormType('company')}
            type="button"
          >
            Spółka
          </button>
          <button
            className={`btn ${formType === 'individual' ? 'btn--primary' : 'btn--ghost'}`}
            onClick={() => setFormType('individual')}
            type="button"
          >
            Osoba fizyczna / JDG
          </button>
        </div>
      </section>

      <section className="glass-card">
        <TokenForm type={formType} getAccessToken={getAccessToken} />
        <TokenForm type={formType} getAccessToken={getAccessToken} />

      </section>
    </main>
  )
}

function TokenForm({ type, getAccessToken }) {
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchToken = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const t = await getAccessToken()
      setToken(t)
    } catch (err) {
      setToken(null)
      setError(err?.message || 'Nie udało się pobrać tokenu')
    } finally {
      setLoading(false)
    }
  }, [getAccessToken])

  useEffect(() => {
    fetchToken()
  }, [fetchToken])

  if (loading) return <p className="loading">Pobieranie tokenu...</p>

  if (!token) {
    return (
      <div>
        <p className="status">Błąd pobrania tokenu: {error || 'brak tokenu'}</p>
        <button className="btn btn--ghost" type="button" onClick={fetchToken}>Ponów</button>
      </div>
    )
  }


  return <ApplicationForm type={type} token={token} />
}
