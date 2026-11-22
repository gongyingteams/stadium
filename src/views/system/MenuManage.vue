<template>
  <div class="menu-manage-container">
    <!-- 1. 顶部操作与标题面板 -->
    <div class="setting-header-panel glass-panel">
      <div class="header-left-meta">
        <div class="header-icon-box">
          <SvgIcon name="SvgMenuList" size="24" />
        </div>
        <div class="header-title-group">
          <div class="title-row">
            <h1 class="page-title">导航菜单配置中心</h1>
            <span class="setting-badge">MENU CONFIG</span>
            <span v-if="!remoteSynced" class="sync-badge offline">离线模式 · 配置未同步</span>
            <span v-else class="sync-badge online">已与后端同步</span>
          </div>
          <p class="page-desc">
            统一维护左侧菜单的「分组」与「菜单项」：文字描述、短标题、链接与显隐开关；同一页面仅允许一个菜单入口指向。保存后侧边栏即时生效，仅总管理员可写。
          </p>
        </div>
      </div>

      <div class="header-action-group">
        <button class="btn-header-action btn-header-neutral" @click="addGroup" title="在末尾新增一个菜单分组">
          <SvgIcon name="SvgAppGrid" size="14" style="margin-right: 4px;" />
          <span>新增分组</span>
        </button>
        <button
          class="btn-header-action btn-header-danger"
          :disabled="isSaving"
          @click="confirmReset"
          title="清空当前配置并恢复出厂默认菜单"
        >
          <el-icon><RefreshRight /></el-icon>
          <span>恢复默认菜单</span>
        </button>
        <button
          class="btn-header-action btn-header-primary"
          :disabled="!isDirty || isSaving"
          @click="saveAll"
          title="提交完整菜单树并即时刷新侧边栏"
        >
          <el-icon><Check /></el-icon>
          <span>{{ isSaving ? '正在保存中...' : (isDirty ? '保存全部改动' : '无未保存改动') }}</span>
        </button>
      </div>
    </div>

    <!-- 1.5 配置说明 (可折叠): 告诉用户哪里是分组 / 哪里是菜单项 / 开关与链接怎么用 -->
    <div class="glass-panel guide-panel">
      <div class="guide-head" @click="toggleGuide">
        <div class="guide-title">
          <el-icon class="guide-icon"><InfoFilled /></el-icon>
          <span class="guide-title-text">配置说明</span>
          <span class="guide-sub">哪里是分组 · 哪里是左侧菜单项 · 开关与链接怎么用</span>
        </div>
        <span class="guide-toggle">{{ guideOpen ? '收起 ▲' : '展开 ▼' }}</span>
      </div>
      <div v-show="guideOpen" class="guide-body">
        <div class="guide-card">
          <div class="guide-line">
            <span class="guide-k"><SvgIcon name="SvgAppGrid" size="14" /> 分组 = 每张卡片</span>
            <span class="guide-v">对应左侧菜单的一个分区；「显示」开关控制整组显隐，删除分组会连带删除组内全部菜单项。</span>
          </div>
          <div class="guide-line">
            <span class="guide-k"><SvgIcon name="SvgMenuList" size="14" /> 菜单项 = 每一行</span>
            <span class="guide-v">左侧菜单中可点击的入口；「完整标题」= 悬停时的文字描述，「短标题」= 侧边栏显示文字（建议 2–4 字），「链接」= 点击打开的页面。</span>
          </div>
          <div class="guide-line">
            <span class="guide-k"><SvgIcon name="SvgPower" size="14" /> 显隐开关</span>
            <span class="guide-v">分组开关 = 整组显隐，菜单项开关 = 单项显隐；隐藏不丢配置可随时重开（虚线低透明度 = 已隐藏，方便找回）。</span>
          </div>
          <div class="guide-line guide-line-warn">
            <span class="guide-k"><SvgIcon name="SvgSecurityShield" size="14" /> 链接唯一</span>
            <span class="guide-v">同一页面（含外链）只能由一个菜单项指向；冲突行会标红「⚠ 链接重复」，需修改后才能保存。</span>
          </div>
          <div class="guide-line">
            <span class="guide-k"><SvgIcon name="SvgUserRole" size="14" /> 角色与角标</span>
            <span class="guide-v">「管理」= 仅总管理员可见；「运维」= 仅运维及以上可见；「角标」= 侧边栏该项的设备数量徽标。</span>
          </div>
          <div class="guide-line">
            <span class="guide-k"><SvgIcon name="SvgDynamicDevice" size="14" /> 外链与动态路径</span>
            <span class="guide-v">下拉选择已注册页面，或手填外链（http/https，新标签页打开）、动态路径（如 /iot/dynamic/group-01）。</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 非 admin 兜底拦截 (路由守卫已拦截, 此为双保险) -->
    <div v-if="!userStore.isAdmin" class="glass-panel no-perm-card">
      <SvgIcon name="SvgSecurityShield" size="40" class="no-perm-icon" />
      <h2 class="no-perm-title">无权访问</h2>
      <p class="no-perm-desc">导航菜单配置仅总管理员 (admin) 可用，您的当前角色无此权限。</p>
    </div>

    <!-- 2. 主体: 菜单分组卡片列表 -->
    <div v-else class="menu-group-list">
      <div
        v-for="(group, gi) in draft.groups"
        :key="gi"
        class="menu-group-card glass-panel"
        :class="{ 'group-hidden': !group.visible }"
      >
        <!-- 分组卡片头: 标题 / 显隐 / 排序 / 增删 -->
        <div class="group-card-head">
          <div class="group-title-zone">
            <SvgIcon :name="group.icon || 'SvgAppGrid'" size="18" class="group-icon" />
            <span class="group-index num-mono">{{ gi + 1 }}</span>
            <span class="group-kind-tag">分组</span>
            <el-input
              v-model="group.title"
              size="default"
              maxlength="32"
              class="group-title-input"
              :placeholder="`分组标题 (第 ${gi + 1} 组)`"
            />
            <el-input
              v-model="group.menuKey"
              size="default"
              class="group-key-input"
              placeholder="分组标识 (留空自动生成)"
            />
          </div>
          <div class="group-ops">
            <span class="switch-zone" title="开关用途：控制整个分组是否显示在左侧菜单中，关闭后配置不丢失">
              <span class="switch-label">显示</span>
              <el-switch v-model="group.visible" />
            </span>
            <el-button
              size="small"
              link
              :disabled="gi === 0"
              @click="moveGroup(gi, -1)"
              title="上移分组"
            >↑ 上移</el-button>
            <el-button
              size="small"
              link
              :disabled="gi === draft.groups.length - 1"
              @click="moveGroup(gi, 1)"
              title="下移分组"
            >↓ 下移</el-button>
            <el-button size="small" type="primary" link @click="addItem(gi)">+ 新增菜单项</el-button>
            <el-button size="small" type="danger" link @click="confirmRemoveGroup(gi)">删除分组</el-button>
          </div>
        </div>

        <!-- 菜单项行列表 (含已隐藏项, 方便重新开启) -->
        <div class="menu-item-list">
          <!-- 列头: 说明每一列是什么 -->
          <div v-if="group.children.length" class="item-row-head">
            <span class="col-icon">图标</span>
            <span class="col-title">完整标题（文字描述）</span>
            <span class="col-short">短标题</span>
            <span class="col-path">页面链接</span>
            <span class="col-flags">标记</span>
            <span class="col-ops">显示与操作</span>
          </div>
          <div
            v-for="(item, ii) in group.children"
            :key="ii"
            class="menu-item-row"
            :class="{ 'item-hidden': !item.visible, 'has-dup': isDuplicateItem(item) }"
          >
            <div class="item-icon-cell" title="点击更换图标" @click="openIconPicker(item)">
              <SvgIcon :name="item.icon || 'SvgPortal'" size="18" />
            </div>

            <el-input
              v-model="item.title"
              size="small"
              maxlength="32"
              class="cell-title"
              :title="item.title"
              placeholder="完整标题（悬停描述）"
            />
            <el-input
              v-model="item.shortTitle"
              size="small"
              maxlength="12"
              class="cell-short-title"
              :title="`侧边栏中实际显示的文字：${item.shortTitle}`"
              placeholder="短标题（侧边栏显示）"
            />
            <el-select
              v-model="item.path"
              size="small"
              filterable
              allow-create
              default-first-option
              :reserve-keyword="false"
              class="cell-path"
              :class="{ 'is-duplicate': isDuplicateItem(item) }"
              :title="isDuplicateItem(item)
                ? `链接重复：该页面已被其他菜单项占用（${dupRivalTitle(item)}），同一页面只能由一个菜单入口指向`
                : '点击后打开的页面，可从下拉选择已注册页面，也可手填外链或动态路径'"
              placeholder="选择已注册页面, 或手填外链/动态路径"
            >
              <el-option
                v-for="opt in routeLinkOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>

            <div class="item-flags">
              <span v-if="isDuplicateItem(item)" class="flag-tag flag-dup" title="该链接已被其他菜单项占用，请修改此项链接或删除重复项">⚠ 链接重复</span>
              <span v-if="item.requiresAdmin" class="flag-tag flag-admin">管理</span>
              <span v-if="item.requiresOps" class="flag-tag flag-ops">运维</span>
              <span v-if="item.badgeType" class="flag-tag flag-badge">角标:{{ item.badgeType }}</span>
            </div>

            <div class="item-ops">
              <span class="switch-zone" title="开关用途：控制该菜单项是否显示在左侧菜单中，关闭后配置不丢失">
                <span class="switch-label">显示</span>
                <el-switch v-model="item.visible" />
              </span>
              <el-button size="small" link :disabled="ii === 0" @click="moveItem(gi, ii, -1)" title="上移">↑</el-button>
              <el-button size="small" link :disabled="ii === group.children.length - 1" @click="moveItem(gi, ii, 1)" title="下移">↓</el-button>
              <el-button size="small" type="danger" link @click="removeItem(gi, ii)">删除</el-button>
            </div>
          </div>
          <div v-if="!group.children.length" class="empty-group-tip">
            暂无菜单项，点击卡片头「+ 新增菜单项」添加。
          </div>
        </div>
      </div>

      <div v-if="!draft.groups.length" class="glass-panel empty-tree-tip">
        菜单树为空（全部分组被删除）。可点击右上角【新增分组】重建，或【恢复默认菜单】还原。
      </div>
    </div>

    <!-- 3. 图标选择弹窗 (选项来自 SvgIcon 已注册图标) -->
    <el-dialog
      v-model="iconPickerVisible"
      title="选择菜单图标"
      width="640px"
      append-to-body
    >
      <div class="icon-grid">
        <div
          v-for="name in ICON_OPTIONS"
          :key="name"
          :class="['icon-chip', { active: pickingItem && pickingItem.icon === name }]"
          @click="pickIcon(name)"
        >
          <SvgIcon :name="name" size="20" />
          <span class="icon-chip-name num-mono">{{ name.replace('Svg', '') }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useMenuStore } from '@/stores/menu'
import { menuConfigService } from '@/services/menuConfigService'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, RefreshRight, InfoFilled } from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'

const userStore = useUserStore()
const menuStore = useMenuStore()
const router = useRouter()

// SvgIcon 已注册的全部图标名 (图标选择弹窗数据源)
const ICON_OPTIONS = [
  'SvgDashboard', 'SvgPortal', 'SvgCompassNav', 'SvgAppGrid', 'SvgIframeApp',
  'SvgIotControl', 'SvgSoundMatrix', 'SvgLighting', 'SvgLedScreen', 'SvgMatchScore',
  'SvgFlagSystem', 'SvgMasterClock', 'SvgCameraMatrix', 'SvgMediaPlayer', 'SvgDynamicDevice',
  'SvgLowCodeConfig', 'SvgDeviceSetting', 'SvgButtonAction', 'SvgAdapterBook', 'SvgMediaLibrary',
  'SvgConfigTemplate', 'SvgMockSandbox', 'SvgMenuList',
  'SvgSecurityShield', 'SvgAlarmBell', 'SvgNotifyChannel', 'SvgAuditLog', 'SvgUserRole', 'SvgTablet',
  'SvgMicrophone', 'SvgSpeaker', 'SvgMusicNote', 'SvgTrophy', 'SvgWhistle', 'SvgStopwatch',
  'SvgSwimmingPool', 'SvgHdHdmi', 'SvgSdiVideo', 'SvgPtzCamera', 'SvgFiberNet', 'SvgSerialPort',
  'SvgTicketGate', 'SvgAirCondition', 'SvgFireFighting', 'SvgAccessDoor', 'SvgParkingCar',
  'SvgElevatorCar', 'SvgEnergyMeter', 'SvgEmergencyHalt', 'SvgTerminalHex', 'SvgSignalWifi',
  'SvgActivity', 'SvgCpu', 'SvgHardDrive', 'SvgSliders', 'SvgMaximize', 'SvgPower',
  'SvgRefresh', 'SvgSearch', 'SvgSettingGear'
]

// 本地编辑副本: 所有编辑只作用于 draft, 保存时整树提交
const draft = ref({ groups: [] })
const isSaving = ref(false)
const iconPickerVisible = ref(false)
const pickingItem = ref(null)

// 配置说明面板展开状态 (记忆用户选择, 默认展开引导新用户)
const GUIDE_KEY = 'ibms_menu_guide_open_v1'
const guideOpen = ref((typeof localStorage !== 'undefined' && localStorage.getItem(GUIDE_KEY)) !== '0')
const toggleGuide = () => {
  guideOpen.value = !guideOpen.value
  try { localStorage.setItem(GUIDE_KEY, guideOpen.value ? '1' : '0') } catch { /* ignore */ }
}

const cloneTree = (groups) => JSON.parse(JSON.stringify(groups || []))

const syncDraft = () => {
  draft.value = { groups: cloneTree(menuStore.groups) }
}

const remoteSynced = computed(() => menuStore.remoteSynced)

// 脏检查: draft 与 store 原始树 (未过滤的完整数据) 的 JSON 差异
const isDirty = computed(() => {
  return JSON.stringify(draft.value.groups) !== JSON.stringify(menuStore.groups)
})

// 链接下拉选项: 来自 router 已注册路由, 排除公开/重定向/动态参数/平板路由
const routeLinkOptions = computed(() => {
  return router.options.routes
    .filter(r => {
      if (!r.path) return false
      if (r.meta?.public) return false
      if (r.path === '/' || r.path.includes(':')) return false
      if (r.path.startsWith('/tablet')) return false
      return true
    })
    .map(r => ({
      value: r.path,
      label: `${r.meta?.shortTitle || r.meta?.title || r.path} · ${r.path}`
    }))
})

// 链接规范化: 去首尾空白 + 去结尾斜杠 ("/iot/audio/" 与 "/iot/audio" 视为同一页面)
const normPath = (p) => {
  const n = String(p || '').trim().replace(/\/+$/, '')
  return n || '/'
}

// 链接重复检测: 同一页面(含外链)禁止两个及以上菜单项同时指向, 避免左侧菜单出现重复入口
const duplicateGroups = computed(() => {
  const map = new Map()
  for (const g of draft.value.groups) {
    for (const c of g.children) {
      if (!String(c.path || '').trim()) continue // 空链接另由"链接不能为空"规则拦截, 不参与重复判断
      const n = normPath(c.path)
      if (!map.has(n)) map.set(n, [])
      map.get(n).push(c)
    }
  }
  return Array.from(map.values()).filter(arr => arr.length > 1)
})

const duplicatePathSet = computed(() => new Set(duplicateGroups.value.map(arr => normPath(arr[0].path))))
const isDuplicateItem = (item) => duplicatePathSet.value.has(normPath(item.path))

// 同一链接的其他占用者标题 (用于行内悬停提示)
const dupRivalTitle = (item) => {
  const n = normPath(item.path)
  const rivals = []
  for (const g of draft.value.groups) {
    for (const c of g.children) {
      if (c !== item && normPath(c.path) === n) {
        rivals.push(String(c.title || c.shortTitle || c.path).trim() || '未命名')
      }
    }
  }
  return rivals.join('、') || '其他菜单项'
}

// ---- 分组操作 ----
const moveGroup = (gi, delta) => {
  const nj = gi + delta
  const arr = draft.value.groups
  if (nj < 0 || nj >= arr.length) return
  const [moved] = arr.splice(gi, 1)
  arr.splice(nj, 0, moved)
}

const addGroup = () => {
  draft.value.groups.push({
    menuKey: '',
    title: `${draft.value.groups.length + 1}. 新分组`,
    icon: 'SvgAppGrid',
    visible: true,
    children: []
  })
  ElMessage.success('已新增分组（记得保存全部改动）')
}

const confirmRemoveGroup = (gi) => {
  const group = draft.value.groups[gi]
  ElMessageBox.confirm(
    `将同时删除组内 ${group.children.length} 个菜单项，确定删除分组「${group.title}」？`,
    '删除分组',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  ).then(() => {
    draft.value.groups.splice(gi, 1)
    ElMessage.success('分组已删除（记得保存全部改动）')
  }).catch(() => {})
}

// ---- 菜单项操作 ----
const moveItem = (gi, ii, delta) => {
  const children = draft.value.groups[gi].children
  const nj = ii + delta
  if (nj < 0 || nj >= children.length) return
  const [moved] = children.splice(ii, 1)
  children.splice(nj, 0, moved)
}

const addItem = (gi) => {
  // 默认链接: 优先取尚未被任何菜单项占用的已注册页面, 避免新增项立即构成重复配置
  const used = new Set(draft.value.groups.flatMap(g => g.children.map(c => normPath(c.path))))
  const defaultPath = routeLinkOptions.value.find(o => !used.has(normPath(o.value)))?.value || ''
  draft.value.groups[gi].children.push({
    menuKey: '',
    title: '新菜单项',
    shortTitle: '新菜单',
    path: defaultPath,
    icon: 'SvgPortal',
    visible: true,
    requiresAdmin: false,
    requiresOps: false,
    badgeType: ''
  })
  ElMessage.success('已新增菜单项（记得保存全部改动）')
}

const removeItem = (gi, ii) => {
  const item = draft.value.groups[gi].children[ii]
  ElMessageBox.confirm(
    `确定删除菜单项「${item.title || item.shortTitle}」？`,
    '删除菜单项',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  ).then(() => {
    draft.value.groups[gi].children.splice(ii, 1)
    ElMessage.success('菜单项已删除（记得保存全部改动）')
  }).catch(() => {})
}

// ---- 图标选择 ----
const openIconPicker = (item) => {
  pickingItem.value = item
  iconPickerVisible.value = true
}

const pickIcon = (name) => {
  if (pickingItem.value) {
    pickingItem.value.icon = name
  }
  iconPickerVisible.value = false
}

// ---- 本地防呆校验 (与后端 400 规则一致, 提前给出友好提示) ----
const validateDraft = () => {
  if (!draft.value.groups.length) {
    return '菜单树不能为空'
  }
  if (!draft.value.groups.some(g => g.visible)) {
    return '至少保留 1 个可见分组, 不能把全部分组隐藏'
  }
  for (const g of draft.value.groups) {
    if (!String(g.title || '').trim()) {
      return '存在标题为空的分组'
    }
    for (const c of g.children) {
      if (!String(c.title || '').trim()) {
        return '存在标题为空的菜单项'
      }
      if (!String(c.path || '').trim()) {
        return `菜单项「${String(c.title).trim()}」的链接不能为空`
      }
    }
  }
  // 链接唯一性: 同一页面禁止两个及以上菜单同时指向 (与后端 PUT /api/menu/config 规则一致)
  const dups = duplicateGroups.value
  if (dups.length) {
    const first = dups[0]
    const names = first.map(c => `「${String(c.title).trim() || String(c.shortTitle).trim() || c.path}」`).join(' 与 ')
    return `链接重复: ${names} 等 ${first.length} 个菜单项同时指向页面 ${normPath(first[0].path)}; 同一页面只能由一个菜单入口指向, 请修改或删除重复项`
  }
  return null
}

// ---- 保存 (整树提交 -> store 刷新 -> 侧边栏即时生效) ----
const saveAll = async () => {
  const err = validateDraft()
  if (err) {
    ElMessage.warning(err)
    return
  }
  isSaving.value = true
  try {
    const result = await menuConfigService.saveMenuTree({ groups: draft.value.groups })
    if (result && result.remoteSaved) {
      ElMessage.success('导航菜单配置已保存并即时生效')
    } else {
      ElMessage.warning('后端不可达，配置仅保存于本机浏览器缓存')
    }
    // 拉取后端回显树 (含服务端自动补全的 id/menuKey), 同步 draft 与侧边栏
    await menuStore.load(true)
    syncDraft()
  } catch (err) {
    ElMessage.error(err?.message || '保存失败, 请稍后重试')
  } finally {
    isSaving.value = false
  }
}

// ---- 恢复默认 ----
const confirmReset = () => {
  ElMessageBox.confirm(
    '将清空当前全部菜单改动并恢复为出厂默认菜单, 确定继续?',
    '恢复默认菜单',
    { type: 'warning', confirmButtonText: '恢复默认', cancelButtonText: '取消' }
  ).then(async () => {
    isSaving.value = true
    try {
      const result = await menuConfigService.resetMenuTree()
      await menuStore.load(true)
      syncDraft()
      if (result && result.remoteSaved) {
        ElMessage.success('已恢复为出厂默认菜单')
      } else {
        ElMessage.warning('后端不可达, 已在本机恢复默认菜单')
      }
    } catch (err) {
      ElMessage.error(err?.message || '恢复默认失败, 请稍后重试')
    } finally {
      isSaving.value = false
    }
  }).catch(() => {})
}

// ---- 离开拦截: 未保存改动二次确认 ----
const confirmDiscard = async () => {
  try {
    await ElMessageBox.confirm(
      '有未保存的菜单改动, 确定离开?',
      '未保存的改动',
      { type: 'warning', confirmButtonText: '离开', cancelButtonText: '继续编辑' }
    )
    return true
  } catch {
    return false
  }
}

onBeforeRouteLeave(async (to, from, next) => {
  if (!isDirty.value) {
    next()
    return
  }
  next(await confirmDiscard())
})

const onBeforeUnload = (e) => {
  if (isDirty.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(async () => {
  window.addEventListener('beforeunload', onBeforeUnload)
  try {
    await menuStore.load(true)
  } catch (err) {
    console.warn('MenuManage: menuStore.load error', err)
  }
  syncDraft()
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
})
</script>

<style scoped>
.menu-manage-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  padding: 16px 20px 28px;
}

/* 顶部操作与标题面板 (沿用 SystemSetting 视觉规范) */
.setting-header-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  gap: 16px;
  flex-wrap: wrap;
}

.header-left-meta {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 0;
  letter-spacing: 0.2px;
}

.setting-badge {
  font-size: 13px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 4px;
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  font-family: var(--font-family-mono);
}

.sync-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
}

.sync-badge.online {
  background: rgba(52, 168, 83, 0.14);
  color: #2e8b57;
}

.sync-badge.offline {
  background: rgba(245, 158, 11, 0.16);
  color: var(--do-warning-deep);
}

.page-desc {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin: 4px 0 0 0;
}

.header-action-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 分组卡片列表 */
.menu-group-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.menu-group-card {
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.03) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: border-color 0.22s ease, opacity 0.22s ease;
}

.menu-group-card.group-hidden {
  opacity: 0.62;
  border-style: dashed;
}

.group-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.14);
  background: rgba(var(--th-accent-rgb), 0.035);
  flex-wrap: wrap;
}

.group-title-zone {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 260px;
}

.group-icon {
  color: var(--do-gold-deep);
  flex-shrink: 0;
}

.group-index {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.1);
  border-radius: 4px;
  padding: 1px 7px;
  flex-shrink: 0;
}

/* 卡片层级标识: 告诉用户这张卡片是一个"分组" */
.group-kind-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
  background: rgba(var(--th-accent-rgb), 0.08);
  color: var(--do-text-secondary);
}

.group-title-input {
  flex: 1;
  min-width: 160px;
}

.group-key-input {
  width: 170px;
  flex-shrink: 0;
}

.group-ops {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.switch-label {
  font-size: 13px;
  color: var(--do-text-secondary);
}

/* 开关与其文字标签组合, 悬停显示用途说明 */
.switch-zone {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: default;
}

/* 菜单项行 */
.menu-item-list {
  padding: 10px 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 列头: 与菜单项行列宽一致, 用文字标明每列含义 */
.item-row-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 10px 2px;
  font-size: 12px;
  font-weight: 600;
  color: var(--do-text-secondary);
  user-select: none;
}

.item-row-head .col-icon { width: 34px; flex-shrink: 0; text-align: center; }
.item-row-head .col-title { width: 220px; flex-shrink: 0; }
.item-row-head .col-short { width: 116px; flex-shrink: 0; }
.item-row-head .col-path { flex: 1 1 auto; min-width: 200px; max-width: 560px; }
.item-row-head .col-flags { width: 120px; flex-shrink: 0; }
.item-row-head .col-ops { flex-shrink: 0; margin-left: auto; }

.menu-item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.14);
  border-radius: var(--radius-sm);
  background: var(--do-bg-card);
  transition: opacity 0.2s ease;
}

/* 列宽: 图标 / 完整标题(文字描述, 固定宽+失焦省略) / 短标题 / 链接(弹性) / 标记 / 操作(右对齐) */
.menu-item-row .item-icon-cell { flex-shrink: 0; }
.menu-item-row .cell-title { width: 220px; flex-shrink: 0; }
.menu-item-row .cell-short-title { width: 116px; flex-shrink: 0; }
.menu-item-row .cell-path { flex: 1 1 auto; min-width: 200px; max-width: 560px; }
.menu-item-row .item-ops { flex-shrink: 0; margin-left: auto; }

/* 链接重复行: 整行淡红警示 */
.menu-item-row.has-dup {
  border-color: rgba(239, 68, 68, 0.45);
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.06), var(--do-bg-card) 35%);
}

.cell-path.is-duplicate :deep(.el-select__wrapper) {
  border-color: var(--do-danger, #ef4444) !important;
  background-color: rgba(239, 68, 68, 0.05);
}

.menu-item-row.item-hidden {
  opacity: 0.6;
  border-style: dashed;
}

.item-icon-cell {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--do-gold-deep);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.item-icon-cell:hover {
  border-color: var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.08);
}

.cell-title :deep(.el-input__wrapper),
.cell-short-title :deep(.el-input__wrapper),
.cell-path :deep(.el-select__wrapper) {
  box-shadow: none;
  border: 1px solid rgba(var(--th-accent-rgb), 0.18);
}

/* 完整标题(文字描述): 固定宽度, 失焦时超长文字省略为 "...", 聚焦时恢复滚动可编辑 (Chromium/WebKit/Firefox 均支持) */
.cell-title :deep(.el-input__inner) {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item-flags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.flag-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.flag-dup {
  background: rgba(239, 68, 68, 0.14);
  color: var(--do-danger-deep, #b91c1c);
}

.flag-admin {
  background: rgba(59, 130, 246, 0.14);
  color: #2563eb;
}

.flag-ops {
  background: rgba(139, 92, 246, 0.14);
  color: #7c3aed;
}

.flag-badge {
  background: rgba(20, 184, 166, 0.14);
  color: #0d9488;
}

.item-ops {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.empty-group-tip,
.empty-tree-tip {
  padding: 18px;
  text-align: center;
  font-size: 13px;
  color: var(--do-text-secondary);
  border-radius: var(--radius-md);
}

/* 非 admin 兜底卡片 */
.no-perm-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 60px 24px;
  text-align: center;
}

.no-perm-icon {
  color: var(--do-warning);
}

.no-perm-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 0;
}

.no-perm-desc {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin: 0;
}

/* 图标选择弹窗 */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 10px;
  max-height: 460px;
  overflow-y: auto;
  padding: 4px;
}

.icon-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 6px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.16);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--do-text-regular);
  transition: border-color 0.18s ease, background 0.18s ease;
}

.icon-chip:hover {
  border-color: var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.06);
}

.icon-chip.active {
  border-color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.icon-chip-name {
  font-size: 11px;
  word-break: break-all;
  text-align: center;
}

@media (max-width: 1200px) {
  /* 窄屏隐藏列头, 行内字段自然换行 */
  .item-row-head {
    display: none;
  }

  .menu-item-row {
    flex-wrap: wrap;
  }

  .menu-item-row .cell-title {
    flex: 1 1 180px;
    width: auto;
  }

  .menu-item-row .cell-short-title {
    flex: 1 1 110px;
    width: auto;
  }

  .menu-item-row .cell-path {
    order: 4;
    flex: 1 1 100%;
    max-width: none;
  }

  .item-flags,
  .item-ops {
    order: 5;
  }
}

/* ============ 配置说明面板 ============ */
.guide-panel {
  overflow: hidden;
}

.guide-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  cursor: pointer;
  user-select: none;
  transition: background 0.18s ease;
}

.guide-head:hover {
  background: rgba(var(--th-accent-rgb), 0.05);
}

.guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.guide-icon {
  color: var(--do-gold-deep);
  font-size: 17px;
  flex-shrink: 0;
}

.guide-title-text {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
  white-space: nowrap;
}

.guide-sub {
  font-size: 13px;
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.guide-toggle {
  font-size: 13px;
  font-weight: 600;
  color: var(--do-gold-deep);
  white-space: nowrap;
  flex-shrink: 0;
}

.guide-body {
  padding: 8px 18px 12px;
  border-top: 1px dashed rgba(var(--th-accent-rgb), 0.18);
}

/* 单卡片多行: 每行一个主题, 左侧主题标签 + 右侧一行说明 */
.guide-card {
  border: 1px solid rgba(var(--th-accent-rgb), 0.14);
  border-radius: var(--radius-sm);
  background: rgba(var(--th-accent-rgb), 0.03);
  padding: 2px 14px;
}

.guide-line {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  padding: 6px 0;
  border-bottom: 1px dashed rgba(var(--th-accent-rgb), 0.1);
}

.guide-line:last-child {
  border-bottom: none;
}

.guide-k {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  width: 148px;
  font-size: 13px;
  font-weight: 700;
  color: var(--do-text-primary);
  white-space: nowrap;
}

.guide-line-warn .guide-k {
  color: var(--do-danger-deep, #b91c1c);
}

.guide-v {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--do-text-secondary);
}
</style>
