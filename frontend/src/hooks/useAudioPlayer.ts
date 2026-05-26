import { useEffect, useRef } from 'react'
import { useStore } from '../store'
import { getStreamUrl } from '../api/library'

export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const { currentTrack, isPlaying } = useStore((s) => s.player)
  const playNext = useStore((s) => s.playNext)

  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio()
      audioRef.current.addEventListener('ended', () => {
        playNext()
      })
    }
  }, [playNext])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    if (currentTrack) {
      const url = getStreamUrl(currentTrack.id)
      if (audio.src !== window.location.origin + url) {
        audio.src = url
        audio.load()
      }
      if (isPlaying) {
        audio.play().catch(() => {})
      } else {
        audio.pause()
      }
    } else {
      audio.pause()
      audio.src = ''
    }
  }, [currentTrack, isPlaying])

  return audioRef
}
