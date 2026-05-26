import { ArtistInfo } from '../../api/library'

interface Props {
  artists: ArtistInfo[]
  onSelect: (artist: string) => void
}

export default function ArtistList({ artists, onSelect }: Props) {
  if (artists.length === 0) {
    return <p className="text-gray-400 text-center py-8">No artists found.</p>
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
      {artists.map((artist) => (
        <div
          key={artist.artist}
          onClick={() => onSelect(artist.artist)}
          className="card cursor-pointer hover:border-green-500 transition-colors flex items-center gap-3"
        >
          <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center text-gray-400">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-medium truncate">{artist.artist}</p>
            <p className="text-xs text-gray-400">{artist.track_count} tracks</p>
          </div>
        </div>
      ))}
    </div>
  )
}
