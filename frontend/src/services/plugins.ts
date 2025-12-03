import api from './api'

export interface PluginMetadata {
  id: string
  name: string
  version: string
  description: string
  author?: string
  homepage?: string
  tags?: string[]
}

export interface PluginState {
  status?: string
  loaded_at?: string | null
  last_error?: string | null
  reload_count?: number
  metadata?: PluginMetadata
}

export interface PluginItem {
  name: string
  loaded: boolean
  state: PluginState
  metadata?: PluginMetadata | null
}

export async function fetchPluginStatus() {
  const response = await api.get('/plugins/status')
  return response.data?.data ?? {}
}

export async function listPlugins(): Promise<PluginItem[]> {
  const response = await api.get('/plugins/list')
  return response.data?.data?.plugins ?? []
}

export async function reloadPlugin(name: string) {
  return api.post(`/plugins/reload/${name}`)
}

export async function unloadPlugin(name: string) {
  return api.post(`/plugins/unload/${name}`)
}

export async function enableHotReload() {
  return api.post('/plugins/hot-reload/enable')
}

export async function disableHotReload() {
  return api.post('/plugins/hot-reload/disable')
}

export async function getPluginConfig(name: string): Promise<Record<string, any>> {
  const response = await api.get(`/plugins/${name}/config`)
  return response.data?.data?.values ?? {}
}

export async function updatePluginConfig(name: string, values: Record<string, any>) {
  const response = await api.post(`/plugins/${name}/config`, { values })
  return response.data?.data?.values ?? {}
}

