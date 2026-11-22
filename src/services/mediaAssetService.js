/**
 * 媒体与数字资产核心业务服务 (Media & Digital Asset Service)
 * 职责：
 * 1. 资源分类管理 (默认: 音频、视频、文件、其他，支持增删改)
 * 2. 资源分组管理 (分组隶属于分类；分类内分组编码唯一；支持增删改)
 * 3. 资源素材库管理 (检索、过滤、删除、引用计数)
 * 4. 严谨对接系统设置：上传时自动读取 systemSettingService 中配置的存储驱动 (LOCAL / ALIYUN / TENCENT)，生成真实入库记录
 *
 * 层级模型 (v2)：
 *   分类 (Category)  ->  分组 (Group)  ->  素材 (Asset)
 *   分组标识 = (categoryCode, groupCode)，分类内分组编码唯一
 *   删除分组 / 分类为级联删除，其包含的素材一并移除
 */

import { systemSettingService } from './systemSettingService'
import mediaAssets197 from '@/data/media_assets_197.json'

const STORAGE_KEY_CATEGORIES = 'venue_media_categories_v1'
const STORAGE_KEY_GROUPS_V1 = 'venue_media_groups_v1'
const STORAGE_KEY_GROUPS = 'venue_media_groups_v2'
const STORAGE_KEY_ASSETS_V1 = 'venue_media_assets_v1'
const STORAGE_KEY_ASSETS = 'venue_media_assets_v2'
const STORAGE_KEY_SCHEMA_VERSION = 'venue_media_schema_version'
const SCHEMA_VERSION = 2

const UPLOADS_MARKER = '/uploads/'

// 历史演示数据中的重复国歌/国旗素材：升旗流程统一使用国家资料库的
// ast_anthem_CN (/uploads/audio/CN.mp3) 与 ast_flag_CN (/uploads/flags/CN.svg)，
// 以下旧记录仅做清理，不再参与展示与播放
const LEGACY_DUPLICATE_ASSET_IDS = ['ast_001', 'ast_003']
const LEGACY_DUPLICATE_FILE_MARKERS = ['anthem_cn_standard.mp3', 'flag_national_standard.svg']

const isLegacyDuplicateAsset = (asset) => {
  if (!asset) return false
  if (LEGACY_DUPLICATE_ASSET_IDS.includes(asset.id)) return true
  const haystack = `${asset.storagePath || ''} ${asset.accessUrl || ''}`.replace(/\\/g, '/')
  return LEGACY_DUPLICATE_FILE_MARKERS.some(marker => haystack.includes(marker))
}

// 已下线的视频素材：对应的视频文件并未随系统提供（本地存储中不存在），
// 种子数据与历史 localStorage 记录一并清理，避免素材库出现无法播放的条目
const REMOVED_MISSING_VIDEO_ASSET_IDS = ['ast_004', 'ast_005']
const REMOVED_MISSING_VIDEO_FILE_MARKERS = ['venue_official_promo_4k.mp4', 'highlights_touch_wall.mp4']

const isRemovedMissingVideoAsset = (asset) => {
  if (!asset) return false
  if (REMOVED_MISSING_VIDEO_ASSET_IDS.includes(asset.id)) return true
  const haystack = `${asset.storagePath || ''} ${asset.accessUrl || ''}`.replace(/\\/g, '/')
  return REMOVED_MISSING_VIDEO_FILE_MARKERS.some(marker => haystack.includes(marker))
}

/**
 * 本地存储素材的访问地址统一归一为「同源相对路径」。
 * 历史数据里存在 http://192.168.1.100:3001/uploads/... 这类硬编码地址，
 * 换一台机器 / 换一个端口访问时浏览器会一直等待不可达主机，媒体播放随之挂起。
 */
const normalizeLocalAccessUrl = (originalAsset) => {
  if (!originalAsset || originalAsset.storageDriver !== 'LOCAL') return originalAsset

  const asset = originalAsset
  const raw = String(asset.accessUrl || '').trim()
  if (!raw) {
    const storagePath = String(asset.storagePath || '').replace(/\\/g, '/')
    const idx = storagePath.indexOf(UPLOADS_MARKER)
    if (idx >= 0) {
      const accessUrl = storagePath.slice(idx)
      return accessUrl === asset.accessUrl ? asset : { ...asset, accessUrl }
    }
    return asset
  }

  if (raw.startsWith('/')) {
    return asset
  }

  try {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost'
    const url = new URL(raw, origin)
    const idx = url.pathname.indexOf(UPLOADS_MARKER)
    if (idx >= 0) {
      const accessUrl = `${url.pathname.slice(idx)}${url.search}${url.hash}`
      return { ...asset, accessUrl }
    }
  } catch (e) {
    // 非法 URL 保持原样，交由播放器错误处理
  }
  return asset
}

// 1. 默认资源分类字典 (4大基础核心分类)
export const DEFAULT_CATEGORIES = [
  { code: 'audio', name: '音频', icon: 'SvgSoundMatrix', isBuiltin: true, sortOrder: 1, desc: '赛事国歌、仪式颁奖乐、背景音乐与广播音频' },
  { code: 'video', name: '视频', icon: 'SvgMediaPlayer', isBuiltin: true, sortOrder: 2, desc: '场馆官方宣传片、赛事精彩集锦与推屏视频' },
  { code: 'document', name: '文件', icon: 'SvgConfigTemplate', isBuiltin: true, sortOrder: 3, desc: '国旗标准规程、竞赛方案、应急预案与技术文档' },
  { code: 'other', name: '其他', icon: 'SvgAppGrid', isBuiltin: true, sortOrder: 4, desc: '场馆SVG徽标、全景漫游包与综合附件资源' }
]

// 2. 默认资源分组字典 (v2：分组隶属于分类，分类内编码唯一)
export const DEFAULT_GROUPS = [
  // 音频
  { code: 'anthem', categoryCode: 'audio', name: '国歌', desc: '用于自动升旗、仪式典礼奏唱的标准权威音源', isBuiltin: true, sortOrder: 1 },
  { code: 'award', categoryCode: 'audio', name: '颁奖音乐', desc: '颁奖、加冕与运动员入场仪式专用配乐', isBuiltin: true, sortOrder: 2 },
  { code: 'bgm', categoryCode: 'audio', name: '背景音乐', desc: '场馆营业与候场时段循环播放的背景音乐', isBuiltin: true, sortOrder: 3 },
  { code: 'other', categoryCode: 'audio', name: '其他音频', desc: '综合备用音源与临时广播物料', isBuiltin: true, sortOrder: 4 },
  // 视频
  { code: 'promo', categoryCode: 'video', name: '宣传片', desc: '全彩主大屏、观众大厅导视屏轮播展播的形象片与广告片', isBuiltin: true, sortOrder: 1 },
  { code: 'highlight', categoryCode: 'video', name: '赛事集锦', desc: '精彩瞬间、破纪录瞬间与慢镜头集锦', isBuiltin: true, sortOrder: 2 },
  { code: 'guide', categoryCode: 'video', name: '导视导播', desc: '观众动线、赛程导播与安全须知短片', isBuiltin: true, sortOrder: 3 },
  { code: 'other', categoryCode: 'video', name: '其他视频', desc: '综合备用推流物料与通用视频附件', isBuiltin: true, sortOrder: 4 },
  // 文件
  { code: 'flag', categoryCode: 'document', name: '国旗国徽', desc: '升旗仪式仿真、大屏展示的国旗国徽高清矢量文件与规范', isBuiltin: true, sortOrder: 1 },
  { code: 'manual', categoryCode: 'document', name: '技术规程', desc: '设备操作规程、尺寸规范与标准化作业标准', isBuiltin: true, sortOrder: 2 },
  { code: 'emergency', categoryCode: 'document', name: '应急预案', desc: '应急预案、处置预案与应急保障方案', isBuiltin: true, sortOrder: 3 },
  { code: 'other', categoryCode: 'document', name: '其他文件', desc: '综合附件与通用文档素材', isBuiltin: true, sortOrder: 4 },
  // 其他
  { code: 'other', categoryCode: 'other', name: '其他', desc: '未归入具体分类的综合素材', isBuiltin: true, sortOrder: 1 }
]

// 2.1 v1 扁平分组字典 (仅用于历史数据迁移)
export const LEGACY_DEFAULT_GROUPS = [
  { code: 'anthem', name: '国歌', desc: '用于自动升旗、仪式典礼奏唱的标准权威国歌音视频', isBuiltin: true, sortOrder: 1 },
  { code: 'flag', name: '国旗', desc: '用于升旗仪式仿真、大屏展示的国旗国徽高清矢量文件与规范', isBuiltin: true, sortOrder: 2 },
  { code: 'promo', name: '宣传片', desc: '用于全彩主大屏、观众大厅导视屏轮播展播的形象片与广告片', isBuiltin: true, sortOrder: 3 },
  { code: 'other', name: '其他', desc: '综合备用音源、临时推流物料与通用辅助素材文件', isBuiltin: true, sortOrder: 4 }
]

// 3. 旧素材分组归位映射 (v1 扁平分组 -> v2 分类内分组)
const ASSET_GROUP_MIGRATION = {
  ast_002: 'anthem',
  ast_006: 'manual',
  ast_007: 'award',
  ast_008: 'emergency'
}

// 3. 默认高保真素材示例库 (满足初始开箱即用)
export const DEFAULT_ASSETS = [
  {
    id: 'ast_002',
    name: '国际奥委会会歌 (奥林匹克颂歌交响版)',
    categoryCode: 'audio',
    groupCode: 'anthem',
    fileType: 'mp3',
    fileSizeBytes: 5359743,
    fileSizeFormatted: '5.11 MB',
    durationSec: 223,
    durationFormatted: '03:43',
    resolution: '44.1kHz 立体声 (192kbps)',
    fileHash: '5b77fa9ecc7314a70c66b37027dcf6d5b74d3957e7c137736092ba484a47ab17',
    storageDriver: 'LOCAL',
    storageBucket: '本地工控服务器',
    storagePath: '/data/venue-ibms/uploads/audio/olympic_hymn_full.mp3',
    accessUrl: '/uploads/audio/olympic_hymn_full.mp3',
    refCount: 1,
    remark: '公有领域录音（Wikimedia Commons《Olympic Anthem》，Spyridon Samaras 作曲），适用于开闭幕式与颁奖典礼奏唱',
    createdAt: '2026-10-18 10:15:00'
  },
  {
    id: 'ast_006',
    name: '重大赛事国旗升降标准技术规程与尺寸规范',
    categoryCode: 'document',
    groupCode: 'manual',
    fileType: 'pdf',
    fileSizeBytes: 3200000,
    fileSizeFormatted: '3.05 MB',
    durationSec: 0,
    durationFormatted: '-',
    resolution: '共 18 页 / PDF A4',
    fileHash: '8f434346648f6b96df89dda901c5176b10e6d0ceec3e6a81e2dd4f04760417b8',
    storageDriver: 'LOCAL',
    storageBucket: '本地工控服务器',
    storagePath: '/data/venue-ibms/uploads/document/flag_ceremony_manual_2026.pdf',
    accessUrl: '/uploads/document/flag_ceremony_manual_2026.pdf',
    refCount: 0,
    remark: '体育总局标准升旗仪式流程与旗手协同作业指南',
    createdAt: '2026-10-20 15:45:00'
  },
  {
    id: 'ast_007',
    name: '颁奖仪式仪仗进行曲 (国家象征·铜管乐版)',
    categoryCode: 'audio',
    groupCode: 'award',
    fileType: 'mp3',
    fileSizeBytes: 4623008,
    fileSizeFormatted: '4.41 MB',
    durationSec: 182,
    durationFormatted: '03:02',
    resolution: '44.1kHz 立体声 (203kbps)',
    fileHash: 'cddc80a0087fd49840194547bc7fef7e261c9eca8b0ea5ff6dd1edc9a7646cdc',
    storageDriver: 'LOCAL',
    storageBucket: '本地工控服务器',
    storagePath: '/data/venue-ibms/uploads/audio/award_ceremony_march.mp3',
    accessUrl: '/uploads/audio/award_ceremony_march.mp3',
    refCount: 1,
    remark: '公有领域录音（Wikimedia Commons《National Emblem》，美国空军仪仗队演奏），用于颁奖加冕环节',
    createdAt: '2026-10-21 08:30:00'
  },
  {
    id: 'ast_008',
    name: '场馆重大赛事弱电及音视频应急广播保障方案',
    categoryCode: 'document',
    groupCode: 'emergency',
    fileType: 'pdf',
    fileSizeBytes: 4250000,
    fileSizeFormatted: '4.05 MB',
    durationSec: 0,
    durationFormatted: '-',
    resolution: '共 26 页 / PDF A4',
    fileHash: 'd7a8fbb307d7809469ca933b02d8cf5ff2a62300deb8d4a459c07978ac2f788a',
    storageDriver: 'LOCAL',
    storageBucket: '本地工控服务器',
    storagePath: '/data/venue-ibms/uploads/document/emergency_broadcast_sop.pdf',
    accessUrl: '/uploads/document/emergency_broadcast_sop.pdf',
    refCount: 0,
    remark: '突发火情/强电故障时公共广播系统一键强切调度预案',
    createdAt: '2026-10-21 09:10:00'
  },
  ...mediaAssets197
]

class MediaAssetService {
  constructor() {
    this.initData()
  }

  // 初始化本地持久化数据 (含 v1 -> v2 层级化迁移)
  initData() {
    if (typeof window === 'undefined') return
    try {
      if (!localStorage.getItem(STORAGE_KEY_CATEGORIES)) {
        localStorage.setItem(STORAGE_KEY_CATEGORIES, JSON.stringify(DEFAULT_CATEGORIES))
      }
      const version = Number(localStorage.getItem(STORAGE_KEY_SCHEMA_VERSION) || 0)
      if (version < SCHEMA_VERSION) {
        this.migrateToHierarchy()
        localStorage.setItem(STORAGE_KEY_SCHEMA_VERSION, String(SCHEMA_VERSION))
      } else {
        if (!localStorage.getItem(STORAGE_KEY_GROUPS)) {
          localStorage.setItem(STORAGE_KEY_GROUPS, JSON.stringify(DEFAULT_GROUPS))
        }
        if (!localStorage.getItem(STORAGE_KEY_ASSETS)) {
          localStorage.setItem(STORAGE_KEY_ASSETS, JSON.stringify(DEFAULT_ASSETS))
        }
      }
      this.purgeLegacyDuplicateAssets()
      this.syncCuratedAssetFiles()
    } catch (e) {
      console.warn('MediaAssetService initData error:', e)
    }
  }

  /**
   * 清理历史 localStorage 中遗留的无效素材：
   * 1. 重复演示素材 ast_001 / ast_003（真实升旗流程使用国家资料库 ast_anthem_CN 与 ast_flag_CN）
   * 2. 文件缺失的演示视频 ast_004 / ast_005（对应视频文件未随系统提供）
   */
  purgeLegacyDuplicateAssets() {
    [STORAGE_KEY_ASSETS_V1, STORAGE_KEY_ASSETS].forEach(key => {
      const list = this.readJson(key, null)
      if (!Array.isArray(list)) return
      const nextList = list.filter(asset => !isLegacyDuplicateAsset(asset) && !isRemovedMissingVideoAsset(asset))
      if (nextList.length !== list.length) {
        localStorage.setItem(key, JSON.stringify(nextList))
      }
    })
  }

  /**
   * 同步内置素材的媒体文件信息。
   * 这两条示例素材的音频文件为后续补充的公共版权录音，已持久化到 localStorage 的
   * 旧记录仍指向不存在的地址或旧格式，这里按 id 用最新种子数据覆盖文件相关字段。
   */
  syncCuratedAssetFiles() {
    const CURATED_ASSET_IDS = ['ast_002', 'ast_007']
    const curated = DEFAULT_ASSETS.filter(asset => CURATED_ASSET_IDS.includes(asset.id))
    if (!curated.length) return
    ;[STORAGE_KEY_ASSETS_V1, STORAGE_KEY_ASSETS].forEach(key => {
      const list = this.readJson(key, null)
      if (!Array.isArray(list)) return
      let changed = false
      const nextList = list.map(asset => {
        const source = curated.find(item => item.id === asset.id)
        if (!source) return asset
        const merged = { ...asset, ...source }
        if (JSON.stringify(merged) !== JSON.stringify(asset)) changed = true
        return merged
      })
      if (changed) localStorage.setItem(key, JSON.stringify(nextList))
    })
  }

  /**
   * v1 (扁平分组) -> v2 (分组隶属于分类) 迁移
   * 规则：
   * 1. 素材按 ASSET_GROUP_MIGRATION 归位到新分组；非内置素材保持原分组编码，仅补齐所属分类
   * 2. 新分组清单 = 内置层级默认分组 + 迁移后素材实际引用到的分组对
   * 3. 用户自建的旧分组若未被素材引用，则保留并挂到「其他」分类下，名称/描述不丢失
   * 4. v1 原始键不删除，便于回溯
   */
  migrateToHierarchy() {
    const legacyGroups = this.readJson(STORAGE_KEY_GROUPS_V1, LEGACY_DEFAULT_GROUPS)
    const legacyAssets = this.readJson(STORAGE_KEY_ASSETS_V1, DEFAULT_ASSETS)

    // 1. 素材分组归位
    const migratedAssets = legacyAssets.map(asset => ({
      ...asset,
      groupCode: ASSET_GROUP_MIGRATION[asset.id] || asset.groupCode
    }))

    // 2. 收集素材实际引用到的 (分类, 分组) 对
    const usedPairs = new Map()
    migratedAssets.forEach(a => {
      const key = `${a.categoryCode}::${a.groupCode}`
      if (!usedPairs.has(key)) usedPairs.set(key, { categoryCode: a.categoryCode, groupCode: a.groupCode })
    })

    // 3. 以内置层级默认分组为基础
    const groups = DEFAULT_GROUPS.map(g => ({ ...g }))
    const pairExists = (cat, code) => groups.some(g => g.categoryCode === cat && g.code === code)

    // 3.1 补齐素材引用到但默认清单中没有的分组
    usedPairs.forEach(pair => {
      if (!pairExists(pair.categoryCode, pair.groupCode)) {
        const legacy = legacyGroups.find(g => g.code === pair.groupCode)
        groups.push({
          code: pair.groupCode,
          categoryCode: pair.categoryCode,
          name: legacy?.name || pair.groupCode,
          desc: legacy?.desc || `${pair.groupCode} 分组`,
          isBuiltin: false,
          sortOrder: groups.filter(g => g.categoryCode === pair.categoryCode).length + 1
        })
      }
    })

    // 3.2 保留未被素材引用、且不在默认清单中的用户自建分组，挂到「其他」分类
    legacyGroups.forEach(legacy => {
      const stillUsed = migratedAssets.some(a => a.groupCode === legacy.code)
      const inDefaults = groups.some(g => g.code === legacy.code)
      if (!stillUsed && !inDefaults) {
        groups.push({
          code: legacy.code,
          categoryCode: 'other',
          name: legacy.name,
          desc: legacy.desc || '',
          isBuiltin: false,
          sortOrder: groups.filter(g => g.categoryCode === 'other').length + 1
        })
      }
    })

    try {
      localStorage.setItem(STORAGE_KEY_GROUPS, JSON.stringify(groups))
      localStorage.setItem(STORAGE_KEY_ASSETS, JSON.stringify(migratedAssets))
    } catch (e) {
      console.warn('MediaAssetService migrateToHierarchy error:', e)
    }
  }

  readJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key)
      return raw ? JSON.parse(raw) : JSON.parse(JSON.stringify(fallback))
    } catch (e) {
      return JSON.parse(JSON.stringify(fallback))
    }
  }

  // ==================== 1. 资源分类 (Category) 管理 ====================
  getCategories() {
    return this.readJson(STORAGE_KEY_CATEGORIES, DEFAULT_CATEGORIES)
  }

  saveCategories(categories) {
    try {
      localStorage.setItem(STORAGE_KEY_CATEGORIES, JSON.stringify(categories))
      this.dispatchChange('categories', categories)
      return { success: true }
    } catch (e) {
      return { success: false, message: e.message }
    }
  }

  addCategory({ code, name, icon, desc }) {
    const list = this.getCategories()
    const cleanCode = (code || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '')
    const cleanName = (name || '').trim()

    if (!cleanCode) {
      return { success: false, message: '分类编码不能为空，且仅支持字母、数字与下划线！' }
    }
    if (!cleanName) {
      return { success: false, message: '分类显示名称不能为空！' }
    }
    if (list.some(c => c.code === cleanCode)) {
      return { success: false, message: `分类编码 [${cleanCode}] 已存在，请勿重复添加！` }
    }

    const newCat = {
      code: cleanCode,
      name: cleanName,
      icon: icon || 'SvgAppGrid',
      desc: (desc || '').trim() || `${cleanName}资源素材`,
      isBuiltin: false,
      sortOrder: list.length + 1
    }
    list.push(newCat)
    this.saveCategories(list)
    return { success: true, data: newCat }
  }

  updateCategory(code, { name, icon, desc }) {
    const list = this.getCategories()
    const idx = list.findIndex(c => c.code === code)
    if (idx === -1) {
      return { success: false, message: '未找到待更新的分类项！' }
    }
    if (name) list[idx].name = name.trim()
    if (icon) list[idx].icon = icon.trim()
    if (desc !== undefined) list[idx].desc = desc.trim()

    this.saveCategories(list)
    return { success: true, data: list[idx] }
  }

  /**
   * 级联删除分类：连带删除其下属全部分组，以及这些分组包含的全部素材
   * @param {string} code 分类编码
   * @param {boolean} confirmed 是否已完成二次确认；未确认时仅返回删除预览
   */
  deleteCategory(code, confirmed = false) {
    const list = this.getCategories()
    const cat = list.find(c => c.code === code)
    if (!cat) {
      return { success: false, message: '分类不存在！' }
    }

    const preview = this.previewDeleteCategory(code)
    if (!preview.success) return preview

    if (!confirmed) {
      return { success: false, needConfirm: true, preview }
    }

    const assets = this.getAssets()
    const remainingAssets = assets.filter(a => a.categoryCode !== code)
    this.saveAssets(remainingAssets)

    const remainingGroups = this.getGroups().filter(g => g.categoryCode !== code)
    this.saveGroups(remainingGroups)

    // 移除分类自身
    const remainingCategories = list.filter(c => c.code !== code)
    this.saveCategories(remainingCategories)

    return {
      success: true,
      message: `分类 [${cat.name}] 及其下属 ${preview.groupCount} 个分组、${preview.assetCount} 个素材资源已全部删除！`,
      deletedGroups: preview.groupCount,
      deletedAssets: preview.assetCount
    }
  }

  // 删除分类前的预览（供二次确认弹窗展示）
  previewDeleteCategory(code) {
    const cat = this.getCategories().find(c => c.code === code)
    if (!cat) {
      return { success: false, message: '分类不存在！' }
    }
    const groups = this.getGroups().filter(g => g.categoryCode === code)
    const assets = this.getAssets().filter(a => a.categoryCode === code)
    return {
      success: true,
      category: cat,
      groups,
      groupCount: groups.length,
      assets,
      assetCount: assets.length,
      referencedCount: assets.filter(a => (a.refCount || 0) > 0).length
    }
  }

  // ==================== 2. 资源分组 (Group) 管理 (隶属于分类) ====================
  /**
   * 获取分组
   * @param {string} [categoryCode] 传入分类编码则只返回该分类下的分组
   */
  getGroups(categoryCode) {
    const list = this.readJson(STORAGE_KEY_GROUPS, DEFAULT_GROUPS)
    if (!categoryCode || categoryCode === 'ALL') return list
    return list.filter(g => g.categoryCode === categoryCode)
  }

  saveGroups(groups) {
    try {
      localStorage.setItem(STORAGE_KEY_GROUPS, JSON.stringify(groups))
      this.dispatchChange('groups', groups)
      return { success: true }
    } catch (e) {
      return { success: false, message: e.message }
    }
  }

  // 按 (分类, 分组) 二元定位分组
  getGroup(categoryCode, groupCode) {
    return this.getGroups().find(g => g.categoryCode === categoryCode && g.code === groupCode) || null
  }

  /**
   * 新增分组（隶属于指定分类）
   * 分组编码在所属分类内唯一，不同分类下允许同名分组
   */
  addGroup({ categoryCode, code, name, desc }) {
    const list = this.getGroups()
    const cleanCode = (code || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '')
    const cleanName = (name || '').trim()

    if (!categoryCode) {
      return { success: false, message: '请先选择分组所属的资源分类！' }
    }
    if (!this.getCategories().some(c => c.code === categoryCode)) {
      return { success: false, message: `所属分类 [${categoryCode}] 不存在！` }
    }
    if (!cleanCode) {
      return { success: false, message: '分组编码不能为空，且仅支持字母、数字与下划线！' }
    }
    if (!cleanName) {
      return { success: false, message: '分组显示名称不能为空！' }
    }
    if (list.some(g => g.categoryCode === categoryCode && g.code === cleanCode)) {
      return { success: false, message: `分组编码 [${cleanCode}] 在该分类下已存在，请勿重复添加！` }
    }

    const newGroup = {
      code: cleanCode,
      categoryCode,
      name: cleanName,
      desc: (desc || '').trim() || `${cleanName}业务分组`,
      isBuiltin: false,
      sortOrder: list.filter(g => g.categoryCode === categoryCode).length + 1
    }
    list.push(newGroup)
    this.saveGroups(list)
    return { success: true, data: newGroup }
  }

  updateGroup(categoryCode, code, { name, desc }) {
    const list = this.getGroups()
    const idx = list.findIndex(g => g.categoryCode === categoryCode && g.code === code)
    if (idx === -1) {
      return { success: false, message: '未找到待更新的分组项！' }
    }
    if (name) list[idx].name = name.trim()
    if (desc !== undefined) list[idx].desc = desc.trim()

    this.saveGroups(list)
    return { success: true, data: list[idx] }
  }

  /**
   * 级联删除分组：连带删除该分组包含的全部素材
   * @param {string} categoryCode 所属分类编码
   * @param {string} code 分组编码
   * @param {boolean} confirmed 是否已完成二次确认
   */
  deleteGroup(categoryCode, code, confirmed = false) {
    const grp = this.getGroup(categoryCode, code)
    if (!grp) {
      return { success: false, message: '分组不存在！' }
    }

    const preview = this.previewDeleteGroup(categoryCode, code)
    if (!preview.success) return preview

    if (!confirmed) {
      return { success: false, needConfirm: true, preview }
    }

    const assets = this.getAssets()
    const remainingAssets = assets.filter(a => !(a.categoryCode === categoryCode && a.groupCode === code))
    this.saveAssets(remainingAssets)

    const remainingGroups = this.getGroups().filter(g => !(g.categoryCode === categoryCode && g.code === code))
    this.saveGroups(remainingGroups)

    return {
      success: true,
      message: `分组 [${grp.name}] 及其包含的 ${preview.assetCount} 个素材资源已全部删除！`,
      deletedAssets: preview.assetCount
    }
  }

  // 删除分组前的预览（供二次确认弹窗展示）
  previewDeleteGroup(categoryCode, code) {
    const grp = this.getGroup(categoryCode, code)
    if (!grp) {
      return { success: false, message: '分组不存在！' }
    }
    const assets = this.getAssets().filter(a => a.categoryCode === categoryCode && a.groupCode === code)
    return {
      success: true,
      group: grp,
      categoryCode,
      assets,
      assetCount: assets.length,
      referencedCount: assets.filter(a => (a.refCount || 0) > 0).length
    }
  }

  // ==================== 3. 资源素材 (Assets) 检索与筛选 ====================
  getAssets(filter = {}) {
    let list = this.readJson(STORAGE_KEY_ASSETS, DEFAULT_ASSETS)
    if (Array.isArray(mediaAssets197)) {
      const existingIds = new Set(list.map(a => a.id))
      const toAdd = mediaAssets197.filter(a => !existingIds.has(a.id))
      if (toAdd.length > 0) {
        list = [...list, ...toAdd]
        this.saveAssets(list)
      }
    }

    const { categoryCode, groupCode, keyword } = filter

    return list.map(normalizeLocalAccessUrl).filter(item => {
      // 1. 分类筛选
      if (categoryCode && categoryCode !== 'ALL' && item.categoryCode !== categoryCode) {
        return false
      }
      // 2. 分组筛选（分组隶属于分类，需同时命中分类）
      if (groupCode && groupCode !== 'ALL' && item.groupCode !== groupCode) {
        return false
      }
      // 3. 关键字搜索
      if (keyword) {
        const q = keyword.trim().toLowerCase()
        const matchName = (item.name || '').toLowerCase().includes(q)
        const matchRemark = (item.remark || '').toLowerCase().includes(q)
        const matchExt = (item.fileType || '').toLowerCase().includes(q)
        const matchStorage = (item.storagePath || '').toLowerCase().includes(q)
        if (!matchName && !matchRemark && !matchExt && !matchStorage) {
          return false
        }
      }
      return true
    })
  }

  saveAssets(assets) {
    try {
      localStorage.setItem(STORAGE_KEY_ASSETS, JSON.stringify(assets))
      this.dispatchChange('assets', assets)
      return { success: true }
    } catch (e) {
      return { success: false, message: e.message }
    }
  }

  // ==================== 4. 核心：读取系统设置进行存储入库 ====================
  /**
   * 上传/入库新素材
   * 严格读取 systemSettingService 中配置的当前存储模式 (LOCAL / ALIYUN / TENCENT)
   */
  uploadAsset(params) {
    const {
      name,
      categoryCode,
      groupCode,
      fileName,
      fileSize = 1024 * 512,
      fileType = 'mp3',
      durationSec = 0,
      resolution = '',
      remark = '',
      operatorName = 'admin'
    } = params

    if (!name || !name.trim()) {
      return { success: false, message: '素材资源名称不能为空！' }
    }
    if (!categoryCode) {
      return { success: false, message: '请选择所属资源分类！' }
    }
    if (!groupCode) {
      return { success: false, message: '请选择所属资源分组！' }
    }
    // 分组隶属于分类：所选分组必须存在于该分类之下
    const targetGroup = this.getGroup(categoryCode, groupCode)
    if (!targetGroup) {
      return { success: false, message: '所选分组不存在或不属于该分类，请重新选择分组！' }
    }

    // 1. 动态读取系统设置中的当前存储策略
    const settings = systemSettingService.getSettings()
    const activeVendor = settings.activeStorageVendor || (settings.storageDriver === 'LOCAL' ? 'LOCAL' : (settings.ossConfig?.vendor || 'ALIYUN'))
    
    // 2. 根据系统设置计算存储路径与外链地址
    const now = new Date()
    const dateFolder = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`
    const timeStamp = now.getTime()
    const safeExt = (fileType || 'dat').toLowerCase().replace(/^\./, '')
    const safeFileName = `${dateFolder}_${timeStamp}.${safeExt}`

    let storageDriver = 'LOCAL'
    let storageBucket = '本地工控服务器'
    let storagePath = ''
    let accessUrl = ''

    if (activeVendor === 'LOCAL') {
      storageDriver = 'LOCAL'
      storageBucket = '本地工控机文件系统'
      const baseDir = (settings.localConfig?.storagePath || '/data/venue-ibms/uploads/').replace(/\\/g, '/').replace(/\/$/, '')
      // 本地驱动的资源始终由同源 /uploads 提供，避免把内网 IP / 端口写死进素材地址
      const rawPrefix = (settings.localConfig?.urlPrefix || '/uploads/').replace(/\/$/, '')
      let urlPrefix = rawPrefix
      if (rawPrefix.startsWith('http://') || rawPrefix.startsWith('https://')) {
        try {
          urlPrefix = new URL(rawPrefix).pathname.replace(/\/$/, '') || '/uploads'
        } catch (e) {
          urlPrefix = '/uploads'
        }
      }
      storagePath = `${baseDir}/${categoryCode}/${safeFileName}`
      accessUrl = `${urlPrefix}/${categoryCode}/${safeFileName}`
    } else if (activeVendor === 'ALIYUN') {
      storageDriver = 'ALIYUN'
      const bucket = settings.ossConfig?.bucket || 'venue-ibms-oss'
      const endpoint = settings.ossConfig?.endpoint || 'oss-cn-beijing.aliyuncs.com'
      const customDomain = (settings.ossConfig?.customDomain || '').trim()
      storageBucket = bucket
      storagePath = `venue-assets/${categoryCode}/${safeFileName}`
      if (customDomain) {
        accessUrl = `https://${customDomain.replace(/^https?:\/\//i, '').replace(/\/$/, '')}/${storagePath}`
      } else {
        accessUrl = `https://${bucket}.${endpoint.replace(/^https?:\/\//i, '').replace(/\/$/, '')}/${storagePath}`
      }
    } else if (activeVendor === 'TENCENT') {
      storageDriver = 'TENCENT'
      const bucket = settings.ossConfig?.bucket || 'venue-ibms-cos'
      const endpoint = settings.ossConfig?.endpoint || 'cos.ap-beijing.myqcloud.com'
      const customDomain = (settings.ossConfig?.customDomain || '').trim()
      storageBucket = bucket
      storagePath = `venue-cos/${categoryCode}/${safeFileName}`
      if (customDomain) {
        accessUrl = `https://${customDomain.replace(/^https?:\/\//i, '').replace(/\/$/, '')}/${storagePath}`
      } else {
        accessUrl = `https://${bucket}.${endpoint.replace(/^https?:\/\//i, '').replace(/\/$/, '')}/${storagePath}`
      }
    }

    // 格式化大小
    const formatBytes = (bytes) => {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    }

    // 格式化时长
    const formatTime = (sec) => {
      if (!sec) return '-'
      const m = Math.floor(sec / 60).toString().padStart(2, '0')
      const s = Math.floor(sec % 60).toString().padStart(2, '0')
      return `${m}:${s}`
    }

    // 生成唯一哈希指纹模拟
    const hash = 'sha256_' + Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join('')

    const newAsset = {
      id: 'ast_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 4),
      name: name.trim(),
      categoryCode,
      groupCode,
      fileType: safeExt,
      fileSizeBytes: fileSize,
      fileSizeFormatted: formatBytes(fileSize),
      durationSec: Number(durationSec) || 0,
      durationFormatted: formatTime(durationSec),
      resolution: resolution || (categoryCode === 'audio' ? '44.1kHz 立体声' : (categoryCode === 'video' ? '1920×1080' : '标准文档')),
      fileHash: hash,
      storageDriver,
      storageBucket,
      storagePath,
      accessUrl,
      refCount: 0,
      remark: (remark || '').trim(),
      createdBy: operatorName,
      createdAt: new Date().toISOString().replace('T', ' ').substring(0, 19)
    }

    const currentAssets = this.getAssets()
    currentAssets.unshift(newAsset)
    this.saveAssets(currentAssets)

    return {
      success: true,
      data: newAsset,
      storageMode: storageDriver,
      message: `素材 [${newAsset.name}] 已成功录入，并按照系统设置落盘至 [${storageDriver}: ${storageBucket}]！`
    }
  }

  // 删除素材
  deleteAsset(id) {
    const list = this.getAssets()
    const target = list.find(a => a.id === id)
    if (!target) {
      return { success: false, message: '未找到指定素材！' }
    }
    if (target.refCount > 0) {
      return {
        success: false,
        message: `素材 [${target.name}] 当前被升旗仪式/大屏推屏任务引用中 (被引用 ${target.refCount} 次)，禁止直接删除！`
      }
    }

    const nextList = list.filter(a => a.id !== id)
    this.saveAssets(nextList)
    return { success: true, message: `素材 [${target.name}] 已从库中成功移除！` }
  }

  // 派发事件
  dispatchChange(type, payload) {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('ibms-media-assets-changed', {
        detail: { type, payload }
      }))
    }
  }
}

export const mediaAssetService = new MediaAssetService()
