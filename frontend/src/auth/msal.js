import { PublicClientApplication } from '@azure/msal-browser'
import { env } from '../config/env'

export const msalInstance = new PublicClientApplication({
  auth: {
    clientId: env.clientId,
    authority: `https://login.microsoftonline.com/${env.tenantId}`,
    redirectUri: window.location.origin
  },
  cache: { cacheLocation: 'sessionStorage' }
})

export const loginRequest = {
  scopes: ['openid', 'profile', 'email', env.apiScope]
}
