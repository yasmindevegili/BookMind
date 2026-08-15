import { useEffect, useState } from 'react'
import AddBookModal from '../components/AddBookModal'
import BookCard from '../components/BookCard'
import { getBooks } from '../services/api'

const FILTERS = [
  { value: 'all', label: 'Todos' },
  { value: 'want_to_read', label: 'Quero Ler' },
  { value: 'reading', label: 'Lendo' },
  { value: 'read', label: 'Lidos' },
  { value: 'abandoned', label: 'Abandonados' },
]

const SORT_OPTIONS = [
  { value: 'title_asc', label: 'Título (A–Z)' },
  { value: 'title_desc', label: 'Título (Z–A)' },
  { value: 'author_asc', label: 'Autor (A–Z)' },
  { value: 'rating_desc', label: 'Avaliação (maior)' },
  { value: 'added_desc', label: 'Adicionado (recente)' },
  { value: 'added_asc', label: 'Adicionado (antigo)' },
]

function sortBooks(books, sort) {
  const copy = [...books]
  switch (sort) {
    case 'title_asc':
      return copy.sort((a, b) => a.title.localeCompare(b.title, 'pt'))
    case 'title_desc':
      return copy.sort((a, b) => b.title.localeCompare(a.title, 'pt'))
    case 'author_asc':
      return copy.sort((a, b) => a.author.localeCompare(b.author, 'pt'))
    case 'rating_desc':
      return copy.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
    case 'added_desc':
      return copy.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    case 'added_asc':
      return copy.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    default:
      return copy
  }
}

export default function Library() {
  const [books, setBooks] = useState([])
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState('title_asc')
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBooks()
  }, [])

  async function loadBooks() {
    try {
      setBooks(await getBooks())
    } finally {
      setLoading(false)
    }
  }

  const filtered = sortBooks(
    filter === 'all' ? books : books.filter((b) => b.status === filter),
    sort,
  )

  return (
    <div className="px-12 py-10">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Minha Biblioteca</h2>
          <p className="text-sm text-gray-500 mt-0.5">{books.length} livros</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
        >
          + Adicionar Livro
        </button>
      </div>

      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-2">
          {FILTERS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                filter === value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 bg-white hover:border-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          {SORT_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Carregando...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">📚</p>
          <p>Nenhum livro aqui ainda.</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-8">
          {filtered.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}

      {showAdd && (
        <AddBookModal
          onClose={() => setShowAdd(false)}
          onSave={() => { setShowAdd(false); loadBooks() }}
        />
      )}
    </div>
  )
}
