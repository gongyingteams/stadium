/**
 * 左侧导航菜单配置业务服务 (Menu Config Service)
 * 管理系统左侧导航菜单的结构 (分组 / 菜单项 / 文字 / 显隐 / 链接)
 * 与 systemSettingService 同款机制: 服务端持久化 + localStorage 离线降级缓存 + 全站事件通知
 * 写操作仅限总管理员 (admin), 由后端接口 JWT 角色强校验。
 */
import { api } from '@/services/api'

const STORAGE_KEY = 'ibms_menu_config_v1'

/**
 * 出厂默认菜单树 (与后端 DEFAULT_MENU_TREE 手工镜像, 结构一致)
 * 首次进入/后端不可达时作为兜底, 保证侧边栏永不空白。
 */
export const DEFAULT_MENU_CONFIG = {
  groups: [
    {
      id: 'g-situation', menuKey: 'g-situation', title: '1. 综合态势', icon: 'SvgDashboard', visible: true,
      children: [
        { id: 'dashboard', menuKey: 'dashboard', title: '场馆综合态势总览工作台', shortTitle: '态势总览', path: '/dashboard', icon: 'SvgDashboard', visible: true, requiresAdmin: false, requiresOps: false, badgeType: '' }
      ]
    },
    {
      id: 'g-portal', menuKey: 'g-portal', title: '2. 应用门户', icon: 'SvgPortal', visible: true,
      children: [
        { id: 'portal-nav', menuKey: 'portal-nav', title: '场馆应用与网站聚合导航大厅', shortTitle: '应用导航', path: '/portal/nav', icon: 'SvgCompassNav', visible: true, requiresAdmin: false, requiresOps: false, badgeType: '' },
        { id: 'portal-external', menuKey: 'portal-external', title: '外部系统与本地软件集成中心', shortTitle: '外部集成', path: '/portal/external', icon: 'SvgIframeApp', visible: true, requiresAdmin: false, requiresOps: false, badgeType: '' }
      ]
    },
    {
      id: 'g-iot', menuKey: 'g-iot', title: '3. 物联控制', icon: 'SvgIotControl', visible: true,
      children: [
        { id: 'iot-audio', menuKey: 'iot-audio', title: '扩声调音与场景音效控制台', shortTitle: '专业扩声', path: '/iot/audio', icon: 'SvgSoundMatrix', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'AUDIO' },
        { id: 'iot-lighting', menuKey: 'iot-lighting', title: '场地照明场景与能耗监测台', shortTitle: '场地照明', path: '/iot/lighting', icon: 'SvgLighting', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'LIGHTING' },
        { id: 'iot-screen', menuKey: 'iot-screen', title: 'LED大屏与推屏调度控制台', shortTitle: '大屏调度', path: '/iot/screen', icon: 'SvgLedScreen', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'SCREEN' },
        { id: 'iot-score', menuKey: 'iot-score', title: '赛事计时计分接收与大屏推屏', shortTitle: '计时计分', path: '/iot/score', icon: 'SvgMatchScore', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'SCORE' },
        { id: 'iot-flag', menuKey: 'iot-flag', title: '自动升旗仪式与音画同步仿真台', shortTitle: '智能升旗', path: '/iot/flag', icon: 'SvgFlagSystem', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'FLAG' },
        { id: 'iot-clock', menuKey: 'iot-clock', title: '标准时钟卫星授时与子钟监测台', shortTitle: '时钟同步', path: '/iot/clock', icon: 'SvgMasterClock', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'CLOCK' },
        { id: 'iot-video', menuKey: 'iot-video', title: '现场摄像机实时监看总控台', shortTitle: '视频监控', path: '/iot/video', icon: 'SvgCameraMatrix', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'VIDEO' },
        { id: 'iot-underwater-video', menuKey: 'iot-underwater-video', title: '水下音像采集控制', shortTitle: '水下采集', path: '/iot/underwater-video', icon: 'SvgCameraMatrix', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'UNDERWATER' },
        { id: 'iot-media', menuKey: 'iot-media', title: '媒体播控台(背景音乐与视频投屏)', shortTitle: '媒体播控', path: '/iot/media', icon: 'SvgMediaPlayer', visible: true, requiresAdmin: false, requiresOps: false, badgeType: 'MEDIA' },
        { id: 'iot-dynamic', menuKey: 'iot-dynamic', title: '动态低代码通用设备控制台', shortTitle: '动态设备', path: '/iot/dynamic/group-01', icon: 'SvgDynamicDevice', visible: true, requiresAdmin: false, requiresOps: false, badgeType: '' }
      ]
    },
    {
      id: 'g-config', menuKey: 'g-config', title: '4. 配置中心', icon: 'SvgLowCodeConfig', visible: true,
      children: [
        { id: 'config-devices', menuKey: 'config-devices', title: '物联硬件设备管理与总控中台', shortTitle: '设备管理', path: '/config/devices', icon: 'SvgDeviceSetting', visible: true, requiresAdmin: false, requiresOps: true, badgeType: 'TOTAL' },
        { id: 'system-users', menuKey: 'system-users', title: '用户角色管理与细粒度权限配置', shortTitle: '角色权限', path: '/system/users', icon: 'SvgUserRole', visible: true, requiresAdmin: true, requiresOps: false, badgeType: '' },
        { id: 'ops-channels', menuKey: 'ops-channels', title: '告警规则与通知渠道配置中心', shortTitle: '告警通道', path: '/ops/channels', icon: 'SvgNotifyChannel', visible: true, requiresAdmin: true, requiresOps: false, badgeType: '' },
        { id: 'ops-audit', menuKey: 'ops-audit', title: '操作审计日志与导出留存中心', shortTitle: '审计日志', path: '/ops/audit', icon: 'SvgAuditLog', visible: true, requiresAdmin: false, requiresOps: true, badgeType: '' },
        { id: 'system-settings', menuKey: 'system-settings', title: '平台系统设置与对象存储中心', shortTitle: '系统设置', path: '/system/settings', icon: 'SvgSettingGear', visible: true, requiresAdmin: true, requiresOps: false, badgeType: '' },
        { id: 'system-menu', menuKey: 'system-menu', title: '导航菜单配置中心', shortTitle: '菜单配置', path: '/system/menu', icon: 'SvgMenuList', visible: true, requiresAdmin: true, requiresOps: false, badgeType: '' }
      ]
    }
  ]
}

class MenuConfigService {
  constructor() {
    // 远端配置同步状态 (true=已从后端数据库成功拉取; false=离线/降级为本地缓存)
    this.remoteSynced = false
    this.initCache()
  }

  // 派发"远端同步状态"事件, 供 Header 离线角标等组件监听
  emitSyncState(synced, message = '') {
    this.remoteSynced = synced
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('ibms-menu-config-sync', { detail: { synced, message } }))
    }
  }

  // 初始化本地缓存, 并异步拉取后端数据
  initCache() {
    try {
      const cached = localStorage.getItem(STORAGE_KEY)
      if (!cached) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_MENU_CONFIG))
      }
    } catch (e) {
      console.warn('MenuConfigService: localStorage access error', e)
    }

    if (typeof window !== 'undefined') {
      setTimeout(() => {
        this.fetchMenuConfig().catch(() => {})
      }, 60)
    }
  }

  // 从后端拉取最新菜单树, 同步本地缓存并派发全站事件; 后端不可达时平滑降级
  async fetchMenuConfig() {
    try {
      const remote = await api.getMenuConfig()
      // __offline = 后端不可达时的沙箱降级响应 (见 api.js handleMockFallback)
      const offlineSandbox = !!(remote && remote.__offline)

      if (remote && Array.isArray(remote.groups) && remote.groups.length > 0) {
        const data = { groups: remote.groups }
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
        } catch (e) {
          console.warn('MenuConfigService: 菜单缓存写入失败', e)
        }
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('ibms-menu-config-changed', { detail: data }))
        }
        this.emitSyncState(!offlineSandbox, offlineSandbox ? '后端不可达, 当前使用本机离线菜单配置' : '')
        return data
      }
      // 后端返回空树: 视为异常, 降级本地缓存, 不覆盖
      this.emitSyncState(false, '后端返回空菜单配置, 使用本地缓存')
    } catch (err) {
      console.warn('MenuConfigService.fetchMenuConfig: 后端连接异常, 使用本地离线菜单配置', err)
      this.emitSyncState(false, '后端连接异常, 当前使用本机离线菜单配置')
    }
    return this.getMenuConfig()
  }

  // 同步获取菜单配置 (本地缓存 → 出厂默认), 永不抛错
  getMenuConfig() {
    try {
      const cached = localStorage.getItem(STORAGE_KEY)
      if (cached) {
        const parsed = JSON.parse(cached)
        if (parsed && Array.isArray(parsed.groups) && parsed.groups.length > 0) {
          // 离线缓存平滑补齐新增的「水下音像采集控制」菜单项
          const hasUw = parsed.groups.some(g =>
            (g.children || []).some(c => c.menuKey === 'iot-underwater-video' || c.path === '/iot/underwater-video')
          )
          if (!hasUw) {
            const iotGroup = parsed.groups.find(g => g.menuKey === 'g-iot' || g.id === 'g-iot')
            if (iotGroup && Array.isArray(iotGroup.children)) {
              const videoIdx = iotGroup.children.findIndex(c => c.menuKey === 'iot-video' || c.path === '/iot/video')
              const uwItem = {
                id: 'iot-underwater-video',
                menuKey: 'iot-underwater-video',
                title: '水下音像采集控制',
                shortTitle: '水下采集',
                path: '/iot/underwater-video',
                icon: 'SvgCameraMatrix',
                visible: true,
                requiresAdmin: false,
                requiresOps: false,
                badgeType: 'UNDERWATER'
              }
              if (videoIdx >= 0) {
                iotGroup.children.splice(videoIdx + 1, 0, uwItem)
              } else {
                iotGroup.children.push(uwItem)
              }
              try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed))
              } catch { /* ignore */ }
            }
          }
          return parsed
        }
      }
    } catch (e) {
      console.error('getMenuConfig error:', e)
    }
    const fallback = JSON.parse(JSON.stringify(DEFAULT_MENU_CONFIG))
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(fallback))
    } catch {
      // ignore
    }
    return fallback
  }

  // 整树保存菜单配置 (仅 admin 可成功; 先写本地再提交后端)
  async saveMenuTree(tree) {
    const payload = { groups: (tree && tree.groups) || [] }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch (e) {
      console.warn('MenuConfigService.saveMenuTree: 本地缓存写入失败', e)
    }

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('ibms-menu-config-changed', { detail: payload }))
    }

    let remoteSaved = false
    let message = ''
    try {
      const res = await api.saveMenuConfig(payload)
      remoteSaved = !(res && res.__offline)
      message = res?.message || ''
      if (!remoteSaved) {
        console.warn('MenuConfigService.saveMenuTree: 后端不可达, 菜单配置仅保存于本机浏览器缓存')
      }
    } catch (apiErr) {
      remoteSaved = false
      message = apiErr?.message || '后端保存失败'
      console.warn('MenuConfigService.saveMenuTree: 后端保存异常(已先写入本地离线配置):', apiErr)
    }
    this.emitSyncState(remoteSaved, remoteSaved ? '' : '后端不可达, 菜单配置仅保存于本机浏览器缓存')

    // 保存成功后拉取一次后端回显, 保证本地与服务端一致 (含服务端自动补全的 id / menuKey)
    if (remoteSaved) {
      try {
        await this.fetchMenuConfig()
      } catch {
        // ignore
      }
    }
    return { success: true, remoteSaved, message }
  }

  // 恢复出厂默认菜单 (仅 admin 可成功)
  async resetMenuTree() {
    let remoteSaved = false
    try {
      const res = await api.resetMenuConfig()
      remoteSaved = !(res && res.__offline)
    } catch (apiErr) {
      remoteSaved = false
      console.warn('MenuConfigService.resetMenuTree: 后端恢复异常:', apiErr)
    }

    if (remoteSaved) {
      // 拉取后端回显的默认树
      try {
        await this.fetchMenuConfig()
      } catch {
        // ignore
      }
    } else {
      // 离线降级: 本地恢复出厂默认
      const fallback = JSON.parse(JSON.stringify(DEFAULT_MENU_CONFIG))
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(fallback))
      } catch {
        // ignore
      }
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('ibms-menu-config-changed', { detail: fallback }))
      }
      this.emitSyncState(false, '后端不可达, 已在本机恢复默认菜单')
    }
    return { success: true, remoteSaved }
  }
}

export const menuConfigService = new MenuConfigService()
