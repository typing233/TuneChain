import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const location = useLocation()

  const linkClass = (path: string) =>
    `px-4 py-2 rounded-lg transition-colors ${
      location.pathname === path
        ? 'bg-green-500 text-white'
        : 'text-gray-300 hover:text-white hover:bg-gray-700'
    }`

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="container mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="text-xl font-bold text-green-400">
          TuneChain
        </Link>
        <div className="flex gap-2">
          <Link to="/" className={linkClass('/')}>
            Download
          </Link>
          <Link to="/library" className={linkClass('/library')}>
            Library
          </Link>
        </div>
      </div>
    </nav>
  )
}
