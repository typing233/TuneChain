import { useState, useEffect, useCallback } from 'react'
import { useStore } from '../store'
import { fetchAlbums, fetchArtists, AlbumInfo, ArtistInfo } from '../api/library'
import TrackTable from '../components/Library/TrackTable'
import AlbumGrid from '../components/Library/AlbumGrid'
import ArtistList from '../components/Library/ArtistList'

type View = 'tracks' | 'albums' | 'artists'

export default function LibraryPage() {
  const [view, setView] = useState<View>('tracks')
  const [search, setSearch] = useState('')
  const [artistFilter, setArtistFilter] = useState('')
  const [albumFilter, setAlbumFilter] = useState('')
  const [albums, setAlbums] = useState<AlbumInfo[]>([])
  const [artists, setArtists] = useState<ArtistInfo[]>([])

  const library = useStore((s) => s.library)
  const loadLibrary = useStore((s) => s.loadLibrary)

  const refresh = useCallback(() => {
    if (view === 'tracks') {
      loadLibrary({ search, artist: artistFilter, album: albumFilter })
    } else if (view === 'albums') {
      fetchAlbums(search).then(setAlbums)
    } else {
      fetchArtists().then(setArtists)
    }
  }, [view, search, artistFilter, albumFilter, loadLibrary])

  useEffect(() => {
    refresh()
  }, [refresh])

  const handleAlbumSelect = (album: string) => {
    setAlbumFilter(album)
    setView('tracks')
  }

  const handleArtistSelect = (artist: string) => {
    setArtistFilter(artist)
    setView('tracks')
  }

  const clearFilters = () => {
    setSearch('')
    setArtistFilter('')
    setAlbumFilter('')
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <h1 className="text-xl font-bold">Library</h1>
        <div className="flex gap-2">
          {(['tracks', 'albums', 'artists'] as View[]).map((v) => (
            <button
              key={v}
              onClick={() => { setView(v); clearFilters() }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                view === v
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-2 items-center">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search..."
          className="input-field max-w-xs"
        />
        {(artistFilter || albumFilter) && (
          <div className="flex gap-2 items-center">
            {artistFilter && (
              <span className="bg-gray-700 text-sm px-2 py-1 rounded flex items-center gap-1">
                Artist: {artistFilter}
                <button onClick={() => setArtistFilter('')} className="text-gray-400 hover:text-white">&times;</button>
              </span>
            )}
            {albumFilter && (
              <span className="bg-gray-700 text-sm px-2 py-1 rounded flex items-center gap-1">
                Album: {albumFilter}
                <button onClick={() => setAlbumFilter('')} className="text-gray-400 hover:text-white">&times;</button>
              </span>
            )}
          </div>
        )}
      </div>

      {view === 'tracks' && <TrackTable tracks={library} />}
      {view === 'albums' && <AlbumGrid albums={albums} onSelect={handleAlbumSelect} />}
      {view === 'artists' && <ArtistList artists={artists} onSelect={handleArtistSelect} />}
    </div>
  )
}
