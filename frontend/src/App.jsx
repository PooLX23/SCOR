import { useEffect, useMemo, useState } from 'react'
import { useMsal } from '@azure/msal-react'
import { loginRequest } from './auth/msal'
import ApplicationForm from './components/ApplicationForm'

export default function App() {
  const { instance, accounts } = useMsal()
  const [formType, setFormType] = useState('company')

  const account = accounts[0]

  const tokenPromise = useMemo(
    () => async () => {
      const response = await instance.acquireTokenSilent({ ...loginRequest, account })
      return response.accessToken
    },
    [instance, account]
  )

  const login = async () => {
    await instance.loginRedirect(loginRequest)
  }

  if (!account) {
    return (
      <main className="page page--centered">
        <section className="premium-card premium-card--auth">
          <div className="brand-bar" />
          <p className="eyebrow">SCOR • SIXT</p>
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
    <main className="page">
      <section className="premium-card premium-card--header">
        <div className="brand-bar" />
        <p className="eyebrow">SCOR • SIXT</p>
        <h1>Nowy wniosek scoringowy</h1>
        <p className="muted">Zalogowano jako: <strong>{account.username}</strong></p>

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

      <section className="premium-card">
        <TokenForm type={formType} tokenPromise={tokenPromise} />
      </section>
    </main>
  )
}

function TokenForm({ type, tokenPromise }) {
  const [token, setToken] = useState(null)

  useEffect(() => {
    tokenPromise().then(setToken).catch(() => setToken(null))
  }, [tokenPromise])

  if (!token) return <p className="loading">Pobieranie tokenu...</p>
  return <ApplicationForm type={type} token={token} />
}
