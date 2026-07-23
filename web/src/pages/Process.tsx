import { useState, useEffect } from 'react'
import { Send, Copy, Download } from 'lucide-react'

interface Operation {
  key: string
  label: string
}

export default function Process() {
  const [text, setText] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [operations, setOperations] = useState<Operation[]>([])
  const [selectedOp, setSelectedOp] = useState('clean')

  useEffect(() => {
    fetchOperations()
  }, [])

  const fetchOperations = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/operations')
      const data = await response.json()
      setOperations(data.operations)
    } catch (error) {
      console.error('Failed to fetch operations:', error)
    }
  }

  const handleProcess = async () => {
    if (!text.trim()) return

    setLoading(true)
    try {
      const response = await fetch('http://localhost:5000/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, operation: selectedOp })
      })
      const data = await response.json()
      setResult(data.result || data.error)
    } catch (error) {
      setResult('Error processing text')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Text Processing</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Input */}
        <div>
          <label className="block text-white font-semibold mb-2">Input Text</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full h-64 bg-slate-800 text-white rounded-lg p-4 border border-slate-700 focus:border-blue-500 outline-none resize-none"
            placeholder="Paste or type your text here..."
          />
        </div>

        {/* Output */}
        <div>
          <label className="block text-white font-semibold mb-2">Result</label>
          <textarea
            value={result}
            readOnly
            className="w-full h-64 bg-slate-800 text-white rounded-lg p-4 border border-slate-700 resize-none"
            placeholder="Result will appear here..."
          />
        </div>
      </div>

      {/* Controls */}
      <div className="mt-6 flex gap-4 items-end flex-wrap">
        <div className="flex-1 min-w-48">
          <label className="block text-white font-semibold mb-2">Operation</label>
          <select
            value={selectedOp}
            onChange={(e) => setSelectedOp(e.target.value)}
            className="w-full bg-slate-800 text-white rounded-lg p-2 border border-slate-700 focus:border-blue-500 outline-none"
          >
            {operations.map(op => (
              <option key={op.key} value={op.key}>{op.label}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleProcess}
          disabled={loading || !text.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-semibold py-2 px-6 rounded-lg flex items-center gap-2 transition"
        >
          <Send size={18} />
          {loading ? 'Processing...' : 'Process'}
        </button>

        {result && (
          <>
            <button
              onClick={() => navigator.clipboard.writeText(result)}
              className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 px-4 rounded-lg flex items-center gap-2 transition"
            >
              <Copy size={18} />
              Copy
            </button>
            <button
              onClick={() => {
                const el = document.createElement('a')
                el.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(result)
                el.download = 'result.txt'
                el.click()
              }}
              className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 px-4 rounded-lg flex items-center gap-2 transition"
            >
              <Download size={18} />
              Download
            </button>
          </>
        )}
      </div>
    </div>
  )
}
