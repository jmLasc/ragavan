import { useState } from 'react'

interface CardMeta {
  name: string
  mana_cost: string
  type_line: string
  rarity: string
  set_name: string
}

interface AskResponse {
  answer: string
  cards: CardMeta[]
  card_names: string[]
}

const API = 'http://localhost:8000'

export default function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [cards, setCards] = useState<CardMeta[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function ask() {
    if (!question.trim()) return
    setLoading(true)
    setAnswer('')
    setCards([])
    setError('')

    try {
      const res = await fetch(`${API}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data: AskResponse = await res.json()
      setAnswer(data.answer)
      setCards(data.cards)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not reach the backend.')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') ask()
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center px-4 py-12">
      <h1 className="text-4xl font-bold mb-2 tracking-tight">Ragavan</h1>
      <p className="text-gray-400 mb-8 text-sm">MTG card Q&amp;A powered by local AI</p>

      <div className="w-full max-w-2xl flex gap-2 mb-6">
        <input
          className="flex-1 rounded-lg bg-gray-800 border border-gray-700 px-4 py-3 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Ask about MTG cards…"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed px-5 py-3 text-sm font-medium transition-colors"
          onClick={ask}
          disabled={loading || !question.trim()}
        >
          {loading ? 'Thinking…' : 'Ask'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm mb-6">
          <span className="animate-spin inline-block w-4 h-4 border-2 border-gray-600 border-t-indigo-400 rounded-full" />
          Querying cards and generating answer…
        </div>
      )}

      {error && (
        <div className="w-full max-w-2xl rounded-lg bg-red-900/40 border border-red-700 px-4 py-3 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {answer && (
        <div className="w-full max-w-2xl rounded-lg bg-gray-800 border border-gray-700 px-5 py-4 mb-8 text-sm leading-relaxed whitespace-pre-wrap">
          {answer}
        </div>
      )}

      {cards.length > 0 && (
        <div className="w-full max-w-2xl">
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">Cards retrieved</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {cards.map((card, i) => (
              <div key={i} className="rounded-lg bg-gray-800 border border-gray-700 px-4 py-3">
                <div className="font-medium text-sm">{card.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">{card.type_line}</div>
                <div className="flex gap-3 text-xs text-gray-500 mt-1">
                  <span>{card.mana_cost || '—'}</span>
                  <span className="capitalize">{card.rarity}</span>
                  <span>{card.set_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
