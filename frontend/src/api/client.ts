import axios from 'axios'

const API_BASE = '/api'

export const api = axios.create({
  baseURL: API_BASE,
})

export interface TaskCreateRequest {
  url: string
  format: string
  quality: string
}

export interface TrackResponse {
  id: string
  spotify_id: string
  title: string
  artist: string
  album: string | null
  year: number | null
  duration_ms: number | null
  cover_art_url: string | null
  youtube_id: string | null
  file_path: string | null
  file_size: number | null
  status: string
  error_message: string | null
}

export interface TaskResponse {
  id: string
  spotify_url: string
  type: string
  format: string
  quality: string
  status: string
  track_count: number
  completed_count: number
  failed_count: number
  created_at: string
  updated_at: string
  tracks: TrackResponse[]
}

export interface TaskListItem {
  id: string
  spotify_url: string
  type: string
  format: string
  status: string
  track_count: number
  completed_count: number
  failed_count: number
  created_at: string
}

export async function submitTask(data: TaskCreateRequest): Promise<TaskResponse> {
  const resp = await api.post<TaskResponse>('/tasks', data)
  return resp.data
}

export async function listTasks(): Promise<TaskListItem[]> {
  const resp = await api.get<TaskListItem[]>('/tasks')
  return resp.data
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  const resp = await api.get<TaskResponse>(`/tasks/${taskId}`)
  return resp.data
}

export async function cancelTask(taskId: string): Promise<void> {
  await api.delete(`/tasks/${taskId}`)
}
