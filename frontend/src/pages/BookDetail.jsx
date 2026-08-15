import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { createAnnotation, getAnnotations, getBook, updateBookStatus } from '../services/api'

const STATUS_OPTIONS = [
  { value: 'none',         label: 'Descobrir' },
  { value: 'want_to_read', label: 'Quero Ler' },
  { value: 'reading',      label: 'Lendo' },
  { value: 'read',         label: 'Lido' },
  { value: 'abandoned',    label: 'Abandonado' },
]

const STATUS_STYLE = {
  read:         'bg-emerald-100 text-emerald-700 border-emerald-200',
  reading:      'bg-blue-100 text-blue-700 border-blue-200',
  want_to_read: 'bg-amber-100 text-amber-700 border-amber-200',
  none:         'bg-gray-100 text-gray-500 border-gray-200',
  abandoned:    'bg-red-100 text-red-600 border-red-200',
}

const TYPE_COLORS = {
  highlight: 'bg-yellow-50 border-yellow-200',
  note: 'bg-blue-50 border-blue-200',
  quote: 'bg-purple-50 border-purple-200',
  reflection: 'bg-green-50 border-green-200',
}

const TYPE_LABELS = {
  highlight: 'Destaque',
  note: 'Nota',
  quote: 'Citação',
  reflection: 'Reflexão',
}

export default function BookDetail() {
  const { id } = useParams()
  const [book, setBook] = useState(null)
  const [annotations, setAnnotations] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ type: 'highlight', content: '', chapter: '', page: '' })
  const [saving, setSaving] = useState(false)
  const [updatingStatus, setUpdatingStatus] = useState(false)

  useEffect(() => {
    Promise.all([getBook(id), getAnnotations(id)]).then(([b, a]) => {
      setBook(b)
      setAnnotations(a)
    })
  }, [id])

  async function handleAdd() {
    if (!form.content.trim()) return
    setSaving(true)
    try {
      const created = await createAnnotation({
        book_id: parseInt(id),
        type: form.type,
        content: form.content,
        chapter: form.chapter || null,
        page: form.page ? parseInt(form.page) : null,
      })
      setAnnotations((prev) => [...prev, created])
      setForm({ type: 'highlight', content: '', chapter: '', page: '' })
      setShowForm(false)
    } finally {
      setSaving(false)
    }
  }

  async function handleStatusChange(e) {
    const newStatus = e.target.value
    setUpdatingStatus(true)
    try {
      const updated = await updateBookStatus(book.id, newStatus)
      setBook(updated)
    } finally {
      setUpdatingStatus(false)
    }
  }

  if (!book) {
    return <div className="p-8 text-gray-400">Carregando...</div>
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <Link to="/" className="text-sm text-indigo-600 hover:underline mb-6 block">
        ← Voltar à biblioteca
      </Link>

      <div className="mb-8">
        <div className="flex gap-6">
          {book.cover_url && (
            <img
              src={book.cover_url}
              alt={book.title}
              className="w-24 h-36 object-cover rounded-lg shadow-md flex-shrink-0"
              onError={(e) => { e.target.style.display = 'none' }}
            />
          )}
          <div>
            <h2 className="text-2xl font-bold text-gray-900 leading-tight">{book.title}</h2>
            <p className="text-lg text-gray-500 mt-1">{book.author}</p>
            <div className="flex flex-wrap gap-3 mt-3 text-sm text-gray-500">
              {book.genre && <span>📖 {book.genre}</span>}
              {book.year_published && <span>📅 {book.year_published}</span>}
              {book.rating && <span>⭐ {book.rating}/5</span>}
            </div>
            {book.description && (
              <p className="mt-3 text-gray-600 text-sm leading-relaxed">{book.description}</p>
            )}
            <div className="mt-4">
              <select
                value={book.status}
                onChange={handleStatusChange}
                disabled={updatingStatus}
                className={`text-xs font-medium px-3 py-1.5 rounded-full border cursor-pointer
                  focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-60
                  ${STATUS_STYLE[book.status] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}
              >
                {STATUS_OPTIONS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-900">
          Anotações <span className="text-gray-400 font-normal">({annotations.length})</span>
        </h3>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-sm px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          + Anotar
        </button>
      </div>

      {showForm && (
        <div className="mb-5 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <div className="flex gap-2">
            <select
              value={form.type}
              onChange={(e) => setForm((p) => ({ ...p, type: e.target.value }))}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              {Object.entries(TYPE_LABELS).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
            <input
              placeholder="Capítulo"
              value={form.chapter}
              onChange={(e) => setForm((p) => ({ ...p, chapter: e.target.value }))}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <input
              placeholder="Pág."
              type="number"
              value={form.page}
              onChange={(e) => setForm((p) => ({ ...p, page: e.target.value }))}
              className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <textarea
            placeholder="Escreva o destaque, nota ou reflexão..."
            value={form.content}
            onChange={(e) => setForm((p) => ({ ...p, content: e.target.value }))}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
          />
          <div className="flex gap-2">
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
            >
              Cancelar
            </button>
            <button
              onClick={handleAdd}
              disabled={saving}
              className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm disabled:opacity-50"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {annotations.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">
            Nenhuma anotação ainda. Comece registrando um destaque!
          </p>
        ) : (
          annotations.map((ann) => (
            <div
              key={ann.id}
              className={`p-4 rounded-xl border ${TYPE_COLORS[ann.type] ?? 'bg-gray-50 border-gray-200'}`}
            >
              <div className="flex justify-between items-center text-xs text-gray-400 mb-2">
                <span className="font-medium">{TYPE_LABELS[ann.type] ?? ann.type}</span>
                <div className="flex gap-3">
                  {ann.chapter && <span>{ann.chapter}</span>}
                  {ann.page && <span>p. {ann.page}</span>}
                  {ann.embedded_at && <span className="text-green-500">✓ indexado</span>}
                </div>
              </div>
              <p className="text-gray-800 text-sm leading-relaxed">{ann.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
