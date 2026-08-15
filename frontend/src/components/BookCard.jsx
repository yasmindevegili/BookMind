import React, { useState } from 'react'
import { Link } from 'react-router-dom'

const STATUS = {
  read:         { label: 'Lido',        css: 'bg-emerald-100 text-emerald-700' },
  reading:      { label: 'Lendo',       css: 'bg-blue-100 text-blue-700' },
  want_to_read: { label: 'Quero ler',   css: 'bg-amber-100 text-amber-700' },
  abandoned:    { label: 'Abandonado',  css: 'bg-red-100 text-red-600' },
}

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

function Stars({ rating }) {
  const full = Math.round(rating)
  return (
    <span className="text-amber-400 text-xs leading-none">
      {'★'.repeat(full)}{'☆'.repeat(5 - full)}
    </span>
  )
}

function PlaceholderCover({ title, author }) {
  const [dark, light] = PALETTE[hashTitle(title)]
  return (
    <div
      className="w-full h-full flex flex-col items-center justify-center px-3 select-none"
      style={{ background: `linear-gradient(160deg, ${dark} 0%, ${light} 100%)` }}
    >
      <span
        className="text-6xl font-black leading-none mb-3 opacity-30"
        style={{ color: '#ffffff' }}
      >
        {title.charAt(0).toUpperCase()}
      </span>
      <p className="text-center text-white/90 text-xs font-semibold line-clamp-3 leading-snug">
        {title}
      </p>
      <p className="text-center text-white/50 text-xs mt-1.5 line-clamp-1">{author}</p>
    </div>
  )
}

export default function BookCard({ book, onWantToRead }) {
  const cover  = betterCover(book.cover_url)
  const status = STATUS[book.status] ?? null
  const [imgFailed, setImgFailed] = useState(false)
  const [adding, setAdding] = useState(false)

  async function handleWantToRead(e) {
    e.preventDefault()
    e.stopPropagation()
    if (!onWantToRead || adding) return
    setAdding(true)
    try {
      await onWantToRead(book)
    } finally {
      setAdding(false)
    }
  }

  const isWantToRead = book.status === 'want_to_read'

  return (
    <Link to={`/books/${book.id}`} className="group block">
      {/* Capa */}
      <div
        className="relative w-full aspect-[2/3] rounded-sm overflow-hidden transition-all duration-300
          shadow-[0_2px_8px_rgba(0,0,0,0.12),0_8px_20px_rgba(0,0,0,0.08)]
          group-hover:shadow-[0_4px_16px_rgba(0,0,0,0.18),0_12px_28px_rgba(0,0,0,0.12)]
          group-hover:-translate-y-1.5"
      >
        {cover && !imgFailed ? (
          <img
            src={cover}
            alt={book.title}
            className="w-full h-full object-cover"
            onError={() => setImgFailed(true)}
            onLoad={(e) => {
              if (e.target.naturalWidth < 10) setImgFailed(true)
            }}
          />
        ) : (
          <PlaceholderCover title={book.title} author={book.author} />
        )}

        {/* Overlay com título + autor ao hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-3">
          <p className="text-white text-xs font-semibold line-clamp-2 leading-snug drop-shadow">{book.title}</p>
          <p className="text-white/70 text-xs mt-0.5 line-clamp-1 drop-shadow">{book.author}</p>
          {book.rating && <Stars rating={book.rating} />}
        </div>

        {/* Botão Quero Ler — sempre visível se ativo, hover nos demais */}
        {onWantToRead && (
          <button
            onClick={handleWantToRead}
            disabled={adding}
            title={isWantToRead ? 'Remover de Quero Ler' : 'Quero Ler'}
            className={`absolute top-2 right-2 transition-all duration-200
              rounded-full w-7 h-7 flex items-center justify-center shadow-md disabled:opacity-50
              ${isWantToRead
                ? 'opacity-100 bg-amber-400 text-white hover:bg-amber-500'
                : 'opacity-0 group-hover:opacity-100 bg-white/90 text-gray-700 hover:bg-amber-400 hover:text-white'
              }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5">
              <path fillRule="evenodd" d="M6.32 2.577a49.255 49.255 0 0 1 11.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 0 1-1.085.67L12 18.089l-7.165 3.583A.75.75 0 0 1 3.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93Z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      {book.rating && (
        <div className="mt-2 px-0.5">
          <span className="text-amber-400 text-xs">{'★'.repeat(Math.round(book.rating))}</span>
        </div>
      )}
    </Link>
  )
}
