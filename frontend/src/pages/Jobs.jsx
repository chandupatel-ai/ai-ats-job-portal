import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API = 'http://127.0.0.1:8000'

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const res = await axios.get(`${API}/jobs`)
      setJobs(res.data.jobs)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.clear()
    navigate('/login')
  }

  return (
    <div>
      <div className="navbar">
        <h1>🎯 AI ATS Portal</h1>
        <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
          <span>Hi, {user.name}!</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <div className="container">
        <h2 style={{margin: '20px 0'}}>Available Jobs ({jobs.length})</h2>

        {loading ? (
          <div className="loading">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="loading">No jobs available yet.</div>
        ) : (
          <div className="jobs-grid">
            {jobs.map(job => (
              <div key={job.id} className="job-card">
                <h3>{job.title}</h3>
                <div className="company">🏢 {job.company}</div>
                <div className="location">📍 {job.location}</div>
                <div className="salary">💰 {job.salary}</div>
                <div className="skills">
                  🛠️ {job.required_skills}
                </div>
                <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '15px'}}>
                  {job.description.substring(0, 100)}...
                </p>
                <button onClick={() => navigate(`/ats/${job.id}`)}>
                  Check ATS Score
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}