import { useEffect, useRef, useState } from 'react'
import BookCard from '../components/BookCard'
import { getCollectionBooks, getCuradoriaCollections, initializeCuradoria } from '../services/api'

const COLLECTION_META = {
  'Nobel de Literatura':  { emoji: '🏅', desc: 'Vencedores do Nobel de Literatura' },
  'Booker Prize':         { emoji: '📖', desc: 'Vencedores do Booker Prize' },
  'Prêmio Jabuti':        { emoji: '🐢', desc: 'Vencedores do Prêmio Jabuti' },
  'Prêmio Pulitzer':      { emoji: '🏆', desc: 'Vencedores do Prêmio Pulitzer' },
  'Prêmio Camões':        { emoji: '✒️', desc: 'Vencedores do Prêmio Camões' },
}

function Carousel({ collection }) {
  const meta = COLLECTION_META[collection.name] ?? { emoji: '🏷️', desc: collection.name }
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const ref = useRef(null)

  useEffect(() => {
    getCollectionBooks(collection.slug)
      .then(setBooks)
      .finally(() => setLoading(false))
  }, [collection.slug])

  const scroll = (dir) => ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })

  return (
    <section className="mb-12">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">{meta.emoji}</span>
        <div>
          <h2 className="text-lg font-bold text-gray-900">{collection.name}</h2>
          <p className="text-xs text-gray-400">{meta.desc} · {collection.book_count} livros</p>
        </div>
        <div className="ml-auto flex gap-1">
          <button
            onClick={() => scroll(-1)}
            className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors"
          >‹</button>
          <button
            onClick={() => scroll(1)}
            className="w-7 h-7 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm transition-colors"
          >›</button>
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-gray-400 text-sm">Carregando...</div>
      ) : books.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-400 text-sm">Nenhum livro nesta coleção.</div>
      ) : (
        <div
          ref={ref}
          className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide"
          style={{ scrollSnapType: 'x mandatory' }}
        >
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

export default function Curadoria() {
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [initializing, setInitializing] = useState(false)

  async function load() {
    setLoading(true)
    try {
      setCollections(await getCuradoriaCollections())
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

  const hasContent = collections.some((c) => c.book_count > 0)

  return (
    <div className="px-12 py-10">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Curadoria</h2>
        <p className="text-sm text-gray-400 mt-0.5">Listas editoriais — prêmios e destaques literários</p>
      </div>

      {loading ? (
        <div className="py-24 text-center text-gray-400">Carregando curadoria...</div>
      ) : !hasContent ? (
        <div className="py-24 text-center">
          <p className="text-5xl mb-4">🏆</p>
          <p className="text-gray-500 font-medium mb-2">Curadoria ainda não indexada</p>
          <p className="text-sm text-gray-400 mb-6">
            Clique em indexar para detectar automaticamente livros premiados no seu acervo.
          </p>
          <button
            onClick={handleInitialize}
            disabled={initializing}
            className="px-5 py-2.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {initializing ? 'Indexando…' : 'Indexar curadoria'}
          </button>
        </div>
      ) : (
        <>
          {collections.filter((c) => c.book_count > 0).map((c) => (
            <Carousel key={c.slug} collection={c} />
          ))}
          <style>{`.scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none}.scrollbar-hide::-webkit-scrollbar{display:none}`}</style>
        </>
      )}
    </div>
  )
}
