import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BookCard from '../components/BookCard'
import {
  createBook,
  getCollectionBooks,
  getCuradoriaCollections,
  getGenreBooks,
  getGenreList,
  getGoogleBooksTrending,
  getLancamentos,
  getTagLivrosTrending,
  getNytTrending,
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

// ── DiscoverCard — livro externo não no acervo ───────────────────

function DiscoverCard({ book, onAdded }) {
  const [state, setState] = useState('idle') // idle | adding | done

  async function handleAdd() {
    setState('adding')
    try {
      await createBook({
        title: book.title,
        author: book.author,
        isbn: book.isbn || undefined,
        cover_url: book.cover_url || undefined,
        description: book.description || undefined,
      })
      setState('done')
      onAdded?.()
    } catch {
      setState('idle')
    }
  }

  return (
    <div className="relative w-36 group flex-none" style={{ scrollSnapAlign: 'start' }}>
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-gradient-to-br from-indigo-50 to-purple-100 mb-2">
        {book.cover_url ? (
          <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-2 text-center">
            <span className="text-2xl mb-1">📘</span>
            <span className="text-xs text-gray-500 line-clamp-3">{book.title}</span>
          </div>
        )}
        {state !== 'done' && (
          <button
            onClick={handleAdd}
            disabled={state === 'adding'}
            className="absolute inset-x-0 bottom-0 bg-indigo-600/90 backdrop-blur-sm text-white text-xs py-1.5 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-60"
          >
            {state === 'adding' ? '…' : '+ Adicionar'}
          </button>
        )}
        {state === 'done' && (
          <div className="absolute inset-x-0 bottom-0 bg-green-600/90 text-white text-xs py-1.5 text-center">
            ✓ Adicionado
          </div>
        )}
      </div>
      <p className="text-xs font-medium text-gray-800 truncate">{book.title}</p>
      <p className="text-xs text-gray-500 truncate">{book.author}</p>
    </div>
  )
}

// ── TrendingCarousel — fonte (Google Books ou NYT) ───────────────

function TrendingCarousel({ fetcher }) {
  const [data, setData]   = useState(null)
  const [loading, setLoading] = useState(true)
  const matchRef   = useRef(null)
  const discoverRef = useRef(null)

  useEffect(() => {
    fetcher().then(setData).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="h-52 flex items-center justify-center text-gray-200 text-sm mb-10">Carregando…</div>
  }

  if (!data) return null

  const { name, matched, discover, configured } = data
  const scroll = (ref, dir) => ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })

  if (!configured) {
    return (
      <section className="mb-10 p-5 rounded-xl border border-dashed border-gray-200 bg-gray-50">
        <p className="font-semibold text-gray-700 mb-1">{name}</p>
        <p className="text-sm text-gray-500 mb-3">
          Configure a chave <code className="bg-gray-100 px-1 rounded text-xs">NYT_API_KEY</code> no <code className="bg-gray-100 px-1 rounded text-xs">.env</code> para ativar esta lista.
        </p>
        <a
          href="https://developer.nytimes.com/get-started"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-indigo-600 hover:underline"
        >
          → Obter chave gratuita em developer.nytimes.com
        </a>
      </section>
    )
  }

  if (matched.length === 0 && discover.length === 0) return null

  return (
    <section className="mb-10">
      <p className="text-base font-bold text-gray-900 mb-4">{name}</p>

      {matched.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">No seu acervo · {matched.length} livros</p>
            <div className="flex gap-1">
              <button onClick={() => scroll(matchRef, -1)} className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm">‹</button>
              <button onClick={() => scroll(matchRef, 1)}  className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm">›</button>
            </div>
          </div>
          <div ref={matchRef} className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollSnapType: 'x mandatory' }}>
            {matched.map((book) => (
              <div key={book.id} className="flex-none w-36" style={{ scrollSnapAlign: 'start' }}>
                <BookCard book={book} />
              </div>
            ))}
          </div>
        </div>
      )}

      {discover.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Descobrir · {discover.length} livros</p>
            <div className="flex gap-1">
              <button onClick={() => scroll(discoverRef, -1)} className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm">‹</button>
              <button onClick={() => scroll(discoverRef, 1)}  className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm">›</button>
            </div>
          </div>
          <div ref={discoverRef} className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollSnapType: 'x mandatory' }}>
            {discover.map((book, i) => (
              <DiscoverCard key={book.isbn ?? i} book={book} />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

// ── Aba Em Alta ──────────────────────────────────────────────────

function EmAltaTab() {
  return (
    <>
      <TrendingCarousel fetcher={() => getTagLivrosTrending('best-sellers')} />
      <TrendingCarousel fetcher={() => getTagLivrosTrending('kits-curadoria')} />
      <TrendingCarousel fetcher={getGoogleBooksTrending} />
    </>
  )
}

// ── ReleaseCard — card unificado para lançamentos ────────────────

function ReleaseCard({ book }) {
  const navigate  = useNavigate()
  const [state, setState] = useState('idle') // idle | adding | done

  async function handleAdd() {
    setState('adding')
    try {
      await createBook({
        title: book.title,
        author: book.author,
        isbn: book.isbn || undefined,
        cover_url: book.cover_url || undefined,
        description: book.description || undefined,
      })
      setState('done')
    } catch {
      setState('idle')
    }
  }

  const inAcervo = book.in_acervo || state === 'done'

  return (
    <div
      className="relative group flex-none w-36 cursor-pointer"
      style={{ scrollSnapAlign: 'start' }}
      onClick={() => inAcervo && book.acervo_id && navigate(`/books/${book.acervo_id}`)}
    >
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-gradient-to-br from-slate-50 to-indigo-100 mb-2">
        {book.cover_url ? (
          <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-2 text-center">
            <span className="text-2xl mb-1">📘</span>
            <span className="text-xs text-gray-500 line-clamp-3">{book.title}</span>
          </div>
        )}

        {inAcervo ? (
          <div className="absolute inset-x-0 bottom-0 bg-indigo-600/80 text-white text-xs py-1 text-center">
            ✓ No acervo
          </div>
        ) : (
          <button
            onClick={(e) => { e.stopPropagation(); handleAdd() }}
            disabled={state === 'adding'}
            className="absolute inset-x-0 bottom-0 bg-indigo-600/90 backdrop-blur-sm text-white text-xs py-1.5 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-60"
          >
            {state === 'adding' ? '…' : '+ Adicionar'}
          </button>
        )}
      </div>

      <p className="text-xs font-medium text-gray-800 truncate">{book.title}</p>
      <p className="text-xs text-gray-500 truncate">{book.author}</p>
      {book.publisher && (
        <p className="text-xs text-indigo-400 truncate">{book.publisher}</p>
      )}
      {book.rating && (
        <p className="text-xs text-amber-500">{'★'.repeat(Math.round(book.rating))} {book.rating.toFixed(1)}</p>
      )}
    </div>
  )
}

// ── Aba Lançamentos ──────────────────────────────────────────────

function LancamentosTab() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const ref = useRef(null)

  useEffect(() => {
    getLancamentos()
      .then((d) => setBooks(d.books || []))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="py-20 text-center text-gray-300">Carregando lançamentos…</div>

  if (books.length === 0) {
    return (
      <div className="py-20 text-center text-gray-400">
        <p className="text-4xl mb-3">📦</p>
        <p>Nenhum lançamento encontrado. Verifique a conexão com o Google Books.</p>
      </div>
    )
  }

  const scroll = (dir) => ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">
            Lançamentos recentes · editoras brasileiras · {books.length} livros
          </p>
        </div>
        <div className="flex gap-1">
          <button onClick={() => scroll(-1)} className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">‹</button>
          <button onClick={() => scroll(1)}  className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors">›</button>
        </div>
      </div>
      <div ref={ref} className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide" style={{ scrollSnapType: 'x mandatory' }}>
        {books.map((book, i) => (
          <ReleaseCard key={book.isbn ?? i} book={book} />
        ))}
      </div>
    </section>
  )
}

// ── Página ───────────────────────────────────────────────────────

const TABS = [
  { value: 'premios',     label: 'Prêmios' },
  { value: 'generos',     label: 'Por Gênero' },
  { value: 'em-alta',     label: 'Em Alta' },
  { value: 'lancamentos', label: 'Lançamentos' },
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

      {tab === 'premios'     && <PremiosTab />}
      {tab === 'generos'     && <GenerosTab />}
      {tab === 'em-alta'     && <EmAltaTab />}
      {tab === 'lancamentos' && <LancamentosTab />}

      <style>{`.scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none}.scrollbar-hide::-webkit-scrollbar{display:none}`}</style>
    </div>
  )
}
