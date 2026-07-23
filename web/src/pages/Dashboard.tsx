import { useEffect, useState } from 'react'
import { TrendingDown, DollarSign, Zap } from 'lucide-react'

interface Stats {
  summary: {
    total_calls: number
    total_tokens: number
    total_cost: number
    by_provider: any[]
    by_model: any[]
    by_operation: any[]
  }
  recommendations: any[]
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-white">Loading statistics...</div>
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Tokens</p>
              <p className="text-white text-2xl font-bold">{stats?.summary.total_tokens.toLocaleString()}</p>
            </div>
            <Zap className="text-yellow-500" size={32} />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Cost</p>
              <p className="text-white text-2xl font-bold">${stats?.summary.total_cost.toFixed(2)}</p>
            </div>
            <DollarSign className="text-green-500" size={32} />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">API Calls</p>
              <p className="text-white text-2xl font-bold">{stats?.summary.total_calls}</p>
            </div>
            <TrendingDown className="text-blue-500" size={32} />
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {stats?.recommendations && stats.recommendations.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">Cost Optimization Tips</h2>
          <div className="space-y-4">
            {stats.recommendations.map((rec, idx) => (
              <div key={idx} className="bg-slate-700 rounded p-4">
                <h3 className="text-white font-semibold">{rec.title}</h3>
                <p className="text-slate-300 text-sm mt-2">{rec.description}</p>
                <p className="text-green-400 text-sm mt-2">💰 Save ~${rec.estimated_savings.toFixed(2)}/month</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
