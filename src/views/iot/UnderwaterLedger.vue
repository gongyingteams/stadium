<template>
  <div class="underwater-ledger-page">
    <!-- 顶部栏 -->
    <section class="ledger-header glass-panel">
      <div class="ledger-heading">
        <button class="btn-back" @click="$router.push('/iot/underwater-video')">← 返回水下音像采集控制</button>
        <div>
          <h1>水下音像采集识别系统 · 数据库台账与实时报警监测</h1>
          <p>数据源：<span class="num-mono">{{ dbSourceText }}</span>（展示全部库表字段 · 定时轮询新增报警并弹窗预警）</p>
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
        <el-button size="small" @click="openDbConfigDialog">
          <el-icon style="margin-right: 4px;"><Setting /></el-icon>
          数据库参数配置
        </el-button>
        <el-button type="primary" size="small" :loading="loading" @click="fetchLedger(false)">
          立即刷新
        </el-button>
      </div>
    </section>

    <!-- 摘要指标卡 -->
    <section class="ledger-kpis">
      <div class="kpi-card glass-panel">
        <span>水下摄像机 (tb_camera)</span>
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
          <el-table :data="cameras" border stripe size="small" max-height="560" empty-text="暂无数据" style="width: 100%">
            <el-table-column prop="id" label="编号" width="75" fixed />
            <el-table-column prop="name" label="摄像机名称" width="130" fixed />
            <el-table-column prop="ip" label="IP 地址" width="130" />
            <el-table-column prop="port" label="端口" width="70" />
            <el-table-column prop="state" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.state === 1 ? 'success' : 'info'" size="small">
                  {{ row.state === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="group" label="分组" width="95" />
            <el-table-column prop="row" label="行号" width="70" />
            <el-table-column prop="col" label="列号" width="70" />
            <el-table-column prop="hik_user" label="海康账号" width="100" />
            <el-table-column prop="hik_password" label="海康密码" width="110" />
            <el-table-column prop="version" label="版本" width="75" />
            <el-table-column prop="bind_device" label="绑定外设" width="105" />
            <el-table-column prop="calibrated" label="标定状态" width="95" />
            <el-table-column prop="crop_top" label="裁剪上边距" width="105" />
            <el-table-column prop="crop_bottom" label="裁剪下边距" width="105" />
            <el-table-column prop="crop_left" label="裁剪左边距" width="105" />
            <el-table-column prop="crop_right" label="裁剪右边距" width="105" />
            <el-table-column prop="channel" label="通道号" width="85" />
            <el-table-column prop="dist" label="距离" width="80" />
            <el-table-column prop="frame_rate" label="帧率" width="80" />
            <el-table-column prop="mtx" label="标定矩阵" width="110" show-overflow-tooltip />
            <el-table-column prop="create_time" label="创建时间" width="160" />
            <el-table-column prop="created_by" label="创建人" width="95" />
            <el-table-column prop="update_time" label="更新时间" width="160" />
            <el-table-column prop="updated_by" label="更新人" width="95" />
          </el-table>
        </el-tab-pane>

        <!-- Tab 2: tb_alert_history -->
        <el-tab-pane :label="`报警历史 tb_alert_history (${alertTotal})`" name="alerts">
          <el-table :data="alerts" border stripe size="small" max-height="560" empty-text="暂无数据" style="width: 100%">
            <el-table-column prop="id" label="编号" width="80" fixed />
            <el-table-column prop="title" label="报警标题" width="150" />
            <el-table-column prop="content" label="报警内容" min-width="220" show-overflow-tooltip />
            <el-table-column prop="camera_id" label="摄像机编号" width="110" />
            <el-table-column prop="camera_group" label="摄像机分组" width="115" />
            <el-table-column prop="push_devices" label="推送外设" width="145" />
            <el-table-column prop="state" label="状态" width="75" />
            <el-table-column prop="push_success" label="推送结果" width="105">
              <template #default="{ row }">
                <el-tag v-if="Number(row.push_success) === 1" type="success" size="small">已推送</el-tag>
                <el-tag v-else type="danger" size="small">未推送</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="创建时间" width="165" />
            <el-table-column prop="created_by" label="创建人" width="95" />
            <el-table-column prop="update_time" label="更新时间" width="165" />
            <el-table-column prop="updated_by" label="更新人" width="95" />
            <el-table-column label="抓拍原图" width="130" fixed="right">
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
          <el-table :data="settings" border stripe size="small" max-height="560" empty-text="暂无数据" style="width: 100%">
            <el-table-column prop="id" label="编号" width="80" />
            <el-table-column prop="key" label="参数键名" width="200" />
            <el-table-column prop="value" label="参数值" width="180" />
            <el-table-column prop="desc" label="参数说明" min-width="180" />
            <el-table-column prop="state" label="状态" width="80" />
            <el-table-column prop="create_time" label="创建时间" width="165" />
            <el-table-column prop="created_by" label="创建人" width="95" />
            <el-table-column prop="update_time" label="更新时间" width="165" />
            <el-table-column prop="updated_by" label="更新人" width="95" />
          </el-table>
        </el-tab-pane>

        <!-- Tab 4: tb_device -->
        <el-tab-pane :label="`联动外设 tb_device (${devices.length})`" name="devices">
          <el-table :data="devices" border stripe size="small" max-height="560" empty-text="暂无数据" style="width: 100%">
            <el-table-column prop="id" label="编号" width="85" />
            <el-table-column prop="name" label="设备名称" width="140" />
            <el-table-column prop="ip" label="IP 地址" width="150" />
            <el-table-column prop="port" label="端口" width="110" />
            <el-table-column prop="type" label="设备类型" width="95" />
            <el-table-column prop="state" label="状态" width="85">
              <template #default="{ row }">
                <el-tag :type="row.state === 1 ? 'success' : 'info'" size="small">{{ row.state }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="创建时间" width="165" />
            <el-table-column prop="created_by" label="创建人" width="95" />
            <el-table-column prop="update_time" label="更新时间" width="165" />
            <el-table-column prop="updated_by" label="更新人" width="95" />
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

    <!-- 水下台账 MySQL 数据库参数配置弹窗 -->
    <el-dialog
      v-model="dbConfigDialogVisible"
      title="水下台账数据库连接参数配置 (MySQL)"
      width="560px"
      destroy-on-close
    >
      <el-form label-position="top" size="default" class="db-cfg-form">
        <div class="db-grid-2">
          <el-form-item label="数据库主机 IP / 域名">
            <el-input v-model="dbForm.host" placeholder="例如 192.168.0.33" clearable />
          </el-form-item>
          <el-form-item label="端口">
            <el-input-number v-model="dbForm.port" :min="1" :max="65535" :controls="false" style="width: 100%;" />
          </el-form-item>
        </div>

        <div class="db-grid-2">
          <el-form-item label="数据库名称">
            <el-input v-model="dbForm.database" placeholder="例如 image_platform" clearable />
          </el-form-item>
          <el-form-item label="字符集">
            <el-select v-model="dbForm.charset" style="width: 100%;">
              <el-option label="utf8mb4" value="utf8mb4" />
              <el-option label="utf8" value="utf8" />
            </el-select>
          </el-form-item>
        </div>

        <div class="db-grid-2">
          <el-form-item label="数据库用户名">
            <el-input v-model="dbForm.user" placeholder="例如 user_view" clearable />
          </el-form-item>
          <el-form-item label="数据库密码">
            <el-input
              v-model="dbForm.password"
              type="password"
              show-password
              :placeholder="dbForm.hasPassword ? '留空表示保持当前已保存密码' : '请输入密码'"
              clearable
            />
          </el-form-item>
        </div>

        <div v-if="dbTestMessage" :class="['db-test-box', dbTestOk ? 'ok' : 'err']">
          {{ dbTestMessage }}
        </div>
      </el-form>

      <template #footer>
        <div class="db-dialog-footer">
          <el-button :loading="testingDb" @click="testDbConnection">测试连接</el-button>
          <div style="flex: 1;"></div>
          <el-button @click="dbConfigDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="savingDb" @click="saveDbConfig">保存并立即刷新</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'
import { api } from '@/services/api'

const activeTab = ref('cameras')
const loading = ref(false)
const dbOnline = ref(false)
const dbError = ref('')
const dbSourceText = ref('192.168.0.33:3306 / image_platform')
const lastSyncTime = ref('')
const pollSeconds = ref(5)

const dbConfigDialogVisible = ref(false)
const testingDb = ref(false)
const savingDb = ref(false)
const dbTestMessage = ref('')
const dbTestOk = ref(false)

const dbForm = reactive({
  host: '192.168.0.33',
  port: 3306,
  user: 'user_view',
  password: '',
  database: 'image_platform',
  charset: 'utf8mb4',
  hasPassword: true
})

const cameras = ref([])
const alerts = ref([])
const settings = ref([])
const devices = ref([])
const alertTotal = ref(0)
const latestAlertId = ref(0)

// 新增报警预警弹窗状态
const alertDialogVisible = ref(false)
const alertDialogTitle = ref('水下影像报警预警提示')
const activeAlert = ref(null)
const previewImageUrl = ref('')
const loadingImage = ref(false)

let lastKnownAlertId = null
let pollTimer = null

const applyDbConfigToForm = (cfg) => {
  if (!cfg) return
  dbForm.host = cfg.host || '192.168.0.33'
  dbForm.port = Number(cfg.port) || 3306
  dbForm.user = cfg.user || ''
  dbForm.password = ''
  dbForm.database = cfg.database || 'image_platform'
  dbForm.charset = cfg.charset || 'utf8mb4'
  dbForm.hasPassword = Boolean(cfg.hasPassword)
  dbSourceText.value = `${dbForm.host}:${dbForm.port} / ${dbForm.database}`
}

const openDbConfigDialog = async () => {
  dbTestMessage.value = ''
  dbConfigDialogVisible.value = true
  try {
    const res = await api.getUnderwaterDbConfig()
    if (res && !res.__offline && res.config) {
      applyDbConfigToForm(res.config)
    }
  } catch { /* ignore */ }
}

const buildDbPayload = () => ({
  host: (dbForm.host || '').trim(),
  port: Number(dbForm.port) || 3306,
  user: (dbForm.user || '').trim(),
  password: dbForm.password,
  keepPassword: dbForm.password === '' && dbForm.hasPassword,
  database: (dbForm.database || '').trim(),
  charset: dbForm.charset || 'utf8mb4'
})

const testDbConnection = async () => {
  const payload = buildDbPayload()
  if (!payload.host || !payload.database) {
    ElMessage.warning('请填写数据库主机地址和数据库名称')
    return
  }
  testingDb.value = true
  dbTestMessage.value = ''
  try {
    const res = await api.testUnderwaterDbConfig(payload)
    if (res && !res.__offline) {
      dbTestOk.value = !!res.ok
      dbTestMessage.value = res.message || (res.ok ? '连接成功' : '连接失败')
      if (res.ok) ElMessage.success(dbTestMessage.value)
      else ElMessage.warning(dbTestMessage.value)
    } else {
      dbTestOk.value = false
      dbTestMessage.value = '后端服务未响应，无法测试数据库连接'
    }
  } catch (err) {
    dbTestOk.value = false
    dbTestMessage.value = `测试失败：${err?.message || err}`
  } finally {
    testingDb.value = false
  }
}

const saveDbConfig = async () => {
  const payload = buildDbPayload()
  if (!payload.host || !payload.database) {
    ElMessage.warning('请填写数据库主机地址和数据库名称')
    return
  }
  savingDb.value = true
  try {
    const res = await api.saveUnderwaterDbConfig(payload)
    if (res && !res.__offline && res.ok) {
      if (res.config) applyDbConfigToForm(res.config)
      dbConfigDialogVisible.value = false
      ElMessage.success(res.message || '数据库配置已保存')
      lastKnownAlertId = null
      await fetchLedger(false)
    } else {
      ElMessage.error(res?.message || '保存数据库配置失败')
    }
  } catch (err) {
    ElMessage.error(`保存失败：${err?.message || err}`)
  } finally {
    savingDb.value = false
  }
}

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
  alertDialogTitle.value = '⚠️ 发现新增水下影像报警预警！'
  activeAlert.value = newAlert
  alertDialogVisible.value = true
  ElNotification({
    title: newAlert.title || '水下影像报警预警',
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
    if (res.database) dbSourceText.value = res.database
    if (res.dbConfig) applyDbConfigToForm(res.dbConfig)
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
.db-cfg-form { display: flex; flex-direction: column; gap: 4px; }
.db-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.db-test-box { padding: 10px 12px; border-radius: 8px; font-size: 13px; line-height: 1.5; }
.db-test-box.ok { background: #ecfdf5; color: #15803d; border: 1px solid #86efac; }
.db-test-box.err { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.db-dialog-footer { display: flex; align-items: center; gap: 8px; width: 100%; }

@media (max-width: 960px) {
  .ledger-kpis { grid-template-columns: repeat(2, 1fr); }
  .db-grid-2 { grid-template-columns: 1fr; }
}
</style>
