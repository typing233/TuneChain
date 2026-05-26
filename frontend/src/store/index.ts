import { create } from 'zustand'
import { TaskListItem, listTasks, submitTask, TaskCreateRequest, TaskResponse } from '../api/client'
import { LibraryTrack, fetchTracks } from '../api/library'

export interface ProgressMessage {
  type: string
  task_id: string
  current_track: number
  total_tracks: number
  track_title: string
  percent: number
  overall_percent: number
  status: string
  error?: string
}

interface PlayerState {
  currentTrack: LibraryTrack | null
  isPlaying: boolean
  queue: LibraryTrack[]
}

interface AppState {
  tasks: TaskListItem[]
  taskProgress: Record<string, ProgressMessage>
  library: LibraryTrack[]
  player: PlayerState

  loadTasks: () => Promise<void>
  addTask: (data: TaskCreateRequest) => Promise<TaskResponse>
  updateProgress: (msg: ProgressMessage) => void
  markTaskComplete: (taskId: string) => void

  loadLibrary: (params?: { search?: string; artist?: string; album?: string }) => Promise<void>

  play: (track: LibraryTrack) => void
  pause: () => void
  resume: () => void
  setQueue: (tracks: LibraryTrack[]) => void
  playNext: () => void
  playPrev: () => void
}

export const useStore = create<AppState>((set, get) => ({
  tasks: [],
  taskProgress: {},
  library: [],
  player: {
    currentTrack: null,
    isPlaying: false,
    queue: [],
  },

  loadTasks: async () => {
    const tasks = await listTasks()
    set({ tasks })
  },

  addTask: async (data) => {
    const task = await submitTask(data)
    const tasks = await listTasks()
    set({ tasks })
    return task
  },

  updateProgress: (msg) => {
    set((state) => ({
      taskProgress: { ...state.taskProgress, [msg.task_id]: msg },
    }))
  },

  markTaskComplete: (taskId) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, status: 'completed' } : t
      ),
    }))
  },

  loadLibrary: async (params) => {
    const tracks = await fetchTracks(params)
    set({ library: tracks })
  },

  play: (track) => {
    set((state) => ({
      player: { ...state.player, currentTrack: track, isPlaying: true },
    }))
  },

  pause: () => {
    set((state) => ({
      player: { ...state.player, isPlaying: false },
    }))
  },

  resume: () => {
    set((state) => ({
      player: { ...state.player, isPlaying: true },
    }))
  },

  setQueue: (tracks) => {
    set((state) => ({
      player: { ...state.player, queue: tracks },
    }))
  },

  playNext: () => {
    const { player } = get()
    if (!player.currentTrack || player.queue.length === 0) return
    const idx = player.queue.findIndex((t) => t.id === player.currentTrack!.id)
    const next = player.queue[idx + 1]
    if (next) {
      set({ player: { ...player, currentTrack: next, isPlaying: true } })
    }
  },

  playPrev: () => {
    const { player } = get()
    if (!player.currentTrack || player.queue.length === 0) return
    const idx = player.queue.findIndex((t) => t.id === player.currentTrack!.id)
    const prev = player.queue[idx - 1]
    if (prev) {
      set({ player: { ...player, currentTrack: prev, isPlaying: true } })
    }
  },
}))
