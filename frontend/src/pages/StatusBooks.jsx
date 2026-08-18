import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BookCard from '../components/BookCard'
import { getBooksByStatus, updateBookStatus } from '../services/api'

const STATUS_META = {
  read:         { label: 'Livros Lidos',   empty: 'Nenhum livro marcado como lido ainda.' },
  want_to_read: { label: 'Quero Ler',      empty: 'Sua lista de desejos está vazia.' },
  reading:      { label: 'Lendo',          empty: 'Você não está lendo nenhum livro no momento.' },
  abandoned:    { label: 'Abandonados',    empty: 'Nenhum livro abandonado. Boa leitura!' },
}

export default function StatusBooks() {
  const { statusKey } = useParams()
  const [books, setBooks]   = useState([])
  const [loading, setLoading] = useState(true)

  const meta = STATUS_META[statusKey] ?? { label: statusKey, empty: 'Nenhum livro encontrado.' }

  useEffect(() => {
    setLoading(true)
    getBooksByStatus(statusKey)
      .then(setBooks)
      .finally(() => setLoading(false))
  }, [statusKey])

  async function handleWantToRead(book) {
    const updated = await updateBookStatus(book.id, book.status === 'want_to_read' ? 'none' : 'want_to_read')
    setBooks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)).filter((b) => b.status === statusKey))
  }

  async function handleRead(book) {
    const updated = await updateBookStatus(book.id, book.status === 'read' ? 'none' : 'read')
    setBooks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)).filter((b) => b.status === statusKey))
  }

  return (
    <div className="px-12 py-10 max-w-6xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <Link to="/profile" className="text-gray-400 hover:text-gray-600 transition-colors">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{meta.label}</h2>
          {!loading && <p className="text-sm text-gray-400 mt-0.5">{books.length} livro{books.length !== 1 ? 's' : ''}</p>}
        </div>
      </div>

      {/* Conteúdo */}
      {loading ? (
        <div className="text-center py-20 text-gray-400">Carregando...</div>
      ) : books.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-4xl mb-3">📚</p>
          <p>{meta.empty}</p>
          <Link to="/" className="mt-4 inline-block text-sm text-indigo-600 hover:underline">
            Ir para a Biblioteca
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-8">
          {books.map((book) => (
            <BookCard key={book.id} book={book} onWantToRead={handleWantToRead} onRead={handleRead} />
          ))}
        </div>
      )}
    </div>
  )
}
