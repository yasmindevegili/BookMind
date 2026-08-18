import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import BookDetail from './pages/BookDetail'
import Chat from './pages/Chat'
import Collections from './pages/Collections'
import Library from './pages/Library'
import Profile from './pages/Profile'
import StatusBooks from './pages/StatusBooks'
import './index.css'

function NavItem({ to, label, exact }) {
  return (
    <NavLink
      to={to}
      end={exact}
      className={({ isActive }) =>
        `block px-4 py-2 rounded-lg transition-colors ${
          isActive
            ? 'bg-indigo-50 text-indigo-700 font-medium'
            : 'text-gray-600 hover:bg-gray-100'
        }`
      }
    >
      {label}
    </NavLink>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <nav className="w-56 bg-white border-r border-gray-200 p-4 flex flex-col">
          <div className="mb-8">
            <h1 className="text-xl font-bold text-indigo-600">📚 BookMind</h1>
            <p className="text-xs text-gray-400 mt-1">Sua biblioteca inteligente</p>
          </div>
          <ul className="space-y-1">
            <li><NavItem to="/" label="Biblioteca" exact /></li>
            <li><NavItem to="/chat" label="Chat" /></li>
            <li><NavItem to="/profile" label="Perfil" /></li>
          </ul>
        </nav>

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Library />} />
            <Route path="/collections" element={<Collections />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/books/:id" element={<BookDetail />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/status/:statusKey" element={<StatusBooks />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
