import React from 'react'
import ReactDOM from 'react-dom/client'
import { MsalProvider } from '@azure/msal-react'
import App from './App'
import { msalInstance } from './auth/msal'
import './styles.css'

async function bootstrap() {
  await msalInstance.initialize()
  const redirectResult = await msalInstance.handleRedirectPromise()

  if (redirectResult?.account) {
    msalInstance.setActiveAccount(redirectResult.account)
  } else {
    const fallbackAccount = msalInstance.getActiveAccount() || msalInstance.getAllAccounts()[0]
    if (fallbackAccount) {
      msalInstance.setActiveAccount(fallbackAccount)
    }
  }

  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  )
}

bootstrap().catch((error) => {
  console.error('MSAL bootstrap error:', error)
})
