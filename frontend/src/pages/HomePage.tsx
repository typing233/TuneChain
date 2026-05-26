import { useEffect } from 'react'
import { useStore } from '../store'
import DownloadForm from '../components/DownloadForm'
import TaskList from '../components/TaskList'

export default function HomePage() {
  const loadTasks = useStore((s) => s.loadTasks)

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <DownloadForm />
      <TaskList />
    </div>
  )
}
