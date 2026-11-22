import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { systemSettingService } from '@/services/systemSettingService'

const routes = [
  // 1. 统一认证登录页 (公开路由 / BlankLayout)
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginPage.vue'),
    meta: { title: '统一身份认证登录页', shortTitle: '身份认证', layout: 'blank', public: true }
  },

  // 默认根重定向至综合态势
  {
    path: '/',
    redirect: '/dashboard'
  },

  // PC 端主控制台路由 (DefaultLayout)
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/DashboardOverview.vue'),
    meta: { title: '场馆综合态势总览工作台', shortTitle: '态势总览', icon: 'SvgDashboard' }
  },

  // 应用聚合门户 (支柱二)
  {
    path: '/portal/nav',
    name: 'PortalNav',
    component: () => import('@/views/portal/PortalNavGrid.vue'),
    meta: { title: '场馆应用与网站聚合导航大厅', shortTitle: '应用导航', icon: 'SvgCompassNav' }
  },
  {
    path: '/portal/external',
    name: 'ExternalIntegration',
    component: () => import('@/views/portal/ExternalIntegrationView.vue'),
    meta: { title: '外部系统与本地软件集成中心', shortTitle: '外部集成', icon: 'SvgIframeApp' }
  },
  {
    path: '/portal/app/:id',
    name: 'IframeContainer',
    component: () => import('@/views/portal/IframeContainer.vue'),
    meta: { title: '第三方系统安全代理内嵌工作台', shortTitle: '内嵌代理', icon: 'SvgIframeApp' }
  },

  // 物联网控制模块 (支柱一)
  {
    path: '/iot/devices',
    name: 'IotDeviceMatrix',
    component: () => import('@/views/iot/IotDeviceMatrixView.vue'),
    meta: { title: '物联硬件设备矩阵与批量总控台', shortTitle: '物联设备', icon: 'SvgIotControl' }
  },
  {
    path: '/iot/audio',
    name: 'AudioMatrixControl',
    component: () => import('@/views/iot/AudioMatrixControl.vue'),
    meta: { title: '扩声调音与场景音效控制台', shortTitle: '专业扩声', icon: 'SvgSoundMatrix' }
  },
  {
    path: '/iot/lighting',
    name: 'LightingEnergyControl',
    component: () => import('@/views/iot/LightingEnergyControl.vue'),
    meta: { title: '场地照明场景与能耗监测台', shortTitle: '场地照明', icon: 'SvgLighting' }
  },
  {
    path: '/iot/screen',
    name: 'ScreenScoreControl',
    component: () => import('@/views/iot/LedScreenDispatchConsole.vue'),
    meta: { title: 'LED大屏与推屏调度控制台', shortTitle: '大屏调度', icon: 'SvgLedScreen' }
  },
  {
    path: '/iot/score',
    name: 'MatchScoreBoard',
    component: () => import('@/views/iot/MatchTimingScoreBoard.vue'),
    meta: { title: '赛事计时计分接收与大屏推屏', shortTitle: '计时计分', icon: 'SvgMatchScore' }
  },
  {
    path: '/iot/flag',
    name: 'FlagAutoControl',
    component: () => import('@/views/iot/FlagAutoControl.vue'),
    meta: { title: '自动升旗仪式与音画同步仿真台', shortTitle: '智能升旗', icon: 'SvgFlagSystem' }
  },
  {
    path: '/iot/flag/countries',
    name: 'FlagCountryLibrary',
    component: () => import('@/views/iot/FlagCountryLibrary.vue'),
    meta: { title: '升旗国家资料库录入与编辑台', shortTitle: '国家资料库', icon: 'SvgAdapterBook' }
  },
  {
    path: '/iot/clock',
    name: 'ClockSyncMonitor',
    component: () => import('@/views/iot/ClockSyncMonitor.vue'),
    meta: { title: '标准时钟卫星授时与子钟监测台', shortTitle: '时钟同步', icon: 'SvgMasterClock' }
  },
  {
    path: '/iot/clock/floorplan',
    name: 'ClockFloorPlan',
    component: () => import('@/views/iot/ClockFloorPlan.vue'),
    meta: { title: '子钟场馆 SVG 平面图点位标注', shortTitle: '平面图点位', icon: 'SvgMasterClock' }
  },
  {
    path: '/iot/video',
    name: 'VideoLiveMatrix',
    component: () => import('@/views/iot/VideoLiveMatrix.vue'),
    meta: { title: '现场摄像机实时监看总控台', shortTitle: '视频监控', icon: 'SvgCameraMatrix' }
  },
  {
    path: '/iot/underwater-video',
    name: 'UnderwaterVideoControl',
    component: () => import('@/views/iot/UnderwaterVideoControl.vue'),
    meta: { title: '水下音像采集控制', shortTitle: '水下采集', icon: 'SvgCameraMatrix' }
  },
  {
    path: '/iot/underwater-video/ledger',
    name: 'UnderwaterLedger',
    component: () => import('@/views/iot/UnderwaterLedger.vue'),
    meta: { title: '水下音像识别台账与报警监视', shortTitle: '水下台账', icon: 'SvgCameraMatrix' }
  },
  {
    path: '/iot/video/ledger',
    redirect: '/iot/underwater-video/ledger'
  },
  {
    path: '/iot/media',
    name: 'MediaPlayConsole',
    component: () => import('@/views/iot/MediaPlayConsole.vue'),
    meta: { title: '媒体播控台(背景音乐与视频投屏)', shortTitle: '媒体播控', icon: 'SvgMediaPlayer' }
  },
  {
    path: '/iot/dynamic/:groupId',
    name: 'DynamicDeviceConsole',
    component: () => import('@/views/iot/DynamicDeviceConsole.vue'),
    meta: { title: '动态低代码通用设备控制台', shortTitle: '动态设备', icon: 'SvgDynamicDevice' }
  },

  // 4. 配置中心
  {
    path: '/config/devices',
    name: 'DeviceConfigCenter',
    component: () => import('@/views/iot/IotDeviceMatrixView.vue'),
    meta: { title: '物联硬件设备管理与总控中台', shortTitle: '设备管理', icon: 'SvgDeviceSetting', requiresOps: true }
  },
  {
    path: '/config/actions',
    name: 'ActionDynamicConfig',
    component: () => import('@/views/config/ActionDynamicConfig.vue'),
    meta: { title: '菜单分组与自定义操作按钮配置', shortTitle: '动作编排', icon: 'SvgButtonAction', requiresOps: true }
  },
  {
    path: '/config/adapters',
    name: 'HardwareAdapterBook',
    component: () => import('@/views/config/HardwareAdapterBook.vue'),
    meta: { title: '外置硬件适配与接线登记台账', shortTitle: '硬件适配', icon: 'SvgAdapterBook', requiresOps: true }
  },
  {
    path: '/config/media',
    name: 'MediaResourceLibrary',
    component: () => import('@/views/config/MediaResourceLibrary.vue'),
    meta: { title: '音频与视频媒体素材资源库', shortTitle: '媒体素材', icon: 'SvgMediaLibrary', requiresOps: true }
  },
  {
    path: '/config/templates',
    name: 'ConfigTemplateCenter',
    component: () => import('@/views/config/ConfigTemplateCenter.vue'),
    meta: { title: '配置模板与JSON导入导出中心', shortTitle: '配置模板', icon: 'SvgConfigTemplate', requiresAdmin: true }
  },
  {
    path: '/config/sandbox',
    name: 'ProtocolMockSandbox',
    component: () => import('@/views/config/ProtocolMockSandbox.vue'),
    meta: { title: '通信沙箱与模拟调试控制台', shortTitle: '协议沙箱', icon: 'SvgMockSandbox', requiresOps: true }
  },

  // 运维与安全审计模块
  {
    path: '/ops/alarms',
    name: 'AlarmMonitorCenter',
    component: () => import('@/views/ops/AlarmMonitorCenter.vue'),
    meta: { title: '全链路保活监控与实时告警中心', shortTitle: '链路告警', icon: 'SvgAlarmBell' }
  },
  {
    path: '/ops/channels',
    name: 'AlarmChannelConfig',
    component: () => import('@/views/ops/AlarmChannelConfig.vue'),
    meta: { title: '告警规则与通知渠道配置中心', shortTitle: '告警通道', icon: 'SvgNotifyChannel', requiresAdmin: true }
  },
  {
    path: '/ops/audit',
    name: 'AuditLogManager',
    component: () => import('@/views/ops/AuditLogManager.vue'),
    meta: { title: '操作审计日志与导出留存中心', shortTitle: '审计日志', icon: 'SvgAuditLog' }
  },
  {
    path: '/system/users',
    name: 'UserRolePermission',
    component: () => import('@/views/system/UserRolePermission.vue'),
    meta: { title: '用户角色管理与细粒度权限配置', shortTitle: '角色权限', icon: 'SvgUserRole', requiresAdmin: true }
  },
  {
    path: '/system/settings',
    name: 'SystemSetting',
    component: () => import('@/views/system/SystemSetting.vue'),
    meta: { title: '平台系统设置与对象存储中心', shortTitle: '系统设置', icon: 'SvgSettingGear', requiresAdmin: true }
  },
  {
    path: '/system/menu',
    name: 'MenuConfig',
    component: () => import('@/views/system/MenuManage.vue'),
    meta: { title: '导航菜单配置中心', shortTitle: '菜单配置', icon: 'SvgMenuList', requiresAdmin: true }
  },


  // 移动平板现场操作专属路由 (TabletLayout)
  {
    path: '/tablet/control',
    name: 'TabletControl',
    component: () => import('@/views/tablet/TabletOperationsView.vue'),
    meta: { title: '移动平板现场操作横屏工作台', shortTitle: '平板控制', layout: 'tablet', icon: 'SvgTablet' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const sysName = systemSettingService.getSettings().systemName || '应用集成管控平台'
  document.title = (to.meta.title ? `${to.meta.title} · ` : '') + sysName

  if (to.meta.public) {
    next()
    return
  }

  if (!userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    next('/dashboard')
    return
  }
  if (to.meta.requiresOps && !userStore.isOpsOrAdmin) {
    next('/dashboard')
    return
  }

  next()
})

export default router
