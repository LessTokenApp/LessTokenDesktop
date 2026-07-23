import { useState } from 'react'
import { ChevronRight, Zap, DollarSign, Layers, Settings } from 'lucide-react'

interface OnboardingProps {
  onComplete: () => void
}

const slides = [
  {
    title: "Welcome to Token Optimizer",
    subtitle: "Control your AI costs like never before",
    description: "Token Optimizer helps you reduce AI API costs by 60-75% through intelligent provider selection, caching, and prompt optimization.",
    icon: Zap,
    color: "from-blue-500 to-blue-600"
  },
  {
    title: "What's a Token?",
    subtitle: "The currency of AI APIs",
    description: "Each word or piece of code is converted to 'tokens'. You pay per token. Our optimization reduces how many tokens you send, saving money.",
    icon: DollarSign,
    color: "from-green-500 to-green-600"
  },
  {
    title: "Multi-Provider Support",
    subtitle: "Choose the best tool for each job",
    description: "Support for Claude, OpenAI, Gemini, and Ollama. Different providers = different costs. We automatically select the cheapest option for your task.",
    icon: Layers,
    color: "from-purple-500 to-purple-600"
  },
  {
    title: "Smart Features",
    subtitle: "Work smarter, pay less",
    description: "• Local Caching: Cache results, avoid duplicate API calls\n• Prompt Optimization: Shorter prompts = fewer tokens\n• Model Routing: Use Haiku for simple tasks, Opus for complex ones\n• Real-time Tracking: Know your exact costs",
    icon: Settings,
    color: "from-orange-500 to-orange-600"
  }
]

export default function Onboarding({ onComplete }: OnboardingProps) {
  const [currentSlide, setCurrentSlide] = useState(0)
  const Slide = slides[currentSlide].icon

  const handleNext = () => {
    if (currentSlide < slides.length - 1) {
      setCurrentSlide(currentSlide + 1)
    } else {
      onComplete()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Slide */}
        <div className="bg-slate-800 rounded-2xl p-12 border border-slate-700 shadow-2xl mb-8">
          {/* Header */}
          <div className={`inline-block p-4 rounded-xl bg-gradient-to-br ${slides[currentSlide].color} mb-6`}>
            <Slide className="text-white" size={32} />
          </div>

          <h1 className="text-4xl font-bold text-white mb-2">{slides[currentSlide].title}</h1>
          <h2 className="text-xl text-slate-300 mb-6">{slides[currentSlide].subtitle}</h2>

          <p className="text-slate-300 text-lg leading-relaxed whitespace-pre-wrap">
            {slides[currentSlide].description}
          </p>
        </div>

        {/* Progress */}
        <div className="flex gap-2 mb-8">
          {slides.map((_, idx) => (
            <div
              key={idx}
              className={`h-2 rounded-full flex-1 transition ${
                idx <= currentSlide ? 'bg-blue-500' : 'bg-slate-700'
              }`}
            />
          ))}
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <div className="text-slate-400 text-sm">
            {currentSlide + 1} of {slides.length}
          </div>
          <button
            onClick={handleNext}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg flex items-center gap-2 transition"
          >
            {currentSlide === slides.length - 1 ? 'Get Started' : 'Next'}
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Quick Tips */}
        <div className="mt-12 bg-slate-700 rounded-lg p-6 border border-slate-600">
          <h3 className="text-white font-semibold mb-3">💡 Quick Tip</h3>
          {currentSlide === 0 && (
            <p className="text-slate-300 text-sm">Token Optimizer works with your existing API keys. No new setup needed!</p>
          )}
          {currentSlide === 1 && (
            <p className="text-slate-300 text-sm">Typical prompt: ~150 tokens. Optimized: ~100 tokens. That's 33% savings per request!</p>
          )}
          {currentSlide === 2 && (
            <p className="text-slate-300 text-sm">Claude Haiku costs 90% less than Claude Opus for simple tasks. Let us pick the best model.</p>
          )}
          {currentSlide === 3 && (
            <p className="text-slate-300 text-sm">Start exploring! Dashboard shows your real-time savings. Check Settings to customize.</p>
          )}
        </div>
      </div>
    </div>
  )
}
