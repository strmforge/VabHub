/**
 * Vuetify 3 类型增强
 * 解决 v-data-table slot 中 item 类型为 unknown 的问题
 * 
 * 注意: Vuetify 3 的 v-data-table slot 参数默认类型为 unknown
 * 这是上游已知问题: https://github.com/vuetifyjs/vuetify/issues/16680
 */

// 为 Vuetify 组件提供更宽松的类型
declare module 'vuetify/components' {
  import type { DefineComponent } from 'vue'
  
  // 覆盖 VDataTable 的 slots 类型
  interface VDataTableSlotItem {
    item: any  // 使用 any 避免 unknown 类型错误
    index: number
    columns: any[]
    isExpanded: (item: any) => boolean
    toggleExpand: (item: any) => void
    isSelected: (items: any | any[]) => boolean
    toggleSelect: (item: any) => void
  }
}

// DataTable header 类型（供组件使用）
export interface DataTableHeader {
  key: string
  title: string
  sortable?: boolean
  align?: 'start' | 'center' | 'end'
  width?: string | number
  minWidth?: string
  maxWidth?: string
  fixed?: boolean
  headerProps?: Record<string, any>
  cellProps?: Record<string, any>
  value?: any
}

// 导出类型供组件使用
export interface VDataTableItem<T = any> {
  item: T
  index: number
}

// 通用数据表行类型
export type DataTableRowItem<T> = T & {
  id?: number | string
}
