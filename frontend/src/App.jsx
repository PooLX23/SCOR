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
      <main>
        <h1>SCOR — logowanie pracownika</h1>
        <button onClick={login}>Zaloguj przez Entra ID</button>
      </main>
    )
  }

  return (
    <main>
      <h1>Nowy wniosek</h1>
      <p>Zalogowano jako: {account.username}</p>
      <label>
        Typ formularza:
        <select value={formType} onChange={(e) => setFormType(e.target.value)}>
          <option value="company">Spółka</option>
          <option value="individual">Osoba fizyczna / JDG</option>
        </select>
      </label>
      <TokenForm type={formType} tokenPromise={tokenPromise} />
    </main>
  )
}

function TokenForm({ type, tokenPromise }) {
  const [token, setToken] = useState(null)

  useEffect(() => {
    tokenPromise().then(setToken).catch(() => setToken(null))
  }, [tokenPromise])

  if (!token) return <p>Pobieranie tokenu...</p>
  return <ApplicationForm type={type} token={token} />
}
