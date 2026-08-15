import { useEffect, useRef, useState } from 'react'
import ChatMessage from '../components/ChatMessage'
import { chat } from '../services/api'

const SUGGESTIONS = [
  'O que aprendi sobre produtividade?',
  'Quais autores que li falam sobre introversão?',
  'Tem alguma citação que salvei sobre coragem?',
  'Me resume o que li sobre relacionamentos',
  'Qual a diferença entre mindset fixo e de crescimento?',
]

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(query) {
    const text = query.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      const result = await chat(text)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: result.answer, sources: result.sources },
      ])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'error', content: `Erro: ${e.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-bold text-gray-900">Chat com sua Biblioteca</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Perguntas em linguagem natural — respostas com citação de fonte
        </p>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center pb-20">
            <p className="text-4xl mb-4">💬</p>
            <p className="text-gray-500 mb-6 text-sm">Tente uma dessas perguntas:</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-full text-sm hover:bg-indigo-100 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
            Buscando nas suas anotações...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-gray-200 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
            placeholder="Pergunte sobre seus livros e anotações..."
            className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 disabled:opacity-40 transition-colors"
          >
            Enviar
          </button>
        </div>
      </div>
    </div>
  )
}
