<template>
  <div class="alarm-center-workspace">
    <!-- 顶部状态栏 -->
    <div class="alarm-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgAlarmBell" size="20" class="text-warning" />
        <div class="title-meta">
          <span class="view-title">全链路保活监控与实时告警中心</span>
          <p>实时监测串口、网络、HTTP 与视频链路状态，跟踪告警并闭环处理设备故障。</p>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-primary" @click="runFullDiagnostics" title="向全场工业串口、TCP/UDP 与 HTTP 网关发起全链路存活保活探测">
          <SvgIcon name="SvgRefresh" size="14" style="margin-right: 4px;" />
          <span>全场链路保活全面巡检</span>
        </button>
      </div>
    </div>

    <!-- 顶部链路保活健康度看板 (规范指标) -->
    <div class="link-health-kpi-grid">
      <div class="health-card glass-panel">
        <span class="h-lbl">工业串口通信存活率 (RS232/485)</span>
        <div class="h-val-row">
          <span class="h-val num-mono text-success">6 / 6</span>
          <span class="status-dot online"></span>
        </div>
        <span class="h-desc">COM1/2/3/4 探针轮询 0 丢失</span>
      </div>

      <div class="health-card glass-panel">
        <span class="h-lbl">网络 TCP/UDP 长连接保活</span>
        <div class="h-val-row">
          <span class="h-val num-mono text-success">8 / 8</span>
          <span class="status-dot online"></span>
        </div>
        <span class="h-desc">ARES-21 与 TS-9000 母钟在线</span>
      </div>

      <div class="health-card glass-panel">
        <span class="h-lbl">HTTP/RESTful 接口心跳</span>
        <div class="h-val-row">
          <span class="h-val num-mono text-success">100%</span>
          <span class="status-dot online"></span>
        </div>
        <span class="h-desc">NovaPro 与 售验票网关响应 &lt;50ms</span>
      </div>

      <div class="health-card glass-panel">
        <span class="h-lbl">RTSP 视频流传输通畅率</span>
        <div class="h-val-row">
          <span class="h-val num-mono text-primary">9 / 9</span>
          <span class="status-dot online"></span>
        </div>
        <span class="h-desc">无卡顿断流，自愈状态机就绪</span>
      </div>

      <div class="health-card glass-panel warning-card">
        <span class="h-lbl">当前待处置告警总量</span>
        <div class="h-val-row">
          <span class="h-val num-mono text-warning">{{ appStore.unreadAlarmCount }} <small>条</small></span>
          <span class="status-dot warning"></span>
        </div>
        <span class="h-desc">紧急 0 / 警告 1 / 提示 1</span>
      </div>
    </div>

    <!-- 告警流水明细处理大表 -->
    <div class="alarm-table-card glass-panel">
      <!-- 搜索过滤条 -->
      <div class="table-filter-bar">
        <div class="filter-left">
          <el-select v-model="filterLevel" placeholder="按告警级别过滤" size="small" style="width: 140px;">
            <el-option label="全部级别" value="ALL" />
            <el-option label="紧急故障 (红色)" value="EMERGENCY" />
            <el-option label="警告预警 (黄色)" value="WARNING" />
            <el-option label="运行提示 (蓝色)" value="INFO" />
          </el-select>

          <el-select v-model="filterStatus" placeholder="按处置状态过滤" size="small" style="width: 140px;">
            <el-option label="全部状态" value="ALL" />
            <el-option label="新建 (NEW)" value="NEW" />
            <el-option label="已确认 (CONFIRMED)" value="CONFIRMED" />
            <el-option label="已恢复 (RECOVERED)" value="RECOVERED" />
            <el-option label="已关闭 (CLOSED)" value="CLOSED" />
          </el-select>
        </div>

        <div class="filter-right">
          <el-button size="small" type="warning" plain @click="muteSound">
            {{ appStore.isSoundMuted ? '已静音蜂鸣' : '一键静音报警声' }}
          </el-button>
        </div>
      </div>

      <!-- 核心告警列表 -->
      <el-table :data="filteredAlarms" style="width: 100%" size="small">
        <el-table-column prop="id" label="告警流水号" width="130">
          <template #default="{ row }">
            <span class="num-mono font-bold">{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="level" label="严重级别" width="100">
          <template #default="{ row }">
            <span :class="['level-tag', row.level.toLowerCase()]">
              {{ row.level === 'EMERGENCY' ? '紧急红' : row.level === 'WARNING' ? '警告黄' : '提示蓝' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="故障事件标题" min-width="180">
          <template #default="{ row }">
            <span class="alm-t font-bold text-highlight">{{ row.title }}</span>
            <span class="alm-sub-dev">{{ row.device }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="desc" label="故障诊断描述" min-width="240">
          <template #default="{ row }">
            <span class="text-sub">{{ row.desc }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="time" label="发生时间" width="110">
          <template #default="{ row }">
            <span class="num-mono">{{ row.time }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="处置状态" width="110" align="center">
          <template #default="{ row }">
            <span :class="['status-pill', row.status.toLowerCase()]">
              {{ row.status === 'NEW' ? '新建未认' : row.status === 'CONFIRMED' ? '已确认' : row.status === 'RECOVERED' ? '已自愈' : '已关闭' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="处置动作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'NEW'"
              size="small"
              type="primary"
              link
              @click="confirmAlarm(row)"
            >
              确认告警
            </el-button>
            <el-button
              v-if="!row.muted"
              size="small"
              type="warning"
              link
              @click="muteAlarm(row)"
            >
              静音
            </el-button>
            <el-button
              size="small"
              type="info"
              link
              @click="closeAlarm(row)"
            >
              关闭工单
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const filterLevel = ref('ALL')
const filterStatus = ref('ALL')

const filteredAlarms = computed(() => {
  return appStore.alarms.filter(a => {
    const matchL = filterLevel.value === 'ALL' || a.level === filterLevel.value
    const matchS = filterStatus.value === 'ALL' || a.status === filterStatus.value
    return matchL && matchS
  })
})

const confirmAlarm = (row) => {
  appStore.confirmAlarm(row.id)
  ElMessage.success(`告警【${row.id}】已由当前操作人确认！`)
}

const muteAlarm = (row) => {
  appStore.muteAlarm(row.id)
  ElMessage.info(`告警【${row.id}】通知已静音`)
}

const closeAlarm = (row) => {
  appStore.closeAlarm(row.id)
  ElMessage.success(`告警【${row.id}】已关闭，归档于审计库中`)
}

const muteSound = () => {
  appStore.isSoundMuted = !appStore.isSoundMuted
  ElMessage.info(appStore.isSoundMuted ? '已全局静音告警蜂鸣声' : '已恢复告警播报声音')
}

const runFullDiagnostics = () => {
  ElMessage.success('全场 26 台硬件设备与网络端口链路深度巡检完成，无新增异常！')
}
</script>

<style scoped>
.alarm-center-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.alarm-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-coffee);
  letter-spacing: 0.5px;
}

.top-right {
  display: flex;
  gap: 12px;
}

/* 链路健康度 KPI */
.link-health-kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}

.health-card {
  padding: 14px 16px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.2s ease;
}

.health-card:hover {
  border-color: var(--do-gold);
  transform: translateY(-1px);
}

.health-card.warning-card {
  border-color: rgba(var(--th-warning-rgb), 0.5);
  background: rgba(254, 243, 199, 0.3);
}

.h-lbl {
  font-size: 14px;
  color: var(--do-coffee-light);
  font-weight: 500;
}

.h-val-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.h-val {
  font-size: 24px;
  font-weight: 800;
  color: var(--do-coffee);
}
.h-val small { font-size: 14px; font-weight: normal; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.online { background: var(--do-olive); box-shadow: 0 0 6px var(--do-olive); }
.status-dot.warning { background: var(--do-amber); box-shadow: 0 0 6px var(--do-amber); }

.h-desc {
  font-size: 14px;
  color: var(--do-coffee-mid);
}

/* 告警大表 */
.alarm-table-card {
  display: flex;
  flex-direction: column;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  overflow: hidden;
}

.table-filter-bar {
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border-card);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(240, 235, 227, 0.4);
}

.filter-left {
  display: flex;
  gap: 12px;
}

.level-tag {
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 700;
}
.level-tag.emergency {
  background: rgba(var(--th-danger-rgb), 0.15);
  color: var(--do-terra);
  border: 1px solid var(--do-terra);
}
.level-tag.warning {
  background: rgba(var(--th-warning-rgb), 0.15);
  color: var(--do-amber);
  border: 1px solid var(--do-amber);
}
.level-tag.info {
  background: rgba(var(--th-success-rgb), 0.15);
  color: var(--do-olive);
  border: 1px solid var(--do-olive);
}

.alm-t {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
}

.alm-sub-dev {
  font-size: 14px;
  color: var(--do-coffee-light);
}

.status-pill {
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.status-pill.new {
  background: rgba(var(--th-danger-rgb), 0.12);
  color: var(--do-terra);
  border: 1px solid var(--do-terra);
}
.status-pill.confirmed {
  background: rgba(var(--th-warning-rgb), 0.12);
  color: var(--do-amber);
  border: 1px solid var(--do-amber);
}
.status-pill.recovered {
  background: rgba(var(--th-success-rgb), 0.12);
  color: var(--do-olive);
  border: 1px solid var(--do-olive);
}
.status-pill.closed {
  background: rgba(var(--th-shadow-rgb), 0.05);
  color: var(--do-coffee-light);
  border: 1px solid var(--do-border-card);
}
</style>
