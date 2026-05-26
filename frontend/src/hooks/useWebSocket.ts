import { useEffect, useRef, useCallback } from 'react'
import { useStore, ProgressMessage } from '../store'

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const updateProgress = useStore((s) => s.updateProgress)
  const markTaskComplete = useStore((s) => s.markTaskComplete)
  const loadTasks = useStore((s) => s.loadTasks)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/all`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const msg: ProgressMessage = JSON.parse(event.data)
        updateProgress(msg)
        if (msg.type === 'task_complete') {
          markTaskComplete(msg.task_id)
          loadTasks()
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [updateProgress, markTaskComplete, loadTasks])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])
}
