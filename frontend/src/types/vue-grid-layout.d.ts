/**
 * vue-grid-layout 类型声明
 * 该库没有官方 TypeScript 类型定义，这里提供最小兜底声明
 */
declare module 'vue-grid-layout' {
  import type { DefineComponent } from 'vue'

  export interface LayoutItem {
    x: number
    y: number
    w: number
    h: number
    i: string
    minW?: number
    minH?: number
    maxW?: number
    maxH?: number
    static?: boolean
    isDraggable?: boolean
    isResizable?: boolean
  }

  export const GridLayout: DefineComponent<{
    layout: LayoutItem[]
    colNum?: number
    rowHeight?: number
    isDraggable?: boolean
    isResizable?: boolean
    isMirrored?: boolean
    autoSize?: boolean
    verticalCompact?: boolean
    margin?: [number, number]
    useCssTransforms?: boolean
    responsive?: boolean
    breakpoints?: Record<string, number>
    cols?: Record<string, number>
  }>

  export const GridItem: DefineComponent<{
    x: number
    y: number
    w: number
    h: number
    i: string
    minW?: number
    minH?: number
    maxW?: number
    maxH?: number
    static?: boolean
    isDraggable?: boolean
    isResizable?: boolean
  }>

  export default GridLayout
}
