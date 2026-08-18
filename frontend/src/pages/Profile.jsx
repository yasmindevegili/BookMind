import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getBooksByStatus, getProfile } from '../services/api'

const PALETTE = [
  ['#1e3a5f', '#2d6a9f'],
  ['#3b1f5e', '#7b4fa6'],
  ['#1f3d2b', '#3a7d54'],
  ['#5c1f1f', '#a83232'],
  ['#2e3b1f', '#6b8c3a'],
  ['#1f2e4a', '#3a5f8c'],
  ['#4a2010', '#9c4a20'],
  ['#1a3a3a', '#2e7070'],
]

function hashTitle(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0
  return h % PALETTE.length
}

function betterCover(url) {
  if (!url) return null
  return url.replace(/zoom=\d+/, 'zoom=0').replace('&edge=curl', '')
}

function MiniCover({ book }) {
  const [failed, setFailed] = useState(false)
  const cover = betterCover(book.cover_url)
  const [dark, light] = PALETTE[hashTitle(book.title)]

  return (
    <Link to={`/books/${book.id}`} title={book.title} className="group block flex-shrink-0">
      <div className="w-16 aspect-[2/3] rounded-lg overflow-hidden shadow-sm group-hover:shadow-lg group-hover:-translate-y-1 transition-all duration-200">
        {cover && !failed ? (
          <img src={cover} alt={book.title} className="w-full h-full object-cover" onError={() => setFailed(true)} />
        ) : (
          <div className="w-full h-full flex items-center justify-center" style={{ background: `linear-gradient(160deg, ${dark} 0%, ${light} 100%)` }}>
            <span className="text-white/80 text-lg font-black">{book.title.charAt(0)}</span>
          </div>
        )}
      </div>
    </Link>
  )
}

const STATUS_CARDS = [
  { key: 'read',         label: 'Livros Lidos',  iconBg: 'bg-emerald-50', iconColor: 'text-emerald-500', ring: 'hover:ring-emerald-200',
    icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> },
  { key: 'want_to_read', label: 'Quero Ler',     iconBg: 'bg-amber-50',   iconColor: 'text-amber-500',   ring: 'hover:ring-amber-200',
    icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}><path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg> },
  { key: 'reading',      label: 'Lendo',          iconBg: 'bg-blue-50',    iconColor: 'text-blue-500',    ring: 'hover:ring-blue-200',
    icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg> },
  { key: 'abandoned',    label: 'Abandonados',    iconBg: 'bg-red-50',     iconColor: 'text-red-400',     ring: 'hover:ring-red-200',
    icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg> },
]

const CURRENT_YEAR = new Date().getFullYear()

export default function Profile() {
  const [stats, setStats]         = useState(null)
  const [booksThisYear, setBooksThisYear] = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const [profile, readBooks] = await Promise.all([
        getProfile(),
        getBooksByStatus('read'),
      ])
      setStats(profile)
      const thisYear = readBooks.filter(b => {
        if (!b.finished_at) return false
        return new Date(b.finished_at).getFullYear() === CURRENT_YEAR
      })
      setBooksThisYear(thisYear)
    } finally {
      setLoading(false)
    }
  }

  const dist = stats?.status_distribution || {}

  if (loading) {
    return <div className="flex-1 flex items-center justify-center text-gray-400 py-32">Carregando...</div>
  }

  return (
    <div className="max-w-4xl mx-auto px-8 py-8">

      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden mb-8 shadow-sm">
        <div className="h-28 bg-gradient-to-br from-indigo-500 via-violet-500 to-purple-600">
          <div className="absolute inset-0 opacity-20"
            style={{
              backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 20%, white 1px, transparent 1px)',
              backgroundSize: '32px 32px',
            }}
          />
        </div>
        <div className="bg-white px-8 pb-6">
          <div className="flex items-end gap-5 -mt-10">
            <div className="relative flex-shrink-0">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 ring-4 ring-white shadow-md flex items-center justify-center">
                <span className="text-white text-2xl font-bold select-none">Y</span>
              </div>
              <button
                title="Alterar foto (em breve)"
                className="absolute bottom-0 right-0 w-6 h-6 bg-white rounded-full border border-gray-200 flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586l-1.207-1.207A1 1 0 0012.5 3.5h-5a1 1 0 00-.707.293L5.586 5H4zm6 9a3 3 0 110-6 3 3 0 010 6z" />
                </svg>
              </button>
            </div>
            <div className="pb-1">
              <h2 className="text-xl font-bold text-gray-900">Yasmin</h2>
              <p className="text-sm text-gray-400">leitora apaixonada</p>
            </div>
          </div>
        </div>
      </div>

      {/* Cards de status — clicáveis */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {STATUS_CARDS.map(({ key, label, icon, iconBg, iconColor, ring }) => (
          <Link
            key={key}
            to={`/status/${key}`}
            className={`bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-5 flex items-center gap-4 ring-2 ring-transparent transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 ${ring}`}
          >
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg} ${iconColor}`}>
              {icon}
            </div>
            <div>
              <p className="text-xl font-bold text-gray-900 leading-tight">{dist[key] ?? 0}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Lidos esse ano */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-sm font-semibold text-gray-800">Lidos em {CURRENT_YEAR}</h3>
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
            {booksThisYear.length}
          </span>
        </div>
        {booksThisYear.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum livro marcado como lido em {CURRENT_YEAR} ainda.</p>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
            {booksThisYear.map(book => <MiniCover key={book.id} book={book} />)}
          </div>
        )}
      </div>

      {/* Minhas Coleções */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5 mb-6">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-sm font-semibold text-gray-800">Minhas Coleções</h3>
          <span className="text-xs bg-indigo-50 text-indigo-500 font-medium px-2 py-0.5 rounded-full">em breve</span>
        </div>
        <p className="text-sm text-gray-400 leading-relaxed">
          Crie coleções personalizadas com a ajuda da IA — descreva um tema e o BookMind monta a lista por você.
        </p>
      </div>

      {/* Gêneros favoritos */}
      {stats?.favorite_genres?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Gêneros favoritos</h3>
          <div className="flex flex-wrap gap-2">
            {stats.favorite_genres.map(([genre, count], i) => {
              const style = i === 0 ? 'bg-indigo-600 text-white' : i === 1 ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'
              return (
                <span key={genre} className={`px-3 py-1.5 text-sm rounded-full font-medium ${style}`}>
                  {genre}
                  <span className="ml-1.5 opacity-60 text-xs">{count}</span>
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
