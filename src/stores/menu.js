import { defineStore } from 'pinia'
import { ref } from 'vue'
import { menuConfigService, DEFAULT_MENU_CONFIG } from '@/services/menuConfigService'

/**
 * 左侧导航菜单全局状态
 * groups: 当前生效菜单树 (分组 + 菜单项), 初始化即从本地缓存/出厂默认取值, 永不空白
 * 数据来源: 后端 sys_menu 表 (admin 可在 /system/menu 管理页维护), 后端不可达时降级本地缓存
 */
export const useMenuStore = defineStore('menu', () => {
  const groups = ref(menuConfigService.getMenuConfig().groups || [])
  const remoteSynced = ref(menuConfigService.remoteSynced)

  // 拉取后端最新菜单; force=true 时强制刷新 (管理页保存/恢复默认后调用)
  const load = async (force = false) => {
    const data = await menuConfigService.fetchMenuConfig()
    if (force || !groups.value.length) {
      groups.value = data.groups || []
    }
    remoteSynced.value = menuConfigService.remoteSynced
    return data
  }

  // 整树保存 (仅 admin 可成功)
  const save = async (tree) => {
    const result = await menuConfigService.saveMenuTree(tree || { groups: groups.value })
    await load(true)
    return result
  }

  // 恢复出厂默认菜单 (仅 admin 可成功)
  const reset = async () => {
    const result = await menuConfigService.resetMenuTree()
    await load(true)
    return result
  }

  // 跨组件 / 跨标签页同步: service 派发的菜单变更事件直接写回 store
  if (typeof window !== 'undefined') {
    window.addEventListener('ibms-menu-config-changed', (e) => {
      const next = e?.detail?.groups || menuConfigService.getMenuConfig().groups
      groups.value = next
    })
    window.addEventListener('storage', (e) => {
      if (e.key === 'ibms_menu_config_v1') {
        groups.value = menuConfigService.getMenuConfig().groups
      }
    })
  }

  return { groups, remoteSynced, load, save, reset, DEFAULT_MENU_CONFIG }
})
