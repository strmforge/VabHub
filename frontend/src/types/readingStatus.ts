/**
 * 阅读状态统一枚举定义
 * SHELF-HUB-FINISH-1 前端实现
 * 
 * 对应后端 app/schemas/reading_status.py
 */

// ==================== 过滤状态枚举 (用于 MyShelf API) ====================
export type ReadingItemFilterStatus = 'active' | 'finished' | 'all'

// ==================== 显示状态枚举 (用于 ReadingHub API) ====================
export type ReadingItemDisplayStatus = 'active' | 'not_started' | 'finished'

/**
 * 阅读状态辅助工具
 */
export class ReadingStatusHelper {
  /**
   * 判断是否为活跃状态 (进行中或未开始)
   */
  static isActiveStatus(isFinished: boolean): boolean {
    return !isFinished
  }

  /**
   * 获取显示状态
   */
  static getDisplayStatus(isFinished: boolean, hasProgress: boolean): ReadingItemDisplayStatus {
    if (isFinished) {
      return 'finished'
    } else if (hasProgress) {
      return 'active'
    } else {
      return 'not_started'
    }
  }

  /**
   * 验证过滤状态
   */
  static validateFilterStatus(status: string | null | undefined): ReadingItemFilterStatus {
    const validStatuses: ReadingItemFilterStatus[] = ['active', 'finished', 'all']
    if (!status) {
      return 'all'
    }
    if (!validStatuses.includes(status as ReadingItemFilterStatus)) {
      throw new Error(`无效的过滤状态: ${status}，有效值为: ${validStatuses.join(', ')}`)
    }
    return status as ReadingItemFilterStatus
  }

  /**
   * 验证显示状态
   */
  static validateDisplayStatus(status: string): ReadingItemDisplayStatus {
    const validStatuses: ReadingItemDisplayStatus[] = ['active', 'not_started', 'finished']
    if (!validStatuses.includes(status as ReadingItemDisplayStatus)) {
      throw new Error(`无效的显示状态: ${status}，有效值为: ${validStatuses.join(', ')}`)
    }
    return status as ReadingItemDisplayStatus
  }

  /**
   * 获取状态标签 (用于前端显示)
   */
  static getStatusLabel(status: ReadingItemDisplayStatus): string {
    const labels = {
      active: '进行中',
      not_started: '未开始',
      finished: '已完成'
    }
    return labels[status] || '未知'
  }

  /**
   * 获取状态颜色 (用于前端显示)
   */
  static getStatusColor(status: ReadingItemDisplayStatus): string {
    const colors = {
      active: 'primary',      // 蓝色 - 进行中
      not_started: 'grey',    // 灰色 - 未开始
      finished: 'success'     // 绿色 - 已完成
    }
    return colors[status] || 'default'
  }

  /**
   * 获取过滤状态标签
   */
  static getFilterStatusLabel(status: ReadingItemFilterStatus): string {
    const labels = {
      active: '进行中',
      finished: '已完成',
      all: '全部'
    }
    return labels[status] || '全部'
  }
}

// 便捷函数
export function isReadingActive(isFinished: boolean): boolean {
  return ReadingStatusHelper.isActiveStatus(isFinished)
}

export function getReadingDisplayStatus(isFinished: boolean, hasProgress: boolean): ReadingItemDisplayStatus {
  return ReadingStatusHelper.getDisplayStatus(isFinished, hasProgress)
}

export function validateReadingFilterStatus(status: string | null | undefined): ReadingItemFilterStatus {
  return ReadingStatusHelper.validateFilterStatus(status)
}

export function getReadingStatusLabel(status: ReadingItemDisplayStatus): string {
  return ReadingStatusHelper.getStatusLabel(status)
}

export function getReadingStatusColor(status: ReadingItemDisplayStatus): string {
  return ReadingStatusHelper.getStatusColor(status)
}
