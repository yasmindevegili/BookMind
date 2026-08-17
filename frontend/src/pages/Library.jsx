import { useEffect, useState } from 'react'
import AddBookModal from '../components/AddBookModal'
import BookCard from '../components/BookCard'
import { getBooks, getDiscoverBooks, updateBookStatus } from '../services/api'

const FILTERS = [
  { value: 'all', label: 'Descobrir' },
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

const DISCOVER_LIMIT = 56

function normalize(str) {
  return (str ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

function levenshtein(a, b) {
  const m = a.length, n = b.length
  const dp = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  )
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
  return dp[m][n]
}

function wordMatches(qWord, tWord) {
  if (tWord.includes(qWord)) return true
  if (qWord.length < 3) return false
  return levenshtein(qWord, tWord) <= Math.ceil(Math.max(qWord.length, tWord.length) / 3)
}

function matchesQuery(book, query) {
  const qWords = normalize(query).split(/\s+/).filter(Boolean)
  const fields = [book.title, book.author, book.genre, ...(book.tags ?? [])].filter(Boolean)
  const tWords = fields.flatMap((f) => normalize(f).split(/\s+/))
  return qWords.every((qw) => tWords.some((tw) => wordMatches(qw, tw)))
}

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
  const [discoverBooks, setDiscoverBooks] = useState([])
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState('title_asc')
  const [query, setQuery] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBooks()
  }, [])

  async function loadBooks() {
    try {
      const recentlyViewed = JSON.parse(localStorage.getItem('bookmind_recently_viewed') || '[]')
      const [all, discovered] = await Promise.all([getBooks(), getDiscoverBooks(recentlyViewed)])
      setBooks(all)
      setDiscoverBooks(discovered)
    } finally {
      setLoading(false)
    }
  }

  async function handleWantToRead(book) {
    const newStatus = book.status === 'want_to_read' ? 'none' : 'want_to_read'
    const updated = await updateBookStatus(book.id, newStatus)
    setBooks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)))
  }

  async function handleRead(book) {
    const newStatus = book.status === 'read' ? 'none' : 'read'
    const updated = await updateBookStatus(book.id, newStatus)
    setBooks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)))
  }

  const searched = query ? books.filter((b) => matchesQuery(b, query)) : books
  const baseList =
    filter === 'all'
      ? query ? searched : discoverBooks
      : searched.filter((b) => b.status === filter)
  const filtered = sortBooks(baseList, sort)

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

      <div className="relative mb-5">
        <span className="absolute inset-y-0 left-3 flex items-center text-gray-400 pointer-events-none">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar por título, autor, gênero ou tag…"
          className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg bg-white text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-400 focus:border-indigo-400"
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-gray-600"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
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
          <p>{query ? `Nenhum resultado para "${query}".` : 'Nenhum livro aqui ainda.'}</p>
        </div>
      ) : (
        <>
          {query && (
            <p className="text-sm text-gray-500 mb-4">
              {filtered.length} resultado{filtered.length !== 1 ? 's' : ''} para &ldquo;{query}&rdquo;
            </p>
          )}
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-8">
            {filtered.map((book) => (
              <BookCard key={book.id} book={book} onWantToRead={handleWantToRead} onRead={handleRead} />
            ))}
          </div>
        </>
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
