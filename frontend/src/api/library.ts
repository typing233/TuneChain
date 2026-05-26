import { api } from './client'

export interface LibraryTrack {
  id: string
  title: string
  artist: string
  album: string | null
  year: number | null
  cover_art_url: string | null
  file_path: string | null
  file_size: number | null
  duration_ms: number | null
}

export interface AlbumInfo {
  album: string
  artist: string
  cover_art_url: string | null
  year: number | null
  track_count: number
}

export interface ArtistInfo {
  artist: string
  track_count: number
}

export async function fetchTracks(params?: {
  search?: string
  artist?: string
  album?: string
  page?: number
  limit?: number
}): Promise<LibraryTrack[]> {
  const resp = await api.get<LibraryTrack[]>('/library/tracks', { params })
  return resp.data
}

export async function fetchAlbums(search?: string): Promise<AlbumInfo[]> {
  const resp = await api.get<AlbumInfo[]>('/library/albums', { params: { search } })
  return resp.data
}

export async function fetchArtists(): Promise<ArtistInfo[]> {
  const resp = await api.get<ArtistInfo[]>('/library/artists')
  return resp.data
}

export function getStreamUrl(trackId: string): string {
  return `/api/files/${trackId}/stream`
}
