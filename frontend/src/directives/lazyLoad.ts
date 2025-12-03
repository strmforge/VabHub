/**
 * 图片懒加载指令
 * 使用 Intersection Observer API 实现图片懒加载
 */

import { Directive, DirectiveBinding } from 'vue'

interface LazyLoadElement extends HTMLElement {
  _lazyLoadObserver?: IntersectionObserver
  _lazyLoadSrc?: string
}

const lazyLoadDirective: Directive = {
  mounted(el: LazyLoadElement, binding: DirectiveBinding) {
    const src = binding.value
    if (!src) return

    // 设置占位符
    el.setAttribute('data-src', src)
    el.setAttribute('src', 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E')
    el.classList.add('lazy-load-placeholder')

    // 创建 Intersection Observer
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as LazyLoadElement
            const dataSrc = img.getAttribute('data-src')
            
            if (dataSrc) {
              // 创建新的 Image 对象预加载
              const image = new Image()
              image.onload = () => {
                img.setAttribute('src', dataSrc)
                img.removeAttribute('data-src')
                img.classList.remove('lazy-load-placeholder')
                img.classList.add('lazy-load-loaded')
              }
              image.onerror = () => {
                img.setAttribute('src', '/default-cover.png')
                img.removeAttribute('data-src')
                img.classList.remove('lazy-load-placeholder')
                img.classList.add('lazy-load-error')
              }
              image.src = dataSrc
            }
            
            // 停止观察
            observer.unobserve(img)
            el._lazyLoadObserver = undefined
          }
        })
      },
      {
        rootMargin: '50px' // 提前50px开始加载
      }
    )

    observer.observe(el)
    el._lazyLoadObserver = observer
  },
  
  updated(el: LazyLoadElement, binding: DirectiveBinding) {
    const src = binding.value
    if (!src) return
    
    // 如果 src 改变，重新设置
    if (el.getAttribute('data-src') !== src) {
      el.setAttribute('data-src', src)
      // 如果已经加载，直接更新
      if (el.classList.contains('lazy-load-loaded')) {
        el.setAttribute('src', src)
      }
    }
  },
  
  unmounted(el: LazyLoadElement) {
    if (el._lazyLoadObserver) {
      el._lazyLoadObserver.disconnect()
      el._lazyLoadObserver = undefined
    }
  }
}

export default lazyLoadDirective

