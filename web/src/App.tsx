import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Process from './pages/Process'
import Settings from './pages/Settings'
import Onboarding from './pages/Onboarding'

function App() {
  const [isFirstVisit, setIsFirstVisit] = useState(false)
  const [apiReady, setApiReady] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user has visited before
    const visited = localStorage.getItem('token-optimizer-visited')
    if (!visited) {
      setIsFirstVisit(true)
      localStorage.setItem('token-optimizer-visited', 'true')
    }

    // Check API health
    fetch('http://localhost:5000/health')
      .then(() => {
        setApiReady(true)
        setLoading(false)
      })
      .catch((err) => {
        console.error('API health check failed:', err)
        setApiReady(false)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', backgroundColor: '#1e293b', color: 'white' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px' }}>Loading...</div>
        </div>
      </div>
    )
  }

  if (isFirstVisit) {
    return <Onboarding onComplete={() => setIsFirstVisit(false)} />
  }

  if (!apiReady) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', backgroundColor: '#1e293b', color: 'white' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px' }}>Connecting to server...</div>
          <div style={{ color: '#94a3b8' }}>Make sure Flask backend is running on port 5000</div>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div style={{ minHeight: '100vh', backgroundColor: '#0f172a', backgroundImage: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/process" element={<Process />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
