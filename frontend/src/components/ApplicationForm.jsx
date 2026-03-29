import { useState } from 'react'
import { submitApplication } from '../services/api'

const baseDefaults = {
  nip: '',
  business_line: 'ST',
  car_model: '',
  rent_amount: '',
  deposit_amount: '',
  vehicle_value: '',
  initial_fee: '',
  car_group: '',
  car_segment: 'standard',
  rental_period_months: ''
}

export default function ApplicationForm({ type, token }) {
  const [form, setForm] = useState(
    type === 'company'
      ? { ...baseDefaults, company_name: '', krs: '' }
      : { ...baseDefaults, customer_name: '', pesel: '', document_number: '' }
  )
  const [files, setFiles] = useState([])
  const [status, setStatus] = useState('')

  const onChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const onSubmit = async (e) => {
    e.preventDefault()
    setStatus('Wysyłanie...')
    try {
      const payload = {
        ...form,
        rent_amount: Number(form.rent_amount),
        deposit_amount: Number(form.deposit_amount),
        vehicle_value: Number(form.vehicle_value),
        initial_fee: Number(form.initial_fee),
        rental_period_months: Number(form.rental_period_months)
      }
      const result = await submitApplication({ token, type, data: payload, files })
      setStatus(`Wysłano. ID wniosku: ${result.id}`)
    } catch (error) {
      setStatus(`Błąd: ${error?.response?.data?.detail || error.message}`)
    }
  }

  return (
    <form onSubmit={onSubmit}>
      {type === 'company' ? (
        <>
          <input required name="company_name" placeholder="Nazwa spółki" onChange={onChange} />
          <input required name="krs" placeholder="KRS" onChange={onChange} />
        </>
      ) : (
        <>
          <input required name="customer_name" placeholder="Nazwa klienta" onChange={onChange} />
          <input required name="pesel" placeholder="PESEL" onChange={onChange} />
          <input required name="document_number" placeholder="Numer dokumentu" onChange={onChange} />
        </>
      )}

      <input required name="nip" placeholder="NIP" onChange={onChange} />
      <select required name="business_line" onChange={onChange} defaultValue="ST">
        {['ST', 'LT', 'AA', 'CFM', 'LOP'].map((v) => (
          <option value={v} key={v}>{v}</option>
        ))}
      </select>
      <input required name="car_model" placeholder="Samochód" onChange={onChange} />
      <input required type="number" step="0.01" name="rent_amount" placeholder="Wysokość czynszu" onChange={onChange} />
      <input required type="number" step="0.01" name="deposit_amount" placeholder="Kwota depozytu" onChange={onChange} />
      <input required type="number" step="0.01" name="vehicle_value" placeholder="Wartość pojazdu" onChange={onChange} />
      <input required type="number" step="0.01" name="initial_fee" placeholder="Opłata wstępna" onChange={onChange} />
      <input required name="car_group" placeholder="Grupa samochodu" onChange={onChange} />
      <select required name="car_segment" onChange={onChange} defaultValue="standard">
        <option value="standard">standard</option>
        <option value="premium">premium</option>
      </select>
      <input required type="number" name="rental_period_months" placeholder="Okres wynajmu (miesiące)" onChange={onChange} />

      <input required type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
      <button type="submit">Zapisz wniosek</button>
      <p>{status}</p>
    </form>
  )
}
