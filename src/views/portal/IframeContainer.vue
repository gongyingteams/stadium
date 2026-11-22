<template>
  <div :class="['iframe-workspace', { 'anti-glare-active': isAntiGlareOn }]">
    <!-- 顶部安全代理管理工具条 -->
    <div class="iframe-toolbar glass-panel">
      <div class="toolbar-left">
        <div class="target-app-info">
          <span class="status-dot online"></span>
          <span class="app-title">{{ currentApp.title }}</span>
          <span class="badge-fallback">iframe 降级内嵌模式</span>
        </div>

        <div class="security-whitelist-pill" title="反向代理仅允许安全域名白名单">
          <SvgIcon name="SvgSecurityShield" size="14" />
          <span>目标白名单: {{ currentApp.whitelistDomain }}</span>
        </div>

        <div class="ticket-countdown num-mono">
          Ticket 凭据有效期: {{ ticketExpireSec }}s
        </div>
      </div>

      <div class="toolbar-right">
        <!-- 防眩光柔光滤镜开关 (规范要求: 防止白底老系统刺眼) -->
        <div class="filter-switch">
          <span class="switch-label">防眩光夜间滤镜:</span>
          <el-switch v-model="isAntiGlareOn" size="small" />
        </div>

        <el-button size="small" plain @click="reloadSession">
          重载会话
        </el-button>

        <el-button size="small" plain @click="openInNewTab">
          独立窗口打开
        </el-button>

        <el-button size="small" type="danger" plain @click="destroyProxySession">
          安全销毁会话
        </el-button>
      </div>
    </div>

    <!-- 降级内嵌安全警告提示条 -->
    <div class="iframe-notice-bar">
      <span>安全隔离提示：当前通过统一反向代理容器访问第三方专网系统，Cookie 独立隔离，禁用跨站脚本注入。</span>
      <span class="ticket-digest num-mono">授权凭证: TKT-{{ mockTicketHash }} (一次性票据)</span>
    </div>

    <!-- 主体内嵌视窗容器 (带 2px 视觉过渡缓冲垫层) -->
    <div class="iframe-cushion-frame">
      <!-- 模拟内嵌系统的内部工作台界面 (售验票/信息发布后台) -->
      <div class="mock-legacy-system-viewport">
        <!-- 传统老系统顶栏 (白底/浅色) -->
        <div class="legacy-topbar">
          <span class="legacy-sys-name">{{ currentApp.title }} - 专用管理后台</span>
          <span class="legacy-user">当前登录操作员: {{ currentApp.operator }} (SSO免密直达)</span>
        </div>

        <!-- 传统老系统内容区 -->
        <div class="legacy-body">
          <div class="legacy-sidebar">
            <div class="legacy-menu-item active">● 实时验票监控大厅</div>
            <div class="legacy-menu-item">● 闸机通道设备状态</div>
            <div class="legacy-menu-item">● 现场应急人工放行</div>
            <div class="legacy-menu-item">● 门票核验统计报表</div>
            <div class="legacy-menu-item">● 黑名单人脸同步</div>
          </div>

          <div class="legacy-main-content">
            <div class="legacy-kpi-row">
              <div class="legacy-kpi-box">
                <div class="box-title">今日总售票数</div>
                <div class="box-num num-mono">8,520 张</div>
              </div>
              <div class="legacy-kpi-box">
                <div class="box-title">已核验入场人数</div>
                <div class="box-num num-mono text-success">6,842 人 (80.3%)</div>
              </div>
              <div class="legacy-kpi-box">
                <div class="box-title">东1门闸机通行速率</div>
                <div class="box-num num-mono">48 人/分钟</div>
              </div>
              <div class="legacy-kpi-box">
                <div class="box-title">异常阻挡报警</div>
                <div class="box-num num-mono text-danger">0 次</div>
              </div>
            </div>

            <!-- 闸机通道实时流水模拟表格 -->
            <div class="legacy-table-wrap">
              <div class="table-caption">主馆入场闸机最新实时核验流水 (自动轮询上报)</div>
              <table class="legacy-table">
                <thead>
                  <tr>
                    <th>通道编号</th>
                    <th>通行方式</th>
                    <th>入场凭证</th>
                    <th>观众看台区域</th>
                    <th>通行核验结果</th>
                    <th>核验时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in ticketFlow" :key="t.time">
                    <td>{{ t.gate }}</td>
                    <td>{{ t.method }}</td>
                    <td class="num-mono">{{ t.ticketNo }}</td>
                    <td>{{ t.seat }}</td>
                    <td><span class="badge-pass">核验成功 · 闸机开门</span></td>
                    <td class="num-mono">{{ t.time }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const isAntiGlareOn = ref(false)
const ticketExpireSec = ref(58)
const mockTicketHash = ref(Math.random().toString(36).substring(2, 10).toUpperCase())

let countdownTimer = null

const currentApp = computed(() => {
  const id = route.params.id || 'ticketing'
  if (id === 'info_publish') {
    return {
      title: '信息发布与排期管理系统后台',
      whitelistDomain: 'infopub-srv.venue.local:8080',
      operator: 'admin_media'
    }
  }
  return {
    title: '场馆售验票与闸机核验专网系统',
    whitelistDomain: 'ticket-core.venue.local:443',
    operator: 'admin_ticketing'
  }
})

// 模拟实时闸机客流流水
const ticketFlow = ref([
  { gate: 'A区南门 01号人脸闸机', method: '动态人脸识别', ticketNo: 'T20261011-8842', seat: '东看台 1层05排12座', time: '15:42:01' },
  { gate: 'A区南门 02号刷证闸机', method: '二代身份证/电子票', ticketNo: 'T20261011-8843', seat: '东看台 1层05排13座', time: '15:42:03' },
  { gate: 'B区贵宾 05号无感通道', method: 'RFID手环/证件', ticketNo: 'T20261011-VIP08', seat: '贵宾主席包厢 02号', time: '15:42:08' },
  { gate: 'A区北门 03号人脸闸机', method: '动态人脸识别', ticketNo: 'T20261011-8844', seat: '北看台 2层11排08座', time: '15:42:15' },
  { gate: 'A区南门 01号人脸闸机', method: '动态人脸识别', ticketNo: 'T20261011-8845', seat: '东看台 1层06排01座', time: '15:42:20' }
])

onMounted(() => {
  countdownTimer = setInterval(() => {
    if (ticketExpireSec.value > 1) {
      ticketExpireSec.value--
    } else {
      ticketExpireSec.value = 60
      mockTicketHash.value = Math.random().toString(36).substring(2, 10).toUpperCase()
    }
  }, 1000)
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

const reloadSession = () => {
  ticketExpireSec.value = 60
  mockTicketHash.value = Math.random().toString(36).substring(2, 10).toUpperCase()
  ElMessage.success('已刷新短时效一次性 Ticket，代理会话重载成功')
}

const openInNewTab = () => {
  ElMessage.info('已在安全反向代理隔离容器中开启独立窗口')
}

const destroyProxySession = () => {
  ElMessage.warning('已主动注销并销毁当前代理会话')
  router.push('/portal/nav')
}
</script>

<style scoped>
.iframe-workspace {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  gap: 10px;
}

/* 顶部工具条 (大马士革白卡片材质) */
.iframe-toolbar {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.target-app-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.badge-fallback {
  font-size: 14px;
  color: var(--do-warning);
  background: var(--do-warning-bg);
  border: 1px solid var(--do-warning-border);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.security-whitelist-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.15);
  border: 1px solid var(--do-border);
  padding: 4px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.ticket-countdown {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 500;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-switch {
  display: flex;
  align-items: center;
  gap: 6px;
}
.switch-label {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.iframe-notice-bar {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 14px;
  color: var(--do-text-secondary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ticket-digest {
  color: var(--do-gold-deep);
  font-weight: 600;
}

/* 撒哈拉细沙色视觉缓冲垫层 */
.iframe-cushion-frame {
  flex: 1;
  background: var(--do-bg-page);
  border: 2px solid var(--do-border);
  border-radius: 6px;
  padding: 6px;
  overflow: hidden;
  box-shadow: inset 0 0 10px rgba(var(--th-shadow-rgb), 0.06);
}

/* 防眩光夜间滤镜样式 */
.anti-glare-active .mock-legacy-system-viewport {
  filter: brightness(0.9) contrast(0.95);
  background-color: var(--do-gold-light) !important;
}

/* 模拟外链第三方系统样式 */
.mock-legacy-system-viewport {
  width: 100%;
  height: 100%;
  background: var(--do-bg-input);
  color: var(--do-text-primary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: var(--font-family-base);
  transition: filter 0.3s ease;
  border-radius: 4px;
}

.legacy-topbar {
  background: var(--do-gold-deep);
  color: #FFFFFF;
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: bold;
}
.legacy-user {
  font-size: 14px;
  font-weight: normal;
  color: var(--do-bg-input);
}

.legacy-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.legacy-sidebar {
  width: 180px;
  background: var(--do-text-primary);
  color: var(--do-border);
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.legacy-menu-item {
  padding: 10px 16px;
  font-size: 14px;
  cursor: pointer;
}
.legacy-menu-item:hover, .legacy-menu-item.active {
  background: rgba(var(--th-accent-rgb), 0.2);
  color: var(--do-gold);
  font-weight: bold;
}

.legacy-main-content {
  flex: 1;
  padding: 16px;
  background: var(--do-bg-input);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.legacy-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.legacy-kpi-box {
  background: #FFFFFF;
  border: 1px solid var(--do-border-light);
  border-radius: 4px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.05);
}

.box-title {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin-bottom: 4px;
}

.box-num {
  font-size: 20px;
  font-weight: bold;
  color: var(--do-text-primary);
}

.legacy-table-wrap {
  background: #FFFFFF;
  border: 1px solid var(--do-border-light);
  border-radius: 4px;
  padding: 12px;
}

.table-caption {
  font-size: 14px;
  font-weight: bold;
  color: var(--do-text-primary);
  margin-bottom: 10px;
}

.legacy-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.legacy-table th {
  background: var(--do-bg-sunken);
  color: var(--do-text-secondary);
  text-align: left;
  padding: 10px 14px;
  border-bottom: 1px solid var(--do-border);
  font-size: 14px;
}

.legacy-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--do-border-light);
  color: var(--do-text-primary);
  font-size: 14px;
}

.badge-pass {
  background: var(--do-success-bg);
  color: var(--do-success);
  border: 1px solid var(--do-success-border);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
}
</style>
