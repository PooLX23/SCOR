import axios from 'axios'
import { env } from '../config/env'

function authHeader(token) {
  return { Authorization: `Bearer ${token}` }
}

export async function submitApplication({ token, type, data, files }) {
  const formData = new FormData()
  formData.append('payload', JSON.stringify(data))
  files.forEach((file) => formData.append('files', file))

  const url = `${env.apiBaseUrl}/applications/${type}`
  const response = await axios.post(url, formData, {
    headers: authHeader(token)
  })
  return response.data
}

export async function fetchCarGroups(token) {
  const url = `${env.apiBaseUrl}/applications/car-groups`
  const response = await axios.get(url, {
    headers: authHeader(token)
  })
  return response.data?.items || []
}

export async function fetchMe(token) {
  const response = await axios.get(`${env.apiBaseUrl}/applications/me`, {
    headers: authHeader(token)
  })
  return response.data
}

export async function fetchMyApplications(token) {
  const response = await axios.get(`${env.apiBaseUrl}/applications/my`, {
    headers: authHeader(token)
  })
  return response.data?.items || []
}

export async function fetchAllApplications(token) {
  const response = await axios.get(`${env.apiBaseUrl}/applications/all`, {
    headers: authHeader(token)
  })
  return response.data?.items || []
}

export async function fetchApplicationDetails(token, applicationId) {
  const response = await axios.get(`${env.apiBaseUrl}/applications/${applicationId}`, {
    headers: authHeader(token)
  })
  return response.data
}


export async function fetchCarBrands(token, q = '') {
  const response = await axios.get(`${env.apiBaseUrl}/applications/car-brands`, {
    headers: authHeader(token),
    params: { q }
  })
  return response.data?.items || []
}

export async function fetchCarModels(token, q = '', brand = '') {
  const response = await axios.get(`${env.apiBaseUrl}/applications/car-models`, {
    headers: authHeader(token),
    params: { q, brand }
  })
  return response.data?.items || []
}

export async function fetchBrandForModel(token, model) {
  const response = await axios.get(`${env.apiBaseUrl}/applications/car-brand-for-model`, {
    headers: authHeader(token),
    params: { model }
  })
  return response.data?.brand || null
}
