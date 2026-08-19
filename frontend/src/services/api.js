const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const getBooks = () => request('/books/')
export const getBook = (id) => request(`/books/${id}`)
export const createBook = (data) => request('/books/', { method: 'POST', body: data })
export const updateBook = (id, data) => request(`/books/${id}`, { method: 'PUT', body: data })
export const deleteBook = (id) => request(`/books/${id}`, { method: 'DELETE' })
export const getTags = () => request('/books/tags')
export const getBooksByTag = (tag) => request(`/books/by-tag/${encodeURIComponent(tag)}`)
export const getBooksByStatus = (status) => request(`/books/by-status/${status}`)

export const updateBookStatus = (id, status) =>
  request(`/books/${id}/status`, { method: 'PATCH', body: { status } })
export const getSimilarBooks = (id, limit = 5) =>
  request(`/books/${id}/similar?limit=${limit}`)

export const getDiscoverBooks = (recentlyViewed = []) => {
  const qs = recentlyViewed.length ? `?recently_viewed=${recentlyViewed.join(',')}` : ''
  return request(`/books/discover${qs}`)
}

export const getAnnotations = (bookId) => request(`/annotations/book/${bookId}`)
export const createAnnotation = (data) => request('/annotations/', { method: 'POST', body: data })
export const deleteAnnotation = (id) => request(`/annotations/${id}`, { method: 'DELETE' })

export const chat = (query) => request('/chat/', { method: 'POST', body: { query } })
export const getProfile = () => request('/profile/')

export const getCuradoriaCollections = () => request('/collections/')
export const getCollectionBooks = (slug) => request(`/collections/${slug}/books`)
export const initializeCuradoria = () => request('/collections/initialize', { method: 'POST' })
