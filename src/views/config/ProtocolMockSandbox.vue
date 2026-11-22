<template>
  <div class="mock-sandbox-workspace">
    <!-- 顶部状态栏与沙箱全局醒目警示徽章 -->
    <div class="sandbox-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgMockSandbox" size="20" class="text-warning" />
        <div class="title-meta">
          <span class="view-title">通信沙箱与模拟调试控制台</span>
          <p>在脱机环境模拟串口、网络及协议报文交互，验证设备应答和业务控制流程。</p>
        </div>
      </div>

      <div class="top-right">
        <!-- Mock 模式开关与作用域 -->
        <div class="mock-scope-badge">
          <span>作用域: {{ appStore.mockScope }}</span>
        </div>
        <el-switch
          v-model="appStore.isMockMode"
          active-text="脱机模拟沙箱已激活"
          inactive-text="真实硬件直连模式"
          @change="handleMockToggle"
        />
      </div>
    </div>

    <!-- 顶部黄色常驻警示条 (规范核心防呆要求) -->
    <div v-if="appStore.isMockMode" class="mock-warning-banner">
      <SvgIcon name="SvgMockSandbox" size="18" />
      <span>【防呆警告提示】当前全系统处于脱机模拟沙箱模式：所有业务控制台与操作按钮下发的指令均被沙箱虚拟拦截，不向物理硬件真实下发，测试报文带专用“模拟”角标！</span>
    </div>

    <!-- 上下分区分屏：上部虚拟设备应答配置 + 下部报文交互收发台 -->
    <div class="sandbox-main-layout">
      <!-- 1. 上部：虚拟下位机应答行为规则配置 -->
      <div class="col-virtual-responder glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <span>虚拟下位机自动应答规则 (Virtual Device Simulator)</span>
            <span class="panel-subtitle">配置下位机在收到特定请求报文时的自动回复报文与响应时延</span>
          </div>
          <el-button size="small" type="primary" plain @click="addRule">+ 新增应答规则</el-button>
        </div>

        <el-table :data="mockRules" style="width: 100%" size="small">
          <el-table-column prop="deviceName" label="模拟目标设备" width="160">
            <template #default="{ row }">
              <span class="num-mono font-bold text-primary">{{ row.deviceName }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="matchPattern" label="接收匹配报文特征 (HEX/ASCII)" min-width="180">
            <template #default="{ row }">
              <span class="num-mono text-warning">{{ row.matchPattern }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="virtualReply" label="虚拟应答回执报文" min-width="200">
            <template #default="{ row }">
              <span class="num-mono text-success">{{ row.virtualReply }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="delayMs" label="模拟时延" width="100" align="center">
            <template #default="{ row }">
              <span class="num-mono">{{ row.delayMs }} ms</span>
            </template>
          </el-table-column>

          <el-table-column prop="enabled" label="启用状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.enabled" size="small" />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 2. 下部：报文交互发包台与实时流水日志 -->
      <div class="col-console glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <span>报文收发调试交互台与流水回显 (Packet Console)</span>
            <span class="panel-subtitle">模拟人工发送报文，毫秒级观察虚拟下位机回复与正则解析结果</span>
          </div>
          <el-button size="small" link @click="clearLogs">清空流水日志</el-button>
        </div>

        <div class="console-body">
          <!-- 发包调试工具栏 -->
          <div class="send-toolbar">
            <el-select v-model="testTargetDevice" size="small" style="width: 200px;">
              <el-option label="主调音台 (Soundcraft RS232)" value="DEV_AUDIO_01" />
              <el-option label="照明主控 (Lutron RS485)" value="DEV_LIGHT_01" />
              <el-option label="自动升旗 PLC (Siemens S7)" value="DEV_FLAG_01" />
              <el-option label="LED大屏视频主控 (HTTP)" value="DEV_SCREEN_01" />
            </el-select>

            <el-radio-group v-model="testFormat" size="small">
              <el-radio-button value="HEX">HEX</el-radio-button>
              <el-radio-button value="ASCII">ASCII</el-radio-button>
            </el-radio-group>

            <el-input
              v-model="testPayload"
              size="small"
              placeholder="输入测试下发报文，例如: 55 AA 01 01 (开机)"
              style="flex: 1;"
            />

            <button class="btn-industrial btn-primary btn-control-action" @click="sendMockPacket">
              模拟发送报文
            </button>
          </div>

          <!-- 收发流水日志窗口 -->
          <div class="packet-stream-viewport num-mono">
            <div v-for="log in streamLogs" :key="log.id" :class="['stream-log-row', log.type.toLowerCase()]">
              <span class="l-time">{{ log.time }}</span>
              <span :class="['l-dir', log.dir]">{{ log.dir }}</span>
              <span class="l-device">[{{ log.device }}]</span>
              <span class="l-payload">{{ log.payload }}</span>
              <span v-if="log.parsedResult" class="l-parsed text-primary">-> 解析变量: {{ log.parsedResult }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const testTargetDevice = ref('DEV_AUDIO_01')
const testFormat = ref('HEX')
const testPayload = ref('55 AA 01 01 00 00')

const mockRules = ref([
  { deviceName: 'DEV_AUDIO_01', matchPattern: '55 AA 01 01 *', virtualReply: '55 AA ACK POWER_ON_OK 9C', delayMs: 25, enabled: true },
  { deviceName: 'DEV_LIGHT_01', matchPattern: '01 03 00 00 *', virtualReply: '01 03 04 00 C8 03 60 CRC', delayMs: 30, enabled: true },
  { deviceName: 'DEV_FLAG_01', matchPattern: '55 AA 02 01 *', virtualReply: '55 AA ACK FLAG_RISING_SPEED_2608', delayMs: 15, enabled: true },
  { deviceName: 'DEV_CLOCK_01', matchPattern: 'PING_TIME_CHECK', virtualReply: 'PONG_TIME_DRIFT_02MS', delayMs: 10, enabled: true }
])

const streamLogs = ref([
  { id: 1, time: '16:00:10.120', dir: 'TX', type: 'TX', device: 'DEV_AUDIO_01', payload: '55 AA 01 01 00 00 (开机指令)', parsedResult: '' },
  { id: 2, time: '16:00:10.145', dir: 'RX', type: 'RX', device: 'DEV_AUDIO_01', payload: '55 AA ACK POWER_ON_OK 9C (虚拟应答)', parsedResult: 'STATUS=ONLINE, POWER=1' },
  { id: 3, time: '16:00:15.000', dir: 'TX', type: 'TX', device: 'DEV_LIGHT_01', payload: '01 03 00 00 00 02 C4 0B (读照度电表)', parsedResult: '' },
  { id: 4, time: '16:00:15.030', dir: 'RX', type: 'RX', device: 'DEV_LIGHT_01', payload: '01 03 04 00 C8 03 60 7A 12 (模拟回执)', parsedResult: 'POWER=142.8kW, LUX=2045' }
])

const handleMockToggle = (val) => {
  ElMessage.info(val ? '已开启脱机模拟沙箱！' : '已切换为真实硬件直连模式！')
}

const sendMockPacket = () => {
  if (!testPayload.value) return
  const now = new Date()
  const timeStr = `${now.toTimeString().split(' ')[0]}.${now.getMilliseconds().toString().padStart(3, '0')}`

  streamLogs.value.unshift({
    id: Date.now(),
    time: timeStr,
    dir: 'TX',
    type: 'TX',
    device: testTargetDevice.value,
    payload: `${testPayload.value} [MOCK]`,
    parsedResult: ''
  })

  // 延迟模拟响应
  setTimeout(() => {
    const rxTime = new Date()
    const rxTimeStr = `${rxTime.toTimeString().split(' ')[0]}.${rxTime.getMilliseconds().toString().padStart(3, '0')}`
    streamLogs.value.unshift({
      id: Date.now() + 1,
      time: rxTimeStr,
      dir: 'RX',
      type: 'RX',
      device: testTargetDevice.value,
      payload: '55 AA ACK_0x55AA_SIMULATOR_REPLY_OK [VIRTUAL]',
      parsedResult: 'ACK=OK, CODE=00'
    })
    ElMessage.success('沙箱虚拟下位机已毫秒应答！')
  }, 120)
}

const addRule = () => {
  mockRules.value.push({
    deviceName: 'DEV_CUSTOM',
    matchPattern: '55 AA *',
    virtualReply: '55 AA ACK_OK',
    delayMs: 20,
    enabled: true
  })
}

const clearLogs = () => {
  streamLogs.value = []
  ElMessage.info('已清空报文交互日志')
}
</script>

<style scoped>
.mock-sandbox-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sandbox-top-bar {
  padding: 10px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.view-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mock-scope-badge {
  font-size: 14px;
  color: var(--do-warning-deep);
  background: var(--do-warning-bg);
  border: 1px dashed var(--do-warning);
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

/* 琥珀亮黄背景 + 贝都因深咖啡文字常驻防呆警示条 */
.mock-warning-banner {
  background: var(--do-gold-light);
  border: 1px solid var(--do-warning);
  border-radius: 6px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--do-warning-deep);
  font-size: 14px;
  line-height: 1.5;
  font-weight: 500;
}

.sandbox-main-layout {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--do-border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(var(--th-accent-rgb), 0.04);
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.col-virtual-responder {
  display: flex;
  flex-direction: column;
}

.col-console {
  display: flex;
  flex-direction: column;
}

.console-body {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.send-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  background: var(--do-bg-input);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--do-border-light);
}

.packet-stream-viewport {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 6px;
  padding: 12px;
  min-height: 220px;
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}

.stream-log-row {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 2px 0;
}

.l-time { color: var(--do-text-placeholder); font-size: 14px; }
.l-dir.TX { color: var(--do-gold-deep); font-weight: bold; }
.l-dir.RX { color: var(--do-success); font-weight: bold; }
.l-device { color: var(--do-text-secondary); }
.l-payload { color: var(--do-text-primary); flex: 1; font-family: var(--font-family-mono); }
.l-parsed { font-size: 14px; }
</style>
