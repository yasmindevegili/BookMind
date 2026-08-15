import { useState } from 'react'

const TYPE_LABELS = {
  highlight: 'destaque',
  note: 'nota',
  quote: 'citação',
  reflection: 'reflexão',
}

export default function ChatMessage({ message }) {
  const [showSources, setShowSources] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm max-w-lg text-sm">
          {message.content}
        </div>
      </div>
    )
  }

  if (message.role === 'error') {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
        {message.content}
      </div>
    )
  }

  return (
    <div className="space-y-1.5 max-w-2xl">
      <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm">
        <p className="text-gray-800 text-sm whitespace-pre-wrap leading-relaxed">
          {message.content}
        </p>
      </div>

      {message.sources?.length > 0 && (
        <div className="ml-1">
          <button
            onClick={() => setShowSources((v) => !v)}
            className="text-xs text-gray-400 hover:text-indigo-500 transition-colors"
          >
            {showSources ? '▾ ocultar fontes' : `▸ ver fontes (${message.sources.length})`}
          </button>

          {showSources && (
            <div className="mt-1.5 space-y-1">
              {message.sources.map((s, i) => (
                <div
                  key={i}
                  className="bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-xs"
                >
                  <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
                    <span className="font-medium text-gray-700">{s.book}</span>
                    <span className="text-gray-300">·</span>
                    <span className="text-gray-400">{s.author}</span>
                    <span className="text-gray-300">·</span>
                    <span className="text-indigo-400">{TYPE_LABELS[s.type] ?? s.type}</span>
                    {s.chapter && (
                      <>
                        <span className="text-gray-300">·</span>
                        <span className="text-gray-400">{s.chapter}</span>
                      </>
                    )}
                  </div>
                  <p className="text-gray-500 italic mt-1">"{s.content}"</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
