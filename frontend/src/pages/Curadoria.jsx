import { useEffect, useRef, useState } from 'react'
import BookCard from '../components/BookCard'
import {
  getCollectionBooks,
  getComputedBooks,
  getComputedMeta,
  getCuradoriaCollections,
  getGenreBooks,
  getGenreList,
  initializeCuradoria,
} from '../services/api'

// Metadados visuais para coleções de prêmios e computed
const META = {
  'Nobel de Literatura': { emoji: '🏅', desc: 'Vencedores do Nobel de Literatura' },
  'Booker Prize':        { emoji: '📖', desc: 'Vencedores do Booker Prize' },
  'Prêmio Jabuti':       { emoji: '🐢', desc: 'Vencedores do Prêmio Jabuti' },
  'Prêmio Pulitzer':     { emoji: '🏆', desc: 'Vencedores do Prêmio Pulitzer' },
  'Prêmio Camões':       { emoji: '✒️', desc: 'Vencedores do Prêmio Camões' },
  'Em Alta no Mundo':    { emoji: '🌍', desc: 'Do seu acervo em destaque global (Open Library)' },
  'Quero Ler':           { emoji: '📌', desc: 'Livros que você marcou para ler' },
  'Já Lidos':            { emoji: '✅', desc: 'Livros que você já leu' },
}

const GENRE_EMOJIS = {
  'Romance':            '💕',
  'História':           '📜',
  'Biografia':          '👤',
  'Suspense':           '🔍',
  'Clássicos':          '🏛️',
  'Fantasia':           '🧙',
  'Aventura':           '⚔️',
  'Filosofia':          '💭',
  'Ficção Científica':  '🚀',
  'Psicologia':         '🧠',
  'Poesia':             '🌸',
  'Terror':             '👻',
  'Contos':             '📖',
  'Infantojuvenil':     '🌈',
  'Ficção Histórica':   '🗺️',
  'Literatura Brasileira': '🌿',
  'Distopia':           '🌑',
}

// ── Componente Carrossel genérico ────────────────────────────────

function Carousel({ name, fetcher, subtitle }) {
  const meta = META[name] ?? {}
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [empty, setEmpty] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    fetcher()
      .then((b) => { setBooks(b); setEmpty(b.length === 0) })
      .finally(() => setLoading(false))
  }, [])

  if (!loading && empty) return null

  const scroll = (dir) => ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })
  const desc = subtitle ?? meta.desc ?? ''

  return (
    <section className="mb-10">
      <div className="flex items-center gap-3 mb-3">
        {meta.emoji && <span className="text-xl">{meta.emoji}</span>}
        <div>
          <h3 className="text-base font-bold text-gray-900">{name}</h3>
          {desc && <p className="text-xs text-gray-400">{desc}{!loading && ` · ${books.length} livros`}</p>}
        </div>
        <div className="ml-auto flex gap-1">
          <button onClick={() => scroll(-1)} className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">‹</button>
          <button onClick={() => scroll(1)}  className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">›</button>
        </div>
      </div>

      {loading ? (
        <div className="h-52 flex items-center justify-center text-gray-300 text-sm">Carregando…</div>
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

// ── Seção com título ─────────────────────────────────────────────

function Section({ title, children }) {
  return (
    <div className="mb-8">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-5">{title}</h2>
      {children}
    </div>
  )
}

// ── Página Curadoria ─────────────────────────────────────────────

export default function Curadoria() {
  const [awards, setAwards]           = useState([])
  const [computed, setComputed]       = useState([])
  const [genres, setGenres]           = useState([])
  const [loading, setLoading]         = useState(true)
  const [initializing, setInitializing] = useState(false)
  const [awardsEmpty, setAwardsEmpty] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const [awardList, computedList, genreList] = await Promise.all([
        getCuradoriaCollections(),
        getComputedMeta(),
        getGenreList(),
      ])
      setAwards(awardList)
      setAwardsEmpty(awardList.every((c) => c.book_count === 0))
      setComputed(computedList)
      setGenres(genreList)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleInitialize() {
    setInitializing(true)
    try {
      await initializeCuradoria()
      await load()
    } finally {
      setInitializing(false)
    }
  }

  if (loading) {
    return (
      <div className="px-12 py-10">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Curadoria</h2>
          <p className="text-sm text-gray-400 mt-0.5">Listas editoriais e destaques do acervo</p>
        </div>
        <div className="py-24 text-center text-gray-400">Carregando curadoria…</div>
      </div>
    )
  }

  return (
    <div className="px-12 py-10">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Curadoria</h2>
        <p className="text-sm text-gray-400 mt-0.5">Listas editoriais e destaques do acervo</p>
      </div>

      {/* Em Alta */}
      <Section title="Em Alta">
        <Carousel
          name="Em Alta no Mundo"
          fetcher={() => getComputedBooks('em-alta')}
        />
      </Section>

      {/* Sua Leitura */}
      <Section title="Sua Leitura">
        {computed.filter((c) => ['quero-ler', 'ja-lidos'].includes(c.slug)).map((c) => (
          <Carousel
            key={c.slug}
            name={c.name}
            fetcher={() => getComputedBooks(c.slug)}
          />
        ))}
      </Section>

      {/* Prêmios Literários */}
      <Section title="Prêmios Literários">
        {awardsEmpty ? (
          <div className="py-10 text-center">
            <p className="text-gray-400 text-sm mb-4">
              Coleções editoriais ainda não indexadas.
            </p>
            <button
              onClick={handleInitialize}
              disabled={initializing}
              className="px-5 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {initializing ? 'Indexando…' : 'Indexar agora'}
            </button>
          </div>
        ) : (
          awards.filter((c) => c.book_count > 0).map((c) => (
            <Carousel
              key={c.slug}
              name={c.name}
              fetcher={() => getCollectionBooks(c.slug)}
            />
          ))
        )}
      </Section>

      {/* Por Gênero */}
      {genres.length > 0 && (
        <Section title="Por Gênero">
          {genres.map((g) => (
            <Carousel
              key={g.name}
              name={g.name}
              subtitle={`${GENRE_EMOJIS[g.name] ?? '📚'} · ${g.count} livros no acervo`}
              fetcher={() => getGenreBooks(g.name)}
            />
          ))}
        </Section>
      )}

      <style>{`.scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none}.scrollbar-hide::-webkit-scrollbar{display:none}`}</style>
    </div>
  )
}
