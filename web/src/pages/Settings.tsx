import { useState, useEffect } from 'react'
import { Save } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    provider: 'claude',
    model: 'claude-3-5-haiku-20241022',
    quality_level: 'balanced',
    caching_enabled: true,
    tracking_enabled: true
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/settings')
      const data = await response.json()
      setSettings(data)
    } catch (error) {
      console.error('Failed to fetch settings:', error)
    }
  }

  const handleSave = async () => {
    try {
      await fetch('http://localhost:5000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Settings</h1>

      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 space-y-6">
        {/* Provider */}
        <div>
          <label className="block text-white font-semibold mb-2">AI Provider</label>
          <select
            value={settings.provider}
            onChange={(e) => setSettings({...settings, provider: e.target.value})}
            className="w-full bg-slate-700 text-white rounded-lg p-3 border border-slate-600 focus:border-blue-500 outline-none"
          >
            <option value="claude">Claude (Anthropic)</option>
            <option value="openai">OpenAI</option>
            <option value="gemini">Gemini (Google)</option>
            <option value="ollama">Ollama (Local)</option>
          </select>
        </div>

        {/* Quality Level */}
        <div>
          <label className="block text-white font-semibold mb-4">Quality Level</label>
          <div className="flex gap-4">
            {['budget', 'balanced', 'premium'].map(level => (
              <label key={level} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value={level}
                  checked={settings.quality_level === level}
                  onChange={(e) => setSettings({...settings, quality_level: e.target.value})}
                  className="w-4 h-4"
                />
                <span className="text-white capitalize">{level}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.caching_enabled}
              onChange={(e) => setSettings({...settings, caching_enabled: e.target.checked})}
              className="w-4 h-4"
            />
            <span className="text-white">Enable Local Caching</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.tracking_enabled}
              onChange={(e) => setSettings({...settings, tracking_enabled: e.target.checked})}
              className="w-4 h-4"
            />
            <span className="text-white">Enable Token Tracking</span>
          </label>
        </div>

        {/* Save Button */}
        <div className="pt-4">
          <button
            onClick={handleSave}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg flex items-center gap-2 transition"
          >
            <Save size={18} />
            Save Settings
          </button>
          {saved && <p className="text-green-400 text-sm mt-2">✓ Settings saved</p>}
        </div>
      </div>
    </div>
  )
}
