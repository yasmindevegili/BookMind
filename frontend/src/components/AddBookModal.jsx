import { useState } from 'react'
import { createBook } from '../services/api'

const FIELD = (label, key, type = 'text', extra = {}) => ({ label, key, type, ...extra })

const FIELDS = [
  FIELD('Título *', 'title'),
  FIELD('Autor *', 'author'),
  FIELD('Gênero', 'genre'),
  FIELD('ISBN', 'isbn'),
  FIELD('Ano de publicação', 'year_published', 'number'),
  FIELD('Nota (0–5)', 'rating', 'number', { step: '0.5', min: '0', max: '5' }),
]

export default function AddBookModal({ onClose, onSave }) {
  const [form, setForm] = useState({
    title: '', author: '', genre: '', isbn: '',
    year_published: '', rating: '', status: 'want_to_read', description: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const update = (key) => (e) => setForm((p) => ({ ...p, [key]: e.target.value }))

  async function handleSave() {
    if (!form.title.trim() || !form.author.trim()) {
      setError('Título e autor são obrigatórios.')
      return
    }
    setSaving(true)
    try {
      await createBook({
        ...form,
        year_published: form.year_published ? parseInt(form.year_published) : null,
        rating: form.rating ? parseFloat(form.rating) : null,
        genre: form.genre || null,
        isbn: form.isbn || null,
      })
      onSave()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Adicionar Livro</h3>

        {error && (
          <p className="text-red-600 text-sm mb-3 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
        )}

        <div className="space-y-3">
          {FIELDS.map(({ label, key, type, ...rest }) => (
            <input
              key={key}
              type={type}
              placeholder={label}
              value={form[key]}
              onChange={update(key)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              {...rest}
            />
          ))}

          <select
            value={form.status}
            onChange={update('status')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            <option value="want_to_read">Quero Ler</option>
            <option value="reading">Lendo</option>
            <option value="read">Lido</option>
          </select>

          <textarea
            placeholder="Descrição (opcional)"
            value={form.description}
            onChange={update('description')}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
          />
        </div>

        <div className="flex gap-2 mt-5">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}
