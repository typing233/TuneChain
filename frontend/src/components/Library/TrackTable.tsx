import { useStore } from '../../store'
import { LibraryTrack } from '../../api/library'

interface Props {
  tracks: LibraryTrack[]
}

export default function TrackTable({ tracks }: Props) {
  const play = useStore((s) => s.play)
  const setQueue = useStore((s) => s.setQueue)
  const currentTrack = useStore((s) => s.player.currentTrack)

  const handlePlay = (track: LibraryTrack) => {
    setQueue(tracks)
    play(track)
  }

  const formatDuration = (ms: number | null) => {
    if (!ms) return '--:--'
    const sec = Math.floor(ms / 1000)
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  if (tracks.length === 0) {
    return <p className="text-gray-400 text-center py-8">No tracks found.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-700">
            <th className="text-left py-2 px-2 w-10">#</th>
            <th className="text-left py-2 px-2">Title</th>
            <th className="text-left py-2 px-2 hidden md:table-cell">Artist</th>
            <th className="text-left py-2 px-2 hidden lg:table-cell">Album</th>
            <th className="text-right py-2 px-2">Duration</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((track, idx) => (
            <tr
              key={track.id}
              onClick={() => handlePlay(track)}
              className={`cursor-pointer hover:bg-gray-700/50 transition-colors ${
                currentTrack?.id === track.id ? 'bg-gray-700/70' : ''
              }`}
            >
              <td className="py-2 px-2 text-gray-400">{idx + 1}</td>
              <td className="py-2 px-2">
                <div className="flex items-center gap-3">
                  {track.cover_art_url && (
                    <img
                      src={track.cover_art_url}
                      alt=""
                      className="w-8 h-8 rounded object-cover"
                    />
                  )}
                  <div className="min-w-0">
                    <p className={`truncate ${currentTrack?.id === track.id ? 'text-green-400' : 'text-white'}`}>
                      {track.title}
                    </p>
                    <p className="text-gray-400 text-xs truncate md:hidden">{track.artist}</p>
                  </div>
                </div>
              </td>
              <td className="py-2 px-2 text-gray-300 hidden md:table-cell">{track.artist}</td>
              <td className="py-2 px-2 text-gray-400 hidden lg:table-cell">{track.album || '-'}</td>
              <td className="py-2 px-2 text-gray-400 text-right">{formatDuration(track.duration_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
