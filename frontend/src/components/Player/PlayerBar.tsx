import { useStore } from '../../store'

export default function PlayerBar() {
  const { currentTrack, isPlaying } = useStore((s) => s.player)
  const pause = useStore((s) => s.pause)
  const resume = useStore((s) => s.resume)
  const playNext = useStore((s) => s.playNext)
  const playPrev = useStore((s) => s.playPrev)

  if (!currentTrack) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 px-4 py-3 z-50">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {currentTrack.cover_art_url && (
            <img
              src={currentTrack.cover_art_url}
              alt=""
              className="w-10 h-10 rounded object-cover"
            />
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{currentTrack.title}</p>
            <p className="text-xs text-gray-400 truncate">{currentTrack.artist}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={playPrev}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
            </svg>
          </button>

          <button
            onClick={isPlaying ? pause : resume}
            className="w-9 h-9 bg-white rounded-full flex items-center justify-center text-black hover:scale-105 transition-transform"
          >
            {isPlaying ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
              </svg>
            ) : (
              <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            )}
          </button>

          <button
            onClick={playNext}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
            </svg>
          </button>
        </div>

        <div className="flex-1" />
      </div>
    </div>
  )
}
