import { ReactNode } from 'react'
import Navbar from './Navbar'
import PlayerBar from './Player/PlayerBar'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAudioPlayer } from '../hooks/useAudioPlayer'

export default function Layout({ children }: { children: ReactNode }) {
  useWebSocket()
  useAudioPlayer()

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto px-4 py-6 pb-28">
        {children}
      </main>
      <PlayerBar />
    </div>
  )
}
