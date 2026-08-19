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
      <div className="w-14 aspect-[2/3] rounded overflow-hidden shadow-sm group-hover:shadow-md group-hover:-translate-y-0.5 transition-all duration-200">
        {cover && !failed ? (
          <img
            src={cover}
            alt={book.title}
            className="w-full h-full object-cover"
            onError={() => setFailed(true)}
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ background: `linear-gradient(160deg, ${dark} 0%, ${light} 100%)` }}
          >
            <span className="text-white/80 text-lg font-black">{book.title.charAt(0)}</span>
          </div>
        )}
      </div>
    </Link>
  )
}

const STATUS_SECTIONS = [
  { key: 'read',         label: 'Lidos',        badge: 'bg-emerald-100 text-emerald-700' },
  { key: 'reading',      label: 'Lendo',        badge: 'bg-blue-100 text-blue-700' },
  { key: 'want_to_read', label: 'Quero Ler',    badge: 'bg-amber-100 text-amber-700' },
  { key: 'abandoned',    label: 'Abandonados',  badge: 'bg-red-100 text-red-600' },
]

const CURRENT_YEAR = new Date().getFullYear()

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4">
      <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

function Stars({ rating }) {
  const full = Math.round(rating)
  return (
    <span className="text-amber-400">
      {'★'.repeat(full)}{'☆'.repeat(5 - full)}
    </span>
  )
}

export default function Profile() {
  const [stats, setStats] = useState(null)
  const [booksByStatus, setBooksByStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [goal, setGoal] = useState(() => parseInt(localStorage.getItem('reading_goal') || '12', 10))
  const [editingGoal, setEditingGoal] = useState(false)
  const [goalInput, setGoalInput] = useState('')

  useEffect(() => {
    load()
  }, [])

  async function load() {
    try {
      const profile = await getProfile()
      setStats(profile)

      const dist = profile.status_distribution || {}
      const results = await Promise.all(
        STATUS_SECTIONS
          .filter(s => (dist[s.key] || 0) > 0)
          .map(async s => [s.key, await getBooksByStatus(s.key)])
      )
      setBooksByStatus(Object.fromEntries(results))
    } finally {
      setLoading(false)
    }
  }

  function startEditGoal() {
    setGoalInput(String(goal))
    setEditingGoal(true)
  }

  function saveGoal() {
    const val = parseInt(goalInput, 10)
    if (val > 0) {
      setGoal(val)
      localStorage.setItem('reading_goal', String(val))
    }
    setEditingGoal(false)
  }

  function handleGoalKey(e) {
    if (e.key === 'Enter') saveGoal()
    if (e.key === 'Escape') setEditingGoal(false)
  }

  const dist = stats?.status_distribution || {}
  const readTotal = dist['read'] || 0
  const readThisYear = stats?.books_read_this_year ?? 0
  const progress = goal > 0 ? Math.min((readThisYear / goal) * 100, 100) : 0
  const avgRating = stats?.average_rating

  if (loading) {
    return <div className="flex-1 flex items-center justify-center text-gray-400 py-32">Carregando...</div>
  }

  return (
    <div className="px-12 py-10 max-w-5xl">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Meu Perfil</h2>
        <p className="text-sm text-gray-500 mt-0.5">Resumo da sua biblioteca</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard label="Total de livros" value={stats?.total_books} />
        <StatCard label="Lidos" value={readTotal} />
        <StatCard label="Quero Ler" value={dist['want_to_read'] || 0} />
        <StatCard
          label="Avaliação média"
          value={avgRating ? <Stars rating={avgRating} /> : '—'}
          sub={avgRating ? `${avgRating.toFixed(1)} / 5` : null}
        />
      </div>

      {/* Meta anual */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-6 py-5 mb-8">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-700">Meta de leitura {CURRENT_YEAR}</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {readThisYear} de{' '}
              {editingGoal ? (
                <input
                  autoFocus
                  type="number"
                  min="1"
                  value={goalInput}
                  onChange={e => setGoalInput(e.target.value)}
                  onBlur={saveGoal}
                  onKeyDown={handleGoalKey}
                  className="w-12 border-b border-indigo-400 text-center text-xs text-indigo-600 bg-transparent outline-none"
                />
              ) : (
                <button
                  onClick={startEditGoal}
                  className="text-indigo-600 hover:underline font-medium"
                >
                  {goal}
                </button>
              )}{' '}
              livros em {CURRENT_YEAR}
            </p>
          </div>
          <span className="text-lg font-bold text-gray-800">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2.5">
          <div
            className="bg-indigo-500 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Clique no número da meta para editar · progresso baseado em livros com <code className="text-xs">finished_at</code> em {CURRENT_YEAR}
        </p>
      </div>

      {/* Listas por status */}
      <div className="space-y-8">
        {STATUS_SECTIONS.map(({ key, label, badge }) => {
          const books = booksByStatus[key]
          if (!books?.length) return null
          return (
            <section key={key}>
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-base font-semibold text-gray-800">{label}</h3>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${badge}`}>
                  {books.length}
                </span>
              </div>
              <div className="flex gap-3 flex-wrap">
                {books.map(book => (
                  <MiniCover key={book.id} book={book} />
                ))}
              </div>
            </section>
          )
        })}
      </div>

      {/* Gêneros favoritos */}
      {stats?.favorite_genres?.length > 0 && (
        <div className="mt-8 bg-white rounded-xl border border-gray-100 shadow-sm px-6 py-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Gêneros favoritos</h3>
          <div className="flex flex-wrap gap-2">
            {stats.favorite_genres.map(([genre, count]) => (
              <span key={genre} className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm rounded-full">
                {genre} <span className="text-indigo-400 text-xs">({count})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
