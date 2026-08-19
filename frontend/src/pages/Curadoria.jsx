import { useEffect, useRef, useState } from 'react'
import BookCard from '../components/BookCard'
import {
  getCollectionBooks,
  getCuradoriaCollections,
  getGenreBooks,
  getGenreList,
  initializeCuradoria,
} from '../services/api'

const AWARD_META = {
  'Nobel de Literatura': { emoji: '🏅', desc: 'Vencedores do Nobel de Literatura' },
  'Booker Prize':        { emoji: '📖', desc: 'Vencedores do Booker Prize' },
  'Prêmio Jabuti':       { emoji: '🐢', desc: 'Vencedores do Prêmio Jabuti' },
  'Prêmio Pulitzer':     { emoji: '🏆', desc: 'Vencedores do Prêmio Pulitzer' },
  'Prêmio Camões':       { emoji: '✒️', desc: 'Vencedores do Prêmio Camões' },
}

const GENRE_EMOJI = {
  'Romance':               '💕',
  'História':              '📜',
  'Biografia':             '👤',
  'Suspense':              '🔍',
  'Clássicos':             '🏛️',
  'Fantasia':              '🧙',
  'Aventura':              '⚔️',
  'Filosofia':             '💭',
  'Ficção Científica':     '🚀',
  'Psicologia':            '🧠',
  'Poesia':                '🌸',
  'Terror':                '👻',
  'Contos':                '📖',
  'Infantojuvenil':        '🌈',
  'Ficção Histórica':      '🗺️',
  'Literatura Brasileira': '🌿',
  'Distopia':              '🌑',
}

// ── Carrossel genérico ───────────────────────────────────────────

function Carousel({ name, emoji, desc, fetcher }) {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const ref = useRef(null)

  useEffect(() => {
    fetcher()
      .then(setBooks)
      .finally(() => setLoading(false))
  }, [])

  if (!loading && books.length === 0) return null

  const scroll = (dir) => ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })

  return (
    <section className="mb-10">
      <div className="flex items-center gap-3 mb-3">
        {emoji && <span className="text-xl">{emoji}</span>}
        <div>
          <h3 className="text-base font-bold text-gray-900">{name}</h3>
          {desc && (
            <p className="text-xs text-gray-400">
              {desc}{!loading && ` · ${books.length} livros`}
            </p>
          )}
        </div>
        <div className="ml-auto flex gap-1">
          <button onClick={() => scroll(-1)} className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">‹</button>
          <button onClick={() => scroll(1)}  className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">›</button>
        </div>
      </div>

      {loading ? (
        <div className="h-52 flex items-center justify-center text-gray-200 text-sm">Carregando…</div>
      ) : (
        <div ref={ref} className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollSnapType: 'x mandatory' }}>
          {books.map((book) => (
            <div key={book.id} className="flex-none w-36" style={{ scrollSnapAlign: 'start' }}>
              <BookCard book={book} />
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

// ── Aba Prêmios ──────────────────────────────────────────────────

function PremiosTab() {
  const [awards, setAwards]         = useState([])
  const [loading, setLoading]       = useState(true)
  const [initializing, setInitializing] = useState(false)

  useEffect(() => {
    getCuradoriaCollections()
      .then(setAwards)
      .finally(() => setLoading(false))
  }, [])

  async function handleInitialize() {
    setInitializing(true)
    try {
      await initializeCuradoria()
      setAwards(await getCuradoriaCollections())
    } finally {
      setInitializing(false)
    }
  }

  if (loading) return <div className="py-20 text-center text-gray-300">Carregando…</div>

  const populated = awards.filter((c) => c.book_count > 0)

  if (populated.length === 0) {
    return (
      <div className="py-20 text-center">
        <p className="text-4xl mb-4">🏆</p>
        <p className="text-gray-500 font-medium mb-2">Coleções ainda não indexadas</p>
        <p className="text-sm text-gray-400 mb-6">
          Clique para detectar automaticamente livros premiados no seu acervo.
        </p>
        <button
          onClick={handleInitialize}
          disabled={initializing}
          className="px-5 py-2.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {initializing ? 'Indexando…' : 'Indexar coleções'}
        </button>
      </div>
    )
  }

  return (
    <>
      {populated.map((c) => {
        const meta = AWARD_META[c.name] ?? { emoji: '🏷️', desc: c.name }
        return (
          <Carousel
            key={c.slug}
            name={c.name}
            emoji={meta.emoji}
            desc={meta.desc}
            fetcher={() => getCollectionBooks(c.slug)}
          />
        )
      })}
    </>
  )
}

// ── Aba Por Gênero ───────────────────────────────────────────────

function GenerosTab() {
  const [genres, setGenres]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getGenreList()
      .then(setGenres)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="py-20 text-center text-gray-300">Carregando…</div>

  if (genres.length === 0) {
    return (
      <div className="py-20 text-center text-gray-400">
        <p className="text-4xl mb-3">📚</p>
        <p>Nenhum gênero encontrado no acervo.</p>
      </div>
    )
  }

  return (
    <>
      {genres.map((g) => (
        <Carousel
          key={g.name}
          name={g.name}
          emoji={GENRE_EMOJI[g.name] ?? '📚'}
          desc={`${g.count} livros no acervo`}
          fetcher={() => getGenreBooks(g.name)}
        />
      ))}
    </>
  )
}

// ── Página ───────────────────────────────────────────────────────

const TABS = [
  { value: 'premios', label: 'Prêmios' },
  { value: 'generos', label: 'Por Gênero' },
]

export default function Curadoria() {
  const [tab, setTab] = useState('premios')

  return (
    <div className="px-12 py-10">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Curadoria</h2>
        <p className="text-sm text-gray-400 mt-0.5">Listas editoriais e seleções por gênero</p>
      </div>

      <div className="flex gap-1 border-b border-gray-200 mb-8">
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

      {tab === 'premios' ? <PremiosTab /> : <GenerosTab />}

      <style>{`.scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none}.scrollbar-hide::-webkit-scrollbar{display:none}`}</style>
    </div>
  )
}
