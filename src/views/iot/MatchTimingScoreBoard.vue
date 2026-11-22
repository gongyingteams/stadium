<template>
  <div class="score-readonly-page">
    <section class="score-header glass-panel">
      <div class="score-title-block">
        <div class="score-icon"><SvgIcon name="SvgMatchScore" size="28" /></div>
        <div>
          <div class="title-line">
            <h1>赛事计时计分接收与大屏推屏</h1>
            <span class="readonly-badge">只读监测</span>
            <span v-if="isDemoData" class="demo-badge">演示数据</span>
          </div>
          <p>只读接收赛事成绩、硬件遥测和大屏推送状态，不提供成绩编辑或设备写入操作。</p>
        </div>
      </div>
      <div class="header-read-status">
        <div class="status-item"><span :class="['status-dot', readState === 'ready' ? 'online' : readState === 'error' ? 'danger' : 'muted']"></span>{{ readStateLabel }}</div>
        <div class="status-item"><strong class="num-mono">{{ onlineDeviceCount }}/{{ scoreDevices.length || 0 }}</strong> 台 SCORE 在线</div>
        <div class="status-item">最近读取 <strong class="num-mono">{{ lastReadAt }}</strong></div>
        <button class="btn-header-action btn-header-primary" :disabled="readState === 'loading'" @click="loadScoreReadModel" title="重新从赛事计时计分网络拉取只读快照数据">
          <SvgIcon name="SvgRefresh" size="14" :class="{ 'spin-icon': readState === 'loading' }" style="margin-right: 4px;" />
          <span>{{ readState === 'loading' ? '正在读取中...' : '刷新读取' }}</span>
        </button>
      </div>
    </section>

    <section class="metric-grid">
      <div class="metric-card glass-panel"><span>当前赛事</span><strong>{{ scoreSnapshot.eventName || '暂无接收快照' }}</strong><em>{{ scoreSnapshot.heat || '等待赛事数据' }}</em></div>
      <div class="metric-card glass-panel"><span>比赛阶段</span><strong>{{ scoreSnapshot.phase || '暂无阶段数据' }}</strong><em>只读状态</em></div>
      <div class="metric-card glass-panel"><span>已接收成绩</span><strong class="num-mono">{{ scoreSnapshot.receivedCount }}</strong><em>条有效记录</em></div>
      <div class="metric-card glass-panel"><span>最新有效成绩</span><strong class="num-mono">{{ scoreSnapshot.latestResult || '—' }}</strong><em>{{ scoreSnapshot.latestReceivedAt || '暂无接收时间' }}</em></div>
      <div class="metric-card glass-panel"><span>推屏目标</span><strong class="num-mono">{{ scoreSnapshot.pushTargetCount }}</strong><em>块大屏状态可见</em></div>
      <div class="metric-card glass-panel"><span>最新数据帧</span><strong class="num-mono">{{ scoreSnapshot.latestFrame || '—' }}</strong><em>{{ scoreSnapshot.latestFrameAt || '暂无数据帧' }}</em></div>
    </section>

    <section v-if="readState === 'error'" class="read-alert glass-panel">
      <el-icon><WarningFilled /></el-icon>
      <div><strong>计时计分只读数据读取失败</strong><span>页面未执行任何设备写入操作，请重新读取或检查数据服务。</span></div>
      <el-button size="small" @click="loadScoreReadModel">重新读取</el-button>
    </section>

    <section class="main-read-grid">
      <div class="results-panel glass-panel">
        <div class="panel-heading"><div><h2>已接收成绩查看</h2><p>数据来自 SCORE 只读接收快照，不提供编辑或推送操作</p></div><span class="readonly-label">READ ONLY</span></div>
        <el-table :data="scoreSnapshot.results" stripe class="results-table" empty-text="暂无成绩接收记录">
          <el-table-column prop="rank" label="名次" width="70" align="center" />
          <el-table-column prop="lane" label="道次 / 序号" width="110" align="center"><template #default="{ row }"><span class="lane-tag num-mono">{{ row.lane || '—' }}</span></template></el-table-column>
          <el-table-column prop="athlete" label="选手 / 队伍" min-width="150" />
          <el-table-column prop="split" label="分段成绩" width="110" align="center"><template #default="{ row }"><span class="num-mono">{{ row.split || '—' }}</span></template></el-table-column>
          <el-table-column prop="result" label="最终成绩" width="120" align="center"><template #default="{ row }"><strong class="result-time num-mono">{{ row.result || '—' }}</strong></template></el-table-column>
          <el-table-column prop="receivedAt" label="接收时间" width="150"><template #default="{ row }"><span class="num-mono">{{ row.receivedAt || '—' }}</span></template></el-table-column>
          <el-table-column prop="dataStatus" label="数据状态" width="105" align="center"><template #default="{ row }"><span :class="['table-state', row.dataStatusClass]">{{ row.dataStatus }}</span></template></el-table-column>
          <el-table-column prop="pushStatus" label="大屏状态" width="125" align="center"><template #default="{ row }"><span :class="['table-state', row.pushStatusClass]">{{ row.pushStatus }}</span></template></el-table-column>
        </el-table>
      </div>

      <aside class="push-panel glass-panel">
        <div class="panel-heading"><div><h2>成绩推屏状态</h2><p>只读展示已存在的推屏回执</p></div><span class="readonly-label">NO WRITE</span></div>
        <div class="push-summary" :class="scoreSnapshot.pushStatusClass"><span class="status-dot"></span><strong>{{ scoreSnapshot.pushStatus }}</strong></div>
        <div class="push-details">
          <div><span>接收成绩</span><strong>{{ scoreSnapshot.receivedCount ? '已接收' : '暂无数据' }}</strong></div>
          <div><span>目标大屏</span><strong>{{ scoreSnapshot.pushTargets.length ? scoreSnapshot.pushTargets.join('、') : '暂无目标记录' }}</strong></div>
          <div><span>最近回执</span><strong>{{ scoreSnapshot.pushReceipt }}</strong></div>
          <div><span>成绩来源</span><strong>{{ scoreSnapshot.sourceDevice }}</strong></div>
        </div>
        <div class="push-note"><el-icon><InfoFilled /></el-icon><span>本页面不执行推屏、撤回、清屏或自动推屏控制。</span></div>
      </aside>
    </section>

    <section class="timeline-panel glass-panel">
      <div class="panel-heading">
        <div><h2>赛事接收时间线</h2><p>仅展示已读取的发令、分段、触壁、解析、校验与推屏状态事实</p></div>
        <el-radio-group v-model="eventFilter" size="small">
          <el-radio-button label="ALL">全部</el-radio-button>
          <el-radio-button label="SCORE">成绩接收</el-radio-button>
          <el-radio-button label="CHECK">数据校验</el-radio-button>
          <el-radio-button label="PUSH">推屏回执</el-radio-button>
        </el-radio-group>
      </div>
      <div v-if="filteredEvents.length" class="timeline-list">
        <div v-for="event in filteredEvents" :key="event.id" class="timeline-item">
          <div class="timeline-marker" :class="event.level"><span></span></div>
          <div class="timeline-time num-mono">{{ event.time }}</div>
          <div class="timeline-main"><div class="event-title"><strong>{{ event.title }}</strong><span :class="['event-state', event.level]">{{ event.state }}</span></div><p>{{ event.summary }}</p><div class="event-meta"><span>来源：{{ event.source }}</span><span class="num-mono">{{ event.trace }}</span><span>校验：{{ event.check }}</span></div></div>
        </div>
      </div>
      <div v-else class="empty-inline"><el-icon><InfoFilled /></el-icon><span>暂无可展示的接收事件</span></div>
    </section>

    <section class="device-section glass-panel">
      <div class="panel-heading"><div><h2>SCORE 计时计分硬件遥测</h2><p>读取全部计时计分设备的连接与数据接收状态</p></div><span class="device-count num-mono">{{ scoreDevices.length }} UNITS READ</span></div>
      <div v-if="scoreDevices.length" class="device-grid">
        <article v-for="device in scoreDevices" :key="device.id" class="device-card" :class="{ active: activeDeviceId === device.id }" @click="activeDeviceId = activeDeviceId === device.id ? null : device.id">
          <div class="device-card-head"><div><span class="device-role">{{ device.role }}</span><h3>{{ device.name }}</h3><span class="device-no num-mono">{{ device.customNo }}</span></div><span :class="['device-status', device.status]"><i></i>{{ statusLabel(device.status) }}</span></div>
          <div class="device-location"><el-icon><Location /></el-icon>{{ device.region }} · {{ device.group }}</div>
          <div class="device-facts"><div><span>协议</span><strong class="num-mono">{{ device.protocol }}</strong></div><div><span>地址</span><strong class="num-mono">{{ device.address }}:{{ device.port }}</strong></div><div><span>最近接收</span><strong class="num-mono">{{ device.lastReceivedAt }}</strong></div><div><span>链路延迟</span><strong class="num-mono">{{ formatMetric(device.latency, 'ms') }}</strong></div><div><span>接收频率</span><strong class="num-mono">{{ formatMetric(device.receiveRate, 'Hz') }}</strong></div><div><span>数据帧</span><strong class="num-mono">{{ device.frameCount }}</strong></div></div>
          <div class="device-footer"><span>校验：{{ device.crcStatus }}</span><span>主备：{{ device.syncStatus }}</span></div>
          <div v-if="activeDeviceId === device.id" class="device-detail"><strong>设备备注</strong><p>{{ device.remark }}</p><span>数据源：只读设备登记与接收快照</span></div>
        </article>
      </div>
      <div v-else class="empty-state"><el-icon><Monitor /></el-icon><strong>暂无 SCORE 设备</strong><span>当前读取范围内没有计时计分硬件登记。</span></div>
    </section>

    <section class="frames-panel glass-panel">
      <div class="panel-heading"><div><h2>最近接收数据帧</h2><p>原始帧摘要仅供查看，不支持编辑、重放或重新发送</p></div><span class="readonly-label">CAPTURED READ ONLY</span></div>
      <div v-if="recentFrames.length" class="frames-list"><div v-for="frame in recentFrames" :key="frame.id" class="frame-row"><span class="frame-time num-mono">{{ frame.time }}</span><span class="frame-source">{{ frame.source }}</span><span class="frame-type">{{ frame.type }}</span><span class="frame-summary">{{ frame.summary }}</span><span class="frame-check" :class="frame.checkClass">{{ frame.check }}</span><code class="frame-raw num-mono">{{ frame.raw }}</code></div></div>
      <div v-else class="empty-inline"><el-icon><InfoFilled /></el-icon><span>暂无接收数据帧</span></div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled, Location, Monitor, Refresh, WarningFilled } from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { iotDeviceService } from '@/services/iotDeviceService'

const scoreDevices = ref([])
const scoreSnapshot = ref(emptyScoreSnapshot())
const receiveEvents = ref([])
const recentFrames = ref([])
const readState = ref('loading')
const isDemoData = ref(false)
const lastReadAt = ref('—')
const activeDeviceId = ref(null)
const eventFilter = ref('ALL')

function emptyScoreSnapshot() {
  return { eventName: '', heat: '', phase: '', receivedCount: 0, latestResult: '', latestReceivedAt: '', latestFrame: '', latestFrameAt: '', pushTargetCount: 0, pushStatus: '暂无推送快照', pushStatusClass: 'muted', pushTargets: [], pushReceipt: '—', sourceDevice: '—', results: [] }
}

const normalizeScoreDevice = (device, index) => ({
  id: Number(device.id), customNo: device.custom_no || `SCORE-${index + 1}`, name: device.device_name || '计时计分设备', role: index === 0 ? '主计时主机' : index === 1 ? '备用热备主机' : '副馆计时设备',
  status: device.online_status === 'ONLINE' ? 'online' : device.online_status === 'FAULT' ? 'warning' : 'offline', group: device.group_name || '—', region: device.region_name || '—', remark: device.remark || '—', protocol: device.connection_type || '—', address: device.target_ip || device.serial_port || '—', port: device.target_port || '—', lastReceivedAt: device.last_received_at || '暂无字段', latency: device.latency_ms ?? '暂无字段', receiveRate: device.receive_rate_hz ?? '暂无字段', frameCount: device.frame_count ?? '暂无字段', packetLoss: device.packet_loss ?? '暂无字段', crcStatus: device.crc_status || '暂无字段', syncStatus: device.sync_status || '暂无字段', source: device
})

const toReadonlyFrame = (log, index) => ({ id: log.id || `frame-${index}`, time: log.created_at || '—', source: log.custom_no || log.device_name || 'SCORE', type: log.command_name || 'SCORE_RX', summary: log.response_payload || log.command_payload || '已读取历史数据帧摘要', check: log.execute_result === 'SUCCESS' ? '校验通过' : log.execute_result || '未知', checkClass: log.execute_result === 'SUCCESS' ? 'ok' : 'warning', raw: truncate(log.response_payload || log.command_payload || '—', 56) })
const toReadonlyEvent = (log, index) => ({ id: log.id || `event-${index}`, time: log.created_at || '—', title: log.command_name || '计时计分数据接收', state: log.execute_result === 'SUCCESS' ? '已确认' : '待核验', level: log.execute_result === 'SUCCESS' ? 'success' : 'warning', summary: log.response_payload || '读取到历史计时计分接收记录', source: log.custom_no || log.device_name || 'SCORE', trace: log.trace_id || 'HISTORICAL', check: log.execute_result || 'UNKNOWN', category: /推屏|同步/.test(log.command_name || '') ? 'PUSH' : /校验|CRC/.test(log.command_name || '') ? 'CHECK' : 'SCORE' })
const truncate = (value, length) => String(value || '—').length > length ? `${String(value).slice(0, length)}…` : String(value || '—')

const demoResults = [
  { rank: 1, lane: '04', athlete: '潘展乐 / 中国队', split: '22.80s', result: '46.80s', receivedAt: '12:15:28.420', dataStatus: '有效', dataStatusClass: 'success', pushStatus: '已同步', pushStatusClass: 'success' },
  { rank: 2, lane: '05', athlete: '大卫·波波维奇 / 罗马尼亚', split: '23.05s', result: '46.90s', receivedAt: '12:15:28.423', dataStatus: '有效', dataStatusClass: 'success', pushStatus: '已同步', pushStatusClass: 'success' },
  { rank: 3, lane: '03', athlete: '凯尔·查默斯 / 澳大利亚', split: '23.12s', result: '47.48s', receivedAt: '12:15:28.426', dataStatus: '有效', dataStatusClass: 'success', pushStatus: '等待确认', pushStatusClass: 'warning' },
  { rank: 4, lane: '06', athlete: '马克西姆·格鲁塞 / 法国', split: '23.30s', result: '47.62s', receivedAt: '12:15:28.429', dataStatus: '待校验', dataStatusClass: 'warning', pushStatus: '未推送', pushStatusClass: 'muted' },
  { rank: 5, lane: '02', athlete: '南多尔·涅梅特 / 匈牙利', split: '23.45s', result: '47.89s', receivedAt: '12:15:28.432', dataStatus: '有效', dataStatusClass: 'success', pushStatus: '未推送', pushStatusClass: 'muted' }
]

const demoEvents = [
  { id: 'demo-event-1', time: '12:15:10.000', title: '赛事发令数据接收', state: '已确认', level: 'success', summary: '主计时主机收到正式比赛发令帧，赛事进入计时阶段。', source: 'TIM-SWIM-MASTER', trace: 'FRAME-000184', check: 'CRC 通过', category: 'SCORE' },
  { id: 'demo-event-2', time: '12:15:18.240', title: '50m 分段成绩接收', state: '已确认', level: 'success', summary: '主机接收 8 条分段计时数据，备用主机镜像帧一致。', source: 'TIM-SWIM-SLAVE', trace: 'FRAME-000269', check: 'CRC 通过', category: 'SCORE' },
  { id: 'demo-event-3', time: '12:15:28.420', title: '触壁终点数据接收', state: '已确认', level: 'success', summary: '全部参赛道次完成触壁，已形成可查看的成绩快照。', source: 'TIM-SWIM-MASTER', trace: 'FRAME-000318', check: 'CRC 通过', category: 'SCORE' },
  { id: 'demo-event-4', time: '12:15:28.455', title: '成绩解析与校验完成', state: '已确认', level: 'success', summary: '赛事成绩完成排序和异常字段检查，1 条记录标记为待复核。', source: 'TIM-SWIM-MASTER', trace: 'SCORE-20261023-01', check: '规则校验', category: 'CHECK' },
  { id: 'demo-event-5', time: '12:15:29.100', title: '成绩推屏状态回执', state: '部分确认', level: 'warning', summary: '中央斗屏和东侧成绩屏已确认，环形屏等待回执。', source: 'SCR-NOVA-CENTER', trace: 'PUSH-20261023-01', check: '2/3 已确认', category: 'PUSH' }
]

const demoFrames = [
  { id: 'demo-frame-1', time: '12:15:28.455', source: 'TIM-SWIM-MASTER', type: 'SCORE_RESULT', summary: '8 lanes · result parsed · best 46.80s', check: 'CRC 通过', checkClass: 'ok', raw: '55 AA 01 08 2E 50 46 80 ... 8F 2C' },
  { id: 'demo-frame-2', time: '12:15:28.423', source: 'TIM-SWIM-SLAVE', type: 'SCORE_MIRROR', summary: 'mirror frame matched with master · drift 0.02ms', check: 'CRC 通过', checkClass: 'ok', raw: '55 AA 02 08 2E 50 46 90 ... A3 10' },
  { id: 'demo-frame-3', time: '12:15:18.240', source: 'TIM-SWIM-MASTER', type: 'SPLIT_TIME', summary: 'lane 01-08 · split 50m received', check: 'CRC 通过', checkClass: 'ok', raw: '55 AA 01 08 16 32 22 80 ... 7C 4B' },
  { id: 'demo-frame-4', time: '12:15:10.000', source: 'TIM-TRACK-01', type: 'START_SIGNAL', summary: 'official start signal observed on TCP channel', check: '待复核', checkClass: 'warning', raw: '7B 22 65 76 65 6E 74 22 ... 7D' }
]

const demoSnapshot = () => ({
  ...emptyScoreSnapshot(), eventName: '2026 全国游泳锦标赛 · 男子100米自由泳', heat: '决赛 · 第1组', phase: '正式成绩已锁定', receivedCount: demoResults.length, latestResult: '46.80s', latestReceivedAt: '12:15:28.420', latestFrame: 'FRAME-000318', latestFrameAt: '12:15:28.420', pushTargetCount: 3, pushStatus: '部分确认', pushStatusClass: 'warning', pushTargets: ['中央四面斗屏', '东侧成绩屏', '看台环形屏'], pushReceipt: '12:15:29.100 · 2/3 已确认', sourceDevice: 'TIM-SWIM-MASTER', results: demoResults
})

const applyDemoSnapshot = () => {
  isDemoData.value = true
  scoreSnapshot.value = demoSnapshot()
  receiveEvents.value = demoEvents
  recentFrames.value = demoFrames
}

const buildScoreSnapshot = (devices, history) => {
  const latest = history[0]
  const pushLogs = history.filter(item => /推屏|同步|SYNC|PUSH/i.test(`${item.command_name || ''}${item.command_payload || ''}`))
  return { ...emptyScoreSnapshot(), eventName: history.length ? '赛事计时计分接收快照' : '', heat: history.length ? '历史接收记录' : '', phase: history.length ? '只读状态已读取' : '', receivedCount: history.length, latestResult: latest?.response_payload ? '已接收' : '', latestReceivedAt: latest?.created_at || '', latestFrame: latest?.trace_id || latest?.id || '', latestFrameAt: latest?.created_at || '', pushTargetCount: pushLogs.length ? 1 : 0, pushStatus: pushLogs.length ? '存在历史推屏回执' : '暂无推屏回执', pushStatusClass: pushLogs.length ? 'success' : 'muted', pushTargets: pushLogs.length ? ['历史回执目标'] : [], pushReceipt: pushLogs[0]?.created_at || '—', sourceDevice: latest?.custom_no || latest?.device_name || '—', results: [] }
}

const loadScoreReadModel = () => {
  readState.value = 'loading'
  try {
    const rawDevices = iotDeviceService.getDevicesByType('SCORE') || []
    const history = iotDeviceService.getCommandLogs?.({ hardwareType: 'SCORE' }) || []
    scoreDevices.value = rawDevices.map(normalizeScoreDevice)
    isDemoData.value = false
    recentFrames.value = history.slice(0, 12).map(toReadonlyFrame)
    receiveEvents.value = history.slice(0, 8).map(toReadonlyEvent)
    scoreSnapshot.value = buildScoreSnapshot(scoreDevices.value, history)
    if (!rawDevices.length || !history.length) applyDemoSnapshot()
    readState.value = scoreDevices.value.length ? 'ready' : 'empty'
    lastReadAt.value = new Date().toLocaleTimeString()
  } catch (error) {
    console.warn('读取计时计分只读数据失败:', error)
    scoreDevices.value = []; scoreSnapshot.value = emptyScoreSnapshot(); receiveEvents.value = []; recentFrames.value = []; isDemoData.value = false; readState.value = 'error'
  }
}

const onlineDeviceCount = computed(() => scoreDevices.value.filter(device => device.status === 'online').length)
const readStateLabel = computed(() => ({ loading: '正在读取', ready: '接收链路正常', empty: '暂无设备数据', error: '读取异常' }[readState.value]))
const filteredEvents = computed(() => eventFilter.value === 'ALL' ? receiveEvents.value : receiveEvents.value.filter(event => event.category === eventFilter.value))
const statusLabel = status => ({ online: '在线', warning: '告警', offline: '离线' }[status] || '未知')
const formatMetric = (value, unit) => value === '—' || value === '暂无字段' ? value : `${value}${unit}`

onMounted(loadScoreReadModel)
</script>

<style scoped>
.score-readonly-page { display: flex; flex-direction: column; gap: 14px; min-width: 0; color: var(--do-text-primary); }
.glass-panel { background: var(--do-bg-card); border: 1px solid var(--do-border); border-radius: 10px; box-shadow: var(--shadow-sm); }
.score-header, .score-title-block, .title-line, .header-read-status, .status-item, .panel-heading, .event-title, .event-meta, .device-card-head, .device-location, .device-footer, .push-summary, .push-note, .frame-row { display: flex; align-items: center; }
.score-header { justify-content: space-between; gap: 20px; padding: 18px 22px; }
.score-title-block { gap: 14px; min-width: 0; }.score-icon { width: 52px; height: 52px; display:grid; place-items:center; flex-shrink:0; color:var(--do-gold); background:var(--do-gold-wash); border:1px solid var(--do-border-dark); border-radius:12px; }
h1,h2,h3,p { margin: 0; } h1 { font-size:21px; line-height:1.3; } h2 { font-size:16px; line-height:1.35; } h3 { font-size:15px; line-height:1.35; }
.title-line { gap: 10px; }.score-title-block p, .panel-heading p { margin-top:5px; color:var(--do-text-secondary); font-size:13px; }.readonly-badge, .readonly-label, .demo-badge { padding:4px 8px; color:var(--do-gold-deep); background:var(--do-gold-wash); border:1px solid var(--do-border-dark); border-radius:5px; font-size:13px; font-weight:700; }.readonly-label { padding:3px 7px; }.demo-badge { color:var(--do-warning-deep); background:var(--do-warning-bg); border-color:var(--do-warning-border); }
.header-read-status { justify-content:flex-end; gap:16px; flex-wrap:wrap; color:var(--do-text-secondary); font-size:13px; }.status-item { gap:6px; white-space:nowrap; }.status-item strong { color:var(--do-text-primary); font-size:15px; }.status-dot { width:8px; height:8px; flex:0 0 auto; border-radius:50%; background:currentColor; }.status-dot.online { color:var(--do-success); box-shadow:0 0 7px currentColor; }.status-dot.danger { color:var(--do-danger); }.status-dot.muted { color:var(--do-text-placeholder); }
.metric-grid { display:grid; grid-template-columns:repeat(6,minmax(135px,1fr)); gap:12px; }.metric-card { min-width:0; padding:15px; }.metric-card span { color:var(--do-text-secondary); font-size:13px; }.metric-card strong { display:block; margin-top:8px; overflow:hidden; color:var(--do-text-primary); font-size:17px; text-overflow:ellipsis; white-space:nowrap; }.metric-card em { display:block; margin-top:5px; overflow:hidden; color:var(--do-text-secondary); font-size:13px; font-style:normal; text-overflow:ellipsis; white-space:nowrap; }
.read-alert { display:flex; align-items:center; gap:12px; padding:13px 16px; color:var(--do-danger-deep); background:var(--do-danger-bg); border-color:var(--do-danger-border); }.read-alert div { flex:1; }.read-alert strong,.read-alert span { display:block; }.read-alert span { margin-top:4px; color:var(--do-text-secondary); font-size:13px; }
.timeline-panel, .results-panel, .push-panel, .device-section, .frames-panel { padding:18px; }.panel-heading { justify-content:space-between; gap:15px; min-width:0; }.panel-heading > div { min-width:0; }.timeline-list { margin-top:18px; }.timeline-item { display:grid; grid-template-columns:18px 150px minmax(0,1fr); gap:12px; min-height:67px; }.timeline-marker { position:relative; display:flex; justify-content:center; }.timeline-marker::after { content:''; position:absolute; top:13px; bottom:-13px; width:1px; background:var(--do-border); }.timeline-item:last-child .timeline-marker::after { display:none; }.timeline-marker span { position:relative; z-index:1; width:10px; height:10px; margin-top:4px; border:3px solid var(--do-bg-card); border-radius:50%; background:var(--do-gold); box-shadow:0 0 0 1px var(--do-gold); }.timeline-marker.success span { background:var(--do-success); box-shadow:0 0 0 1px var(--do-success); }.timeline-marker.warning span { background:var(--do-warning); box-shadow:0 0 0 1px var(--do-warning); }.timeline-time { padding-top:1px; color:var(--do-text-secondary); font-size:13px; }.timeline-main { padding-bottom:13px; border-bottom:1px solid var(--do-border-light); }.event-title { gap:8px; }.event-title strong { font-size:14px; }.event-state { padding:3px 7px; border-radius:10px; font-size:13px; font-weight:700; }.event-state.success { color:var(--do-success-deep); background:var(--do-success-bg); }.event-state.warning { color:var(--do-warning-deep); background:var(--do-warning-bg); }.timeline-main p { margin-top:5px; color:var(--do-text-regular); font-size:13px; }.event-meta { gap:15px; margin-top:8px; color:var(--do-text-secondary); font-size:13px; }
.main-read-grid { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(300px,.45fr); gap:14px; align-items:start; }.results-table { margin-top:16px; }.lane-tag { padding:4px 7px; color:var(--do-gold-deep); background:var(--do-gold-wash); border-radius:4px; }.result-time { color:var(--do-gold-deep); font-size:15px; }.table-state { display:inline-flex; padding:4px 8px; border-radius:12px; font-size:13px; font-weight:700; }.table-state.success { color:var(--do-success-deep); background:var(--do-success-bg); }.table-state.warning { color:var(--do-warning-deep); background:var(--do-warning-bg); }.table-state.muted { color:var(--do-text-secondary); background:var(--do-bg-sunken); }.push-summary { gap:9px; margin-top:18px; padding:16px; color:var(--do-text-secondary); background:var(--do-bg-sunken); border-radius:8px; }.push-summary.success { color:var(--do-success-deep); background:var(--do-success-bg); }.push-details { display:grid; gap:12px; margin-top:15px; }.push-details div { display:flex; justify-content:space-between; gap:14px; padding-bottom:10px; border-bottom:1px solid var(--do-border-light); }.push-details span { color:var(--do-text-secondary); font-size:13px; }.push-details strong { max-width:65%; color:var(--do-text-primary); font-size:14px; text-align:right; }.push-note { gap:7px; margin-top:15px; padding:10px; color:var(--do-text-secondary); background:var(--do-bg-sunken); border-radius:6px; font-size:13px; }
.device-count { color:var(--do-gold-deep); font-size:13px; font-weight:700; }.device-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:16px; }.device-card { padding:14px; border:1px solid var(--do-border); border-radius:8px; background:var(--do-bg-sunken); cursor:pointer; transition:border-color .2s, box-shadow .2s; }.device-card:hover,.device-card.active { border-color:var(--do-gold); box-shadow:var(--shadow-hover); }.device-role { color:var(--do-gold-deep); font-size:13px; font-weight:700; }.device-card h3 { margin-top:5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.device-no { display:block; margin-top:4px; color:var(--do-text-secondary); font-size:13px; }.device-status { display:inline-flex; align-items:center; gap:5px; flex-shrink:0; padding:4px 8px; border-radius:13px; font-size:13px; font-weight:700; }.device-status i { width:7px; height:7px; border-radius:50%; background:currentColor; }.device-status.online { color:var(--do-success-deep); background:var(--do-success-bg); }.device-status.warning { color:var(--do-warning-deep); background:var(--do-warning-bg); }.device-status.offline { color:var(--do-text-secondary); background:var(--do-bg-card); }.device-location { gap:5px; margin-top:13px; color:var(--do-text-secondary); font-size:13px; }.device-facts { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:14px; }.device-facts div { min-width:0; }.device-facts span { display:block; color:var(--do-text-secondary); font-size:13px; }.device-facts strong { display:block; margin-top:4px; overflow:hidden; font-size:13px; text-overflow:ellipsis; white-space:nowrap; }.device-footer { justify-content:space-between; gap:8px; margin-top:14px; padding-top:10px; border-top:1px solid var(--do-border-light); color:var(--do-text-secondary); font-size:13px; }.device-detail { margin-top:12px; padding:11px; color:var(--do-text-secondary); background:var(--do-bg-card); border-radius:6px; font-size:13px; }.device-detail strong { color:var(--do-text-primary); }.device-detail p { margin-top:5px; line-height:1.5; }.device-detail span { display:block; margin-top:7px; }.frames-list { margin-top:16px; overflow-x:auto; }.frame-row { display:grid; grid-template-columns:145px 145px 150px minmax(220px,1fr) 100px minmax(190px,260px); gap:10px; min-width:950px; padding:10px 8px; border-bottom:1px solid var(--do-border-light); font-size:13px; }.frame-row:first-child { background:var(--do-bg-sunken); border-radius:5px; }.frame-time,.frame-source,.frame-type,.frame-raw { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.frame-source { color:var(--do-gold-deep); font-weight:700; }.frame-type { color:var(--do-text-regular); }.frame-summary { overflow:hidden; color:var(--do-text-secondary); text-overflow:ellipsis; white-space:nowrap; }.frame-check { font-weight:700; }.frame-check.ok { color:var(--do-success-deep); }.frame-check.warning { color:var(--do-warning-deep); }.frame-raw { color:var(--do-text-secondary); }.empty-inline,.empty-state { display:flex; align-items:center; justify-content:center; gap:8px; min-height:90px; color:var(--do-text-secondary); font-size:14px; }.empty-state { flex-direction:column; min-height:140px; }.empty-state .el-icon { font-size:30px; color:var(--do-text-placeholder); }.num-mono { font-family:var(--font-mono,'SFMono-Regular',Consolas,monospace); }
@media (max-width:1300px) { .metric-grid { grid-template-columns:repeat(3,minmax(150px,1fr)); }.device-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.main-read-grid { grid-template-columns:1fr; } }
@media (max-width:800px) { .score-header { align-items:flex-start; flex-direction:column; }.header-read-status { justify-content:flex-start; }.metric-grid,.device-grid { grid-template-columns:1fr; }.timeline-item { grid-template-columns:18px 1fr; gap:9px; }.timeline-time { grid-column:2; }.timeline-main { grid-column:2; }.panel-heading { align-items:flex-start; flex-direction:column; }.event-meta { align-items:flex-start; flex-direction:column; gap:4px; }.push-details div { align-items:flex-start; flex-direction:column; gap:5px; }.push-details strong { max-width:none; text-align:left; } }
</style>
