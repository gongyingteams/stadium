import { defineStore } from 'pinia'
import { ref } from 'vue'
import countries197 from '@/data/countries_197.json'

/**
 * 升旗仪式 · 全球 197 主权国家与地区资料库集中状态
 * ----------------------------------------------------------------------------
 * - countries: 197 国全量数组 (区域 / 国旗矢量SVG与颜色 / 国歌音频与时长 / 中英文 / ISO代码)
 * - 持久化: localStorage key `ibms-flag-countries`, 首次加载自动注入 197 国官方基线库
 * - 控制台与资料页 (/iot/flag/countries) 共享同一 store 实例, 增删改即时双向同步
 * - 国旗矢量图: /uploads/flags/{CODE}.svg
 * - 国歌音频源: /uploads/audio/{CODE}.mp3
 * ----------------------------------------------------------------------------
 */

export const REGIONS = ['亚洲', '欧洲', '非洲', '北美洲', '南美洲', '大洋洲', '其他']

export const PATTERN_OPTIONS = [
  { value: 'solid', label: '纯色单色旗' },
  { value: 'stripes', label: '横条纹双色旗' },
  { value: 'triband-h', label: '三横色带旗' },
  { value: 'tricolor', label: '三纵色带旗' },
  { value: 'stars', label: '星徽旗' },
  { value: 'sun', label: '太阳/国徽圆旗' },
  { value: 'cross', label: '十字旗' },
  { value: 'cn', label: '五星红旗式 (大星+四小星)' }
]

const STORAGE_KEY = 'ibms-flag-countries'

function defaultCountries() {
  return countries197
}

function loadCountries() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const arr = JSON.parse(raw)
      const standardMap = new Map(countries197.map(c => [c.code, c]))
      if (Array.isArray(arr) && arr.length > 0) {
        let needsSync = false
        const existingCodes = new Set(arr.map(c => c.code))

        // 1. 同步现有条目的时长及修正
        let synced = arr.map(c => {
          const std = standardMap.get(c.code)
          if (std && (c.anthemDurationPrecise !== std.anthemDurationPrecise || (c.code === 'CN' && c.anthemDuration === 46) || (c.code === 'AE' && c.anthemDuration === 149))) {
            needsSync = true
            return {
              ...c,
              anthemDuration: std.anthemDuration,
              anthemDurationPrecise: std.anthemDurationPrecise
            }
          }
          return c
        })

        // 2. 检查是否有缺失的标准国家/地区（例如新加入的 HK, MO, TW 等）
        const missing = countries197.filter(std => !existingCodes.has(std.code))
        if (missing.length > 0) {
          needsSync = true
          if (arr.length < 150) {
            const customMap = new Map(arr.map(c => [c.code, c]))
            synced = countries197.map(c => {
              const userMod = customMap.get(c.code)
              return userMod ? { ...c, ...userMod } : c
            })
          } else {
            const cnIndex = synced.findIndex(c => c.code === 'CN')
            if (cnIndex !== -1) {
              synced.splice(cnIndex + 1, 0, ...missing)
            } else {
              synced.push(...missing)
            }
          }
        }

        if (needsSync) {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(synced))
        }
        return synced
      }
    }
  } catch (e) { /* 静默回退默认库 */ }
  return defaultCountries()
}

/** 国旗 CSS 微缩样式 (面板/台账/档位卡片共用, 尺寸由各调用方 CSS 类控制) */
export function flagStyle(c) {
  const base = {
    borderRadius: '2px',
    border: '1px solid rgba(15,23,42,0.22)'
  }
  if (!c) return { ...base, background: 'var(--do-bg-sunken)' }
  if (c.imageUrl) {
    return {
      ...base,
      backgroundImage: `url(${c.imageUrl})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundColor: c.c1 || '#FFFFFF'
    }
  }
  const c1 = c.c1
  const c2 = c.c2
  const c3 = c.c3
  switch (c.pattern) {
    case 'stripes':
      return { ...base, background: `repeating-linear-gradient(180deg, ${c1} 0 7px, ${c2} 7px 14px)` }
    case 'triband-h':
      return { ...base, background: `linear-gradient(180deg, ${c1} 0 33.3%, ${c2} 33.3% 66.7%, ${c3} 66.7% 100%)` }
    case 'tricolor':
      return { ...base, background: `linear-gradient(90deg, ${c1} 0 33.3%, ${c2} 33.3% 66.7%, ${c3} 66.7% 100%)` }
    case 'stars':
      return {
        ...base,
        backgroundColor: c1,
        backgroundImage: `radial-gradient(circle at 28% 32%, ${c2} 3.5px, transparent 4.5px),
          radial-gradient(circle at 62% 24%, ${c2} 2.6px, transparent 3.6px),
          radial-gradient(circle at 74% 52%, ${c2} 2.6px, transparent 3.6px),
          radial-gradient(circle at 52% 70%, ${c2} 2.6px, transparent 3.6px),
          radial-gradient(circle at 26% 72%, ${c2} 2.4px, transparent 3.4px)`
      }
    case 'sun':
      return { ...base, backgroundColor: c1, backgroundImage: `radial-gradient(circle at 50% 50%, ${c2} 9px, transparent 10px)` }
    case 'cross':
      return {
        ...base,
        backgroundColor: c1,
        backgroundImage: `linear-gradient(90deg, transparent 36%, ${c2} 36% 50%, transparent 50%),
          linear-gradient(0deg, transparent 38%, ${c2} 38% 52%, transparent 52%)`
      }
    case 'cn':
      return {
        ...base,
        backgroundColor: c1,
        backgroundImage: `radial-gradient(circle at 24% 30%, ${c2} 5px, transparent 6px),
          radial-gradient(circle at 48% 13%, ${c2} 1.8px, transparent 2.8px),
          radial-gradient(circle at 58% 22%, ${c2} 1.8px, transparent 2.8px),
          radial-gradient(circle at 56% 38%, ${c2} 1.8px, transparent 2.8px),
          radial-gradient(circle at 42% 38%, ${c2} 1.8px, transparent 2.8px)`
      }
    default:
      return { ...base, backgroundColor: c1 }
  }
}

export const useFlagCountriesStore = defineStore('flagCountries', () => {
  const countries = ref(loadCountries())

  /** 持久化到 localStorage */
  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(countries.value))
    } catch (e) { /* 隐私模式或配额超限，静默跳过持久化 */ }
  }

  /** 新增或更新国家; editingId 为 null 时新增, 返回 { ok, error } */
  function upsertCountry(payload, editingId = null) {
    const dup = countries.value.find(c => c.code === payload.code && c.id !== editingId)
    if (dup) {
      return { ok: false, error: `已存在缩写「${payload.code}」的国家：${dup.nameCn}` }
    }
    if (editingId) {
      const i = countries.value.findIndex(c => c.id === editingId)
      if (i === -1) {
        return { ok: false, error: '目标国家不存在，可能已被删除，请重试' }
      }
      countries.value[i] = { ...countries.value[i], ...payload }
    } else {
      countries.value.push({ id: payload.code || ('C' + Date.now().toString(36).toUpperCase()), ...payload })
    }
    persist()
    return { ok: true }
  }

  /** 按 id 删除国家 */
  function removeCountry(id) {
    countries.value = countries.value.filter(c => c.id !== id)
    persist()
  }

  /** 一键重置为官方 197 国标准资料库 */
  function resetToDefault() {
    countries.value = JSON.parse(JSON.stringify(countries197))
    persist()
    return countries.value
  }

  return {
    countries,
    persist,
    upsertCountry,
    removeCountry,
    resetToDefault
  }
})
