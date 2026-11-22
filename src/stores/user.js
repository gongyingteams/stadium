import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

const emptyUser = () => ({
  id: 0,
  username: '',
  displayName: '',
  roleCode: '',
  roleName: '',
  sessionExpiresIn: 0
})

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('venue_access_token') || '')
  const currentUser = ref(JSON.parse(localStorage.getItem('venue_current_user') || 'null') || emptyUser())

  const presetRoles = ref([
    { code: 'admin', name: '系统管理员', desc: '拥有系统全部功能、全协议修改、参数配置与导入导出权限' },
    { code: 'ops', name: '运维工程师', desc: '负责链路排查、告警处置、模拟沙箱及参数调优' },
    { code: 'operator', name: '场馆操作员', desc: '现场赛事执行，仅操作按钮，严格物理隔离通信配置' },
    { code: 'viewer', name: '只读查看者', desc: '各级领导及调度坐席，仅大盘态势只读' }
  ])

  const isLoggedIn = computed(() => Boolean(token.value && currentUser.value.username))
  const isAdmin = computed(() => currentUser.value.roleCode === 'admin')
  const isOpsOrAdmin = computed(() => ['admin', 'ops'].includes(currentUser.value.roleCode))
  const isOperator = computed(() => currentUser.value.roleCode === 'operator')

  const persist = () => {
    if (token.value) localStorage.setItem('venue_access_token', token.value)
    else localStorage.removeItem('venue_access_token')
    localStorage.setItem('venue_current_user', JSON.stringify(currentUser.value))
  }

  const login = async (username, password) => {
    const result = await api.login(username, password)
    token.value = result.access_token
    currentUser.value = {
      id: username,
      username: result.user.username,
      displayName: result.user.display_name,
      roleCode: result.user.role,
      roleName: result.user.role_name,
      sessionExpiresIn: result.expires_in
    }
    persist()
    return result
  }

  const logout = async () => {
    try {
      if (token.value) await api.logout()
    } finally {
      token.value = ''
      currentUser.value = emptyUser()
      persist()
    }
  }

  const refreshUser = async () => {
    if (!token.value) return false
    try {
      const user = await api.me()
      currentUser.value = {
        id: user.username,
        username: user.username,
        displayName: user.display_name,
        roleCode: user.role,
        roleName: user.role_name,
        sessionExpiresIn: Math.max(0, user.expires_at - Math.floor(Date.now() / 1000))
      }
      persist()
      return true
    } catch {
      await logout()
      return false
    }
  }

  // 角色切换不再由前端伪造；管理员必须通过真实用户/角色管理接口完成授权。
  const switchRole = () => false

  return {
    token,
    currentUser,
    presetRoles,
    isLoggedIn,
    isAdmin,
    isOpsOrAdmin,
    isOperator,
    switchRole,
    login,
    logout,
    refreshUser
  }
})
