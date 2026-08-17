import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BookCard from '../components/BookCard'
import { createAnnotation, getAnnotations, getBook, getSimilarBooks, updateBookStatus } from '../services/api'

const STATUS_OPTIONS = [
  { value: 'want_to_read', label: 'Quero Ler',  active: 'bg-amber-100 text-amber-700 border-amber-300',  inactive: 'bg-white text-gray-500 border-gray-200 hover:border-amber-200 hover:text-amber-600' },
  { value: 'reading',      label: 'Lendo',       active: 'bg-blue-100 text-blue-700 border-blue-300',    inactive: 'bg-white text-gray-500 border-gray-200 hover:border-blue-200 hover:text-blue-600' },
  { value: 'read',         label: 'Lido',        active: 'bg-emerald-100 text-emerald-700 border-emerald-300', inactive: 'bg-white text-gray-500 border-gray-200 hover:border-emerald-200 hover:text-emerald-600' },
  { value: 'abandoned',    label: 'Abandonado',  active: 'bg-red-100 text-red-600 border-red-300',       inactive: 'bg-white text-gray-500 border-gray-200 hover:border-red-200 hover:text-red-500' },
]


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
  const [similarBooks, setSimilarBooks] = useState([])

  useEffect(() => {
    Promise.all([getBook(id), getAnnotations(id)]).then(([b, a]) => {
      setBook(b)
      setAnnotations(a)
    })
    getSimilarBooks(id, 12).then(setSimilarBooks).catch(() => {})

    // Registra visita para influenciar o algoritmo de Descobrir
    const key = 'bookmind_recently_viewed'
    const prev = JSON.parse(localStorage.getItem(key) || '[]')
    localStorage.setItem(key, JSON.stringify(
      [Number(id), ...prev.filter((x) => x !== Number(id))].slice(0, 10)
    ))
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

  async function handleStatusChange(value) {
    const newStatus = book.status === value ? 'none' : value
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

            <div className="flex flex-wrap gap-2 mt-3">
              {book.genre && (
                <span className="text-xs px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full">{book.genre}</span>
              )}
              {book.year_published && (
                <span className="text-xs px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full">{book.year_published}</span>
              )}
              {book.rating && (
                <span className="text-xs px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full">
                  {'★'.repeat(Math.round(book.rating))} {book.rating}/5
                </span>
              )}
            </div>

            {book.tags && book.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {book.tags.map((tag) => (
                  <span key={tag} className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="mt-3 space-y-1 text-xs text-gray-500">
              {book.isbn && (
                <p><span className="text-gray-400">ISBN</span> {book.isbn}</p>
              )}
              {book.started_at && (
                <p><span className="text-gray-400">Início</span> {new Date(book.started_at).toLocaleDateString('pt-BR')}</p>
              )}
              {book.finished_at && (
                <p><span className="text-gray-400">Término</span> {new Date(book.finished_at).toLocaleDateString('pt-BR')}</p>
              )}
            </div>

            {book.description && (
              <p className="mt-3 text-gray-600 text-sm leading-relaxed">{book.description}</p>
            )}
            <div className="mt-4">
              <p className="text-xs text-gray-400 mb-1.5 font-medium">Status</p>
              <div className="flex flex-wrap gap-2">
                {STATUS_OPTIONS.map(({ value, label, active, inactive }) => (
                  <button
                    key={value}
                    onClick={() => handleStatusChange(value)}
                    disabled={updatingStatus}
                    className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors disabled:opacity-50 cursor-pointer
                      ${book.status === value ? active : inactive}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
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

      {similarBooks.length > 0 && (
        <div className="mt-10 pt-8 border-t border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">Você também pode gostar</h3>
          <div className="grid grid-cols-4 gap-4">
            {similarBooks.map((b) => (
              <BookCard key={b.id} book={b} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
