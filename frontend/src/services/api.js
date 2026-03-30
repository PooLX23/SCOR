import axios from 'axios'
import { env } from '../config/env'

export async function submitApplication({ token, type, data, files }) {
  const formData = new FormData()
  formData.append('payload', JSON.stringify(data))
  files.forEach((file) => formData.append('files', file))

  const url = `${env.apiBaseUrl}/applications/${type}`
  const response = await axios.post(url, formData, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}
