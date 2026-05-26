import { useStore } from '../store'
import TaskCard from './TaskCard'

export default function TaskList() {
  const tasks = useStore((s) => s.tasks)

  if (tasks.length === 0) {
    return (
      <div className="card text-center text-gray-400 py-8">
        No download tasks yet. Paste a Spotify link above to get started.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Tasks</h2>
      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} />
      ))}
    </div>
  )
}
