import { useState } from 'react'
import { useStore } from '../store'

export default function DownloadForm() {
  const [url, setUrl] = useState('')
  const [format, setFormat] = useState('mp3')
  const [quality, setQuality] = useState('320')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const addTask = useStore((s) => s.addTask)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError('')
    try {
      await addTask({ url: url.trim(), format, quality })
      setUrl('')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to submit task'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card space-y-4">
      <h2 className="text-lg font-semibold">Download Music</h2>

      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="Paste Spotify link (track, album, or playlist)"
        className="input-field"
      />

      <div className="flex flex-wrap gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Format</label>
          <div className="flex gap-2">
            {['mp3', 'flac', 'm4a'].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFormat(f)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  format === f
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {f.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Quality</label>
          <div className="flex gap-2">
            {format === 'flac' ? (
              <span className="px-3 py-1.5 rounded-md text-sm bg-gray-700 text-gray-300">
                Lossless
              </span>
            ) : (
              ['128', '192', '320'].map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => setQuality(q)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    quality === q
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {q}kbps
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={loading || !url.trim()}
        className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Processing...' : 'Download'}
      </button>
    </form>
  )
}
