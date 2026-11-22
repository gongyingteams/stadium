<template>
  <div class="audit-workspace">
    <!-- 1. 顶部状态栏 -->
    <div class="audit-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgAuditLog" size="24" class="text-primary" />
        <div class="title-group">
          <span class="view-title">操作审计日志与不可篡改留存中心</span>
          <p class="view-subtitle">工业级合规追溯，记录全量操作指令与配置变更流水，支持审计检索和归档导出。</p>
        </div>
      </div>

      <div class="top-right">
        <el-button type="default" :loading="isRefreshing" @click="refreshLogs" class="btn-action-refresh">
          <SvgIcon name="SvgRefresh" size="14" :class="{ 'spin-icon': isRefreshing }" style="margin-right: 4px;" />
          <span>刷新数据</span>
        </el-button>
        <button class="btn-header-action btn-header-primary" @click="exportExcel" title="导出格式化 Excel 电子表格">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>导出 Excel 报表</span>
        </button>
        <button class="btn-header-action btn-header-manage" @click="exportCsv" title="导出标准逗号分隔 CSV 文本用于离线归档">
          <SvgIcon name="SvgTerminalHex" size="14" style="margin-right: 4px;" />
          <span>导出 CSV 留存</span>
        </button>
      </div>
    </div>

    <!-- 2. 统计卡片与指标看板 -->
    <div class="audit-stats-grid">
      <div class="stat-card glass-panel">
        <div class="stat-icon-wrap primary">
          <SvgIcon name="SvgAuditLog" size="20" />
        </div>
        <div class="stat-meta">
          <span class="stat-label">审计流水总数</span>
          <span class="stat-val num-mono">{{ totalLogsCount }} <small>条</small></span>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon-wrap success">
          <SvgIcon name="SvgSecurityShield" size="20" />
        </div>
        <div class="stat-meta">
          <span class="stat-label">执行成功率</span>
          <span class="stat-val num-mono text-success">{{ successRate }}%</span>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon-wrap warning">
          <SvgIcon name="SvgCpu" size="20" />
        </div>
        <div class="stat-meta">
          <span class="stat-label">今日操作事件</span>
          <span class="stat-val num-mono text-gold">{{ todayLogsCount }} <small>条</small></span>
        </div>
      </div>

      <div class="stat-card glass-panel">
        <div class="stat-icon-wrap neutral">
          <SvgIcon name="SvgUserRole" size="20" />
        </div>
        <div class="stat-meta">
          <span class="stat-label">涉及操作账号</span>
          <span class="stat-val num-mono text-primary">{{ uniqueUsersCount }} <small>人</small></span>
        </div>
      </div>
    </div>

    <!-- 3. 检索过滤控制栏 -->
    <div class="audit-filter-bar glass-panel">
      <div class="filter-inputs">
        <el-input
          v-model="searchKeyword"
          placeholder="检索 TraceID / 操作人 / 动作 / 目标 / IP..."
          prefix-icon="Search"
          clearable
          class="filter-search-input"
          @clear="handleFilterChange"
          @input="handleFilterChange"
        />

        <el-select v-model="filterEventType" placeholder="事件分类" clearable class="filter-select" @change="handleFilterChange">
          <el-option label="全部事件类型" value="ALL" />
          <el-option label="身份登录 (LOGIN)" value="LOGIN" />
          <el-option label="安全登出 (LOGOUT)" value="LOGOUT" />
          <el-option label="系统配置变更 (CONFIG/SETTINGS)" value="CONFIG" />
          <el-option label="外部软件调度 (EXTERNAL_APP)" value="EXTERNAL_APP" />
          <el-option label="硬件指令下发 (CMD_EXEC)" value="CMD_EXEC" />
          <el-option label="脱机沙箱切换 (MOCK_TOGGLE)" value="MOCK_TOGGLE" />
        </el-select>

        <el-select v-model="filterResult" placeholder="执行结果" clearable class="filter-select-sm" @change="handleFilterChange">
          <el-option label="全部状态" value="ALL" />
          <el-option label="成功 (SUCCESS)" value="SUCCESS" />
          <el-option label="失败 (FAILURE)" value="FAILURE" />
        </el-select>

        <el-select v-model="filterRole" placeholder="所属角色" clearable class="filter-select-sm" @change="handleFilterChange">
          <el-option label="全部角色" value="ALL" />
          <el-option label="管理员 (admin)" value="admin" />
          <el-option label="运维人员 (ops)" value="ops" />
          <el-option label="操作员 (operator)" value="operator" />
          <el-option label="查看者 (viewer)" value="viewer" />
        </el-select>

        <button class="btn-filter-reset" @click="resetFilters" title="重置全部筛选条件">
          <SvgIcon name="SvgRefresh" size="13" />
          <span>重置</span>
        </button>
      </div>

      <div class="total-stats">
        <span class="num-mono text-muted">
          已筛选 <strong>{{ filteredLogs.length }}</strong> / 共 {{ totalLogsCount }} 条
        </span>
      </div>
    </div>

    <!-- 4. 不可篡改审计日志流水表格 -->
    <div class="audit-table-card glass-panel">
      <el-table
        :data="paginatedLogs"
        style="width: 100%"
        size="default"
        stripe
        border
        highlight-current-row
        class="custom-audit-table"
      >
        <!-- 序号 / Trace ID -->
        <el-table-column prop="traceId" label="链路 TraceID" width="135" fixed="left">
          <template #default="{ row }">
            <span class="trace-badge num-mono" :title="row.traceId">{{ row.traceId }}</span>
          </template>
        </el-table-column>

        <!-- 操作时间 -->
        <el-table-column prop="time" label="操作时间" width="170">
          <template #default="{ row }">
            <span class="num-mono time-stamp">{{ formatTimestamp(row.time) }}</span>
          </template>
        </el-table-column>

        <!-- 操作人员与角色 -->
        <el-table-column prop="username" label="操作人员与角色" width="170">
          <template #default="{ row }">
            <div class="user-role-cell">
              <span class="op-user">{{ row.username }}</span>
              <span :class="['role-pill', getRoleClass(row.role)]">{{ getRoleLabel(row.role) }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 终端 / 客户端IP -->
        <el-table-column prop="terminal" label="终端与IP地址" width="160">
          <template #default="{ row }">
            <div class="terminal-ip-cell" :title="row.ip || '127.0.0.1'">
              <span class="terminal-tag num-mono">{{ row.terminal || 'PC' }}</span>
              <span class="ip-text num-mono">{{ formatIp(row.ip) }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 事件分类 -->
        <el-table-column prop="eventType" label="事件分类" width="125">
          <template #default="{ row }">
            <el-tag size="small" :type="getEventTagType(row.eventType)" effect="light" class="event-tag">
              {{ getEventLabel(row.eventType) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 受控目标资源 -->
        <el-table-column prop="target" label="受控目标资源" width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="target-name font-bold">{{ formatTarget(row.target) }}</span>
          </template>
        </el-table-column>

        <!-- 下发动作或指令报文摘要 -->
        <el-table-column prop="action" label="下发动作与指令摘要" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="action-summary num-mono">{{ formatAction(row.action, row.eventType) }}</span>
          </template>
        </el-table-column>

        <!-- 耗时 -->
        <el-table-column prop="costMs" label="耗时" width="85" align="center">
          <template #default="{ row }">
            <span class="num-mono text-muted">{{ row.costMs || 15 }}ms</span>
          </template>
        </el-table-column>

        <!-- 执行结果 -->
        <el-table-column prop="result" label="执行结果" width="95" align="center">
          <template #default="{ row }">
            <span :class="['status-tag', row.result === 'SUCCESS' ? 'success' : 'danger']">
              <span class="status-dot"></span>
              {{ row.result === 'SUCCESS' ? '成功' : '失败' }}
            </span>
          </template>
        </el-table-column>

        <!-- 操作：查看详情 -->
        <el-table-column label="详情" width="85" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showDetail(row)" class="btn-detail-link">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页栏 -->
      <div class="audit-pagination-bar">
        <div class="pagination-info text-muted">
          当前呈现第 {{ (currentPage - 1) * pageSize + 1 }} ~ {{ Math.min(currentPage * pageSize, filteredLogs.length) }} 条，共 {{ filteredLogs.length }} 条
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 15, 20, 50, 100]"
          :total="filteredLogs.length"
          layout="total, sizes, prev, pager, next, jumper"
          background
          size="small"
        />
      </div>
    </div>

    <!-- 5. 结构化日志详情模态框 -->
    <el-dialog
      v-model="detailVisible"
      :title="`审计流水追踪详情 · ${activeRow?.traceId || ''}`"
      width="720px"
      append-to-body
      destroy-on-close
      class="audit-detail-dialog"
    >
      <div v-if="activeRow" class="audit-detail-body">
        <!-- 基础元数据网格 -->
        <div class="detail-meta-grid">
          <div class="meta-item">
            <span class="meta-lbl">链路追踪号</span>
            <span class="meta-val num-mono text-primary font-bold">{{ activeRow.traceId }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">记录序号</span>
            <span class="meta-val num-mono">#{{ activeRow.id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">操作发生时间</span>
            <span class="meta-val num-mono">{{ formatTimestamp(activeRow.time) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">操作员账号</span>
            <span class="meta-val font-bold">{{ activeRow.username }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">所属角色</span>
            <span class="meta-val">{{ getRoleLabel(activeRow.role) }} ({{ activeRow.role }})</span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">来源终端 / IP</span>
            <span class="meta-val num-mono">{{ activeRow.terminal || 'PC' }} · {{ activeRow.ip || '127.0.0.1' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">事件类型</span>
            <span class="meta-val">
              <el-tag size="small" :type="getEventTagType(activeRow.eventType)">{{ getEventLabel(activeRow.eventType) }}</el-tag>
            </span>
          </div>
          <div class="meta-item">
            <span class="meta-lbl">执行状态</span>
            <span class="meta-val">
              <span :class="['status-tag', activeRow.result === 'SUCCESS' ? 'success' : 'danger']">
                {{ activeRow.result === 'SUCCESS' ? '执行成功' : '执行失败' }}
              </span>
            </span>
          </div>
        </div>

        <!-- 目标与动作概要 -->
        <div class="detail-section">
          <span class="detail-section-title">受控目标与执行动作</span>
          <div class="detail-action-card">
            <div class="dac-row">
              <span class="dac-lbl">受控资源目标：</span>
              <span class="dac-val font-bold text-highlight">{{ formatTarget(activeRow.target) }}</span>
            </div>
            <div class="dac-row">
              <span class="dac-lbl">下发动作概要：</span>
              <span class="dac-val num-mono">{{ formatAction(activeRow.action, activeRow.eventType) }}</span>
            </div>
          </div>
        </div>

        <!-- 详细数据载荷 / 报文参数 -->
        <div class="detail-section">
          <div class="detail-payload-header">
            <span class="detail-section-title">详细审计报文与变更载荷 (Payload)</span>
            <el-button size="small" link type="primary" @click="copyPayload(activeRow.details)">复制JSON</el-button>
          </div>
          <div class="detail-payload-box num-mono">
            <pre>{{ formatPayload(activeRow.details) }}</pre>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭窗口</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const isRefreshing = ref(false)
const searchKeyword = ref('')
const filterEventType = ref('ALL')
const filterResult = ref('ALL')
const filterRole = ref('ALL')

// 分页控制
const currentPage = ref(1)
const pageSize = ref(15)

// 详情弹窗
const detailVisible = ref(false)
const activeRow = ref(null)

const showDetail = (row) => {
  activeRow.value = row
  detailVisible.value = true
}

const handleFilterChange = () => {
  currentPage.value = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterEventType.value = 'ALL'
  filterResult.value = 'ALL'
  filterRole.value = 'ALL'
  currentPage.value = 1
}

// 统计指标
const totalLogsCount = computed(() => appStore.auditLogs.length)

const successRate = computed(() => {
  const list = appStore.auditLogs
  if (!list.length) return 100
  const succ = list.filter(l => l.result === 'SUCCESS').length
  return Math.round((succ / list.length) * 100)
})

const todayLogsCount = computed(() => {
  const todayStr = new Date().toISOString().slice(0, 10)
  return appStore.auditLogs.filter(l => (l.time || '').includes(todayStr) || /^\d{2}:\d{2}/.test(l.time)).length
})

const uniqueUsersCount = computed(() => {
  const s = new Set(appStore.auditLogs.map(l => l.username).filter(Boolean))
  return s.size || 1
})

// 过滤后的列表
const filteredLogs = computed(() => {
  return appStore.auditLogs.filter(log => {
    // 1. 类型过滤
    let matchType = true
    if (filterEventType.value !== 'ALL') {
      if (filterEventType.value === 'CONFIG') {
        matchType = ['CONFIG_CHANGE', 'SYSTEM_SETTINGS_UPDATE'].includes(log.eventType)
      } else if (filterEventType.value === 'EXTERNAL_APP') {
        matchType = (log.eventType || '').startsWith('EXTERNAL_APP')
      } else {
        matchType = log.eventType === filterEventType.value
      }
    }

    // 2. 状态过滤
    const matchResult = filterResult.value === 'ALL' || log.result === filterResult.value

    // 3. 角色过滤
    const matchRole = filterRole.value === 'ALL' || (log.role || '').toLowerCase() === filterRole.value.toLowerCase()

    // 4. 关键词过滤
    const kw = searchKeyword.value.trim().toLowerCase()
    let matchKw = true
    if (kw) {
      matchKw =
        (log.traceId && log.traceId.toLowerCase().includes(kw)) ||
        (log.username && log.username.toLowerCase().includes(kw)) ||
        (log.action && log.action.toLowerCase().includes(kw)) ||
        (log.target && log.target.toLowerCase().includes(kw)) ||
        (log.ip && log.ip.toLowerCase().includes(kw))
    }

    return matchType && matchResult && matchRole && matchKw
  })
})

// 分页列表
const paginatedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredLogs.value.slice(start, start + pageSize.value)
})

// 时间格式化 YYYY-MM-DD HH:mm:ss
const formatTimestamp = (raw) => {
  if (!raw) return '--'
  if (/^\d{2}:\d{2}:\d{2}$/.test(raw)) return raw
  try {
    const d = new Date(raw)
    if (isNaN(d.getTime())) return raw
    const pad = n => String(n).padStart(2, '0')
    const Y = d.getFullYear()
    const M = pad(d.getMonth() + 1)
    const D = pad(d.getDate())
    const h = pad(d.getHours())
    const m = pad(d.getMinutes())
    const s = pad(d.getSeconds())
    return `${Y}-${M}-${D} ${h}:${m}:${s}`
  } catch {
    return raw
  }
}

// 格式化 IP
const formatIp = (ip) => {
  if (!ip) return '127.0.0.1'
  if (ip.length > 20) {
    return ip.slice(0, 16) + '...'
  }
  return ip
}

// 角色展示
const getRoleLabel = (role) => {
  const map = {
    admin: '系统管理员',
    ops: '运维工程师',
    operator: '场馆操作员',
    viewer: '只读查看者'
  }
  return map[role] || role || '普通用户'
}

const getRoleClass = (role) => {
  if (role === 'admin') return 'role-admin'
  if (role === 'ops') return 'role-ops'
  if (role === 'operator') return 'role-operator'
  return 'role-viewer'
}

// 事件类型
const getEventLabel = (type) => {
  const map = {
    LOGIN: '身份登录',
    LOGOUT: '安全退出',
    SYSTEM_SETTINGS_UPDATE: '全局设置变更',
    CONFIG_CHANGE: '通信参数配置',
    EXTERNAL_APP_LAUNCH: '唤起外部应用',
    EXTERNAL_APP_ADD: '添加外部应用',
    EXTERNAL_APP_UPDATE: '编辑外部应用',
    EXTERNAL_APP_DELETE: '删除外部应用',
    CMD_EXEC: '硬件指令下发',
    DEVICE_COMMAND: '硬件设备指令',
    MOCK_TOGGLE: '脱机沙箱切换'
  }
  return map[type] || type || '系统事件'
}

const getEventTagType = (type) => {
  if (['LOGIN', 'LOGOUT'].includes(type)) return 'info'
  if (['CMD_EXEC', 'DEVICE_COMMAND'].includes(type)) return 'danger'
  if (['SYSTEM_SETTINGS_UPDATE', 'CONFIG_CHANGE'].includes(type)) return 'warning'
  if ((type || '').startsWith('EXTERNAL_APP')) return 'primary'
  if (type === 'MOCK_TOGGLE') return 'warning'
  return 'default'
}

// 目标展示映射
const formatTarget = (t) => {
  if (t === 'auth') return '统一鉴权服务 (Auth)'
  if (t === 'mock') return '脱机仿真沙箱 (Mock)'
  return t || '系统核心'
}

// 动作描述映射
const formatAction = (act, eventType) => {
  if (act === 'login') return '账号密码身份凭证验证通过'
  if (act === 'logout') return '注销当前会话并清除令牌'
  if (act === 'UPDATE' && eventType === 'SYSTEM_SETTINGS_UPDATE') return '修改系统品牌全称/版权/Logo等全局配置'
  if (act === 'LAUNCH') return '调度客户端安全代理启动受控应用程序'
  if (act === 'CREATE') return '新增集成应用程序登记与网络策略'
  if (act === 'DELETE') return '注销移除受控应用程序'
  if (act === 'toggle') return '切换系统正式/脱机模拟运行环境'
  return act || '执行业务指令'
}

// 载荷 JSON 格式化
const formatPayload = (details) => {
  if (!details) return '（无附加变更载荷）'
  if (typeof details === 'object') {
    return JSON.stringify(details, null, 2)
  }
  try {
    const parsed = JSON.parse(details)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return String(details)
  }
}

// 复制载荷
const copyPayload = (details) => {
  const text = formatPayload(details)
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制载荷内容到剪贴板！')
  }).catch(() => {
    ElMessage.info('复制失败，请手动选择复制')
  })
}

// 刷新
const refreshLogs = async () => {
  isRefreshing.value = true
  try {
    await appStore.hydrateOperationalData()
    ElMessage.success('已拉取最新不可篡改审计流水！')
  } catch (err) {
    ElMessage.error('拉取失败: ' + err.message)
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 400)
  }
}

// 导出 CSV
const exportCsv = () => {
  const rows = [
    ['链路TraceID', '操作时间', '操作人员', '所属角色', '终端', 'IP地址', '事件分类', '受控目标', '动作摘要', '耗时(ms)', '执行结果']
  ]
  filteredLogs.value.forEach(l => {
    rows.push([
      l.traceId || '',
      formatTimestamp(l.time),
      l.username || '',
      getRoleLabel(l.role),
      l.terminal || 'PC',
      l.ip || '127.0.0.1',
      getEventLabel(l.eventType),
      l.target || '',
      `"${(l.action || '').replace(/"/g, '""')}"`,
      l.costMs || 0,
      l.result === 'SUCCESS' ? '成功' : '失败'
    ])
  })

  const csvContent = '\uFEFF' + rows.map(e => e.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `venue_audit_logs_${new Date().toISOString().slice(0, 10)}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success(`已生成 ${filteredLogs.value.length} 条审计流水 CSV 归档文件并开始下载！`)
}

// 导出 Excel (兼容 CSV 模式)
const exportExcel = () => {
  exportCsv()
}

onMounted(async () => {
  await refreshLogs()
})
</script>

<style scoped>
.audit-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
  padding-bottom: 24px;
}

/* 顶部状态栏 */
.audit-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.view-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--do-text-primary);
  letter-spacing: 0.3px;
}

.view-subtitle {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-action-refresh {
  border-color: var(--do-border);
  background: var(--do-bg-input);
  color: var(--do-text-primary);
  font-size: 13px;
  height: 32px;
  border-radius: 4px;
}

.btn-action-refresh:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

/* 统计卡片网格 */
.audit-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-wrap.primary {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.stat-icon-wrap.success {
  background: rgba(var(--th-success-rgb), 0.12);
  color: var(--do-success);
}

.stat-icon-wrap.warning {
  background: rgba(var(--th-warning-rgb), 0.12);
  color: var(--do-warning-deep);
}

.stat-icon-wrap.neutral {
  background: rgba(100, 116, 139, 0.12);
  color: #475569;
}

.stat-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.stat-val {
  font-size: 22px;
  font-weight: 800;
  color: var(--do-text-primary);
  line-height: 1.2;
}

.stat-val small {
  font-size: 12px;
  font-weight: normal;
  color: var(--do-text-secondary);
  margin-left: 2px;
}

/* 过滤栏 */
.audit-filter-bar {
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  flex-wrap: wrap;
  gap: 12px;
}

.filter-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-search-input {
  width: 260px;
}

.filter-select {
  width: 170px;
}

.filter-select-sm {
  width: 120px;
}

.btn-filter-reset {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 12px;
  border-radius: 4px;
  border: 1px solid var(--do-border);
  background: var(--do-bg-input);
  color: var(--do-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-filter-reset:hover {
  color: var(--do-text-primary);
  border-color: var(--do-gold);
}

.total-stats {
  font-size: 13px;
}

/* 表格卡片 */
.audit-table-card {
  display: flex;
  flex-direction: column;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  overflow: hidden;
}

.custom-audit-table :deep(.el-table__header-wrapper th) {
  background: var(--do-bg-sunken) !important;
  color: var(--do-text-primary);
  font-weight: 700;
  font-size: 13px;
  padding: 10px 0;
}

.custom-audit-table :deep(.el-table__row td) {
  padding: 8px 0;
}

.trace-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.1);
  padding: 3px 6px;
  border-radius: 4px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  display: inline-block;
  white-space: nowrap;
}

.time-stamp {
  font-size: 12px;
  color: var(--do-text-regular);
  white-space: nowrap;
}

.user-role-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}

.op-user {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-text-primary);
  white-space: nowrap;
}

.role-pill {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 600;
  white-space: nowrap;
}

.role-admin {
  background: #FEE2E2;
  color: #991B1B;
}

.role-ops {
  background: #E0F2FE;
  color: #0369A1;
}

.role-operator {
  background: #DCFCE7;
  color: #166534;
}

.role-viewer {
  background: #F1F5F9;
  color: #475569;
}

.terminal-ip-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.terminal-tag {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 2px;
  background: #E2E8F0;
  color: #475569;
  font-weight: 700;
}

.ip-text {
  font-size: 12px;
  color: var(--do-text-secondary);
  white-space: nowrap;
}

.target-name {
  font-size: 13px;
  color: var(--do-text-primary);
}

.action-summary {
  font-size: 13px;
  color: var(--do-text-primary);
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 700;
}

.status-tag.success {
  background: rgba(var(--th-success-rgb), 0.12);
  color: #15803D;
  border: 1px solid rgba(var(--th-success-rgb), 0.3);
}

.status-tag.danger {
  background: rgba(var(--th-danger-rgb), 0.12);
  color: #B91C1C;
  border: 1px solid rgba(var(--th-danger-rgb), 0.3);
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.btn-detail-link {
  font-weight: 600;
}

/* 分页栏 */
.audit-pagination-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: var(--do-bg-sunken);
  border-top: 1px solid var(--do-border-light);
  flex-wrap: wrap;
  gap: 10px;
}

.pagination-info {
  font-size: 12px;
}

/* 详情弹窗 */
.audit-detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  background: var(--do-bg-sunken);
  padding: 14px;
  border-radius: 6px;
  border: 1px solid var(--do-border-light);
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 4px 6px;
}

.meta-lbl {
  color: var(--do-text-secondary);
}

.meta-val {
  color: var(--do-text-primary);
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.detail-action-card {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.dac-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.dac-lbl {
  color: #64748B;
  flex-shrink: 0;
}

.dac-val {
  color: #1E293B;
  word-break: break-all;
}

.detail-payload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-payload-box {
  background: #0F172A;
  color: #E2E8F0;
  padding: 14px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 260px;
  overflow: auto;
  border: 1px solid #334155;
}

.detail-payload-box pre {
  margin: 0;
  font-family: Consolas, Monaco, "Courier New", monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

@media (max-width: 1200px) {
  .audit-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .audit-stats-grid {
    grid-template-columns: 1fr;
  }
  .filter-search-input,
  .filter-select,
  .filter-select-sm {
    width: 100%;
  }
  .detail-meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
