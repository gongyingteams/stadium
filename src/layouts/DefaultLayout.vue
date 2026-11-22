<template>
  <div :class="['default-layout', { 'is-embedded': isEmbeddedMode }]">
    <!-- 1. 全局顶部导航栏 Header Bar -->
    <header v-if="!isEmbeddedMode" class="top-header">
      <!-- 左侧：系统品牌标牌 + 运行环境模式胶囊 (正式环境 / 测试环境) -->
      <div class="header-left">
        <div class="brand-box" @click="router.push('/dashboard')">
          <div class="logo-shield">
            <img
              v-if="(systemSettings.logoType === 'CUSTOM' || !systemSettings.logoType) && (systemSettings.logoUrl || systemSettings.systemLogo)"
              :src="systemSettings.logoUrl || systemSettings.systemLogo" class="custom-header-logo" alt="系统Logo" />
            <SvgIcon v-else :name="systemSettings.logoPresetName || systemSettings.systemLogoPreset || 'SvgPortal'"
              size="28" />
          </div>
          <div class="title-meta">
            <span class="main-title">{{ systemSettings.systemName || '应用集成管控平台' }}</span>
            <span class="sub-title">{{ systemSettings.systemSubTitle || 'IBMS CONSOLE v1.0' }}</span>
          </div>
        </div>

        <span class="brand-env-divider"></span>

        <!-- 精致环境状态胶囊 (简化为：正式环境 / 测试环境) -->
        <div class="env-mode-capsule cursor-pointer" :class="appStore.isMockMode ? 'is-test' : 'is-prod'"
          :title="appStore.isMockMode ? '当前为【测试环境】(脱机沙箱调试，指令不向物理硬件真实发送)，点击切换' : '当前为【正式环境】(真实物理硬件连通，支持全协议双向下发)，点击切换'"
          @click="openEnvDialog">
          <span class="env-status-dot"></span>
          <span class="env-text">{{ appStore.isMockMode ? '测试环境' : '正式环境' }}</span>
          <el-icon class="env-arrow">
            <ArrowDown />
          </el-icon>
        </div>

        <!-- 离线模式提示角标: 后端不可达 / 配置未同步到服务器时如实告知, 避免各终端 Logo 与配置显示不一致而无人察觉 -->
        <div v-if="!settingsSyncState.synced" class="offline-sync-badge"
          :title="settingsSyncState.message || '后端服务不可达，当前展示的是本机浏览器缓存配置，系统Logo等品牌配置尚未同步到服务器数据库！'">
          <span class="offline-dot"></span>
          <span class="offline-text">离线模式 · 配置未同步</span>
        </div>
      </div>

      <!-- 中间：全场综合态势岛 (全链路保活状态 + 北斗授时，盘活中间黄金区域) -->
      <div class="header-center">
        <div class="central-pulse-island">
          <!-- 1. 全链路弱电子系统通信状态 -->
          <div class="pulse-item cursor-pointer" @click="router.push('/ops/alarms')" title="全场弱电子系统链路实时健康探测，点击查看">
            <span class="pulse-dot" :class="appStore.linkStats.fault > 0 ? 'fault' : 'online'"></span>
            <span class="pulse-lbl">全链路通信:</span>
            <span class="pulse-val online num-mono">正常 {{ appStore.linkStats.online }}</span>
            <span v-if="appStore.linkStats.fault > 0" class="pulse-val fault num-mono">/ 故障 {{ appStore.linkStats.fault
            }}</span>
          </div>

          <span class="pulse-divider"></span>

          <!-- 2. 北斗卫星授时标准时钟 -->
          <div class="pulse-item cursor-pointer" @click="router.push('/iot/clock')" title="北斗三号/GPS高精度授时同步，点击查看时钟网">
            <SvgIcon name="SvgMasterClock" size="14" class="pulse-clock-icon" />
            <span class="pulse-lbl">北斗授时:</span>
            <span class="pulse-val time num-mono">{{ currentTimeStr || '10:50:21' }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧：快捷工具组 + 细分割线 + 用户卡片 (舒展排布，彻底消除拥挤) -->
      <div class="header-right">
        <!-- 快捷操作工具组 -->
        <div class="header-actions-group">
          <!-- 未读告警铃铛 -->
          <div class="alarm-bell-btn cursor-pointer" title="实时未读告警流水" @click="appStore.isAlarmDrawerOpen = true">
            <SvgIcon name="SvgAlarmBell" size="18" />
            <span v-if="appStore.unreadAlarmCount > 0" class="alarm-counter num-mono">
              {{ appStore.unreadAlarmCount }}
            </span>
          </div>

          <!-- 平板视图入口 -->
          <el-tooltip content="切换为移动平板现场横屏触控台" placement="bottom">
            <button class="icon-action-btn" @click="router.push('/tablet/control')">
              <SvgIcon name="SvgTablet" size="18" />
            </button>
          </el-tooltip>

          <!-- 全屏切换 -->
          <el-tooltip content="全屏/退出全屏" placement="bottom">
            <button class="icon-action-btn" @click="toggleFullScreen">
              <el-icon>
                <FullScreen />
              </el-icon>
            </button>
          </el-tooltip>

          <!-- 蓝色主题切换器 (真实场景微缩模型调色盘) -->
          <el-popover v-model:visible="isThemePopoverOpen" trigger="click" placement="bottom-end" :width="390"
            popper-class="theme-picker-popover" :show-arrow="false" :offset="8">
            <template #reference>
              <button class="icon-action-btn theme-switch-btn" title="点击切换蓝色主题配色">
                <el-icon>
                  <Brush />
                </el-icon>
                <span class="theme-color-indicator" :style="{ background: themeStore.currentTheme.primary }"></span>
              </button>
            </template>

            <div class="theme-palette-panel">
              <div class="palette-header">
                <div class="palette-title">
                  <el-icon class="palette-icon">
                    <Brush />
                  </el-icon>
                  <span class="palette-text">系统主题配色方案</span>
                  <span class="palette-sub">(4 款蓝色基调)</span>
                </div>
                <span class="palette-active-badge">
                  当前: {{ themeStore.currentTheme.name }}
                </span>
              </div>

              <!-- 2x2 真实微缩界面卡片网格 -->
              <div class="theme-cards-grid">
                <div v-for="t in themes" :key="t.id"
                  :class="['theme-mini-card', { 'is-active': themeStore.currentThemeId === t.id }]"
                  @click="selectTheme(t.id)">
                  <!-- 微缩后台界面场景 (Mini UI Mockup) -->
                  <div class="mini-ui-mockup" :style="{ background: t.contentBg }">
                    <!-- 微缩顶部导航栏 Header -->
                    <div class="mockup-header" :style="{ background: t.headerBg }">
                      <span class="mockup-logo-dot" :style="{ background: t.primary }"></span>
                      <span class="mockup-title-bar"></span>
                      <div class="mockup-right-dots">
                        <span class="mockup-action-dot"></span>
                        <span class="mockup-action-dot"></span>
                      </div>
                    </div>

                    <!-- 微缩主体区 Body (Sidebar + Content) -->
                    <div class="mockup-body">
                      <!-- 微缩侧边栏 Sidebar -->
                      <div class="mockup-sidebar" :style="{ background: t.sidebarBg }">
                        <div class="mockup-nav-item is-active" :style="{ background: t.primary }"></div>
                        <div class="mockup-nav-item"></div>
                        <div class="mockup-nav-item"></div>
                        <div class="mockup-nav-item"></div>
                      </div>

                      <!-- 微缩工作台 Content -->
                      <div class="mockup-content">
                        <div class="mockup-stat-card" :style="{ background: t.cardBg }">
                          <span class="mockup-badge-pill" :style="{ background: t.primary }"></span>
                          <span class="mockup-num-bar"></span>
                        </div>
                        <div class="mockup-table-card" :style="{ background: t.cardBg }">
                          <span class="mockup-line-row"></span>
                          <span class="mockup-line-row short"></span>
                        </div>
                      </div>
                    </div>

                    <!-- 激活选中光晕角标 -->
                    <div v-if="themeStore.currentThemeId === t.id" class="mockup-active-badge">
                      <el-icon>
                        <Check />
                      </el-icon>
                    </div>
                  </div>

                  <!-- 卡片底部信息与色彩 DNA -->
                  <div class="mini-card-meta">
                    <div class="meta-title-row">
                      <span class="meta-name">{{ t.name }}</span>
                      <span class="meta-tag" :class="{ 'dark-tag': t.id === 'tech-blue' }">{{ t.modeTag }}</span>
                    </div>
                    <div class="meta-dna-row"
                      :title="`顶栏: ${t.headerBg} · 侧栏: ${t.sidebarBg} · 主色: ${t.primary} · 底色: ${t.contentBg}`">
                      <div class="dna-swatches">
                        <span class="dna-circle" :style="{ background: t.headerBg }" title="顶部 Header 真实色"></span>
                        <span class="dna-circle" :style="{ background: t.sidebarBg }" title="左侧 Sidebar 真实色"></span>
                        <span class="dna-circle" :style="{ background: t.primary }" title="系统 Primary 核心主色"></span>
                        <span class="dna-circle is-border" :style="{ background: t.contentBg }"
                          title="内容区 Background 底色"></span>
                      </div>
                      <span class="meta-desc">{{ t.description.split('·')[0].trim() }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 底部说明栏 -->
              <div class="palette-footer">
                <span class="footer-tip">点击卡片直观即时切换，全站弱电子系统联动渲染</span>
              </div>
            </div>
          </el-popover>
        </div>

        <!-- 细竖分割线 -->
        <span class="header-sep-divider"></span>

        <!-- 当前用户与角色切换 (演示用便捷切换) -->
        <el-dropdown trigger="click" @command="handleRoleSwitch">
          <div class="user-profile-badge cursor-pointer" title="点击查看当前账号与切换角色">
            <div class="user-avatar-wrap">
              <div class="user-avatar">{{ formattedUserName.charAt(0) }}</div>
              <span class="user-status-dot online" title="会话在线"></span>
            </div>
            <div class="user-info">
              <span class="user-name">{{ formattedUserName }}</span>
              <span class="user-role-tag">{{ userStore.currentUser.roleName || '系统管理员' }}</span>
            </div>
            <el-icon class="user-arrow-down">
              <ArrowDown />
            </el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>当前角色由服务端权限管理：</el-dropdown-item>
              <el-dropdown-item v-for="r in userStore.presetRoles" :key="r.code" disabled>
                <span :class="{ 'text-primary font-bold': userStore.currentUser.roleCode === r.code }">
                  {{ r.name }}
                </span>
              </el-dropdown-item>
              <el-dropdown-item divided command="slo_logout">
                <span style="color: var(--do-danger-deep); font-weight: bold;">一键 SLO 登出全部系统</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 2. 下部主体：侧边栏 + 内容区 -->
    <div class="main-container">
      <!-- 左侧菜单导航树 (PC 端 22 个静态节点 + 动态节点) -->
      <aside v-if="!isEmbeddedMode" :class="['sidebar-nav', { collapsed: isSidebarCollapsed }]">
        <div class="sidebar-scroll">
          <div v-for="(grp, gIdx) in menuGroups" :key="grp.id" class="menu-group-block">
            <!-- 分组间分隔线 (仅保留细金渐隐线) -->
            <div v-if="gIdx > 0" class="menu-group-separator" :title="grp.title.replace(/^\d+\.\s*/, '')">
              <span class="sep-line"></span>
            </div>

            <ul class="sub-menu-list">
              <li v-for="sub in grp.children" :key="sub.menuKey || sub.path"
                :class="['menu-item', { active: currentPath === sub.path, disabled: !hasPermission(sub) }]"
                :title="sub.title" @click="navigateMenu(sub)">
                <div class="menu-item-content">
                  <SvgIcon :name="sub.icon" size="20" stroke-width="2.2" class="item-icon" />
                  <span v-if="!isSidebarCollapsed" class="item-title">{{ sub.shortTitle || sub.title }}</span>
                </div>
                <div v-if="!isSidebarCollapsed && getMenuItemBadge(sub)" class="item-extra-tags">
                  <span :class="['device-count-pill', 'num-mono', { 'alert-badge': sub.badge }]"
                    :title="`当前分类已纳管 ${getMenuItemBadge(sub)} 台设备`">
                    {{ getMenuItemBadge(sub) }}
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- 侧边栏折叠按钮 -->
        <div class="sidebar-footer">
          <button class="btn-collapse" @click="isSidebarCollapsed = !isSidebarCollapsed">
            <el-icon v-if="isSidebarCollapsed">
              <Expand />
            </el-icon>
            <el-icon v-else>
              <Fold />
            </el-icon>
            <span v-if="!isSidebarCollapsed" style="margin-left: 8px;">收起导航</span>
          </button>
        </div>
      </aside>

      <!-- 右侧内容工作区 -->
      <section class="content-viewport">
        <!-- 顶部面包屑与快捷信息 -->
        <div v-if="!isEmbeddedMode" class="viewport-breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">
              <span class="crumb-home-link">
                <SvgIcon name="SvgDashboard" size="14" class="crumb-icon" />
                <span>首页</span>
              </span>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentGroupName && currentPath !== '/dashboard'">
              <span class="crumb-group-text">{{ currentGroupName }}</span>
            </el-breadcrumb-item>
            <el-breadcrumb-item>
              <span class="crumb-active-text">{{ currentRouteTitle }}</span>
            </el-breadcrumb-item>
          </el-breadcrumb>

          <div class="breadcrumb-right">
            <span class="session-clock num-mono">会话有效: {{ Math.floor(userStore.currentUser.sessionExpiresIn / 60)
            }}m</span>
          </div>
        </div>

        <!-- 视图插槽 -->
        <div class="page-content-wrapper">
          <slot />
        </div>
      </section>
    </div>

    <!-- 3. 全局滑出式未读告警抽屉 -->
    <el-drawer v-model="appStore.isAlarmDrawerOpen" title="全链路设备实时告警中心" size="480px" direction="rtl">
      <div class="alarm-drawer-content">
        <div class="drawer-toolbar">
          <span class="drawer-stats">当前待处置: {{ appStore.unreadAlarmCount }} 条</span>
          <el-button size="small" type="warning" plain @click="muteAllAlarms">
            {{ appStore.isSoundMuted ? '已静音' : '一键静音蜂鸣' }}
          </el-button>
        </div>

        <div class="alarm-cards-list">
          <div v-for="alm in appStore.alarms" :key="alm.id" :class="['alarm-card-item', alm.level.toLowerCase()]">
            <div class="alm-header">
              <span class="alm-level-tag">{{ alm.level === 'EMERGENCY' ? '紧急故障' : alm.level === 'WARNING' ? '警告预警' :
                '运行提示'
              }}</span>
              <span class="alm-time num-mono">{{ alm.time }}</span>
            </div>
            <div class="alm-title">{{ alm.title }}</div>
            <div class="alm-device">涉及设备: {{ alm.device }}</div>
            <div class="alm-desc">{{ alm.desc }}</div>
            <div class="alm-actions">
              <el-button v-if="alm.status === 'NEW'" size="small" type="primary" @click="appStore.confirmAlarm(alm.id)">
                确认告警
              </el-button>
              <el-button size="small" type="info" plain @click="appStore.closeAlarm(alm.id)">
                关闭处置
              </el-button>
              <el-button size="small" link @click="router.push('/ops/alarms')">
                查看全量流水
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 4. 一键 SLO 登出模态窗 -->
    <el-dialog v-model="showSloDialog" title="一键 SLO 单点登出确认" width="540px">
      <div class="slo-dialog-body">
        <p class="slo-desc">
          本次操作将执行 SLO (Single Logout) 广播，同步注销本管控平台会话、Redis 联合 Session，并向已接入的 13 类第三方子系统及 iframe 代理容器下发注销凭证：
        </p>

        <div class="slo-subsystem-table">
          <div v-for="app in sloApps" :key="app.name" class="slo-app-row">
            <span class="app-name">{{ app.name }}</span>
            <span :class="['app-status', app.status]">
              {{ app.status === 'SUCCESS' ? '已注销' : app.status === 'PENDING' ? '等待销毁' : '正在下发...' }}
            </span>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSloDialog = false">取消</el-button>
          <el-button type="danger" :loading="isSloLoading" @click="executeSloLogout">
            确认全部安全登出
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 5. 运行环境模式切换弹窗 (正式环境 / 测试环境) -->
    <el-dialog v-model="showMockDialog" title="运行环境模式切换（正式环境 / 测试环境）" width="480px">
      <div class="mock-dialog-body">
        <el-alert title="防呆机制警告：模式切换将影响全场馆所有弱电子系统控制指令的真实物理下发行为！" type="warning" :closable="false" show-icon
          style="margin-bottom: 16px;" />
        <el-form label-position="top">
          <el-form-item label="当前运行环境">
            <el-switch v-model="tempMockState" active-text="测试环境 (脱机沙箱，拦截指令不发下位机)"
              inactive-text="正式环境 (真实物理硬件，下发真实串口/网口指令)" />
          </el-form-item>
          <el-form-item label="切换原因说明 (将写入操作审计日志)">
            <el-input v-model="mockReason" placeholder="例如：现场声控联调完毕，切回正式环境真实下发" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showMockDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMockState">确认应用变更</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { useThemeStore, THEMES as themes } from '@/stores/theme'
import { useMenuStore } from '@/stores/menu'
import { iotDeviceService } from '@/services/iotDeviceService'
import { systemSettingService } from '@/services/systemSettingService'
import {
  ArrowDown,
  FullScreen,
  Fold,
  Expand,
  Brush,
  Check
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const themeStore = useThemeStore()
const menuStore = useMenuStore()

// 判断当前是否处于嵌入视窗预览模式（例如在视窗切换或外部 iframe 嵌入中，路由参数带 embedded=1）
const isEmbeddedMode = computed(() => {
  return route.query.embedded === '1' || route.query.embedded === 'true'
})

// 纯用户名展示 (例如: Admin, Ops, Operator)
const formattedUserName = computed(() => {
  const u = userStore.currentUser?.username
  if (u) {
    return u.charAt(0).toUpperCase() + u.slice(1)
  }
  return 'Admin'
})

// 系统设置响应式数据与动态更新监听
const systemSettings = ref({ ...systemSettingService.getSettings() })
const onSettingsChange = (e) => {
  const latest = e?.detail || systemSettingService.getSettings()
  systemSettings.value = { ...latest }
}
const onStorageChange = (e) => {
  if (e.key === 'ibms_system_settings_v1') {
    systemSettings.value = { ...systemSettingService.getSettings() }
  }
}

// 远端配置同步状态 (后端不可达时显示"离线模式·配置未同步"角标)
const settingsSyncState = ref({ synced: true, message: '' })
const onSettingsSyncState = (e) => {
  settingsSyncState.value = { synced: !!e?.detail?.synced, message: e?.detail?.message || '' }
}
const onApiStatus = (e) => {
  if (e?.detail && e.detail.online === false) {
    settingsSyncState.value = { synced: false, message: '后端服务不可达，当前展示的是本机浏览器缓存配置' }
  }
}

const isSidebarCollapsed = ref(false)
const showSloDialog = ref(false)
const showMockDialog = ref(false)
const isSloLoading = ref(false)
const tempMockState = ref(appStore.isMockMode)
const mockReason = ref('现场脱机联调测试')

// 北斗授时标准时钟实时走动
const currentTimeStr = ref('')
const updateClock = () => {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  currentTimeStr.value = `${h}:${m}:${s}`
}
let clockTimer = null
onMounted(async () => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  window.addEventListener('ibms-system-settings-changed', onSettingsChange)
  window.addEventListener('ibms-system-settings-sync', onSettingsSyncState)
  window.addEventListener('ibms-api-status', onApiStatus)
  window.addEventListener('storage', onStorageChange)
  // 拉取后端最新菜单树 (后端不可达时 service 内部降级本地缓存)
  try {
    await menuStore.load()
  } catch (err) {
    console.warn('DefaultLayout: menuStore.load error', err)
  }
  try {
    const remote = await systemSettingService.fetchRemoteSettings()
    if (remote) {
      systemSettings.value = { ...remote }
    }
  } catch (err) {
    console.warn('DefaultLayout: fetchRemoteSettings error', err)
  }
})
onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  window.removeEventListener('ibms-system-settings-changed', onSettingsChange)
  window.removeEventListener('ibms-system-settings-sync', onSettingsSyncState)
  window.removeEventListener('ibms-api-status', onApiStatus)
  window.removeEventListener('storage', onStorageChange)
})

// 打开运行环境切换弹窗
const openEnvDialog = () => {
  tempMockState.value = appStore.isMockMode
  showMockDialog.value = true
}

const currentPath = computed(() => route.path)
const currentRouteTitle = computed(() => route.meta.title || '')

// 完整的菜单树: 由 menuStore 提供 (后端 sys_menu 数据驱动), 后端不可达时降级出厂默认菜单
// 隐藏(visible=false)的分组/菜单项不渲染; 分组内全部项隐藏时整组隐藏
const menuGroups = computed(() => {
  const list = menuStore.groups && menuStore.groups.length
    ? menuStore.groups
    : menuStore.DEFAULT_MENU_CONFIG.groups
  return list
    .map(g => ({
      ...g,
      children: (g.children || []).filter(c => c.visible !== false)
    }))
    .filter(g => g.visible !== false && g.children.length > 0)
})

// 动态计算菜单项右侧的设备数量 Badge (由菜单配置的 badgeType 驱动: 硬件类型或全场总数)
const getMenuItemBadge = (sub) => {
  const badgeType = sub.badgeType
  if (badgeType && badgeType !== 'TOTAL') {
    try {
      const list = iotDeviceService.getDevices(badgeType)
      return list && list.length ? `${list.length}` : (sub.deviceCount ? `${sub.deviceCount}` : null)
    } catch (e) {
      return sub.deviceCount ? `${sub.deviceCount}` : null
    }
  }
  if (badgeType === 'TOTAL' || sub.showTotalCount) {
    try {
      const all = iotDeviceService.getDevices()
      return all && all.length ? `${all.length}` : null
    } catch (e) {
      return null
    }
  }
  return sub.badge || (sub.deviceCount ? `${sub.deviceCount}` : null)
}

// 提取当前路由所属一级分类分组名称 (用于面包屑清晰层级)
const currentGroupName = computed(() => {
  for (const group of menuGroups.value) {
    if (group.children?.some(c => c.path === currentPath.value)) {
      return group.title.replace(/^\d+\.\s*/, '')
    }
  }
  return ''
})

// 权限校验判断 (场馆操作员严格物理隔离通信配置)
const hasPermission = (menuItem) => {
  if (menuItem.requiresAdmin && !userStore.isAdmin) return false
  if (menuItem.requiresOps && !userStore.isOpsOrAdmin) return false
  return true
}

const navigateMenu = (sub) => {
  if (!hasPermission(sub)) {
    ElMessage.warning('当前角色无权访问底层敏感配置，已启动安全防呆保护！')
    return
  }
  // 外链 (http/https 开头): 新标签页打开, 不 hijack 站内路由
  if (/^https?:\/\//i.test(sub.path || '')) {
    window.open(sub.path, '_blank', 'noopener,noreferrer')
    return
  }
  router.push(sub.path)
}

const handleRoleSwitch = (command) => {
  if (command === 'slo_logout') {
    showSloDialog.value = true
  }
}

const isThemePopoverOpen = ref(false)

const handleThemeSwitch = (themeId) => {
  themeStore.setTheme(themeId)
  const theme = themes.find(t => t.id === themeId)
  if (theme) {
    ElMessage.success(`已切换至「${theme.name}」主题`)
  }
}

const selectTheme = (themeId) => {
  handleThemeSwitch(themeId)
  isThemePopoverOpen.value = false
}

// SLO 单点登出执行
const sloApps = ref([
  { name: '体育场馆IBMS统一主平台 Session', status: 'PENDING' },
  { name: '售验票管理系统后台 (Ticketing SSO)', status: 'PENDING' },
  { name: '信息发布与排期系统 (InfoPub SSO)', status: 'PENDING' },
  { name: '计时计分成绩推送代理会话', status: 'PENDING' },
  { name: 'Redis联合鉴权缓存令牌池', status: 'PENDING' }
])

const executeSloLogout = async () => {
  isSloLoading.value = true
  try {
    sloApps.value.forEach(app => { app.status = 'PENDING' })
    await userStore.logout()
    sloApps.value.forEach(app => { app.status = 'SUCCESS' })
    showSloDialog.value = false
    ElMessage.success('SLO 全部会话注销完成，已退出系统')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.message || 'SLO注销失败，请重试')
  } finally {
    isSloLoading.value = false
  }
}

// 运行环境模式切换
const saveMockState = async () => {
  try {
    await appStore.toggleMockMode(tempMockState.value, mockReason.value)
    showMockDialog.value = false
    ElMessage.success(
      tempMockState.value
        ? '已成功切换至【测试环境】(脱机沙箱调试，指令不向物理硬件真实发送)'
        : '已成功切换至【正式环境】(真实物理硬件连通，支持全协议双向下发)'
    )
  } catch (error) {
    ElMessage.error(error.message || '环境模式切换失败')
  }
}

const muteAllAlarms = () => {
  appStore.isSoundMuted = !appStore.isSoundMuted
  ElMessage.info(appStore.isSoundMuted ? '已全局静音当前告警蜂鸣' : '已恢复告警声音播报')
}

const toggleFullScreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}
</script>

<style scoped>
.default-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--do-bg-page);
}

/* 顶部导航 Header (贝都因深咖啡底座 · 细金描边 · 克制光晕) */
.top-header {
  height: 60px;
  flex-shrink: 0;
  background:
    radial-gradient(700px 120px at 20% 0%, var(--th-header-glow), transparent 70%),
    linear-gradient(180deg, var(--th-header-grad-1) 0%, var(--th-header-grad-2) 55%, var(--th-header-grad-3) 100%);
  border-bottom: 1px solid var(--th-header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: 0 18px;
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  box-shadow: 0 2px 10px var(--th-header-shadow);
}

/* 顶栏底部 1px 金色工控饰线 */
.top-header::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--th-header-line) 20%, var(--th-header-line) 80%, transparent);
  pointer-events: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.brand-box {
  display: flex;
  align-items: center;
  gap: 11px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: var(--transition-fast);
}

.brand-box:hover .main-title {
  color: var(--do-text-inverse);
}

/* Logo 容器：完全透明背景，无底色 */
.logo-shield {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  box-sizing: border-box;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

/* 鼠标悬浮在 Logo 上或品牌区域时，坚决不显示任何背景色 */
.brand-box:hover .logo-shield,
.logo-shield:hover {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
}

.custom-header-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  overflow: hidden;
}

.title-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.main-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-text-inverse);
  letter-spacing: 0.6px;
  line-height: 1.2;
  transition: color var(--transition-fast);
}

.sub-title {
  font-family: var(--font-family-mono);
  font-size: 14px;
  color: var(--do-text-inverse-sub);
  letter-spacing: 1.4px;
  line-height: 1.2;
}

/* 品牌与环境胶囊间微分割线 */
.brand-env-divider {
  width: 1px;
  height: 18px;
  background: rgba(255, 255, 255, 0.18);
  margin: 0 2px;
}

/* 离线模式 · 配置未同步 角标 (后端不可达时如实提示，避免各终端品牌/Logo 显示不一致) */
.offline-sync-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 600;
  user-select: none;
  white-space: nowrap;
  background: rgba(239, 68, 68, 0.16);
  border: 1px solid rgba(239, 68, 68, 0.45);
  color: #FCA5A5;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.18);
  animation: offline-pulse 1.8s ease-in-out infinite;
}

.offline-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #EF4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.9);
}

.offline-text {
  letter-spacing: 0.2px;
}

@keyframes offline-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.62; }
}

/* 简化版运行环境状态胶囊 (正式环境 / 测试环境) */
.env-mode-capsule {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.22s ease;
  user-select: none;
  border: 1px solid transparent;
}

/* 测试环境 (琥珀黄底微光) */
.env-mode-capsule.is-test {
  background: rgba(245, 158, 11, 0.16);
  border-color: rgba(245, 158, 11, 0.45);
  color: #FCD34D;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.15);
}

.env-mode-capsule.is-test:hover {
  background: rgba(245, 158, 11, 0.26);
  border-color: #F59E0B;
  box-shadow: 0 0 14px rgba(245, 158, 11, 0.3);
}

/* 正式环境 (翡翠绿底微光) */
.env-mode-capsule.is-prod {
  background: rgba(16, 185, 129, 0.16);
  border-color: rgba(16, 185, 129, 0.45);
  color: #6EE7B7;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
}

.env-mode-capsule.is-prod:hover {
  background: rgba(16, 185, 129, 0.26);
  border-color: #10B981;
  box-shadow: 0 0 14px rgba(16, 185, 129, 0.3);
}

.env-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.env-mode-capsule.is-test .env-status-dot {
  background: #F59E0B;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.8);
}

.env-mode-capsule.is-prod .env-status-dot {
  background: #10B981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.8);
  animation: pulseDot 2s infinite ease-in-out;
}

@keyframes pulseDot {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.6;
    transform: scale(0.85);
  }
}

.env-text {
  font-size: 13px;
  letter-spacing: 0.3px;
}

.env-arrow {
  font-size: 13px !important;
  opacity: 0.85;
  transition: transform 0.2s ease;
}

.env-mode-capsule:hover .env-arrow {
  transform: translateY(1px);
  opacity: 1;
}

/* 中间：全场综合态势岛 (盘活中间，居中陈列) */
.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-width: 0;
  padding: 0 16px;
}

.central-pulse-island {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 4px 16px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: 20px;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: all 0.25s ease;
  user-select: none;
}

.central-pulse-island:hover {
  border-color: rgba(var(--th-accent-rgb), 0.5);
  box-shadow: 0 4px 14px rgba(var(--th-accent-rgb), 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.pulse-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--do-text-inverse);
  transition: all 0.2s ease;
}

.pulse-item:hover {
  color: var(--do-gold);
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.pulse-dot.online {
  background: #10B981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.8);
}

.pulse-dot.fault {
  background: #EF4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.8);
}

.pulse-lbl {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
}

.pulse-val.online {
  color: #34D399;
  font-weight: 700;
}

.pulse-val.fault {
  color: #F87171;
  font-weight: 700;
}

.pulse-val.time {
  color: #F8FAFC;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.pulse-clock-icon {
  color: var(--do-gold);
}

.pulse-divider {
  width: 1px;
  height: 14px;
  background: rgba(255, 255, 255, 0.22);
}

/* 右侧：快捷工具组 + 分割线 + 用户卡片 (舒展排布，消除拥挤) */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.header-actions-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-sep-divider {
  width: 1px;
  height: 18px;
  background: rgba(255, 255, 255, 0.18);
  margin: 0 2px;
}

.alarm-bell-btn {
  position: relative;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: var(--radius-sm);
  color: var(--do-gold);
  transition: var(--transition-fast);
}

.alarm-bell-btn:hover {
  background: var(--th-menu-hover-grad);
  border-color: var(--do-gold);
  color: var(--do-text-inverse);
  transform: translateY(-1px);
}

.alarm-counter {
  position: absolute;
  top: -5px;
  right: -5px;
  background: var(--do-danger);
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 700;
  min-width: 17px;
  height: 17px;
  line-height: 17px;
  text-align: center;
  padding: 0 4px;
  border-radius: var(--radius-pill);
  border: 1.5px solid var(--th-alarm-counter-border);
  box-shadow: 0 2px 6px var(--th-alarm-counter-shadow);
}

.icon-action-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: var(--radius-sm);
  color: var(--do-text-inverse);
  font-size: 16px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.icon-action-btn:hover {
  border-color: var(--do-gold);
  color: var(--do-gold);
  background: var(--th-menu-hover-grad);
  transform: translateY(-1px);
}

/* 当前登录用户信息区域 (高质感通透毛玻璃圆润胶囊，层次分明，呼应左侧环境胶囊) */
.user-profile-badge {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 3px 12px 3px 5px;
  /* background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 20px; */
  color: #FFFFFF;
  transition: all var(--transition-fast);
  user-select: none;
  backdrop-filter: blur(8px);
}


.user-avatar-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar {
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0.1) 100%);
  color: #FFFFFF;
  border: 1.5px solid rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.user-profile-badge:hover .user-avatar {
  transform: scale(1.06);
  border-color: #FFFFFF;
}

.user-status-dot {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  border: 1.5px solid var(--th-header-bg, #003366);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.8);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  gap: 2px;
}

.user-name {
  font-size: 13px;
  font-weight: 700;
  color: #FFFFFF;
  line-height: 1.25;
  letter-spacing: 0.3px;
}

.user-role-tag {
  font-size: 13px;
  color: #FDE68A;
  line-height: 1.25;
  font-weight: 500;
  opacity: 0.95;
}

.user-arrow-down {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-left: 2px;
  transition: all var(--transition-fast);
}

.user-profile-badge:hover .user-arrow-down {
  color: #FDE68A;
  transform: translateY(1px);
}

/* 主结构 Main Container */
.main-container {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* 侧边栏 Sidebar (贝都因深沉石黑底座 · 细金侧线) */
.sidebar-nav {
  width: 228px;
  background:
    radial-gradient(300px 200px at 0% 0%, var(--th-sidebar-glow), transparent 65%),
    linear-gradient(180deg, var(--th-sidebar-grad-1) 0%, var(--th-sidebar-grad-2) 45%, var(--th-sidebar-grad-3) 100%);
  border-right: 1px solid var(--th-sidebar-border);
  display: flex;
  flex-direction: column;
  transition: width var(--dur-normal) var(--ease-out-expo);
  user-select: none;
  flex-shrink: 0;
  position: sticky;
  top: 60px;
  height: calc(100vh - 60px);
}

.sidebar-nav.collapsed {
  width: 60px;
}

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 8px 16px;
}

.menu-group-block {
  margin-bottom: 3px;
}

/* 分类分隔线：克制的细金渐隐线，不干扰菜单阅读 */
.menu-group-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 6px;
  margin: 8px 0 6px 0;
}

.sep-line {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--th-sidebar-sep) 30%, var(--th-sidebar-sep) 70%, transparent);
}

.sidebar-nav.collapsed .menu-group-separator {
  padding: 8px 2px;
}

.sub-menu-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

/* 菜单项：左侧金边 + 柔光底，加大行高与触控面积 */
.menu-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 11px 12px;
  min-height: 44px;
  line-height: 1.45;
  margin-bottom: 4px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--th-menu-text, #DCE7F5);
  font-weight: 500;
  transition: var(--transition-fast);
  border-left: 3px solid transparent;
}

.menu-item::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--th-menu-hover-grad), transparent 70%);
  opacity: 0;
  transition: opacity var(--dur-fast) var(--ease-out-expo);
  pointer-events: none;
}

.menu-item:hover {
  color: var(--th-menu-hover-text, #FFFFFF);
  transform: translateX(2px);
}

.menu-item:hover::after {
  opacity: 1;
}

.menu-item.active {
  background: linear-gradient(90deg, var(--th-menu-active-grad-1), var(--th-menu-active-grad-2));
  color: var(--th-menu-active-text, #FFFFFF);
  border-left-color: var(--th-menu-active-border, #60A5FA);
  font-weight: 700;
  box-shadow: inset 0 0 0 1px var(--th-menu-active-shadow-1), -3px 0 12px var(--th-menu-active-shadow-2);
}

.menu-item.active .item-title {
  color: var(--th-menu-active-text, #FFFFFF);
  font-weight: 700;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.45);
}

.menu-item.disabled {
  opacity: 0.32;
  cursor: not-allowed;
}

.menu-item.disabled:hover {
  transform: none;
  color: var(--th-menu-text, #DCE7F5);
}

.menu-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.item-icon {
  width: 20px;
  height: 20px;
  min-width: 20px;
  min-height: 20px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--th-menu-icon);
  transition: all var(--transition-fast);
}

.menu-item:hover .item-icon {
  color: var(--th-menu-icon-hover, #FFFFFF);
  filter: drop-shadow(0 0 4px var(--th-menu-icon-hover-glow));
}

.menu-item.active .item-icon {
  color: var(--th-menu-icon-active, #FFFFFF);
  filter: drop-shadow(0 0 6px var(--th-menu-icon-active-glow));
}

.crumb-icon {
  width: 14px;
  height: 14px;
  min-width: 14px;
  min-height: 14px;
  flex-shrink: 0;
}

.item-title {
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 1px;
  line-height: 1.4;
  transition: color var(--dur-fast) ease;
}

.item-extra-tags {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.device-count-pill {
  background: var(--th-pill-bg);
  border: 1px solid var(--th-pill-border);
  color: var(--th-pill-text, var(--th-menu-icon));
  font-family: var(--font-family-mono);
  font-size: 14px;
  font-weight: 700;
  padding: 0 8px;
  height: 19px;
  line-height: 17px;
  border-radius: var(--radius-pill);
  transition: all var(--transition-fast);
}

.menu-item:hover .device-count-pill {
  background: var(--th-pill-hover-bg);
  border-color: var(--th-pill-hover-border);
  color: var(--th-pill-hover-text, #FFFFFF);
}

.menu-item.active .device-count-pill {
  background: var(--th-menu-active-pill-bg, var(--el-color-primary));
  border-color: var(--th-menu-active-pill-border, var(--th-menu-active-border));
  color: #FFFFFF;
  box-shadow: 0 1px 4px var(--th-pill-active-shadow);
  font-weight: 700;
}

.device-count-pill.alert-badge {
  background: rgba(var(--th-danger-rgb), 0.3);
  color: var(--do-danger-border);
  border-color: var(--do-danger);
}

.item-badge {
  background: rgba(var(--th-danger-rgb), 0.25);
  color: var(--do-danger-border);
  border: 1px solid var(--do-danger);
  font-size: var(--fs-sm);
  padding: 0 8px;
  border-radius: var(--radius-pill);
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid var(--th-sidebar-footer-border);
  flex-shrink: 0;
}

.btn-collapse {
  width: 100%;
  padding: 9px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--th-menu-text, #DCE7F5);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1.4;
  transition: var(--transition-fast);
}

.btn-collapse:hover {
  background: rgba(var(--th-accent-rgb), 0.18);
  border-color: rgba(var(--th-accent-rgb), 0.35);
  color: var(--th-menu-hover-text, #FFFFFF);
}

/* 视口区 Content Viewport (撒哈拉细沙温暖工作台) */
.content-viewport {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--do-bg-page);
  overflow-x: hidden;
}

.viewport-breadcrumb {
  height: 42px;
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--th-crumb-grad-1) 0%, var(--th-crumb-grad-2) 100%);
  border-bottom: 1px solid var(--do-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: 0 20px;
  font-size: var(--fs-sm);
  box-shadow: var(--shadow-xs);
}

.viewport-breadcrumb :deep(.el-breadcrumb) {
  display: inline-flex;
  align-items: center;
  font-size: var(--fs-sm);
  line-height: 1;
}

/* 链接项 / 首页 */
.viewport-breadcrumb :deep(.el-breadcrumb__inner.is-link),
.viewport-breadcrumb :deep(.el-breadcrumb__inner a) {
  color: var(--th-crumb-link) !important;
  font-weight: 500 !important;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: var(--transition-fast);
  cursor: pointer;
}

.viewport-breadcrumb :deep(.el-breadcrumb__inner.is-link:hover),
.viewport-breadcrumb :deep(.el-breadcrumb__inner a:hover) {
  color: var(--do-gold-deep) !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* 面包屑分隔斜杠：清晰可见 */
.viewport-breadcrumb :deep(.el-breadcrumb__separator) {
  color: var(--th-crumb-sep) !important;
  font-weight: 400 !important;
  margin: 0 4px !important;
  font-size: var(--fs-sm) !important;
}

/* 中间一级分类文字 */
.crumb-group-text {
  color: var(--th-crumb-link) !important;
  font-weight: 500 !important;
}

/* 最后一级当前活动页面标题：深沉高对比 */
.viewport-breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner),
.crumb-active-text {
  color: var(--th-crumb-active) !important;
  font-weight: 700 !important;
  letter-spacing: 0.2px;
  cursor: default;
}

.crumb-home-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: inherit;
}

.crumb-icon {
  color: var(--do-gold-deep);
}

.breadcrumb-right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.session-clock {
  font-size: var(--fs-sm);
  color: var(--th-clock-text) !important;
  font-weight: 700;
  background: linear-gradient(180deg, var(--th-clock-grad-1), var(--th-clock-grad-2));
  border: 1px solid var(--th-clock-border);
  padding: 2px 10px;
  border-radius: var(--radius-sm);
}

.page-content-wrapper {
  flex: 1;
  padding: var(--pad-page);
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

/* 抽屉与弹窗样式 */
.alarm-drawer-content {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.drawer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-3);
  padding-bottom: 11px;
  border-bottom: 1px solid var(--do-border-light);
}

.drawer-stats {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--do-text-primary);
}

.alarm-cards-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alarm-card-item {
  position: relative;
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.22s ease, box-shadow 0.22s ease, transform 0.22s ease;
}

.alarm-card-item:hover {
  box-shadow: 0 4px 16px rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-gold);
}

.alarm-card-item.emergency {
  border-color: rgba(var(--th-danger-rgb, 239, 68, 68), 0.35);
  background: linear-gradient(135deg, var(--do-bg-card) 0%, rgba(var(--th-danger-rgb, 239, 68, 68), 0.06) 100%);
}

.alarm-card-item.warning {
  border-color: rgba(var(--th-warning-rgb, 245, 158, 11), 0.35);
  background: linear-gradient(135deg, var(--do-bg-card) 0%, rgba(var(--th-warning-rgb, 245, 158, 11), 0.06) 100%);
}

.alarm-card-item.info {
  border-color: rgba(var(--th-accent-rgb), 0.28);
  background: linear-gradient(135deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.06) 100%);
}

.alm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.alm-level-tag {
  font-size: var(--fs-sm);
  font-weight: 700;
  letter-spacing: 0.3px;
}

.emergency .alm-level-tag {
  color: var(--do-danger-deep);
}

.warning .alm-level-tag {
  color: var(--do-warning-deep);
}

.info .alm-level-tag {
  color: var(--do-text-secondary);
}

.alm-time {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
}

.alm-title {
  font-size: var(--fs-body);
  font-weight: 700;
  color: var(--do-text-primary);
  margin-bottom: 3px;
}

.alm-device {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
  margin-bottom: 5px;
}

.alm-desc {
  font-size: var(--fs-sm);
  color: var(--do-text-regular);
  line-height: var(--lh-loose);
  margin-bottom: 10px;
}

.alm-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* SLO 弹窗 */
.slo-dialog-body {
  font-size: var(--fs-body);
  color: var(--do-text-primary);
}

.slo-desc {
  margin-bottom: var(--sp-4);
  line-height: var(--lh-loose);
}

.slo-subsystem-table {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.slo-app-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-3);
  font-size: var(--fs-sm);
  padding: 7px 0;
  border-bottom: 1px solid var(--do-border-light);
}

.slo-app-row:last-child {
  border-bottom: none;
}

.app-status {
  font-weight: 700;
  flex-shrink: 0;
}

.app-status.SUCCESS {
  color: var(--do-success-deep);
}

.app-status.PENDING {
  color: var(--do-text-placeholder);
}

.cursor-pointer {
  cursor: pointer;
}

/* ---- 蓝色主题切换器 ---- */
.theme-switch-btn {
  position: relative;
  overflow: visible;
}

.theme-color-indicator {
  position: absolute;
  bottom: -3px;
  right: -3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1.5px solid var(--do-bg-card);
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
  transition: var(--transition-fast);
}

.theme-switch-btn:hover .theme-color-indicator {
  transform: scale(1.25);
}

.theme-dropdown-menu {
  min-width: 190px;
  padding: 6px !important;
}

.theme-dropdown-menu .el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px !important;
  border-radius: var(--radius-sm) !important;
}

.theme-swatch {
  display: inline-block;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid var(--do-border);
  flex-shrink: 0;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: var(--transition-fast);
}

.el-dropdown-menu__item:hover .theme-swatch {
  border-color: var(--do-gold);
  transform: scale(1.1);
}

.theme-name {
  flex: 1;
  font-size: var(--fs-sm);
  font-weight: 500;
}

.theme-check {
  color: var(--do-gold);
  font-size: 14px;
  flex-shrink: 0;
}

.el-dropdown-menu__item.is-active-theme {
  background: var(--do-gold-wash) !important;
  color: var(--do-gold-deep) !important;
  font-weight: 700 !important;
}

/* ============================================================
 * 嵌入式纯净模式（视窗切换 / 小部件无缝内嵌）
 * ============================================================ */
.default-layout.is-embedded {
  min-height: 100% !important;
  height: 100% !important;
  background-color: var(--do-bg-page);
}

.default-layout.is-embedded .main-container {
  height: 100% !important;
}

.default-layout.is-embedded .content-viewport {
  height: 100% !important;
}

.default-layout.is-embedded .page-content-wrapper {
  padding: 8px 10px !important;
}
</style>
