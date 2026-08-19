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

function RingProgress({ percent, size = 96, stroke = 9 }) {
  const r = (size - stroke) / 2
  const circ = 2 * Math.PI * r
  const dash = (percent / 100) * circ
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e0e7ff" strokeWidth={stroke} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke="url(#ring-grad)" strokeWidth={stroke}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
      <defs>
        <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
      </defs>
    </svg>
  )
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
  { key: 'reading',      label: 'Lendo agora',   dot: 'bg-blue-500',    text: 'text-blue-700',    bg: 'bg-blue-50' },
  { key: 'read',         label: 'Lidos',          dot: 'bg-emerald-500', text: 'text-emerald-700', bg: 'bg-emerald-50' },
  { key: 'want_to_read', label: 'Quero ler',      dot: 'bg-amber-400',   text: 'text-amber-700',   bg: 'bg-amber-50' },
  { key: 'abandoned',    label: 'Abandonados',    dot: 'bg-red-400',     text: 'text-red-600',     bg: 'bg-red-50' },
]

const CURRENT_YEAR = new Date().getFullYear()


const STAT_ICONS = {
  total: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  ),
  read: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  want: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
    </svg>
  ),
  reading: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" />
    </svg>
  ),
}

function StatCard({ label, value, icon, iconBg, iconColor }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg} ${iconColor}`}>
        {icon}
      </div>
      <div>
        <p className="text-xl font-bold text-gray-900 leading-tight">{value ?? '—'}</p>
        <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      </div>
    </div>
  )
}

export default function Profile() {
  const [stats, setStats] = useState(null)
  const [booksByStatus, setBooksByStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [goal, setGoal] = useState(() => parseInt(localStorage.getItem('reading_goal') || '12', 10))
  const [editingGoal, setEditingGoal] = useState(false)
  const [goalInput, setGoalInput] = useState('')

  useEffect(() => { load() }, [])

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
  const readingNow = dist['reading'] || 0
  const readThisYear = stats?.books_read_this_year ?? 0
  const progress = goal > 0 ? Math.min((readThisYear / goal) * 100, 100) : 0

  const now = new Date()
  const monthsElapsed = now.getMonth() + 1 + now.getDate() / 31
  const expectedByNow = goal > 0 ? (goal * monthsElapsed) / 12 : 0
  const onTrack = readThisYear >= expectedByNow
  const remaining = Math.max(goal - readThisYear, 0)
  const monthsLeft = 12 - now.getMonth() - now.getDate() / 31
  const paceNeeded = monthsLeft > 0 && remaining > 0 ? (remaining / monthsLeft).toFixed(1) : null

  function paceMessage() {
    if (readThisYear >= goal) return { text: 'Meta alcançada! 🎉', color: 'text-emerald-600' }
    if (onTrack) return { text: 'Você está no ritmo', color: 'text-emerald-600' }
    const behind = Math.ceil(expectedByNow - readThisYear)
    return { text: `${behind} livro${behind > 1 ? 's' : ''} atrás do ritmo`, color: 'text-amber-600' }
  }
  const pace = paceMessage()

  if (loading) {
    return <div className="flex-1 flex items-center justify-center text-gray-400 py-32">Carregando...</div>
  }

  return (
    <div className="max-w-4xl mx-auto px-8 py-8">

      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden mb-8 shadow-sm">
        <div className="h-28 bg-gradient-to-br from-indigo-500 via-violet-500 to-purple-600">
          {/* decoração sutil */}
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

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <StatCard label="Total de livros" value={stats?.total_books}         icon={STAT_ICONS.total}   iconBg="bg-indigo-50"  iconColor="text-indigo-500" />
        <StatCard label="Lidos"           value={readTotal}                  icon={STAT_ICONS.read}    iconBg="bg-emerald-50" iconColor="text-emerald-500" />
        <StatCard label="Quero ler"       value={dist['want_to_read'] || 0}  icon={STAT_ICONS.want}    iconBg="bg-amber-50"   iconColor="text-amber-500" />
        <StatCard label="Lendo agora"     value={readingNow}                 icon={STAT_ICONS.reading} iconBg="bg-blue-50"    iconColor="text-blue-500" />
      </div>

      {/* Meta anual */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5 mb-6 flex items-center gap-6">
        <div className="relative flex-shrink-0">
          <RingProgress percent={progress} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-indigo-600">{Math.round(progress)}%</span>
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-gray-800">Meta de leitura {CURRENT_YEAR}</h3>
            <span className={`text-xs font-semibold ${pace.color}`}>{pace.text}</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {readThisYear}
            <span className="text-base font-normal text-gray-400"> / </span>
            {editingGoal ? (
              <input
                autoFocus
                type="number"
                min="1"
                value={goalInput}
                onChange={e => setGoalInput(e.target.value)}
                onBlur={saveGoal}
                onKeyDown={handleGoalKey}
                className="w-14 border-b-2 border-indigo-400 text-center text-2xl font-bold text-indigo-600 bg-transparent outline-none"
              />
            ) : (
              <button
                onClick={() => { setGoalInput(String(goal)); setEditingGoal(true) }}
                className="text-gray-400 hover:text-indigo-600 font-bold transition-colors"
                title="Clique para editar a meta"
              >
                {goal}
              </button>
            )}
            <span className="text-sm font-normal text-gray-400 ml-1">livros</span>
          </p>
          <div className="flex items-center gap-4 mt-2">
            {remaining > 0 && (
              <span className="text-xs text-gray-400">
                <span className="font-semibold text-gray-600">{remaining}</span> restantes
              </span>
            )}
            {paceNeeded && remaining > 0 && (
              <span className="text-xs text-gray-400">
                <span className="font-semibold text-gray-600">{paceNeeded}/mês</span> para fechar
              </span>
            )}
            <span className="text-xs text-gray-400 ml-auto">clique no total para editar</span>
          </div>
        </div>
      </div>

      {/* Listas por status */}
      <div className="space-y-6 mb-6">
        {STATUS_SECTIONS.map(({ key, label, dot, text, bg }) => {
          const books = booksByStatus[key]
          if (!books?.length) return null
          return (
            <div key={key} className="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5">
              <div className="flex items-center gap-2 mb-4">
                <span className={`w-2 h-2 rounded-full ${dot}`} />
                <h3 className="text-sm font-semibold text-gray-800">{label}</h3>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${bg} ${text} ml-1`}>
                  {books.length}
                </span>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-1 scrollbar-none">
                {books.map(book => (
                  <MiniCover key={book.id} book={book} />
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Gêneros favoritos */}
      {stats?.favorite_genres?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Gêneros favoritos</h3>
          <div className="flex flex-wrap gap-2">
            {stats.favorite_genres.map(([genre, count], i) => {
              const opacity = i === 0 ? 'bg-indigo-600 text-white' : i === 1 ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'
              return (
                <span key={genre} className={`px-3 py-1.5 text-sm rounded-full font-medium ${opacity}`}>
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
