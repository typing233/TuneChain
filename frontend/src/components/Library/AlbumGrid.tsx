import { AlbumInfo } from '../../api/library'

interface Props {
  albums: AlbumInfo[]
  onSelect: (album: string) => void
}

export default function AlbumGrid({ albums, onSelect }: Props) {
  if (albums.length === 0) {
    return <p className="text-gray-400 text-center py-8">No albums found.</p>
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {albums.map((album) => (
        <div
          key={`${album.album}-${album.artist}`}
          onClick={() => onSelect(album.album)}
          className="card cursor-pointer hover:border-green-500 transition-colors group"
        >
          <div className="aspect-square bg-gray-700 rounded-lg mb-2 overflow-hidden">
            {album.cover_art_url ? (
              <img
                src={album.cover_art_url}
                alt={album.album}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-500">
                <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
                </svg>
              </div>
            )}
          </div>
          <p className="text-sm font-medium truncate">{album.album}</p>
          <p className="text-xs text-gray-400 truncate">{album.artist}</p>
          <p className="text-xs text-gray-500">{album.track_count} tracks{album.year ? ` · ${album.year}` : ''}</p>
        </div>
      ))}
    </div>
  )
}
