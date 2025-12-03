/**
 * 格式化工具函数
 */

/**
 * 格式化时长（秒 -> 中文格式）
 * 
 * @param seconds 秒数（可能为 null/undefined）
 * @returns 格式化后的时长字符串，例如 "1小时2分3秒"、"1分30秒"
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || isNaN(seconds)) {
    return '未知时长'
  }
  
  const totalSeconds = Math.floor(seconds)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60
  
  const parts: string[] = []
  
  if (hours > 0) {
    parts.push(`${hours}小时`)
  }
  if (minutes > 0 || hours > 0) {
    parts.push(`${minutes}分`)
  }
  if (secs > 0 && hours === 0) {
    // 只有小于1小时时才显示秒
    parts.push(`${secs}秒`)
  }
  
  return parts.length > 0 ? parts.join('') : '0秒'
}

/**
 * 格式化音频质量信息
 * 
 * @param meta 音频元数据片段
 * @returns 格式化后的质量字符串，例如 "128 kbps / 44.1 kHz / 立体声"
 */
export function formatAudioQuality(meta: {
  bitrate_kbps?: number | null
  sample_rate_hz?: number | null
  channels?: number | null
}): string {
  const parts: string[] = []
  
  if (meta.bitrate_kbps != null && !isNaN(meta.bitrate_kbps)) {
    parts.push(`${meta.bitrate_kbps} kbps`)
  }
  
  if (meta.sample_rate_hz != null && !isNaN(meta.sample_rate_hz)) {
    const khz = meta.sample_rate_hz / 1000
    parts.push(`${khz.toFixed(1)} kHz`)
  }
  
  if (meta.channels != null && !isNaN(meta.channels)) {
    if (meta.channels === 1) {
      parts.push('单声道')
    } else if (meta.channels === 2) {
      parts.push('立体声')
    } else {
      parts.push(`${meta.channels}声道`)
    }
  }
  
  return parts.length > 0 ? parts.join(' / ') : '-'
}

/**
 * 格式化声道数
 * 
 * @param channels 声道数
 * @returns 格式化后的声道描述
 */
export function formatChannels(channels: number | null | undefined): string {
  if (channels === null || channels === undefined || isNaN(channels)) {
    return '-'
  }
  
  if (channels === 1) {
    return '单声道'
  } else if (channels === 2) {
    return '立体声'
  } else {
    return `${channels}声道`
  }
}

/**
 * 格式化日期时间
 * 
 * @param value ISO 格式日期时间字符串或 null
 * @returns 格式化后的日期时间字符串，例如 "2023-11-22 08:30:00"
 */
export function formatDateTime(value: string | null): string {
  if (!value) {
    return '-'
  }
  
  try {
    const date = new Date(value)
    if (isNaN(date.getTime())) {
      return '-'
    }
    
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (e) {
    return '-'
  }
}

/**
 * 格式化相对时间
 * 
 * @param value ISO 格式日期时间字符串或 null
 * @returns 相对时间描述，例如 "2小时前"、"3天前"
 */
export function formatRelativeTime(value: string | null): string {
  if (!value) {
    return '从未'
  }
  
  try {
    const date = new Date(value)
    if (isNaN(date.getTime())) {
      return '-'
    }
    
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffSeconds < 60) {
      return '刚刚'
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`
    } else if (diffHours < 24) {
      return `${diffHours}小时前`
    } else if (diffDays < 30) {
      return `${diffDays}天前`
    } else {
      // 超过30天，显示具体日期
      return formatDateTime(value)
    }
  } catch (e) {
    return '-'
  }
}

