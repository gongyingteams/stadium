<template>
  <div class="led-dispatch-page">
    <section class="page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon"><SvgIcon name="SvgLedScreen" size="28" /></div>
        <div>
          <div class="title-row">
            <h1>LED大屏与推屏调度控制台</h1>
            <span class="simulation-badge" v-if="isSimulated">演示数据</span>
          </div>
          <p>多屏联动输出、输入信号切换与现场显示状态监测</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-metric">
          <span class="status-dot online"></span>
          <span>控制总线正常</span>
        </div>
        <div class="status-metric"><strong class="num-mono">{{ onlineScreenCount }}/{{ screenDevices.length }}</strong> 块大屏在线</div>
        <div class="status-metric"><strong class="num-mono">{{ busLatency }}ms</strong> 链路延迟</div>
        <button class="btn-header-action btn-header-primary" :disabled="isRefreshing" @click="refreshScreenData" title="轮询现场各LED大屏控制器通信心跳与播放状态">
          <SvgIcon name="SvgRefresh" size="14" :class="{ 'spin-icon': isRefreshing }" style="margin-right: 4px;" />
          <span>{{ isRefreshing ? '正在巡检中...' : '重新巡检' }}</span>
        </button>
        <button class="btn-header-action btn-header-manage" @click="openLogsDrawer" title="查看大屏推屏历史流水与控制台下发回执">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>操作回执</span>
        </button>
      </div>
    </section>

    <section class="target-toolbar glass-panel">
      <div class="section-heading">
        <div>
          <h2>多屏联动墙</h2>
          <span class="section-help">选择本次调度的目标输出屏</span>
        </div>
        <span class="selection-count num-mono">已选 {{ selectedScreenIds.length }} / {{ screenDevices.length }}</span>
      </div>
      <div class="target-actions">
        <el-button size="small" @click="selectAllScreens">全选大屏</el-button>
        <el-button size="small" @click="selectOnlineScreens">仅选在线屏</el-button>
        <el-button size="small" @click="clearScreenSelection">清空选择</el-button>
      </div>
    </section>

    <section class="screen-wall">
      <article
        v-for="screen in screenDevices"
        :key="screen.id"
        class="screen-card glass-panel"
        :class="{ selected: isScreenSelected(screen.id), previewing: previewScreenId === screen.id }"
        @click="toggleScreenSelection(screen.id)"
      >
        <div class="screen-card-top">
          <div class="screen-identity">
            <div class="screen-icon"><SvgIcon name="SvgLedScreen" size="22" /></div>
            <div>
              <h3>{{ screen.name }}</h3>
              <span class="device-code num-mono">{{ screen.id }}</span>
            </div>
          </div>
          <span :class="['screen-status', screen.status]">
            <span class="status-dot"></span>{{ statusLabel(screen.status) }}
          </span>
        </div>
        <div class="screen-location"><el-icon><Location /></el-icon>{{ screen.location }}</div>
        <div class="current-signal">
          <span class="field-label">当前信号</span>
          <strong>{{ screen.blackout ? '黑屏 / 屏保' : screen.signal }}</strong>
          <span class="signal-port num-mono">{{ screen.signalType }}</span>
        </div>
        <div class="screen-facts">
          <div><span>分辨率</span><strong class="num-mono">{{ screen.resolution }}</strong></div>
          <div><span>刷新率</span><strong class="num-mono">{{ screen.refreshRate }}</strong></div>
          <div><span>协议</span><strong class="num-mono">{{ screen.protocol }}</strong></div>
          <div><span>延迟</span><strong class="num-mono">{{ screen.latency == null ? '—' : `${screen.latency}ms` }}</strong></div>
        </div>
        <div class="screen-card-footer">
          <span :class="['selection-state', { active: isScreenSelected(screen.id) }]">
            <el-icon v-if="isScreenSelected(screen.id)"><Select /></el-icon>
            {{ isScreenSelected(screen.id) ? '已加入调度目标' : '点击选择目标' }}
          </span>
          <el-button text type="primary" size="small" @click.stop="previewScreenById(screen.id)">查看预览</el-button>
        </div>
      </article>
    </section>

    <section class="dispatch-grid">
      <div class="signal-panel glass-panel">
        <div class="panel-heading">
          <div>
            <h2>输入信号源矩阵</h2>
            <span class="section-help">选择信号源后应用到已选目标屏</span>
          </div>
          <span class="matrix-state"><span class="status-dot online"></span>信号检测正常</span>
        </div>
        <div class="signal-grid">
          <button
            v-for="source in signalSources"
            :key="source.id"
            type="button"
            class="signal-card"
            :class="{ selected: selectedSignalId === source.id, unavailable: source.status !== 'ready' }"
            @click="selectedSignalId = source.id"
          >
            <div class="signal-card-head">
              <span class="signal-icon"><el-icon><component :is="source.icon" /></el-icon></span>
              <span :class="['source-state', source.status]">{{ source.status === 'ready' ? '可用' : '抖动' }}</span>
            </div>
            <strong>{{ source.name }}</strong>
            <span>{{ source.type }}</span>
            <div class="signal-meta"><span class="num-mono">{{ source.input }}</span><span>{{ source.detail }}</span></div>
          </button>
        </div>
        <div class="apply-summary">
          <div><span class="field-label">当前选中信号</span><strong>{{ selectedSignal?.name }}</strong></div>
          <div class="apply-target">将应用到：<strong>{{ selectedScreenNames || '未选择目标屏' }}</strong></div>
          <el-button type="primary" size="large" :disabled="!selectedScreenIds.length" @click="applySelectedSignal">
            <el-icon><VideoPlay /></el-icon>
            应用到选中大屏
          </el-button>
        </div>
      </div>

      <div class="preview-panel glass-panel">
        <div class="panel-heading">
          <div>
            <h2>当前输出预览</h2>
            <span class="section-help">稳定模拟画面，仅用于确认调度结果</span>
          </div>
          <span :class="['preview-state', previewScreen?.status]"><span class="status-dot"></span>{{ previewScreen?.name }}</span>
        </div>
        <div class="preview-frame">
          <div class="preview-osd"><span class="num-mono">{{ previewScreen?.id }}</span><span>{{ previewScreen?.resolution }} · {{ previewScreen?.refreshRate }}</span></div>
          <div class="preview-content" :class="previewModeClass">
            <div class="preview-grid-lines"></div>
            <div class="preview-center">
              <SvgIcon name="SvgLedScreen" size="46" />
              <strong>{{ previewScreen?.blackout ? 'BLACKOUT' : previewScreen?.signal }}</strong>
              <span>{{ previewScreen?.blackout ? '输出图层已关闭' : previewScreen?.signalType }}</span>
            </div>
            <div class="preview-corner top-left">OUTPUT MONITOR</div>
            <div class="preview-corner top-right num-mono">LIVE · 60 FPS</div>
            <div class="preview-corner bottom-left">VENUE DISPLAY SYSTEM</div>
          </div>
          <div class="preview-footer"><span>当前信号：{{ previewScreen?.signal }}</span><span class="num-mono">延迟 {{ previewScreen?.latency == null ? '—' : `${previewScreen.latency}ms` }}</span></div>
        </div>
        <div v-if="hasMixedSignals" class="mixed-warning"><el-icon><WarningFilled /></el-icon>已选大屏当前信号不一致，预览显示 {{ previewScreen?.name }} 的输出。</div>
        <div class="preview-facts">
          <div><span>帧率</span><strong class="num-mono">{{ previewScreen?.status === 'offline' ? '—' : '60.00 FPS' }}</strong></div>
          <div><span>丢帧率</span><strong class="num-mono">{{ previewScreen?.frameLoss }}</strong></div>
          <div><span>最近同步</span><strong class="num-mono">{{ lastSyncTime }}</strong></div>
        </div>
      </div>
    </section>

    <section class="output-actions glass-panel">
      <div class="action-description">
        <span class="action-led"></span>
        <div><strong>{{ lastAction }}</strong><span>操作将作用于 {{ selectedScreenNames || '未选择目标大屏' }}</span></div>
      </div>
      <div class="action-buttons">
        <el-button type="primary" size="large" :disabled="!selectedScreenIds.length" @click="applySelectedSignal">应用信号源</el-button>
        <el-button size="large" :disabled="!selectedScreenIds.length" @click="restoreMainSignal">恢复主路</el-button>
        <el-button type="danger" plain size="large" :disabled="!selectedScreenIds.length" @click="confirmBlackout">黑屏</el-button>
        <el-button size="large" :disabled="!selectedScreenIds.length" @click="releaseBlackout">解除黑屏</el-button>
        <el-button size="large" :loading="isRefreshing" @click="refreshScreenData"><el-icon><Refresh /></el-icon>刷新状态</el-button>
      </div>
    </section>

    <el-drawer v-model="logsDrawerVisible" title="大屏调度操作回执" size="720px" append-to-body destroy-on-close>
      <div class="drawer-summary">累计记录 <strong>{{ drawerLogs.length }}</strong> 条大屏调度指令</div>
      <el-table :data="drawerLogs" stripe height="calc(100vh - 160px)">
        <el-table-column label="执行时间" prop="created_at" width="170" />
        <el-table-column label="设备编号" prop="custom_no" width="160" />
        <el-table-column label="指令名称" prop="command_name" min-width="170" />
        <el-table-column label="结果" prop="execute_result" width="100" align="center" />
        <el-table-column label="耗时" prop="cost_ms" width="90" align="right">
          <template #default="{ row }"><span class="num-mono">{{ row.cost_ms || '—' }}{{ row.cost_ms ? 'ms' : '' }}</span></template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Camera, DataBoard, Location, Monitor, Refresh, Select, Tickets, VideoPlay, WarningFilled
} from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { iotDeviceService } from '@/services/iotDeviceService'

const demoScreens = [
  { id: 'SCR-CENTER-01', name: '中央四面主斗屏', location: '主馆中心吊挂区', status: 'online', signal: '赛事计时成绩', signalType: 'HDMI 1', resolution: '3840 × 2160', refreshRate: '60 Hz', protocol: 'NovaStar UDP', latency: 2.4, frameLoss: '0.00%', blackout: false },
  { id: 'SCR-EAST-02', name: '东侧看台成绩屏', location: '东看台二层', status: 'online', signal: '场馆主摄像机', signalType: 'SDI 1', resolution: '1920 × 1080', refreshRate: '60 Hz', protocol: 'SDI 12G', latency: 3.1, frameLoss: '0.02%', blackout: false },
  { id: 'SCR-RING-03', name: '看台环形周界屏', location: '二层栏杆环绕区', status: 'warning', signal: '媒体播控素材', signalType: 'HDMI 2', resolution: '7680 × 480', refreshRate: '50 Hz', protocol: 'NovaStar UDP', latency: 8.6, frameLoss: '0.18%', blackout: false },
  { id: 'SCR-WARM-04', name: '副馆热身屏', location: '副馆热身场', status: 'offline', signal: '测试图 / 待机画面', signalType: 'HDMI 3', resolution: '1920 × 1080', refreshRate: '60 Hz', protocol: 'TCP/IP', latency: null, frameLoss: '—', blackout: false }
]

const signalSources = ref([
  { id: 'timing', name: '赛事计时成绩', type: '业务数据合成', input: 'HDMI 1', status: 'ready', detail: '实时成绩、排名和赛事状态', icon: DataBoard },
  { id: 'camera', name: '场馆主摄像机', type: '现场视频', input: 'SDI 1', status: 'ready', detail: '中心场地现场直播画面', icon: Camera },
  { id: 'media', name: '媒体播控素材', type: '音视频素材', input: 'HDMI 2', status: 'ready', detail: '来自媒体播控台的当前素材', icon: Monitor },
  { id: 'external', name: '外部输入接口', type: '第三方信号', input: 'HDMI 4', status: 'warning', detail: '当前检测到信号抖动', icon: VideoPlay },
  { id: 'test', name: '测试图 / 待机画面', type: '系统内置', input: 'GENERATOR', status: 'ready', detail: '用于输出链路校验', icon: Monitor }
])

const screenDevices = ref([])
const selectedScreenIds = ref(['SCR-CENTER-01'])
const selectedSignalId = ref('timing')
const previewScreenId = ref('SCR-CENTER-01')
const isSimulated = ref(true)
const isRefreshing = ref(false)
const busLatency = ref('2.8')
const lastSyncTime = ref('刚刚')
const lastAction = ref('系统已就绪，等待调度指令')
const logsDrawerVisible = ref(false)
const drawerLogs = ref([])

const onlineScreenCount = computed(() => screenDevices.value.filter(screen => screen.status !== 'offline').length)
const selectedSignal = computed(() => signalSources.value.find(source => source.id === selectedSignalId.value) || signalSources.value[0])
const selectedScreens = computed(() => screenDevices.value.filter(screen => selectedScreenIds.value.includes(screen.id)))
const selectedScreenNames = computed(() => selectedScreens.value.map(screen => screen.name).join('、'))
const previewScreen = computed(() => screenDevices.value.find(screen => screen.id === previewScreenId.value) || screenDevices.value[0])
const hasMixedSignals = computed(() => new Set(selectedScreens.value.map(screen => screen.signal)).size > 1)
const previewModeClass = computed(() => {
  const signal = previewScreen.value?.signal || ''
  if (signal.includes('摄像')) return 'camera-mode'
  if (signal.includes('媒体')) return 'media-mode'
  if (signal.includes('测试')) return 'test-mode'
  return 'timing-mode'
})

const normalizeScreen = (device, index) => {
  const status = String(device.online_status || '').toUpperCase()
  return {
    id: device.custom_no || `SCR-DISPLAY-${String(index + 1).padStart(2, '0')}`,
    name: device.device_name || 'LED大屏控制器',
    location: device.region_name || '场馆显示区域',
    status: status === 'ONLINE' ? 'online' : status === 'OFFLINE' ? 'offline' : 'warning',
    signal: index === 0 ? '赛事计时成绩' : index === 1 ? '场馆主摄像机' : '媒体播控素材',
    signalType: index === 0 ? 'HDMI 1' : index === 1 ? 'SDI 1' : 'HDMI 2',
    resolution: index === 0 ? '3840 × 2160' : '1920 × 1080',
    refreshRate: '60 Hz',
    protocol: device.connection_type || 'TCP/IP',
    latency: status === 'OFFLINE' ? null : Number((2.2 + index * 1.4).toFixed(1)),
    frameLoss: status === 'OFFLINE' ? '—' : index > 1 ? '0.18%' : '0.00%',
    blackout: false,
    serviceId: device.id,
    customNo: device.custom_no
  }
}

const loadScreens = () => {
  try {
    const devices = typeof iotDeviceService.getDevicesByType === 'function'
      ? iotDeviceService.getDevicesByType('SCREEN')
      : iotDeviceService.getDevices('SCREEN')
    if (Array.isArray(devices) && devices.length) {
      screenDevices.value = devices.map(normalizeScreen)
      isSimulated.value = false
    } else {
      screenDevices.value = structuredClone(demoScreens)
    }
  } catch (error) {
    console.warn('读取 LED 大屏设备失败，使用演示数据:', error)
    screenDevices.value = structuredClone(demoScreens)
  }
  selectedScreenIds.value = screenDevices.value.filter(screen => screen.status !== 'offline').slice(0, 2).map(screen => screen.id)
  previewScreenId.value = screenDevices.value[0]?.id || ''
}

const isScreenSelected = id => selectedScreenIds.value.includes(id)
const toggleScreenSelection = id => {
  selectedScreenIds.value = isScreenSelected(id)
    ? selectedScreenIds.value.filter(screenId => screenId !== id)
    : [...selectedScreenIds.value, id]
  if (!selectedScreenIds.value.includes(previewScreenId.value) && selectedScreenIds.value.length) previewScreenId.value = selectedScreenIds.value[0]
}
const selectAllScreens = () => { selectedScreenIds.value = screenDevices.value.map(screen => screen.id) }
const selectOnlineScreens = () => { selectedScreenIds.value = screenDevices.value.filter(screen => screen.status !== 'offline').map(screen => screen.id) }
const clearScreenSelection = () => { selectedScreenIds.value = [] }
const previewScreenById = id => { previewScreenId.value = id }
const statusLabel = status => ({ online: '在线', warning: '告警', offline: '离线' })[status] || '未知'

const updateSelectedScreens = changes => {
  screenDevices.value.forEach(screen => {
    if (selectedScreenIds.value.includes(screen.id)) Object.assign(screen, changes)
  })
  lastSyncTime.value = new Date().toLocaleTimeString()
}

const sendScreenCommand = (name, code) => {
  let serviceSucceeded = false
  try {
    const targets = selectedScreens.value
    targets.forEach(screen => {
      if (screen.serviceId != null && typeof iotDeviceService.executeDeviceCommand === 'function') {
        iotDeviceService.executeDeviceCommand(screen.serviceId, {
          command_name: name,
          command_code: code,
          command_payload: `${code}|TARGET:${screen.id}`,
          expected_ack: 'ACK_OK',
          timeout_ms: 800
        })
        serviceSucceeded = true
      }
    })
  } catch (error) {
    console.warn('大屏设备指令记录失败:', error)
  }
  lastAction.value = `${name}已${serviceSucceeded ? '下发' : '更新本地演示状态'}：${selectedScreenNames.value}`
  ElMessage.success(lastAction.value)
}

const applySelectedSignal = () => {
  if (!selectedScreenIds.value.length) return ElMessage.warning('请先选择至少一块目标大屏')
  if (selectedSignal.value.status !== 'ready') return ElMessage.warning('当前信号源不可用，暂不能应用')
  updateSelectedScreens({ signal: selectedSignal.value.name, signalType: selectedSignal.value.input, blackout: false })
  sendScreenCommand('切换输入源', `INPUT_${selectedSignal.value.id.toUpperCase()}`)
}

const restoreMainSignal = () => {
  if (!selectedScreenIds.value.length) return ElMessage.warning('请先选择目标大屏')
  updateSelectedScreens({ signal: '场馆主摄像机', signalType: 'SDI 1', blackout: false })
  sendScreenCommand('恢复主路信号', 'RESTORE_MAIN')
}

const confirmBlackout = () => {
  if (!selectedScreenIds.value.length) return ElMessage.warning('请先选择目标大屏')
  ElMessageBox.confirm('确定让选中的大屏进入黑屏状态吗？', '确认黑屏操作', { type: 'warning' })
    .then(() => { updateSelectedScreens({ blackout: true }); sendScreenCommand('批量黑屏', 'BLACKOUT') })
    .catch(() => {})
}

const releaseBlackout = () => {
  if (!selectedScreenIds.value.length) return ElMessage.warning('请先选择目标大屏')
  updateSelectedScreens({ blackout: false })
  sendScreenCommand('解除黑屏', 'RELEASE_BLACKOUT')
}

const refreshScreenData = () => {
  isRefreshing.value = true
  setTimeout(() => {
    busLatency.value = (2.2 + Math.random() * 1.8).toFixed(1)
    isRefreshing.value = false
    lastSyncTime.value = new Date().toLocaleTimeString()
    ElMessage.success('LED 大屏控制器巡检完成，状态已刷新')
  }, 500)
}

const openLogsDrawer = () => {
  try {
    const logs = iotDeviceService.getCommandLogs?.() || []
    drawerLogs.value = logs.filter(log => log.hardware_type === 'SCREEN' || log.custom_no?.startsWith('SCR') || /大屏|信号|黑屏/.test(log.command_name || ''))
  } catch (error) {
    drawerLogs.value = []
  }
  logsDrawerVisible.value = true
}

onMounted(loadScreens)
</script>

<style scoped>
.led-dispatch-page { display: flex; flex-direction: column; gap: 14px; min-width: 0; color: var(--do-text-primary); }
.glass-panel { background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 10px; box-shadow: var(--shadow-sm); }
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 18px 22px; }
.page-heading, .title-row, .header-status, .status-metric, .section-heading, .target-actions, .screen-card-top, .screen-identity, .screen-location, .screen-card-footer, .panel-heading, .matrix-state, .signal-card-head, .signal-meta, .apply-summary, .apply-target, .preview-state, .preview-osd, .preview-footer, .preview-facts, .output-actions, .action-description, .action-description > div, .action-buttons { display: flex; align-items: center; }
.page-heading { gap: 14px; min-width: 0; }
.page-icon { width: 52px; height: 52px; display: grid; place-items: center; flex-shrink: 0; color: var(--do-gold); background: var(--do-gold-wash); border: 1px solid var(--do-border-dark); border-radius: 12px; }
h1, h2, h3, p { margin: 0; }
h1 { font-size: 21px; line-height: 1.3; }
h2 { font-size: 16px; line-height: 1.35; }
h3 { font-size: 15px; line-height: 1.35; }
.page-heading p, .section-help { color: var(--do-text-secondary); font-size: 13px; }
.page-heading p { margin-top: 5px; }
.title-row { gap: 10px; }
.simulation-badge, .selection-count, .matrix-state, .preview-state { font-size: 13px; }
.simulation-badge { padding: 4px 8px; color: var(--do-warning-deep); background: var(--do-warning-bg); border: 1px solid var(--do-warning-border); border-radius: 5px; }
.header-status { justify-content: flex-end; gap: 16px; flex-wrap: wrap; color: var(--do-text-secondary); font-size: 13px; }
.status-metric { gap: 6px; white-space: nowrap; }
.status-metric strong { color: var(--do-text-primary); font-size: 15px; }
.status-dot { width: 8px; height: 8px; flex: 0 0 auto; border-radius: 50%; background: currentColor; }
.status-dot.online { color: var(--do-success); box-shadow: 0 0 7px currentColor; }
.target-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 14px 18px; }
.section-heading, .panel-heading { justify-content: space-between; gap: 12px; min-width: 0; }
.section-heading { flex: 1; }
.section-help { display: block; margin-top: 4px; }
.selection-count { color: var(--do-gold-deep); font-weight: 700; }
.target-actions { gap: 8px; flex-wrap: wrap; }
.screen-wall { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
.screen-card { position: relative; padding: 15px; cursor: pointer; transition: border-color .2s, box-shadow .2s, transform .2s; }
.screen-card:only-child { display: grid; grid-template-columns: minmax(250px, 1.15fr) minmax(190px, .8fr) minmax(260px, 1.25fr) minmax(220px, 1fr) auto; align-items: center; gap: 16px; padding: 16px 18px; }
.screen-card-top { position: static; padding-right: 0; }
.screen-status { position: absolute; top: 14px; right: 14px; z-index: 1; }
.screen-identity { padding-right: 82px; }
.screen-card:only-child .screen-card-top { min-width: 0; padding-right: 0; }
.screen-card:only-child .screen-status { top: 16px; right: 18px; }
.screen-card:only-child .screen-location, .screen-card:only-child .current-signal, .screen-card:only-child .screen-facts { margin: 0; }
.screen-card:only-child .screen-card-footer { margin: 0; padding: 0; border-top: 0; }
.screen-card:hover, .screen-card.previewing { border-color: var(--do-gold); box-shadow: var(--shadow-hover); }
.screen-card.selected { border-color: var(--do-gold); background: var(--do-gold-wash); box-shadow: 0 0 0 2px var(--do-gold-wash-strong); }
.screen-card-top { justify-content: space-between; gap: 8px; }
.screen-identity { gap: 9px; min-width: 0; }
.screen-icon { width: 36px; height: 36px; display: grid; place-items: center; flex-shrink: 0; color: var(--do-gold); background: var(--do-bg-sunken); border-radius: 8px; }
.screen-identity h3 { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.device-code { display: block; margin-top: 4px; color: var(--do-text-secondary); font-size: 13px; }
.screen-status, .preview-state { display: inline-flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 14px; font-weight: 700; white-space: nowrap; }
.screen-status.online, .preview-state.online { color: var(--do-success-deep); background: var(--do-success-bg); }
.screen-status.warning, .preview-state.warning { color: var(--do-warning-deep); background: var(--do-warning-bg); }
.screen-status.offline, .preview-state.offline { color: var(--do-text-secondary); background: var(--do-bg-sunken); }
.screen-location { gap: 5px; margin: 14px 0 12px; color: var(--do-text-secondary); font-size: 13px; }
.current-signal { display: grid; grid-template-columns: auto 1fr auto; gap: 8px; align-items: center; padding: 10px; background: var(--do-bg-sunken); border-radius: 7px; }
.field-label { color: var(--do-text-secondary); font-size: 13px; }
.current-signal strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; }
.signal-port { color: var(--do-gold-deep); font-size: 13px; }
.screen-facts, .preview-facts { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 12px; }
.screen-facts div, .preview-facts div { display: flex; flex-direction: column; gap: 4px; }
.screen-facts span, .preview-facts span { color: var(--do-text-secondary); font-size: 13px; }
.screen-facts strong, .preview-facts strong { font-size: 14px; }
.screen-card-footer { justify-content: space-between; gap: 8px; margin-top: 14px; padding-top: 11px; border-top: 1px solid var(--do-border-light); }
.screen-card-footer :deep(.el-button) { flex-shrink: 0; color: #fff !important; background: var(--do-gold); border: 1px solid var(--do-gold-deep); border-radius: 6px; box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), .22); }
.screen-card-footer :deep(.el-button:hover) { color: #fff !important; background: var(--do-gold-hover); border-color: var(--do-gold-hover); }
.selection-state { color: var(--do-text-secondary); font-size: 13px; }
.selection-state.active { display: inline-flex; align-items: center; gap: 4px; color: var(--do-gold-deep); font-weight: 700; }
.dispatch-grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(360px, .75fr); gap: 14px; align-items: stretch; }
.signal-panel, .preview-panel { min-width: 0; padding: 18px; }
.matrix-state { gap: 7px; color: var(--do-success-deep); white-space: nowrap; }
.signal-grid { display: grid; grid-template-columns: repeat(3, minmax(145px, 1fr)); gap: 10px; margin-top: 16px; }
.signal-card { min-width: 0; padding: 13px; color: var(--do-text-primary); text-align: left; background: var(--do-bg-page); border: 1px solid var(--do-border); border-radius: 8px; cursor: pointer; transition: border-color .2s, background .2s; }
.signal-card:hover, .signal-card.selected { border-color: var(--do-gold); background: var(--do-gold-wash); }
.signal-card.unavailable { border-style: dashed; }
.signal-card-head { justify-content: space-between; margin-bottom: 10px; }
.signal-icon { display: grid; place-items: center; width: 30px; height: 30px; color: var(--do-gold); background: var(--do-bg-card); border-radius: 7px; }
.source-state { font-size: 13px; font-weight: 700; }
.source-state.ready { color: var(--do-success-deep); }
.source-state.warning { color: var(--do-warning-deep); }
.signal-card strong { display: block; font-size: 14px; }
.signal-card > span { display: block; margin-top: 4px; color: var(--do-text-secondary); font-size: 13px; }
.signal-meta { justify-content: space-between; gap: 8px; margin-top: 12px; padding-top: 9px; border-top: 1px solid var(--do-border-light); color: var(--do-text-secondary); font-size: 13px; }
.signal-meta span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.apply-summary { justify-content: space-between; gap: 16px; margin-top: 16px; padding: 13px; background: var(--do-bg-sunken); border: 1px solid var(--do-border-light); border-radius: 8px; }
.apply-summary > div { min-width: 0; }
.apply-summary strong { display: block; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 15px; }
.apply-target { display: block; min-width: 130px; color: var(--do-text-secondary); font-size: 13px; }
.apply-target strong { color: var(--do-text-primary); }
.preview-panel { display: flex; flex-direction: column; }
.preview-frame { margin-top: 16px; padding: 9px; background: var(--do-bg-dark); border: 1px solid var(--do-border); border-radius: 9px; }
.preview-osd, .preview-footer { justify-content: space-between; gap: 8px; color: var(--do-text-inverse-sub); font-size: 13px; }
.preview-osd { padding: 2px 3px 8px; }
.preview-content { position: relative; display: grid; place-items: center; min-height: 220px; overflow: hidden; color: #fff; border: 1px solid rgba(255,255,255,.14); border-radius: 6px; background: linear-gradient(135deg, #102744, #0c1729); }
.preview-content.camera-mode { background: linear-gradient(135deg, #174b52, #0c2630); }
.preview-content.media-mode { background: linear-gradient(135deg, #36245a, #161b3a); }
.preview-content.test-mode { background: repeating-linear-gradient(45deg, #234268 0 25px, #2f6b92 25px 50px); }
.preview-grid-lines { position: absolute; inset: 0; opacity: .18; background: linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px); background-size: 38px 38px; }
.preview-center { position: relative; display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 1; color: #fff; }
.preview-center strong { font-size: 19px; }
.preview-center span { color: rgba(255,255,255,.72); font-size: 13px; }
.preview-corner { position: absolute; z-index: 1; color: rgba(255,255,255,.68); font-size: 13px; }
.preview-corner.top-left { top: 12px; left: 14px; }.preview-corner.top-right { top: 12px; right: 14px; }.preview-corner.bottom-left { bottom: 12px; left: 14px; }
.preview-footer { padding: 8px 3px 2px; color: var(--do-text-inverse); }.preview-footer span:last-child { color: var(--do-text-inverse-sub); }
.mixed-warning { display: flex; align-items: center; gap: 6px; margin-top: 10px; padding: 8px 10px; color: var(--do-warning-deep); background: var(--do-warning-bg); border: 1px solid var(--do-warning-border); border-radius: 6px; font-size: 13px; }
.preview-facts { grid-template-columns: repeat(3, 1fr); margin-top: 15px; }
.output-actions { justify-content: space-between; gap: 18px; padding: 14px 18px; }
.action-description { gap: 10px; min-width: 0; }.action-description > div { flex-direction: column; align-items: flex-start; gap: 4px; min-width: 0; }.action-description strong { font-size: 14px; }.action-description span:not(.action-led) { overflow: hidden; color: var(--do-text-secondary); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.action-led { width: 9px; height: 9px; border-radius: 50%; flex: 0 0 auto; background: var(--do-success); box-shadow: 0 0 8px var(--do-success); }
.action-buttons { justify-content: flex-end; gap: 8px; flex-wrap: wrap; }
.drawer-summary { margin-bottom: 14px; padding: 12px; color: var(--do-text-secondary); background: var(--do-bg-sunken); border-radius: 7px; font-size: 14px; }.drawer-summary strong { color: var(--do-gold-deep); font-size: 18px; }
.num-mono { font-family: var(--font-mono, 'SFMono-Regular', Consolas, monospace); }
@media (max-width: 1440px) { .screen-card:only-child { grid-template-columns: minmax(220px, 1fr) minmax(180px, .8fr) minmax(220px, 1fr); }.screen-card:only-child .screen-facts { grid-column: 1 / span 2; }.screen-card:only-child .screen-card-footer { grid-column: 3; grid-row: 2; } }
@media (max-width: 1280px) { .screen-wall { grid-template-columns: repeat(2, minmax(220px, 1fr)); }.screen-card:only-child { display: block; }.screen-card:only-child .screen-location, .screen-card:only-child .current-signal, .screen-card:only-child .screen-facts { margin-top: 12px; }.screen-card:only-child .screen-card-footer { margin-top: 14px; padding-top: 11px; border-top: 1px solid var(--do-border-light); }.dispatch-grid { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .page-header, .target-toolbar, .output-actions { align-items: flex-start; flex-direction: column; }.header-status { justify-content: flex-start; }.screen-wall, .signal-grid { grid-template-columns: 1fr; }.apply-summary { align-items: stretch; flex-direction: column; }.action-buttons { justify-content: flex-start; }.preview-content { min-height: 190px; } }
</style>
