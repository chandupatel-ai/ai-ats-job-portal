import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

const API = 'http://127.0.0.1:8000'

export default function ATSScore() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [resume, setResume] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleScore = async () => {
    if (!resume.trim()) {
      setError('Please paste your resume text')
      return
    }
    try {
      setError('')
      setLoading(true)
      const res = await axios.post(`${API}/ats/score`, {
        resume_text: resume,
        job_id: parseInt(jobId)
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Scoring failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="navbar">
        <h1>🎯 AI ATS Portal</h1>
        <button onClick={() => navigate('/jobs')}>← Back to Jobs</button>
      </div>

      <div className="ats-container">
        {!result ? (
          <div className="score-card">
            <h2 style={{marginBottom: '20px'}}>Check Your ATS Score</h2>
            {error && <div className="error">{error}</div>}
            <p style={{marginBottom: '10px', color: '#666'}}>
              Paste your resume text below:
            </p>
            <textarea
              className="textarea-box"
              placeholder="Paste your resume here..."
              value={resume}
              onChange={e => setResume(e.target.value)}
            />
            <button
              className="btn-primary"
              onClick={handleScore}
              disabled={loading}
            >
              {loading ? '⏳ Analyzing...' : '🚀 Analyze My Resume'}
            </button>
          </div>
        ) : (
          <>
            <div className="score-card">
              <div className="score-number">{result.match_score}%</div>
              <div className="score-label">
                ATS Match Score for {result.job_title} at {result.company}
              </div>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{width: `${result.match_score}%`}}
                />
              </div>
              <p style={{color: '#555', lineHeight: '1.6'}}>
                {result.summary}
              </p>
            </div>

            <div className="score-card">
              <div className="skills-section">
                <h3>✅ Matched Skills</h3>
                <div className="skill-tags">
                  {result.matched_skills.map((s, i) => (
                    <span key={i} className="skill-tag matched">{s}</span>
                  ))}
                </div>

                <h3>❌ Missing Skills</h3>
                <div className="skill-tags">
                  {result.missing_skills.length === 0 ? (
                    <span className="skill-tag matched">No missing skills!</span>
                  ) : (
                    result.missing_skills.map((s, i) => (
                      <span key={i} className="skill-tag missing">{s}</span>
                    ))
                  )}
                </div>

                <h3>💪 Strengths</h3>
                <ul style={{paddingLeft: '20px', marginBottom: '15px'}}>
                  {result.strengths.map((s, i) => (
                    <li key={i} style={{marginBottom: '5px', color: '#555'}}>{s}</li>
                  ))}
                </ul>

                <h3>🎯 Improvements</h3>
                <ul style={{paddingLeft: '20px'}}>
                  {result.improvements.map((s, i) => (
                    <li key={i} style={{marginBottom: '5px', color: '#555'}}>{s}</li>
                  ))}
                </ul>
              </div>
            </div>

            <button
              className="btn-primary"
              onClick={() => setResult(null)}
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  )
}