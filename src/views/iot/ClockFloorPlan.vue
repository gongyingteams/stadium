<template>
  <div class="floorplan-workspace">
    <!-- 顶部栏 -->
    <section class="fp-header glass-panel">
      <div class="fp-heading">
        <button class="btn-back" @click="goBack" title="返回标准时钟监测台">
          ← 返回监测台
        </button>
        <div class="fp-title-wrap">
          <h1>子钟场馆 SVG 平面图点位标注</h1>
          <p>支持上传场馆 SVG 平面图，将全部子钟拖拽安放至平面图对应位置（坐标自动限制在图幅内）</p>
        </div>
      </div>

      <div class="fp-actions">
        <div class="fp-stat-pill ok">
          <span class="dot"></span>
          <span>正常 {{ normalCount }}</span>
        </div>
        <div class="fp-stat-pill fault">
          <span class="dot"></span>
          <span>故障/离线 {{ faultCount }}</span>
        </div>
        <div class="fp-stat-pill info">
          <span>已安放 {{ placedCount }}/{{ subClocks.length }}</span>
        </div>
        <div v-if="!isAdmin" class="fp-stat-pill readonly">
          <span>只读预览（仅 admin 可拖拽编辑布局）</span>
        </div>

        <button class="btn-fp" @click="fetchSubClocks" :disabled="loading">
          {{ loading ? '刷新中...' : '刷新子钟' }}
        </button>
        <template v-if="isAdmin">
          <label class="btn-fp btn-upload" title="上传自定义 SVG 格式平面图作为背景">
            <input type="file" accept=".svg,image/svg+xml" class="hidden-file" @change="handleSvgUpload" />
            <span>上传 SVG 平面图</span>
          </label>
          <button v-if="customSvgDataUrl" class="btn-fp" @click="resetDefaultSvg" title="恢复内置默认体育场馆 SVG 平面图">
            恢复默认图
          </button>
          <button class="btn-fp" @click="autoPlaceRemaining" :disabled="unplacedClocks.length === 0">
            一键安放未放置 ({{ unplacedClocks.length }})
          </button>
          <button class="btn-fp btn-danger-outline" @click="clearAllPlacements" :disabled="placedCount === 0">
            清空点位
          </button>
        </template>
      </div>
    </section>

    <!-- 主工作区：左侧子钟清单 + 右侧 SVG 平面图画布 -->
    <section class="fp-main">
      <!-- 左侧：全部子钟列表（支持拖入平面图） -->
      <aside class="fp-sidebar glass-panel">
        <div class="sidebar-head">
          <div class="sidebar-title">子钟台账列表 ({{ filteredClocks.length }})</div>
          <el-input
            v-model="searchKw"
            size="small"
            placeholder="搜索 #MAC / 房间 / 状态"
            clearable
          />
          <div v-if="mysqlError" class="sidebar-warn">{{ mysqlError }}（当前优先显示最近缓存台账）</div>
          <div class="sidebar-tip">
            {{ isAdmin ? '拖动下方任意子钟到右侧 SVG 平面图上即可安放；已安放子钟可在图上继续拖动微调。' : '当前为非 admin 账号，仅可查看子钟点位与状态（悬浮或点击图标查看详情）。' }}
          </div>
        </div>

        <div class="clock-pool-scroll">
          <div
            v-for="clk in filteredClocks"
            :key="clk.mac"
            class="pool-clock-item"
            :class="[
              isNormal(clk) ? 'is-normal' : 'is-fault',
              { 'is-placed': !!placements[clk.mac], 'is-selected': selectedMac === clk.mac, 'is-readonly': !isAdmin }
            ]"
            :draggable="isAdmin"
            @dragstart="onListDragStart($event, clk)"
            @click="selectClock(clk)"
          >
            <div class="pool-row-top">
              <span class="status-led" :class="isNormal(clk) ? 'ok' : 'err'"></span>
              <span class="pool-mac num-mono">#{{ clk.mac }}</span>
              <span class="pool-room">{{ clk.room || '未命名区域' }}</span>
              <span class="pool-placed-tag" v-if="placements[clk.mac]">已安放</span>
              <span class="pool-unplaced-tag" v-else>未安放</span>
            </div>
            <div class="pool-row-sub">
              <span>{{ clk.build || '--' }}栋 {{ clk.floor || '--' }}层 · {{ clk.model }}</span>
              <span :class="isNormal(clk) ? 'txt-ok' : 'txt-err'">{{ clk.status || '离线' }}</span>
            </div>
          </div>

          <div v-if="loading && subClocks.length === 0" class="pool-empty">正在读取子钟台账...</div>
          <div v-else-if="filteredClocks.length === 0" class="pool-empty">暂无匹配的子钟记录</div>
        </div>
      </aside>

      <!-- 右侧：SVG 场景平面图画布 -->
      <div class="fp-canvas-panel glass-panel">
        <div class="canvas-toolbar">
          <span class="toolbar-info">
            当前平面图：<strong>{{ customSvgName || '内置体育场馆标准平面图 (SVG)' }}</strong>
          </span>
          <div class="legend-group">
            <span class="legend-item"><i class="lg-dot ok"></i> 状态正常（绿色）</span>
            <span class="legend-item"><i class="lg-dot err"></i> 故障 / 离线（红色告警）</span>
          </div>
        </div>

        <div class="canvas-stage-scroll">
          <!-- 图片容器：所有拖拽点位严格约束在此容器边界内 -->
          <div
            ref="mapBoxRef"
            class="svg-map-box"
            @dragover.prevent
            @drop="onCanvasDrop"
          >
            <!-- 背景 SVG：优先显示用户上传的 SVG，否则使用已绘制的场馆 SVG 底图 -->
            <img
              :src="customSvgDataUrl || '/venue-clock-floorplan.svg'"
              class="svg-bg-img"
              alt="场馆 SVG 平面图"
              draggable="false"
            />

            <!-- 已安放在 SVG 图片上的子钟标注点（圆形钟表图标 + 悬浮详情卡片） -->
            <div
              v-for="clk in placedClocks"
              :key="clk.mac"
              class="clock-pin"
              :class="[
                isNormal(clk) ? 'pin-normal' : 'pin-fault',
                {
                  'is-selected': selectedMac === clk.mac,
                  'is-dragging': draggingMac === clk.mac,
                  'is-readonly': !isAdmin,
                  'tip-bottom': (placements[clk.mac]?.yPct ?? 50) < 22
                }
              ]"
              :style="getPinStyle(clk.mac)"
              @pointerdown="onPinPointerDown($event, clk)"
              @click.stop="selectClock(clk)"
            >
              <span class="pin-pulse" v-if="isNormal(clk)"></span>
              <span class="pin-clock-circle">
                <svg class="pin-clock-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="9" />
                  <polyline points="12 7 12 12 15.5 14" />
                </svg>
              </span>
              <span class="pin-mac-badge num-mono">#{{ clk.mac }}</span>

              <!-- 鼠标悬浮时显示子钟名称、编号、状态等信息 -->
              <div class="pin-hover-card">
                <div class="hover-head">
                  <span class="hover-mac num-mono">#{{ clk.mac }}</span>
                  <span class="hover-room">{{ clk.room || '未命名区域' }}</span>
                  <span class="hover-status" :class="isNormal(clk) ? 'ok' : 'err'">{{ clk.status || '离线' }}</span>
                </div>
                <div class="hover-meta">
                  <span>{{ clk.build || '--' }}栋 {{ clk.floor || '--' }}层 · {{ clk.model }}</span>
                  <span class="num-mono">亮度 {{ clk.bright }}档 · 音量 {{ clk.volume === 0 ? '静音' : `${clk.volume}档` }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部选中子钟详情条 -->
        <div v-if="selectedClock" class="selected-detail-bar">
          <div class="detail-left">
            <span class="status-led" :class="isNormal(selectedClock) ? 'ok' : 'err'"></span>
            <strong class="num-mono">#{{ selectedClock.mac }}</strong>
            <span>{{ selectedClock.room }}</span>
            <span class="detail-meta">{{ selectedClock.build || '--' }}栋 {{ selectedClock.floor || '--' }}层 · {{ selectedClock.model }}</span>
            <span class="detail-meta" :class="isNormal(selectedClock) ? 'txt-ok' : 'txt-err'">
              状态：{{ selectedClock.status || '离线' }}
            </span>
            <span class="detail-meta num-mono" v-if="placements[selectedClock.mac]">
              坐标：({{ placements[selectedClock.mac].xPct.toFixed(1) }}%, {{ placements[selectedClock.mac].yPct.toFixed(1) }}%)
            </span>
          </div>
          <div class="detail-right">
            <el-button
              v-if="isAdmin && placements[selectedClock.mac]"
              size="small"
              type="danger"
              plain
              @click="removePlacement(selectedClock.mac)"
            >
              从平面图移除
            </el-button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/services/api'
import { useUserStore } from '@/stores/user'

const PLACEMENTS_STORAGE_KEY = 'clock_floorplan_placements_v1'
const CUSTOM_SVG_STORAGE_KEY = 'clock_floorplan_custom_svg_v1'
const CLOCK_CACHE_KEY = 'stadium_clock_last_real_cache_v1'

const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)
const mapBoxRef = ref(null)

const loading = ref(false)
const mysqlError = ref('')
const subClocks = ref([])
const searchKw = ref('')
const selectedMac = ref(null)
const draggingMac = ref(null)

// { [mac]: { xPct: number, yPct: number } }
const placements = ref({})
const customSvgDataUrl = ref('')
const customSvgName = ref('')

let refreshTimer = null

const isNormal = (clk) => (clk?.status || '').trim() === '正常'

const loadLocalState = () => {
  try {
    const rawPos = localStorage.getItem(PLACEMENTS_STORAGE_KEY)
    if (rawPos) placements.value = JSON.parse(rawPos) || {}
  } catch { /* ignore */ }
  try {
    const rawSvg = localStorage.getItem(CUSTOM_SVG_STORAGE_KEY)
    if (rawSvg) {
      const parsed = JSON.parse(rawSvg)
      customSvgDataUrl.value = parsed.dataUrl || ''
      customSvgName.value = parsed.name || ''
    }
  } catch { /* ignore */ }
}

const savePlacements = () => {
  if (!isAdmin.value) return
  try {
    localStorage.setItem(PLACEMENTS_STORAGE_KEY, JSON.stringify(placements.value))
  } catch { /* ignore */ }
}

const loadCachedSubClocks = () => {
  try {
    const raw = localStorage.getItem(CLOCK_CACHE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed?.items)) {
      return parsed.items.map(c => ({ ...c, status: '离线', faultReason: '台账缓存（当前离线）' }))
    }
  } catch { /* ignore */ }
  return []
}

const saveCachedSubClocks = (items) => {
  try {
    localStorage.setItem(CLOCK_CACHE_KEY, JSON.stringify({ items, cachedAt: Date.now() }))
  } catch { /* ignore */ }
}

const fetchSubClocks = async () => {
  loading.value = true
  try {
    const res = await api.clockSubclocks()
    if (res && res.online && Array.isArray(res.items)) {
      mysqlError.value = ''
      subClocks.value = res.items
      saveCachedSubClocks(res.items)
    } else {
      mysqlError.value = res?.error || (!res?.configured ? '尚未配置 MySQL 台账' : 'MySQL 暂时不可达')
      const cached = (res?.items && res.items.length) ? res.items : loadCachedSubClocks()
      if (cached.length) {
        subClocks.value = cached
      }
    }
    if (!selectedMac.value && subClocks.value.length) {
      selectedMac.value = subClocks.value[0].mac
    }
  } catch (e) {
    mysqlError.value = e?.message || '台账加载失败'
    const cached = loadCachedSubClocks()
    if (cached.length && subClocks.value.length === 0) {
      subClocks.value = cached
    }
  } finally {
    loading.value = false
  }
}

const filteredClocks = computed(() => {
  const kw = searchKw.value.trim().toLowerCase()
  if (!kw) return subClocks.value
  return subClocks.value.filter(c =>
    String(c.mac).includes(kw) ||
    (c.room || '').toLowerCase().includes(kw) ||
    (c.status || '').toLowerCase().includes(kw) ||
    (c.model || '').toLowerCase().includes(kw)
  )
})

const placedClocks = computed(() => subClocks.value.filter(c => !!placements.value[c.mac]))
const unplacedClocks = computed(() => subClocks.value.filter(c => !placements.value[c.mac]))
const placedCount = computed(() => placedClocks.value.length)
const normalCount = computed(() => subClocks.value.filter(isNormal).length)
const faultCount = computed(() => subClocks.value.length - normalCount.value)
const selectedClock = computed(() => subClocks.value.find(c => c.mac === selectedMac.value) || null)

const clampPct = (xPct, yPct) => {
  // 严格限制在图片内部边界内（留出标注胶囊边缘安全距，确保不超出 SVG 图片外）
  const box = mapBoxRef.value
  let minX = 3
  let maxX = 95
  let minY = 4
  let maxY = 96
  if (box && box.clientWidth > 0 && box.clientHeight > 0) {
    const padX = Math.min(12, (24 / box.clientWidth) * 100)
    const padY = Math.min(12, (18 / box.clientHeight) * 100)
    minX = padX
    maxX = 100 - padX
    minY = padY
    maxY = 100 - padY
  }
  return {
    xPct: Math.min(Math.max(xPct, minX), maxX),
    yPct: Math.min(Math.max(yPct, minY), maxY),
  }
}

const getPinStyle = (mac) => {
  const pos = placements.value[mac]
  if (!pos) return {}
  return {
    left: `${pos.xPct}%`,
    top: `${pos.yPct}%`,
  }
}

// 从左侧列表拖放到 SVG 平面图
const onListDragStart = (event, clk) => {
  if (!isAdmin.value) {
    event.preventDefault()
    return
  }
  event.dataTransfer.setData('text/plain', String(clk.mac))
  event.dataTransfer.effectAllowed = 'move'
  selectedMac.value = clk.mac
}

const onCanvasDrop = (event) => {
  if (!isAdmin.value) return
  const macStr = event.dataTransfer.getData('text/plain')
  const mac = Number(macStr)
  if (!mac || !mapBoxRef.value) return
  const rect = mapBoxRef.value.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) return

  const rawXPct = ((event.clientX - rect.left) / rect.width) * 100
  const rawYPct = ((event.clientY - rect.top) / rect.height) * 100
  placements.value = {
    ...placements.value,
    [mac]: clampPct(rawXPct, rawYPct),
  }
  selectedMac.value = mac
  savePlacements()
}

// 在 SVG 平面图内部直接鼠标拖拽已安放的子钟点位（严格限制不能拖出图片外）
const onPinPointerDown = (event, clk) => {
  if (event.button !== 0 || !mapBoxRef.value) return
  selectedMac.value = clk.mac
  if (!isAdmin.value) return
  event.preventDefault()
  draggingMac.value = clk.mac

  const rect = mapBoxRef.value.getBoundingClientRect()
  const moveHandler = (ev) => {
    if (!rect.width || !rect.height) return
    const rawXPct = ((ev.clientX - rect.left) / rect.width) * 100
    const rawYPct = ((ev.clientY - rect.top) / rect.height) * 100
    placements.value = {
      ...placements.value,
      [clk.mac]: clampPct(rawXPct, rawYPct),
    }
  }
  const upHandler = () => {
    draggingMac.value = null
    savePlacements()
    window.removeEventListener('pointermove', moveHandler)
    window.removeEventListener('pointerup', upHandler)
  }

  window.addEventListener('pointermove', moveHandler)
  window.addEventListener('pointerup', upHandler)
}

const selectClock = (clk) => {
  selectedMac.value = clk.mac
}

const removePlacement = (mac) => {
  if (!isAdmin.value) return
  const next = { ...placements.value }
  delete next[mac]
  placements.value = next
  savePlacements()
}

const clearAllPlacements = () => {
  if (!isAdmin.value) return
  placements.value = {}
  savePlacements()
  ElMessage.info('已清空平面图上的全部子钟点位')
}

const autoPlaceRemaining = () => {
  if (!isAdmin.value) return
  const rem = unplacedClocks.value
  if (!rem.length) return
  const next = { ...placements.value }
  const cols = Math.min(5, Math.max(3, Math.ceil(Math.sqrt(rem.length))))
  rem.forEach((clk, idx) => {
    const col = idx % cols
    const row = Math.floor(idx / cols)
    const xPct = 14 + (col / Math.max(cols - 1, 1)) * 72
    const yPct = 18 + (row * 16) % 68
    next[clk.mac] = clampPct(xPct, yPct)
  })
  placements.value = next
  savePlacements()
  ElMessage.success(`已自动安放 ${rem.length} 台子钟，可继续在图上拖拽微调`)
}

const handleSvgUpload = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.svg') && file.type !== 'image/svg+xml') {
    ElMessage.warning('请选择 .svg 格式的场景平面图文件')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    const dataUrl = String(reader.result || '')
    customSvgDataUrl.value = dataUrl
    customSvgName.value = file.name
    try {
      localStorage.setItem(CUSTOM_SVG_STORAGE_KEY, JSON.stringify({ dataUrl, name: file.name }))
    } catch {
      ElMessage.warning('SVG 文件较大，仅本次会话生效')
    }
    ElMessage.success(`已加载自定义 SVG 平面图：${file.name}`)
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

const resetDefaultSvg = () => {
  customSvgDataUrl.value = ''
  customSvgName.value = ''
  try {
    localStorage.removeItem(CUSTOM_SVG_STORAGE_KEY)
  } catch { /* ignore */ }
  ElMessage.info('已恢复内置体育场馆 SVG 平面图')
}

const goBack = () => {
  router.push('/iot/clock')
}

onMounted(() => {
  loadLocalState()
  fetchSubClocks()
  refreshTimer = setInterval(fetchSubClocks, 15000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.floorplan-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
  color: var(--do-text-primary);
}

.glass-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 10px;
  box-shadow: var(--shadow-sm);
}

.fp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  flex-wrap: wrap;
}

.fp-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.btn-back {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid var(--do-border);
  background: var(--do-bg-sunken);
  color: var(--do-text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.btn-back:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.fp-title-wrap h1 {
  margin: 0;
  font-size: 19px;
  line-height: 1.3;
}
.fp-title-wrap p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--do-text-secondary);
}

.fp-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.fp-stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid var(--do-border);
  background: var(--do-bg-sunken);
}
.fp-stat-pill .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.fp-stat-pill.ok .dot { background: #16a34a; }
.fp-stat-pill.fault .dot { background: #dc2626; }
.fp-stat-pill.readonly { color: #b45309; background: #fffbeb; border-color: #fde68a; }

.btn-fp {
  padding: 7px 12px;
  border-radius: 7px;
  border: 1px solid var(--do-border);
  background: var(--do-bg-card);
  color: var(--do-text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.btn-fp:hover:not(:disabled) {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}
.btn-fp:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn-upload {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #fff;
}
.btn-upload:hover {
  opacity: 0.92;
  color: #fff;
}
.btn-danger-outline {
  color: #dc2626;
  border-color: #fecaca;
}
.hidden-file {
  display: none;
}

.fp-main {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
  min-height: 640px;
}

.fp-sidebar {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 760px;
}
.sidebar-head {
  padding: 14px;
  border-bottom: 1px solid var(--do-border-light);
  background: var(--do-bg-sunken);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sidebar-title {
  font-size: 14px;
  font-weight: 700;
}
.sidebar-tip {
  font-size: 12px;
  color: var(--do-text-secondary);
  line-height: 1.45;
}
.sidebar-warn {
  font-size: 12px;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 5px 8px;
  line-height: 1.4;
}

.clock-pool-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pool-clock-item {
  padding: 9px 11px;
  border-radius: 8px;
  border: 1px solid var(--do-border);
  background: var(--do-bg-card);
  cursor: grab;
  transition: border-color 0.2s, box-shadow 0.2s;
  user-select: none;
}
.pool-clock-item:hover {
  border-color: var(--do-gold);
  box-shadow: var(--shadow-sm);
}
.pool-clock-item.is-selected {
  border-color: var(--do-gold);
  box-shadow: 0 0 0 2px rgba(var(--th-accent-rgb), 0.16);
}
.pool-clock-item.is-fault {
  border-left: 3px solid #dc2626;
}
.pool-clock-item.is-normal {
  border-left: 3px solid #16a34a;
}

.pool-row-top {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-led {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-led.ok {
  background: #16a34a;
  box-shadow: 0 0 6px rgba(22, 163, 74, 0.7);
}
.status-led.err {
  background: #dc2626;
  box-shadow: 0 0 6px rgba(220, 38, 38, 0.7);
}
.pool-mac {
  font-size: 12.5px;
  font-weight: 700;
}
.pool-room {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
}
.pool-placed-tag,
.pool-unplaced-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}
.pool-placed-tag {
  background: #dcfce7;
  color: #15803d;
}
.pool-unplaced-tag {
  background: #f1f5f9;
  color: #64748b;
}
.pool-row-sub {
  margin-top: 4px;
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--do-text-secondary);
}
.txt-ok { color: #16a34a; font-weight: 600; }
.txt-err { color: #dc2626; font-weight: 600; }
.pool-empty {
  text-align: center;
  padding: 24px 12px;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.fp-canvas-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.canvas-toolbar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--do-border-light);
  background: var(--do-bg-sunken);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
}
.legend-group {
  display: flex;
  align-items: center;
  gap: 14px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
}
.lg-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.lg-dot.ok { background: #16a34a; }
.lg-dot.err { background: #dc2626; }

.canvas-stage-scroll {
  flex: 1;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  overflow: auto;
}

.svg-map-box {
  position: relative;
  display: inline-block;
  width: 100%;
  max-width: 1120px;
  border-radius: 8px;
  overflow: visible;
  border: 1px solid #cbd5e1;
  background: #fff;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.08);
  user-select: none;
}

.svg-bg-builtin,
.svg-bg-img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 8px;
  pointer-events: none;
}

/* 平面图上的子钟标注点（圆形钟表图标 + 悬浮详情卡片） */
.clock-pin {
  position: absolute;
  transform: translate(-50%, -50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  cursor: grab;
  transition: transform 0.14s ease, box-shadow 0.15s ease;
  z-index: 2;
}
.pool-clock-item.is-readonly,
.clock-pin.is-readonly {
  cursor: pointer;
}

.clock-pin:hover {
  z-index: 20;
  transform: translate(-50%, -50%) scale(1.1);
}
.clock-pin:active,
.clock-pin.is-dragging {
  cursor: grabbing;
  transform: translate(-50%, -50%) scale(1.12);
  z-index: 25;
}
.clock-pin.is-selected {
  z-index: 12;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.35);
}

.pin-clock-circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.28);
  border: 2.5px solid #ffffff;
}
.pin-clock-svg {
  width: 21px;
  height: 21px;
}

.clock-pin.pin-normal .pin-clock-circle {
  background: #16a34a;
  color: #ffffff;
}
.clock-pin.pin-fault .pin-clock-circle {
  background: #dc2626;
  color: #ffffff;
}

.pin-mac-badge {
  position: absolute;
  bottom: -6px;
  right: -8px;
  padding: 1px 5px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.2;
  background: #0f172a;
  color: #ffffff;
  border: 1.5px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  pointer-events: none;
}

.pin-pulse {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(22, 163, 74, 0.45);
  animation: pinPulse 1.9s infinite;
  pointer-events: none;
}
@keyframes pinPulse {
  0% { transform: scale(1); opacity: 0.85; }
  100% { transform: scale(1.75); opacity: 0; }
}

/* 悬浮信息卡片 */
.pin-hover-card {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 10px);
  transform: translateX(-50%);
  min-width: 200px;
  max-width: 260px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.94);
  color: #f8fafc;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.32);
  border: 1px solid rgba(255, 255, 255, 0.14);
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s ease, visibility 0.15s ease;
  white-space: nowrap;
  z-index: 30;
}
.clock-pin.tip-bottom .pin-hover-card {
  bottom: auto;
  top: calc(100% + 10px);
}
.clock-pin:hover .pin-hover-card {
  opacity: 1;
  visibility: visible;
}
.clock-pin.is-dragging .pin-hover-card {
  opacity: 0;
  visibility: hidden;
}

.hover-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 700;
  margin-bottom: 4px;
}
.hover-mac {
  color: #93c5fd;
}
.hover-room {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hover-status {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.hover-status.ok {
  background: rgba(22, 163, 74, 0.25);
  color: #4ade80;
}
.hover-status.err {
  background: rgba(220, 38, 38, 0.28);
  color: #fca5a5;
}
.hover-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11.5px;
  color: #cbd5e1;
}

.selected-detail-bar {
  padding: 10px 16px;
  border-top: 1px solid var(--do-border-light);
  background: var(--do-bg-card);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.detail-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 13px;
}
.detail-meta {
  color: var(--do-text-secondary);
}

.num-mono {
  font-family: var(--font-family-mono, 'SF Mono', Consolas, monospace);
}

@media (max-width: 1024px) {
  .fp-main {
    grid-template-columns: 1fr;
  }
  .fp-sidebar {
    max-height: 280px;
  }
}
</style>
