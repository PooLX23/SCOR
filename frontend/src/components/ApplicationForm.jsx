import { useEffect, useMemo, useState } from 'react'
import { submitApplication } from '../services/api'

const vehicleDefaults = {
  business_line: 'ST',
  car_make: '',
  car_model: '',
  rent_amount: '',
  deposit_amount: '',
  vehicle_value: '',
  initial_fee: '',
  car_group: '',
  car_class: 'standard',
  rental_period_months: ''
}

const createVehicle = () => ({ ...vehicleDefaults })

export default function ApplicationForm({ type, token }) {
  const [main, setMain] = useState(
    type === 'company'
      ? { company_name: '', nip: '', krs: '' }
      : { customer_name: '', pesel: '', nip: '', document_number: '' }
  )
  const [vehicles, setVehicles] = useState([createVehicle()])
  const [files, setFiles] = useState([])
  const [status, setStatus] = useState('')

  useEffect(() => {
    setMain(type === 'company' ? { company_name: '', nip: '', krs: '' } : { customer_name: '', pesel: '', nip: '', document_number: '' })
    setVehicles([createVehicle()])
    setFiles([])
    setStatus('')
  }, [type])

  const totals = useMemo(() => {
    const numeric = (v) => Number(v || 0)
    return {
      rent: vehicles.reduce((sum, row) => sum + numeric(row.rent_amount), 0),
      deposit: vehicles.reduce((sum, row) => sum + numeric(row.deposit_amount), 0),
      value: vehicles.reduce((sum, row) => sum + numeric(row.vehicle_value), 0),
      initial: vehicles.reduce((sum, row) => sum + numeric(row.initial_fee), 0)
    }
  }, [vehicles])

  const onMainChange = (e) => setMain((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const onVehicleChange = (index, name, value) => {
    setVehicles((prev) => prev.map((row, idx) => (idx === index ? { ...row, [name]: value } : row)))
  }

  const addVehicle = () => setVehicles((prev) => [...prev, createVehicle()])
  const removeVehicle = (index) => setVehicles((prev) => prev.filter((_, idx) => idx !== index))

  const onSubmit = async (e) => {
    e.preventDefault()
    setStatus('Wysyłanie...')
    try {
      const payload = {
        ...main,
        vehicles: vehicles.map((row) => ({
          ...row,
          rent_amount: Number(row.rent_amount),
          deposit_amount: Number(row.deposit_amount),
          vehicle_value: Number(row.vehicle_value),
          initial_fee: Number(row.initial_fee),
          rental_period_months: Number(row.rental_period_months)
        }))
      }

      const result = await submitApplication({ token, type, data: payload, files })
      setStatus(`Wysłano. ID: ${result.id}`)
    } catch (error) {
      setStatus(`Błąd: ${error?.response?.data?.detail || error.message}`)
    }
  }

  return (
    <form onSubmit={onSubmit} className="application-form">
      <h2>{type === 'company' ? 'Sekcja 1: Dane spółki i załączniki' : 'Sekcja 1: Dane klienta i załączniki'}</h2>

      <div className="form-grid">
        {type === 'company' ? (
          <>
            <Field name="company_name" label="Nazwa spółki" value={main.company_name} onChange={onMainChange} />
            <Field name="nip" label="NIP" value={main.nip} minLength={10} maxLength={20} onChange={onMainChange} />
            <Field name="krs" label="KRS" value={main.krs} onChange={onMainChange} />
          </>
        ) : (
          <>
            <Field name="customer_name" label="Nazwa klienta" value={main.customer_name} onChange={onMainChange} />
            <Field name="pesel" label="PESEL" value={main.pesel} minLength={11} maxLength={11} onChange={onMainChange} />
            <Field name="nip" label="NIP" value={main.nip} minLength={10} maxLength={20} onChange={onMainChange} />
            <Field name="document_number" label="Numer dokumentu" value={main.document_number} onChange={onMainChange} />
          </>
        )}
      </div>

      <label className="file-input">
        Załączniki
        <input required type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
      </label>

      <div className="section-divider" />
      <h2>Sekcja 2: Pojazdy</h2>

      {vehicles.map((vehicle, index) => (
        <div className="vehicle-card" key={`vehicle-${index}`}>
          <div className="vehicle-header">
            <strong>Pojazd #{index + 1}</strong>
            {vehicles.length > 1 && (
              <button type="button" className="btn btn--ghost btn--small" onClick={() => removeVehicle(index)}>
                Usuń
              </button>
            )}
          </div>

          <div className="form-grid">
            <label>
              Linia biznesowa
              <select required value={vehicle.business_line} onChange={(e) => onVehicleChange(index, 'business_line', e.target.value)}>
                {['ST', 'LT', 'AA', 'CFM', 'LOP'].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </label>

            <Field label="Marka" value={vehicle.car_make} onChange={(e) => onVehicleChange(index, 'car_make', e.target.value)} />
            <Field label="Model" value={vehicle.car_model} onChange={(e) => onVehicleChange(index, 'car_model', e.target.value)} />
            <Field type="number" step="0.01" label="Wysokość czynszu" value={vehicle.rent_amount} onChange={(e) => onVehicleChange(index, 'rent_amount', e.target.value)} />
            <Field type="number" step="0.01" label="Kwota depozytu" value={vehicle.deposit_amount} onChange={(e) => onVehicleChange(index, 'deposit_amount', e.target.value)} />
            <Field type="number" step="0.01" label="Wartość pojazdu" value={vehicle.vehicle_value} onChange={(e) => onVehicleChange(index, 'vehicle_value', e.target.value)} />
            <Field type="number" step="0.01" label="Opłata wstępna" value={vehicle.initial_fee} onChange={(e) => onVehicleChange(index, 'initial_fee', e.target.value)} />
            <Field label="Grupa samochodu" value={vehicle.car_group} onChange={(e) => onVehicleChange(index, 'car_group', e.target.value)} />

            <label>
              Klasa samochodu
              <select required value={vehicle.car_class} onChange={(e) => onVehicleChange(index, 'car_class', e.target.value)}>
                <option value="standard">standard</option>
                <option value="premium">premium</option>
              </select>
            </label>

            <Field type="number" label="Okres wynajmu (miesiące)" value={vehicle.rental_period_months} onChange={(e) => onVehicleChange(index, 'rental_period_months', e.target.value)} />
          </div>
        </div>
      ))}

      <button type="button" className="btn btn--ghost" onClick={addVehicle}>+ Dodaj pojazd</button>

      <div className="totals-grid">
        <ReadOnlyField label="Suma czynszu" value={totals.rent.toFixed(2)} />
        <ReadOnlyField label="Suma depozytu" value={totals.deposit.toFixed(2)} />
        <ReadOnlyField label="Suma wartości pojazdów" value={totals.value.toFixed(2)} />
        <ReadOnlyField label="Suma opłat wstępnych" value={totals.initial.toFixed(2)} />
      </div>

      <button className="btn btn--primary" type="submit">Zapisz wniosek</button>
      {status && <p className="status">{status}</p>}
    </form>
  )
}

function Field({ name, label, type = 'text', step, value, onChange, ...rest }) {
  return (
    <label>
      {label}
      <input required name={name} type={type} step={step} value={value} onChange={onChange} {...rest} />
    </label>
  )
}

function ReadOnlyField({ label, value }) {
  return (
    <label>
      {label}
      <input value={value} readOnly />
    </label>
  )
}
