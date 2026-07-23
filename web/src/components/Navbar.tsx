import { Link } from 'react-router-dom'
import { Zap, Settings } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="bg-slate-900 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2">
          <Zap className="text-blue-500" size={28} />
          <span className="text-white text-xl font-bold">Token Optimizer</span>
        </Link>

        <div className="flex gap-6">
          <Link to="/" className="text-slate-300 hover:text-white transition">Dashboard</Link>
          <Link to="/process" className="text-slate-300 hover:text-white transition">Process</Link>
          <Link to="/settings" className="text-slate-300 hover:text-white transition">
            <Settings size={20} />
          </Link>
        </div>
      </div>
    </nav>
  )
}
