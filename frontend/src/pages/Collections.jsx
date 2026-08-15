import { useEffect, useRef, useState } from 'react'
import BookCard from '../components/BookCard'
import { getBooksByTag, getTags } from '../services/api'

const TAG_LABELS = {
  'Nobel de Literatura':    { emoji: '🏅', desc: 'Vencedores do Nobel de Literatura' },
  'Booker Prize':           { emoji: '📖', desc: 'Vencedores do Booker Prize' },
  'Prêmio Jabuti':          { emoji: '🐢', desc: 'Vencedores do Prêmio Jabuti' },
  'Escritas por Mulheres':  { emoji: '✍️', desc: 'Obras de autoras mulheres' },
}

function Carousel({ tag, books }) {
  const meta = TAG_LABELS[tag] ?? { emoji: '🏷️', desc: tag }
  const ref  = useRef(null)

  function scroll(dir) {
    ref.current?.scrollBy({ left: dir * 240, behavior: 'smooth' })
  }

  return (
    <section className="mb-10">
      <div className="flex items-baseline gap-3 mb-3">
        <span className="text-xl">{meta.emoji}</span>
        <div>
          <h2 className="text-lg font-bold text-gray-900">{tag}</h2>
          <p className="text-xs text-gray-400">{meta.desc} · {books.length} livros</p>
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

      <div
        ref={ref}
        className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {books.map((book) => (
          <div
            key={book.id}
            className="flex-none w-36"
            style={{ scrollSnapAlign: 'start' }}
          >
            <BookCard book={book} />
          </div>
        ))}
      </div>
    </section>
  )
}

export default function Collections() {
  const [tags, setTags]         = useState([])
  const [data, setData]         = useState({})   // { tag: books[] }
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    getTags().then(async (tagList) => {
      // Filtra só as tags curadas (as que têm label definido)
      const curadas = tagList.filter((t) => TAG_LABELS[t])
      setTags(curadas)

      const entries = await Promise.all(
        curadas.map(async (tag) => [tag, await getBooksByTag(tag)])
      )
      setData(Object.fromEntries(entries))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Carregando coleções...</div>
  }

  if (tags.length === 0) {
    return (
      <div className="p-8 text-center text-gray-400">
        <p className="text-4xl mb-3">🏷️</p>
        <p>Nenhuma coleção ainda.</p>
      </div>
    )
  }

  // Ordem de exibição preferencial
  const ORDER = ['Nobel de Literatura', 'Booker Prize', 'Prêmio Jabuti', 'Escritas por Mulheres']
  const sorted = [...tags].sort((a, b) => {
    const ia = ORDER.indexOf(a), ib = ORDER.indexOf(b)
    if (ia === -1 && ib === -1) return a.localeCompare(b)
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Coleções</h2>
        <p className="text-sm text-gray-500 mt-0.5">Livros premiados e catálogos de editoras</p>
      </div>

      {sorted.map((tag) => (
        <Carousel key={tag} tag={tag} books={data[tag] ?? []} />
      ))}

      <style>{`
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  )
}
