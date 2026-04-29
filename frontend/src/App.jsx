import { useCallback, useEffect, useState } from 'react'
import { useMsal } from '@azure/msal-react'
import { loginRequest } from './auth/msal'
import ApplicationForm from './components/ApplicationForm'
import { env } from './config/env'
import {
  fetchAllApplications,
  fetchApplicationDetails,
  fetchCollectionPreview,
  fetchMe,
  fetchMyApplications,
  saveCollectionDecision,
} from './services/api'

export default function App() {
  const { instance, accounts } = useMsal()
  const [formType, setFormType] = useState('company')
  const [activeTab, setActiveTab] = useState('new')
  const tabHeaderTitles = {
    new: 'Nowy wniosek scoringowy',
    my: 'Moje wnioski',
    verify: 'Weryfikacja wniosków',
    collection: 'Windykacja',
  }

  const account = accounts[0] || instance.getActiveAccount()

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
            <h1>{tabHeaderTitles[activeTab] || tabHeaderTitles.new}</h1>
            <p className="muted">Zalogowano jako: <strong>{account.username}</strong></p>
          </div>
          <div className="header-actions">
            {env.appLogoUrl && <img className="app-logo" src={env.appLogoUrl} alt="Logo aplikacji" />}
            <button className="btn btn--ghost" type="button" onClick={logout}>Wyloguj</button>
          </div>
        </div>
      </section>

      <section className="glass-card">
        <TokenGate
          getAccessToken={getAccessToken}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          formType={formType}
          setFormType={setFormType}
        />
      </section>
    </main>
  )
}

function TokenGate({ getAccessToken, activeTab, setActiveTab, formType, setFormType }) {
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

  return (
    <ApplicationsPanel
      token={token}
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      formType={formType}
      setFormType={setFormType}
    />
  )
}

function ApplicationsPanel({ token, activeTab, setActiveTab, formType, setFormType }) {
  const [profile, setProfile] = useState({ user: '', is_reviewer: false, is_collection: false })
  const [myItems, setMyItems] = useState([])
  const [allItems, setAllItems] = useState([])
  const [details, setDetails] = useState(null)
  const [collectionPreview, setCollectionPreview] = useState(null)
  const [collectionLoading, setCollectionLoading] = useState(false)
  const [collectionDecision, setCollectionDecision] = useState('pozytywna')
  const [collectionComment, setCollectionComment] = useState('')

  const loadMy = useCallback(() => fetchMyApplications(token).then(setMyItems), [token])
  const loadAll = useCallback(() => fetchAllApplications(token).then(setAllItems), [token])

  useEffect(() => {
    fetchMe(token).then(setProfile)
    loadMy()
  }, [token, loadMy])

  useEffect(() => {
    if (profile.is_collection) {
      setActiveTab('collection')
    }
  }, [profile.is_collection, setActiveTab])

  useEffect(() => {
    if (profile.is_reviewer && activeTab === 'verify') {
      loadAll()
    }
    if (profile.is_collection && activeTab === 'collection') {
      loadAll()
    }
  }, [profile.is_reviewer, profile.is_collection, activeTab, loadAll])

  const openDetails = async (id) => {
    setCollectionLoading(false)
    const row = await fetchApplicationDetails(token, id)
    setDetails(row)
    if (profile.is_collection && activeTab === 'collection' && !row.collection_decision) {
      setCollectionLoading(true)
      const preview = await fetchCollectionPreview(token, id)
      setCollectionPreview(preview)
      setCollectionLoading(false)
    } else {
      setCollectionPreview(null)
    }
  }

  const submitCollectionDecision = async () => {
    if (!details || !collectionPreview) return
    await saveCollectionDecision(token, details.id, {
      decision: collectionDecision,
      comment: collectionComment,
      avg_days_past_due: collectionPreview.avg_days_past_due,
      deposits_aa_cfm_rac: collectionPreview.deposits_aa_cfm_rac,
      deposits_orders: collectionPreview.deposits_orders,
      source_position: collectionPreview.position,
    })
    await loadAll()
    const refreshed = await fetchApplicationDetails(token, details.id)
    setDetails(refreshed)
    setCollectionPreview(null)
  }

  return (
    <div className="panel-grid">
      <div className="tabs" role="tablist" aria-label="Sekcje aplikacji">
        {!profile.is_collection && (
          <>
            <button
              className={`tab ${activeTab === 'new' ? 'tab--active' : ''}`}
              type="button"
              role="tab"
              aria-selected={activeTab === 'new'}
              onClick={() => setActiveTab('new')}
            >
              Nowy wniosek
            </button>
            <button
              className={`tab ${activeTab === 'my' ? 'tab--active' : ''}`}
              type="button"
              role="tab"
              aria-selected={activeTab === 'my'}
              onClick={() => setActiveTab('my')}
            >
              Moje wnioski
            </button>
          </>
        )}
        {profile.is_reviewer && !profile.is_collection && (
          <button
            className={`tab ${activeTab === 'verify' ? 'tab--active' : ''}`}
            type="button"
            role="tab"
            aria-selected={activeTab === 'verify'}
            onClick={() => setActiveTab('verify')}
          >
            Weryfikacja
          </button>
        )}
        {profile.is_collection && (
          <button className={`tab ${activeTab === 'collection' ? 'tab--active' : ''}`} type="button" role="tab" aria-selected={activeTab === 'collection'} onClick={() => setActiveTab('collection')}>Windykacja</button>
        )}
      </div>

      {activeTab === 'new' && !profile.is_collection && (
        <>
          <div className="type-switcher">
            <button className={`btn ${formType === 'company' ? 'btn--primary' : 'btn--ghost'}`} onClick={() => setFormType('company')} type="button">Spółka</button>
            <button className={`btn ${formType === 'individual' ? 'btn--primary' : 'btn--ghost'}`} onClick={() => setFormType('individual')} type="button">Osoba fizyczna / JDG</button>
          </div>
          <ApplicationForm type={formType} token={token} />
        </>
      )}

      {activeTab === 'my' && (
        <ApplicationsTable title="Moje wnioski" items={myItems} onOpen={openDetails} />
      )}

      {activeTab === 'verify' && profile.is_reviewer && (
        <ApplicationsTable title="Wszystkie wnioski" items={allItems} onOpen={openDetails} />
      )}

      {activeTab === 'collection' && profile.is_collection && (
        <ApplicationsTable title="Wszystkie wnioski" items={allItems} onOpen={openDetails} />
      )}

      {details && (
        <div className="details-card">
          <h3>Szczegóły wniosku #{details.id}</h3>
          <p>Status: <strong>{details.status}</strong></p>
          <p>Decyzja windykacji: <strong>{details.collection_decision || '-'}</strong></p>
          <p>Użytkownik: {details.submitted_by}</p>
          <p>Typ: {details.applicant_type}</p>
          <p>Liczba pojazdów: {details.total_vehicle_count}</p>
          {activeTab === 'collection' && profile.is_collection && collectionLoading && (
            <div>
              <p>Ładowanie danych windykacyjnych...</p>
              <progress />
            </div>
          )}
          {activeTab === 'collection' && profile.is_collection && !collectionLoading && (collectionPreview || details.collection_snapshot) && (
            <div>
              <p>Średnia Dni Po Terminie Płatności: <strong>{Number((collectionPreview || details.collection_snapshot).avg_days_past_due || 0).toFixed(2)}</strong></p>
              <p>Depozyty AA/CFM/RAC: <strong>{Number((collectionPreview || details.collection_snapshot).deposits_aa_cfm_rac || 0).toFixed(2)}</strong></p>
              <p>Depozyty Orders (status=2): <strong>{Number((collectionPreview || details.collection_snapshot).deposits_orders || 0).toFixed(2)}</strong></p>
              {!details.collection_decision && (
                <>
                  <label>Decyzja Windykacji
                    <select value={collectionDecision} onChange={(e) => setCollectionDecision(e.target.value)}>
                      <option value="pozytywna">pozytywna</option>
                      <option value="negatywna">negatywna</option>
                    </select>
                  </label>
                  <label>Komentarz
                    <input value={collectionComment} onChange={(e) => setCollectionComment(e.target.value)} />
                  </label>
                  <button className="btn btn--primary" type="button" onClick={submitCollectionDecision}>Zapisz decyzję</button>
                </>
              )}
            </div>
          )}
          <button className="btn btn--ghost" type="button" onClick={() => setDetails(null)}>Zamknij</button>
        </div>
      )}
    </div>
  )
}

function ApplicationsTable({ title, items, onOpen }) {
  return (
    <div>
      <h3>{title}</h3>
      <table className="apps-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Data</th>
            <th>Status</th>
            <th>Wnioskodawca</th>
            <th>Decyzja windykacji</th>
            <th>Akcja</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{new Date(item.created_at).toLocaleString()}</td>
              <td>{item.status}</td>
              <td>{item.company_name || item.customer_name || item.submitted_by}</td>
              <td>{item.collection_decision === 'pozytywna' ? '✅' : item.collection_decision === 'negatywna' ? '❌' : '-'}</td>
              <td><button className="btn btn--ghost btn--small" type="button" onClick={() => onOpen(item.id)}>Szczegóły</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
