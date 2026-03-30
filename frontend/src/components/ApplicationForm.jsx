import { useEffect, useState } from 'react'
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

  useEffect(() => {
    setForm(
      type === 'company'
        ? { ...baseDefaults, company_name: '', krs: '' }
        : { ...baseDefaults, customer_name: '', pesel: '', document_number: '' }
    )
    setFiles([])
    setStatus('')
  }, [type])

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
    <form onSubmit={onSubmit} className="application-form">
      <h2>{type === 'company' ? 'Formularz spółki' : 'Formularz osoby fizycznej / JDG'}</h2>

      <div className="form-grid">
        {type === 'company' ? (
          <>
            <Field name="company_name" placeholder="Nazwa spółki" onChange={onChange} />
            <Field name="krs" placeholder="KRS" onChange={onChange} />
          </>
        ) : (
          <>
            <Field name="customer_name" placeholder="Nazwa klienta" onChange={onChange} />
            <Field name="pesel" placeholder="PESEL" onChange={onChange} />
            <Field name="document_number" placeholder="Numer dokumentu" onChange={onChange} />
          </>
        )}

        <Field name="nip" placeholder="NIP" minLength={10} maxLength={20} onChange={onChange} />

        <label>
          Linia biznesowa
          <select required name="business_line" onChange={onChange} defaultValue="ST">
            {['ST', 'LT', 'AA', 'CFM', 'LOP'].map((v) => (
              <option value={v} key={v}>{v}</option>
            ))}
          </select>
        </label>

        <Field name="car_model" placeholder="Samochód" onChange={onChange} />
        <Field name="rent_amount" type="number" step="0.01" placeholder="Wysokość czynszu" onChange={onChange} />
        <Field name="deposit_amount" type="number" step="0.01" placeholder="Kwota depozytu" onChange={onChange} />
        <Field name="vehicle_value" type="number" step="0.01" placeholder="Wartość pojazdu" onChange={onChange} />
        <Field name="initial_fee" type="number" step="0.01" placeholder="Opłata wstępna" onChange={onChange} />
        <Field name="car_group" placeholder="Grupa samochodu" onChange={onChange} />

        <label>
          Segment samochodu
          <select required name="car_segment" onChange={onChange} defaultValue="standard">
            <option value="standard">standard</option>
            <option value="premium">premium</option>
          </select>
        </label>

        <Field name="rental_period_months" type="number" placeholder="Okres wynajmu (miesiące)" onChange={onChange} />
      </div>

      <label className="file-input">
        Załączniki (wiele plików)
        <input required type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
      </label>

      <button className="btn btn--primary" type="submit">Zapisz wniosek</button>
      {status && <p className="status">{status}</p>}
    </form>
  )
}

function Field({ name, placeholder, type = 'text', step, onChange, ...rest }) {
  return (
    <label>
      {placeholder}
      <input required name={name} type={type} step={step} placeholder={placeholder} onChange={onChange} {...rest} />
    </label>
  )
}
