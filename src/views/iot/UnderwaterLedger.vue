<template>
  <div class="underwater-ledger-page">
    <!-- 顶部栏 -->
    <section class="ledger-header glass-panel">
      <div class="ledger-heading">
        <button class="btn-back" @click="$router.push('/iot/video')">← 返回视频监控台</button>
        <div>
          <h1>现场影像采集识别系统 · 数据库台账与实时报警监测</h1>
          <p>数据源：192.168.0.33:3306 / image_platform（展示全部库表字段 · 定时轮询新增报警并弹窗预警）</p>
        </div>
      </div>

      <div class="ledger-actions">
        <div class="status-pill" :class="dbOnline ? 'online' : 'offline'">
          <span class="dot"></span>
          <span>{{ dbOnline ? 'MySQL 已连接' : (dbError || '连接数据库失败') }}</span>
        </div>

        <div class="poll-control">
          <span class="poll-lbl">轮询间隔：</span>
          <el-select v-model="pollSeconds" size="small" style="width: 88px;" @change="restartPolling">
            <el-option label="5 秒" :value="5" />
            <el-option label="10 秒" :value="10" />
            <el-option label="30 秒" :value="30" />
          </el-select>
        </div>

        <span v-if="lastSyncTime" class="last-sync num-mono">上次刷新：{{ lastSyncTime }}</span>
        <el-button type="primary" size="small" :loading="loading" @click="fetchLedger(false)">
          立即刷新
        </el-button>
      </div>
    </section>

    <!-- 摘要指标卡 -->
    <section class="ledger-kpis">
      <div class="kpi-card glass-panel">
        <span>现场摄像机 (tb_camera)</span>
        <strong class="num-mono">{{ cameras.length }} 台</strong>
        <em>启用中 {{ cameras.filter(c => c.state === 1).length }} 台 · 停用 {{ cameras.filter(c => c.state !== 1).length }} 台</em>
      </div>
      <div class="kpi-card glass-panel">
        <span>报警历史总计 (tb_alert_history)</span>
        <strong class="num-mono">{{ alertTotal }} 条</strong>
        <em>当前展示最新 {{ alerts.length }} 条 · 最新 ID #{{ latestAlertId || '--' }}</em>
      </div>
      <div class="kpi-card glass-panel">
        <span>识别算法参数 (tb_alert_settings)</span>
        <strong class="num-mono">{{ settings.length }} 项</strong>
        <em>像素阈值 / 分辨率 / 帧率配置</em>
      </div>
      <div class="kpi-card glass-panel">
        <span>联动推送外设 (tb_device)</span>
        <strong class="num-mono">{{ devices.length }} 台</strong>
        <em>手表 / 声光报警 / 平板终端</em>
      </div>
    </section>

    <!-- 数据表 Tabs（展示全部字段） -->
    <section class="ledger-body glass-panel">
      <el-tabs v-model="activeTab" class="ledger-tabs">
        <!-- Tab 1: tb_camera -->
        <el-tab-pane :label="`摄像机台账 tb_camera (${cameras.length})`" name="cameras">
          <el-table :data="cameras" border stripe size="small" max-height="560" style="width: 100%">
            <el-table-column prop="id" label="id" width="75" fixed />
            <el-table-column prop="name" label="name" width="75" fixed />
            <el-table-column prop="ip" label="ip" width="130" />
            <el-table-column prop="port" label="port" width="70" />
            <el-table-column prop="state" label="state" width="85">
              <template #default="{ row }">
                <el-tag :type="row.state === 1 ? 'success' : 'info'" size="small">
                  {{ row.state === 1 ? '1 (启用)' : `${row.state} (停用)` }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="group" label="group" width="95" />
            <el-table-column prop="row" label="row" width="60" />
            <el-table-column prop="col" label="col" width="60" />
            <el-table-column prop="hik_user" label="hik_user" width="90" />
            <el-table-column prop="hik_password" label="hik_password" width="110" />
            <el-table-column prop="version" label="version" width="75" />
            <el-table-column prop="bind_device" label="bind_device" width="105" />
            <el-table-column prop="calibrated" label="calibrated" width="90" />
            <el-table-column prop="crop_top" label="crop_top" width="85" />
            <el-table-column prop="crop_bottom" label="crop_bottom" width="100" />
            <el-table-column prop="crop_left" label="crop_left" width="85" />
            <el-table-column prop="crop_right" label="crop_right" width="90" />
            <el-table-column prop="channel" label="channel" width="80" />
            <el-table-column prop="dist" label="dist" width="80" />
            <el-table-column prop="frame_rate" label="frame_rate" width="95" />
            <el-table-column prop="mtx" label="mtx" width="100" show-overflow-tooltip />
            <el-table-column prop="create_time" label="create_time" width="160" />
            <el-table-column prop="created_by" label="created_by" width="95" />
            <el-table-column prop="update_time" label="update_time" width="160" />
            <el-table-column prop="updated_by" label="updated_by" width="95" />
          </el-table>
        </el-tab-pane>

        <!-- Tab 2: tb_alert_history -->
        <el-tab-pane :label="`报警历史 tb_alert_history (${alertTotal})`" name="alerts">
          <el-table :data="alerts" border stripe size="small" max-height="560" style="width: 100%">
            <el-table-column prop="id" label="id" width="80" fixed />
            <el-table-column prop="title" label="title" width="150" />
            <el-table-column prop="content" label="content" min-width="220" show-overflow-tooltip />
            <el-table-column prop="camera_id" label="camera_id" width="95" />
            <el-table-column prop="camera_group" label="camera_group" width="115" />
            <el-table-column prop="push_devices" label="push_devices" width="145" />
            <el-table-column prop="state" label="state" width="75" />
            <el-table-column prop="push_success" label="push_success" width="105" />
            <el-table-column prop="create_time" label="create_time" width="165" />
            <el-table-column prop="created_by" label="created_by" width="95" />
            <el-table-column prop="update_time" label="update_time" width="165" />
            <el-table-column prop="updated_by" label="updated_by" width="95" />
            <el-table-column label="image (抓拍原图)" width="130" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.has_image"
                  size="small"
                  type="primary"
                  link
                  @click="previewAlertImage(row)"
                >
                  查看抓拍图
                </el-button>
                <span v-else class="txt-muted">无图片</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab 3: tb_alert_settings -->
        <el-tab-pane :label="`识别参数 tb_alert_settings (${settings.length})`" name="settings">
          <el-table :data="settings" border stripe size="small" max-height="560" style="width: 100%">
            <el-table-column prop="id" label="id" width="80" />
            <el-table-column prop="key" label="key" width="200" />
            <el-table-column prop="value" label="value" width="180" />
            <el-table-column prop="desc" label="desc" min-width="180" />
            <el-table-column prop="state" label="state" width="80" />
            <el-table-column prop="create_time" label="create_time" width="165" />
            <el-table-column prop="created_by" label="created_by" width="95" />
            <el-table-column prop="update_time" label="update_time" width="165" />
            <el-table-column prop="updated_by" label="updated_by" width="95" />
          </el-table>
        </el-tab-pane>

        <!-- Tab 4: tb_device -->
        <el-tab-pane :label="`联动外设 tb_device (${devices.length})`" name="devices">
          <el-table :data="devices" border stripe size="small" max-height="560" style="width: 100%">
            <el-table-column prop="id" label="id" width="85" />
            <el-table-column prop="name" label="name" width="140" />
            <el-table-column prop="ip" label="ip" width="150" />
            <el-table-column prop="port" label="port" width="110" />
            <el-table-column prop="type" label="type" width="80" />
            <el-table-column prop="state" label="state" width="85">
              <template #default="{ row }">
                <el-tag :type="row.state === 1 ? 'success' : 'info'" size="small">{{ row.state }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="create_time" width="165" />
            <el-table-column prop="created_by" label="created_by" width="95" />
            <el-table-column prop="update_time" label="update_time" width="165" />
            <el-table-column prop="updated_by" label="updated_by" width="95" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- 新增报警预警弹窗 -->
    <el-dialog
      v-model="alertDialogVisible"
      :title="alertDialogTitle"
      width="680px"
      destroy-on-close
    >
      <div v-if="activeAlert" class="alert-modal-body">
        <div class="alert-banner">
          <div class="alert-title">{{ activeAlert.title }}</div>
          <div class="alert-content">{{ activeAlert.content }}</div>
          <div class="alert-meta num-mono">
            <span>报警 ID：#{{ activeAlert.id }}</span>
            <span>摄像机 ID：{{ activeAlert.camera_id }}</span>
            <span>分组：{{ activeAlert.camera_group || '--' }}</span>
            <span>时间：{{ activeAlert.create_time }}</span>
          </div>
        </div>
        <div class="alert-img-box">
          <div v-if="loadingImage" class="img-loading">正在加载抓拍原图...</div>
          <img v-else-if="previewImageUrl" :src="previewImageUrl" class="alert-snapshot-img" alt="报警抓拍" />
          <div v-else class="img-loading">暂无抓拍图像</div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="alertDialogVisible = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { api } from '@/services/api'

const activeTab = ref('cameras')
const loading = ref(false)
const dbOnline = ref(false)
const dbError = ref('')
const lastSyncTime = ref('')
const pollSeconds = ref(5)

const cameras = ref([])
const alerts = ref([])
const settings = ref([])
const devices = ref([])
const alertTotal = ref(0)
const latestAlertId = ref(0)

// 新增报警预警弹窗状态
const alertDialogVisible = ref(false)
const alertDialogTitle = ref('现场影像报警预警提示')
const activeAlert = ref(null)
const previewImageUrl = ref('')
const loadingImage = ref(false)

let lastKnownAlertId = null
let pollTimer = null

const loadAlertImage = async (alertId) => {
  previewImageUrl.value = ''
  loadingImage.value = true
  try {
    const res = await api.underwaterAlertImage(alertId)
    previewImageUrl.value = res?.image || ''
  } catch {
    previewImageUrl.value = ''
  } finally {
    loadingImage.value = false
  }
}

const previewAlertImage = async (row) => {
  alertDialogTitle.value = `报警抓拍原图 · #${row.id}`
  activeAlert.value = row
  alertDialogVisible.value = true
  await loadAlertImage(row.id)
}

const triggerNewAlertPopup = async (newAlert) => {
  alertDialogTitle.value = '⚠️ 发现新增现场影像报警预警！'
  activeAlert.value = newAlert
  alertDialogVisible.value = true
  ElNotification({
    title: newAlert.title || '现场影像报警预警',
    message: `${newAlert.content || ''} (${newAlert.create_time || ''})`,
    type: 'error',
    duration: 6000,
  })
  if (newAlert.has_image) {
    await loadAlertImage(newAlert.id)
  } else {
    previewImageUrl.value = ''
  }
}

const fetchLedger = async (silent = true) => {
  if (!silent) loading.value = true
  try {
    const res = await api.underwaterLedger(50)
    if (!res || res.__offline) return
    dbOnline.value = !!res.online
    dbError.value = res.error || ''
    lastSyncTime.value = new Date().toLocaleTimeString()
    if (!res.online) return

    cameras.value = res.cameras || []
    alerts.value = res.alerts || []
    settings.value = res.settings || []
    devices.value = res.devices || []
    alertTotal.value = res.alertTotal || 0
    latestAlertId.value = res.latestAlertId || 0

    const maxId = Number(res.latestAlertId || 0)
    if (lastKnownAlertId !== null && maxId > lastKnownAlertId) {
      const newest = (res.alerts || []).find(a => Number(a.id) > lastKnownAlertId) || res.alerts?.[0]
      if (newest) {
        triggerNewAlertPopup(newest)
      }
    }
    if (maxId > 0) {
      lastKnownAlertId = maxId
    }
  } finally {
    if (!silent) loading.value = false
  }
}

const restartPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => fetchLedger(true), pollSeconds.value * 1000)
}

onMounted(() => {
  fetchLedger(false)
  restartPolling()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.underwater-ledger-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  color: var(--do-text-primary);
}
.glass-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 10px;
  box-shadow: var(--shadow-sm);
}
.ledger-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  flex-wrap: wrap;
}
.ledger-heading {
  display: flex;
  align-items: center;
  gap: 14px;
}
.ledger-heading h1 {
  margin: 0;
  font-size: 19px;
}
.ledger-heading p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--do-text-secondary);
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
}
.btn-back:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}
.ledger-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid var(--do-border);
}
.status-pill.online { background: #ecfdf5; color: #15803d; border-color: #86efac; }
.status-pill.offline { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
.status-pill .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.poll-control { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.poll-lbl, .last-sync { font-size: 12.5px; color: var(--do-text-secondary); }

.ledger-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 12px;
}
.kpi-card {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kpi-card span { font-size: 13px; color: var(--do-text-secondary); }
.kpi-card strong { font-size: 20px; color: var(--do-text-primary); }
.kpi-card em { font-size: 12px; font-style: normal; color: var(--do-text-secondary); }

.ledger-body {
  padding: 12px 16px 16px;
}
.txt-muted { color: var(--do-text-secondary); font-size: 12px; }
.num-mono { font-family: var(--font-family-mono, 'SF Mono', Consolas, monospace); }

.alert-modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.alert-banner {
  padding: 12px 14px;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
}
.alert-title { font-size: 15px; font-weight: 700; color: #b91c1c; }
.alert-content { margin-top: 4px; font-size: 13.5px; color: #7f1d1d; }
.alert-meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #991b1b;
}
.alert-img-box {
  min-height: 220px;
  max-height: 440px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
}
.alert-snapshot-img {
  max-width: 100%;
  max-height: 440px;
  object-fit: contain;
}
.img-loading { color: #cbd5e1; font-size: 13px; }

@media (max-width: 960px) {
  .ledger-kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
