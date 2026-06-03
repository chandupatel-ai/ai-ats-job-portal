import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API = 'http://127.0.0.1:8000'

export default function Signup() {
  const [form, setForm] = useState({
    name: '', email: '', password: '', role: 'candidate'
  })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSignup = async () => {
    try {
      setError('')
      await axios.post(`${API}/signup`, form)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed')
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h2>Create Account</h2>
        {error && <div className="error">{error}</div>}
        <input
          placeholder="Full Name"
          value={form.name}
          onChange={e => setForm({...form, name: e.target.value})}
        />
        <input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={e => setForm({...form, email: e.target.value})}
        />
        <input
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={e => setForm({...form, password: e.target.value})}
        />
        <select
          value={form.role}
          onChange={e => setForm({...form, role: e.target.value})}
        >
          <option value="candidate">Candidate</option>
          <option value="recruiter">Recruiter</option>
        </select>
        <button onClick={handleSignup}>Create Account</button>
        <p>
          Already have an account?{' '}
          <a onClick={() => navigate('/login')}>Login</a>
        </p>
      </div>
    </div>
  )
}