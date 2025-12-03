/**
 * 漫画下载任务API服务
 */

import apiClient from './api'
import type {
  MangaDownloadJob,
  MangaDownloadJobSummary,
  CreateDownloadJobRequest,
  MangaDownloadJobListResponse
} from '@/types/mangaDownloadJob'

export const mangaDownloadJobApi = {
  /**
   * 创建下载任务
   */
  async createJob(request: CreateDownloadJobRequest): Promise<MangaDownloadJob> {
    const endpoint = request.mode === 'CHAPTER' 
      ? `/api/manga/local/chapters/${request.chapter_id}/download`
      : `/api/manga/local/series/${request.remote_series_id}/download`
    
    const response = await apiClient.post(endpoint, {
      source_id: request.source_id,
      remote_series_id: request.remote_series_id,
      mode: request.mode.toLowerCase(),
      latest_n: request.latest_n
    })
    
    return response.data.data
  },

  /**
   * 获取下载任务摘要
   */
  async getSummary(): Promise<MangaDownloadJobSummary> {
    const response = await apiClient.get('/api/manga/local/download-jobs/summary')
    return response.data.data
  },

  /**
   * 获取下载任务列表
   */
  async getJobs(params?: {
    page?: number
    page_size?: number
    status?: string
    mode?: string
  }): Promise<MangaDownloadJobListResponse> {
    const response = await apiClient.get('/api/manga/local/download-jobs', { params })
    return response.data.data
  },

  /**
   * 获取下载任务详情
   */
  async getJob(jobId: number): Promise<MangaDownloadJob> {
    const response = await apiClient.get(`/api/manga/local/download-jobs/${jobId}`)
    return response.data.data
  },

  /**
   * 获取用户的下载任务列表（便捷方法）
   */
  async getUserJobs(params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<MangaDownloadJobListResponse> {
    const response = await apiClient.get('/api/manga/local/download-jobs/user', { params })
    return response.data.data
  }
}
