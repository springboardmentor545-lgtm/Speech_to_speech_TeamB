import { Routes, Route, NavLink } from 'react-router-dom'
import { FileAudio, Mic, BarChart3, Settings } from 'lucide-react'
import BatchTranscription from './pages/BatchTranscription'
import LiveTranscription from './pages/LiveTranscription'
import Analytics from './pages/Analytics'

function Layout() {
  const navItems = [
    { name: 'Batch Processing', path: '/', icon: FileAudio },
    { name: 'Live Recognition', path: '/live', icon: Mic },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  ]

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 glass-panel border-r flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <FileAudio className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Speech Platform</h1>
              <p className="text-xs text-gray-400">Team B Edition</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all">
            <Settings className="w-5 h-5" />
            <span className="font-medium">Settings</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<BatchTranscription />} />
            <Route path="/live" element={<LiveTranscription />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return <Layout />
}
