import { useEffect, useRef, useState } from 'react'
import AddBookModal from '../components/AddBookModal'
import BookCard from '../components/BookCard'
import { getBooks, getBooksByTag, getTags, updateBookStatus } from '../services/api'

/* ── Curadoria ───────────────────────────────────────────────── */

const TAG_LABELS = {
  'Nobel de Literatura':   { emoji: '🏅', desc: 'Vencedores do Nobel de Literatura' },
  'Booker Prize':          { emoji: '📖', desc: 'Vencedores do Booker Prize' },
  'Prêmio Jabuti':         { emoji: '🐢', desc: 'Vencedores do Prêmio Jabuti' },
  'Escritas por Mulheres': { emoji: '✍️', desc: 'Obras de autoras mulheres' },
}

const CURADORIA_ORDER = ['Nobel de Literatura', 'Booker Prize', 'Prêmio Jabuti', 'Escritas por Mulheres']

function Carousel({ tag, books }) {
  const meta = TAG_LABELS[tag] ?? { emoji: '🏷️', desc: tag }
  const ref = useRef(null)
  const scroll = (dir) => ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })

  return (
    <section className="mb-10">
      <div className="flex items-baseline gap-3 mb-3">
        <span className="text-xl">{meta.emoji}</span>
        <div>
          <h2 className="text-lg font-bold text-gray-900">{tag}</h2>
          <p className="text-xs text-gray-400">{meta.desc} · {books.length} livros</p>
        </div>
        <div className="ml-auto flex gap-1">
          <button onClick={() => scroll(-1)} className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">‹</button>
          <button onClick={() => scroll(1)}  className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">›</button>
        </div>
      </div>
      <div ref={ref} className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollSnapType: 'x mandatory' }}>
        {books.map((book) => (
          <div key={book.id} className="flex-none w-36" style={{ scrollSnapAlign: 'start' }}>
            <BookCard book={book} />
          </div>
        ))}
      </div>
    </section>
  )
}

function CuradoriaPanel() {
  const [tags, setTags]   = useState([])
  const [data, setData]   = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getTags().then(async (tagList) => {
      const curadas = tagList.filter((t) => TAG_LABELS[t])
      setTags(curadas)
      const entries = await Promise.all(curadas.map(async (tag) => [tag, await getBooksByTag(tag)]))
      setData(Object.fromEntries(entries))
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="py-16 text-center text-gray-400">Carregando curadoria...</div>
  if (tags.length === 0) return (
    <div className="py-16 text-center text-gray-400">
      <p className="text-4xl mb-3">🏷️</p>
      <p>Nenhuma coleção editorial ainda.</p>
    </div>
  )

  const sorted = [...tags].sort((a, b) => {
    const ia = CURADORIA_ORDER.indexOf(a), ib = CURADORIA_ORDER.indexOf(b)
    if (ia === -1 && ib === -1) return a.localeCompare(b)
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })

  return (
    <>
      {sorted.map((tag) => <Carousel key={tag} tag={tag} books={data[tag] ?? []} />)}
      <style>{`.scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none}.scrollbar-hide::-webkit-scrollbar{display:none}`}</style>
    </>
  )
}

/* ── Biblioteca ──────────────────────────────────────────────── */

const SORT_OPTIONS = [
  { value: 'title_asc',   label: 'Título (A–Z)' },
  { value: 'title_desc',  label: 'Título (Z–A)' },
  { value: 'author_asc',  label: 'Autor (A–Z)' },
  { value: 'rating_desc', label: 'Avaliação (maior)' },
  { value: 'added_desc',  label: 'Adicionado (recente)' },
  { value: 'added_asc',   label: 'Adicionado (antigo)' },
]

function sortBooks(books, sort) {
  const copy = [...books]
  switch (sort) {
    case 'title_asc':   return copy.sort((a, b) => a.title.localeCompare(b.title, 'pt'))
    case 'title_desc':  return copy.sort((a, b) => b.title.localeCompare(a.title, 'pt'))
    case 'author_asc':  return copy.sort((a, b) => a.author.localeCompare(b.author, 'pt'))
    case 'rating_desc': return copy.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
    case 'added_desc':  return copy.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    case 'added_asc':   return copy.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    default: return copy
  }
}

function BibliotecaPanel() {
  const [books, setBooks]     = useState([])
  const [sort, setSort]       = useState('title_asc')
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadBooks() }, [])

  async function loadBooks() {
    try { setBooks(await getBooks()) } finally { setLoading(false) }
  }

  async function handleWantToRead(book) {
    const updated = await updateBookStatus(book.id, book.status === 'want_to_read' ? 'none' : 'want_to_read')
    setBooks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)))
  }

  async function handleRead(book) {
    const updated = await updateBookStatus(book.id, book.status === 'read' ? 'none' : 'read')
    setBooks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)))
  }

  const sorted = sortBooks(books, sort)

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <p className="text-sm text-gray-500">{sorted.length} livros</p>
        <div className="flex items-center gap-3">
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 bg-white hover:border-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-400"
          >
            {SORT_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button
            onClick={() => setShowAdd(true)}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          >
            + Adicionar Livro
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Carregando...</div>
      ) : sorted.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">📚</p>
          <p>Nenhum livro aqui ainda.</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-8">
          {sorted.map((book) => (
            <BookCard key={book.id} book={book} onWantToRead={handleWantToRead} onRead={handleRead} />
          ))}
        </div>
      )}

      {showAdd && (
        <AddBookModal
          onClose={() => setShowAdd(false)}
          onSave={() => { setShowAdd(false); loadBooks() }}
        />
      )}
    </>
  )
}

/* ── Page ────────────────────────────────────────────────────── */

const TABS = [
  { value: 'biblioteca', label: 'Minha Biblioteca' },
  { value: 'curadoria',  label: 'Curadoria' },
]

export default function Library() {
  const [tab, setTab] = useState('biblioteca')

  return (
    <div className="px-12 py-10">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Biblioteca</h2>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === value
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'biblioteca' ? <BibliotecaPanel /> : <CuradoriaPanel />}
    </div>
  )
}
