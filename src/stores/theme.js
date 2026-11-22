import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 主题状态管理 · 4 种蓝色主题
 * ----------------------------------------------------------------------------
 * 科技深蓝 (tech-blue)   —— 深色模式，#0F172A 底色 + #3B82F6 高亮
 * 经典商务蓝 (classic)    —— 浅色模式，#2563EB 品牌主色 + 白底
 * 现代亮蓝 (vibrant)      —— 浅色模式，#0066FF 电光蓝主色
 * 远山青蓝 (sky)          —— 浅色模式，#0284C7 天空蓝 + #EFF6FF 底色
 * ----------------------------------------------------------------------------
 */

export const THEMES = [
  {
    id: 'classic-blue',
    name: '经典商务蓝',
    modeTag: '商务白底',
    description: '沉稳大厂商务蓝 · 明亮耐看',
    primary: '#2563EB',
    headerBg: '#1E3A8A',
    sidebarBg: '#172554',
    contentBg: '#F5F7FA',
    cardBg: '#FFFFFF',
    accentLight: '#60A5FA',
    swatch: 'linear-gradient(135deg, #1E3A8A 0%, #172554 50%, #2563EB 100%)'
  },
  {
    id: 'tech-blue',
    name: '科技深蓝',
    modeTag: '极客深色',
    description: '硬核极客黑蓝 · 数据管控大屏',
    primary: '#3B82F6',
    headerBg: '#0B1120',
    sidebarBg: '#020617',
    contentBg: '#0F172A',
    cardBg: '#1E293B',
    accentLight: '#38BDF8',
    swatch: 'linear-gradient(135deg, #0B1120 0%, #0F172A 50%, #3B82F6 100%)'
  },
  {
    id: 'vibrant-blue',
    name: '现代亮蓝',
    modeTag: '活力电光',
    description: '高饱和皇家电光蓝 · 年轻现代',
    primary: '#0066FF',
    headerBg: '#0052CC',
    sidebarBg: '#003D99',
    contentBg: '#F8FAFC',
    cardBg: '#FFFFFF',
    accentLight: '#38BDF8',
    swatch: 'linear-gradient(135deg, #0052CC 0%, #003D99 50%, #0066FF 100%)'
  },
  {
    id: 'sky-blue',
    name: '远山青蓝',
    modeTag: '苍山湖青',
    description: '松石青天蓝 · 通透高雅质感',
    primary: '#0284C7',
    headerBg: '#0C4A6E',
    sidebarBg: '#075985',
    contentBg: '#EFF6FF',
    cardBg: '#FFFFFF',
    accentLight: '#38BDF8',
    swatch: 'linear-gradient(135deg, #0C4A6E 0%, #075985 50%, #0284C7 100%)'
  }
]

const STORAGE_KEY = 'ibms-theme-id'
const DEFAULT_THEME_ID = 'classic-blue'

export const useThemeStore = defineStore('theme', () => {
  const currentThemeId = ref(DEFAULT_THEME_ID)

  const currentTheme = computed(() => {
    return THEMES.find(t => t.id === currentThemeId.value) || THEMES[0]
  })

  const isDark = computed(() => currentThemeId.value === 'tech-blue')

  /** 从 localStorage 恢复主题 */
  const hydrate = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved && THEMES.some(t => t.id === saved)) {
        currentThemeId.value = saved
      }
    } catch {
      // localStorage 不可用时使用默认主题
    }
    applyTheme(currentThemeId.value)
  }

  /** 将 data-theme 属性写入 <html> 元素，CSS 变量随之切换 */
  const applyTheme = (themeId) => {
    const root = document.documentElement
    root.setAttribute('data-theme', themeId)
  }

  /** 切换主题并持久化 */
  const setTheme = (themeId) => {
    const theme = THEMES.find(t => t.id === themeId)
    if (!theme) return
    currentThemeId.value = themeId
    applyTheme(themeId)
    try {
      localStorage.setItem(STORAGE_KEY, themeId)
    } catch {
      // 忽略存储失败
    }
  }

  return {
    currentThemeId,
    currentTheme,
    isDark,
    hydrate,
    setTheme
  }
})
