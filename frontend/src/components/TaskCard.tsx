import { useStore, ProgressMessage } from '../store'
import { TaskListItem } from '../api/client'
import ProgressBar from './ProgressBar'

interface Props {
  task: TaskListItem
}

export default function TaskCard({ task }: Props) {
  const progress: ProgressMessage | undefined = useStore((s) => s.taskProgress[task.id])

  const statusColor = {
    pending: 'text-yellow-400',
    processing: 'text-blue-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
    cancelled: 'text-gray-400',
  }[task.status] || 'text-gray-400'

  const overallPercent = progress?.overall_percent ??
    (task.track_count > 0 ? (task.completed_count / task.track_count) * 100 : 0)

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-400 truncate">{task.spotify_url}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs font-medium ${statusColor}`}>
              {task.status.toUpperCase()}
            </span>
            <span className="text-xs text-gray-500">
              {task.type} &middot; {task.format.toUpperCase()}
            </span>
            <span className="text-xs text-gray-500">
              {task.completed_count}/{task.track_count} tracks
            </span>
          </div>
        </div>
      </div>

      {(task.status === 'processing' || task.status === 'pending') && (
        <div className="mt-2">
          <ProgressBar percent={overallPercent} />
          {progress && (
            <p className="text-xs text-gray-400 mt-1">
              Track {progress.current_track}/{progress.total_tracks}: {progress.track_title}
              {progress.percent > 0 && ` (${Math.round(progress.percent)}%)`}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
