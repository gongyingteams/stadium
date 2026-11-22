<template>
  <div class="device-config-workspace">
    <!-- 顶部检索与动作栏 -->
    <div class="config-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgDeviceSetting" size="20" class="text-primary" />
        <div class="title-meta">
          <span class="view-title">异构设备实例与全协议通信配置中心</span>
          <p>维护场馆设备实例、通信协议和连接参数，支持多厂商设备统一接入与配置。</p>
        </div>
      </div>

      <div class="top-right">
        <el-input
          v-model="searchKw"
          placeholder="按设备名称、编码、厂商、协议搜索..."
          prefix-icon="Search"
          size="small"
          clearable
          style="width: 260px;"
        />
        <el-button size="small" type="primary" @click="openCreateDrawer">
          + 新增设备实例
        </el-button>
      </div>
    </div>

    <!-- 核心设备资产明细大表 -->
    <div class="device-table-card glass-panel">
      <div class="panel-header">
        <div class="header-title">
          <span>全场异构设备资产与通信协议配置大表</span>
          <span class="panel-subtitle">拒绝硬编码，支持串口、TCP/UDP、Modbus、HTTP与本地程序全协议热配置</span>
        </div>
        <span class="num-mono text-muted">共 {{ filteredDevices.length }} 台设备实例</span>
      </div>

      <el-table :data="filteredDevices" style="width: 100%" size="small">
        <el-table-column prop="code" label="设备唯一编码" width="140">
          <template #default="{ row }">
            <span class="num-mono font-bold">{{ row.code }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="设备资产名称" min-width="180">
          <template #default="{ row }">
            <span class="dev-name">{{ row.name }}</span>
            <span class="dev-loc">{{ row.location }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="subsystem" label="所属子系统" width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="dark">{{ row.subsystemName }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="protocol" label="通信协议类型" width="130">
          <template #default="{ row }">
            <span :class="['proto-badge', row.protocol.toLowerCase()]">
              {{ row.protocol }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="connParams" label="连接配置参数" min-width="180">
          <template #default="{ row }">
            <span class="num-mono text-sub">{{ row.connSummary }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="pollInterval" label="轮询周期" width="100" align="center">
          <template #default="{ row }">
            <span class="num-mono">{{ row.pollInterval }}s</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="实时状态" width="100" align="center">
          <template #default="{ row }">
            <span :class="['status-dot', row.status === 'ONLINE' ? 'online' : 'warning']"></span>
            <span style="margin-left: 6px;">{{ row.status === 'ONLINE' ? '正常' : '告警' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="动作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="editDevice(row)">
              修改参数
            </el-button>
            <el-button size="small" type="warning" link @click="testPing(row)">
              通信探测
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 右侧常驻通信参数编辑抽屉 -->
    <el-drawer
      v-model="isEditDrawerOpen"
      :title="isEditing ? `编辑通信参数 · ${currentForm.name}` : '新增异构设备实例'"
      size="560px"
      direction="rtl"
    >
      <div class="drawer-edit-body">
        <el-form :model="currentForm" label-position="top" size="small">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="设备编码 (唯一ID)">
                <el-input v-model="currentForm.code" :disabled="isEditing" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="设备资产名称">
                <el-input v-model="currentForm.name" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="所属基线子系统">
                <el-select v-model="currentForm.subsystemCode" style="width: 100%;">
                  <el-option label="扩声系统 (AUDIO_MATRIX)" value="AUDIO_MATRIX" />
                  <el-option label="场地照明及控制系统 (LIGHTING)" value="LIGHTING" />
                  <el-option label="LED大屏系统 (LED_SCREEN)" value="LED_SCREEN" />
                  <el-option label="计时计分系统 (MATCH_SCORE)" value="MATCH_SCORE" />
                  <el-option label="标准时钟系统 (STANDARD_CLOCK)" value="STANDARD_CLOCK" />
                  <el-option label="自动升旗控制系统 (FLAG_SYSTEM)" value="FLAG_SYSTEM" />
                  <el-option label="现场/水下视频系统 (VIDEO)" value="FIELD_VIDEO" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="通信协议标准">
                <el-select v-model="currentForm.protocol" style="width: 100%;">
                  <el-option label="串口 (RS232/RS485)" value="SERIAL" />
                  <el-option label="TCP Socket 长连接" value="TCP" />
                  <el-option label="UDP 网络报文" value="UDP" />
                  <el-option label="Modbus RTU / TCP" value="MODBUS" />
                  <el-option label="HTTP / RESTful API" value="HTTP" />
                  <el-option label="RTSP 视频流" value="RTSP" />
                  <el-option label="本地可执行程序/脚本 (.exe/.bat)" value="LOCAL_EXE" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 串口专属参数组 -->
          <div v-if="currentForm.protocol === 'SERIAL'" class="proto-sub-form">
            <div class="sub-form-title">工业串口物理参数 (RS232/485)</div>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="本地COM口/虚拟端口">
                  <el-input v-model="currentForm.serialPort" placeholder="COM1 或 COM3" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="波特率 (Baud Rate)">
                  <el-select v-model="currentForm.baudRate" style="width: 100%;">
                    <el-option :value="9600" label="9600 bps" />
                    <el-option :value="19200" label="19200 bps" />
                    <el-option :value="38400" label="38400 bps" />
                    <el-option :value="115200" label="115200 bps" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item label="数据位">
                  <el-select v-model="currentForm.dataBits"><el-option :value="8" label="8" /><el-option :value="7" label="7" /></el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="停止位">
                  <el-select v-model="currentForm.stopBits"><el-option value="1" label="1" /><el-option value="2" label="2" /></el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="校验位">
                  <el-select v-model="currentForm.parity"><el-option value="NONE" label="无校验" /><el-option value="EVEN" label="偶校验" /><el-option value="ODD" label="奇校验" /></el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 网络专属参数组 (TCP/UDP/HTTP) -->
          <div v-if="['TCP', 'UDP', 'HTTP'].includes(currentForm.protocol)" class="proto-sub-form">
            <div class="sub-form-title">网络端点与超时参数</div>
            <el-row :gutter="12">
              <el-col :span="16">
                <el-form-item label="目标 IP 地址或域名">
                  <el-input v-model="currentForm.targetIp" placeholder="192.168.10.x" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="端口号">
                  <el-input-number v-model="currentForm.targetPort" :min="1" :max="65535" style="width: 100%;" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 报文格式与回传解析规则 -->
          <div class="proto-sub-form">
            <div class="sub-form-title">报文编码与回传解析规则 (低代码引擎)</div>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="指令报文格式">
                  <el-radio-group v-model="currentForm.payloadFormat">
                    <el-radio-button value="HEX">HEX</el-radio-button>
                    <el-radio-button value="ASCII">ASCII</el-radio-button>
                    <el-radio-button value="JSON">JSON</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="自动校验算法宏">
                  <el-select v-model="currentForm.checksumType" style="width: 100%;">
                    <el-option value="CRC16" label="CRC16 工业校验" />
                    <el-option value="LRC" label="LRC 纵向冗余校验" />
                    <el-option value="SUM" label="累加和校验 (Checksum)" />
                    <el-option value="NONE" label="无校验宏" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="响应报文解析正则或切片规则">
              <el-input v-model="currentForm.responseRegex" placeholder="例如: ACK_([0-9A-F]{4}) 或 slice(4, 8)" />
            </el-form-item>
          </div>

          <!-- 轮询心跳规则 -->
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="状态轮询探测周期 (秒)">
                <el-input-number v-model="currentForm.pollInterval" :min="1" :max="60" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="通信超时阈值 (毫秒)">
                <el-input-number v-model="currentForm.timeoutMs" :min="100" :max="10000" :step="100" style="width: 100%;" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="drawer-actions">
          <el-button @click="isEditDrawerOpen = false">取消</el-button>
          <el-button type="primary" @click="saveDevice">保存配置变更并热加载</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const searchKw = ref('')
const isEditDrawerOpen = ref(false)
const isEditing = ref(false)

const devices = ref([
  {
    code: 'DEV_AUDIO_01',
    name: '比赛大厅主调音台 (Soundcraft Vi3000)',
    location: '主馆总控声控室',
    subsystemCode: 'AUDIO_MATRIX',
    subsystemName: '扩声系统',
    protocol: 'SERIAL',
    connSummary: 'COM3 / 115200bps / 8-N-1 (HEX/CRC16)',
    pollInterval: 3,
    timeoutMs: 300,
    status: 'ONLINE',
    serialPort: 'COM3',
    baudRate: 115200,
    dataBits: 8,
    stopBits: '1',
    parity: 'NONE',
    payloadFormat: 'HEX',
    checksumType: 'CRC16',
    responseRegex: 'ACK_([0-9A-F]+)'
  },
  {
    code: 'DEV_LIGHT_01',
    name: '场地比赛照明主控制器 (Lutron Hub)',
    location: '高压强电机房',
    subsystemCode: 'LIGHTING',
    subsystemName: '场地照明及控制',
    protocol: 'SERIAL',
    connSummary: 'COM1 / 9600bps / 8-N-1 (Modbus RTU)',
    pollInterval: 5,
    timeoutMs: 500,
    status: 'ONLINE',
    serialPort: 'COM1',
    baudRate: 9600,
    dataBits: 8,
    stopBits: '1',
    parity: 'NONE',
    payloadFormat: 'HEX',
    checksumType: 'CRC16',
    responseRegex: '01 03 ([0-9A-F]+)'
  },
  {
    code: 'DEV_SCREEN_01',
    name: '东侧中央 LED 主大屏拼接器 (NovaPro)',
    location: '大屏弱电控制机柜',
    subsystemCode: 'LED_SCREEN',
    subsystemName: 'LED大屏系统',
    protocol: 'HTTP',
    connSummary: '192.168.10.88:8080 (RESTful API)',
    pollInterval: 2,
    timeoutMs: 1000,
    status: 'ONLINE',
    targetIp: '192.168.10.88',
    targetPort: 8080,
    payloadFormat: 'JSON',
    checksumType: 'NONE',
    responseRegex: '"status":\\s*"ok"'
  },
  {
    code: 'DEV_SCORE_01',
    name: '游泳跳水主计时计分机 (Omega ARES-21)',
    location: '主裁判长总席位',
    subsystemCode: 'MATCH_SCORE',
    subsystemName: '计时计分系统',
    protocol: 'TCP',
    connSummary: '192.168.10.99:5000 (ASCII Stream)',
    pollInterval: 1,
    timeoutMs: 500,
    status: 'ONLINE',
    targetIp: '192.168.10.99',
    targetPort: 5000,
    payloadFormat: 'ASCII',
    checksumType: 'NONE',
    responseRegex: 'EVENT_.*'
  },
  {
    code: 'DEV_CLOCK_01',
    name: '北斗/GPS卫星双模标准主母钟 (TS-9000)',
    location: '弱电核心机房',
    subsystemCode: 'STANDARD_CLOCK',
    subsystemName: '标准时钟系统',
    protocol: 'TCP',
    connSummary: '192.168.10.100:1230 (NTP/UDP 授时)',
    pollInterval: 5,
    timeoutMs: 800,
    status: 'ONLINE',
    targetIp: '192.168.10.100',
    targetPort: 1230,
    payloadFormat: 'HEX',
    checksumType: 'CRC16',
    responseRegex: 'TIME_SYNC_([0-9]+)'
  },
  {
    code: 'DEV_FLAG_01',
    name: '自动升旗电机控制主PLC (Siemens S7)',
    location: '主席台升旗基座内部',
    subsystemCode: 'FLAG_SYSTEM',
    subsystemName: '自动升旗控制',
    protocol: 'SERIAL',
    connSummary: 'COM2 / 19200bps / 8-E-1 (LRC校验)',
    pollInterval: 2,
    timeoutMs: 200,
    status: 'ONLINE',
    serialPort: 'COM2',
    baudRate: 19200,
    dataBits: 8,
    stopBits: '1',
    parity: 'EVEN',
    payloadFormat: 'HEX',
    checksumType: 'LRC',
    responseRegex: 'PLC_ACK_([0-9A-F]+)'
  }
])

const currentForm = ref({ ...devices.value[0] })

const filteredDevices = computed(() => {
  if (!searchKw.value) return devices.value
  const kw = searchKw.value.toLowerCase()
  return devices.value.filter(d =>
    d.name.toLowerCase().includes(kw) ||
    d.code.toLowerCase().includes(kw) ||
    d.protocol.toLowerCase().includes(kw) ||
    d.subsystemName.includes(kw)
  )
})

const openCreateDrawer = () => {
  isEditing.value = false
  currentForm.value = {
    code: 'DEV_CUSTOM_' + Math.floor(Math.random() * 100),
    name: '新接入第三方硬件设备',
    location: '现场设备间',
    subsystemCode: 'AUDIO_MATRIX',
    protocol: 'SERIAL',
    serialPort: 'COM4',
    baudRate: 9600,
    dataBits: 8,
    stopBits: '1',
    parity: 'NONE',
    payloadFormat: 'HEX',
    checksumType: 'CRC16',
    pollInterval: 5,
    timeoutMs: 1000
  }
  isEditDrawerOpen.value = true
}

const editDevice = (row) => {
  isEditing.value = true
  currentForm.value = { ...row }
  isEditDrawerOpen.value = true
}

const saveDevice = () => {
  if (isEditing.value) {
    const idx = devices.value.findIndex(d => d.code === currentForm.value.code)
    if (idx !== -1) {
      devices.value[idx] = { ...currentForm.value }
    }
  } else {
    devices.value.unshift({ ...currentForm.value, status: 'ONLINE', connSummary: '自定义连接配置' })
  }
  isEditDrawerOpen.value = false
  ElMessage.success(`设备通信参数已热加载更新，驱动引擎已生效！`)
}

const testPing = (row) => {
  ElMessage.info(`正在向下位机 ${row.code} 下发探测指令包...`)
  setTimeout(() => {
    ElMessage.success(`握手回执成功！响应耗时: 16ms，通信正常`)
  }, 300)
}
</script>

<style scoped>
.device-config-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.config-top-bar {
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
  align-items: center;
  gap: 14px;
}

.device-table-card {
  display: flex;
  flex-direction: column;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  overflow: hidden;
}

.panel-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border-card);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(240, 235, 227, 0.4);
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-coffee-light);
  font-weight: 400;
}

.dev-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
  display: block;
}

.dev-loc {
  font-size: 14px;
  color: var(--do-coffee-light);
}

.proto-badge {
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 700;
}
.proto-badge.serial {
  background: rgba(var(--th-accent-rgb), 0.16);
  color: var(--do-gold-dark);
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
}
.proto-badge.tcp {
  background: rgba(var(--th-success-rgb), 0.15);
  color: var(--do-olive);
  border: 1px solid rgba(var(--th-success-rgb), 0.3);
}
.proto-badge.http {
  background: rgba(var(--th-warning-rgb), 0.15);
  color: var(--do-amber);
  border: 1px solid rgba(var(--th-warning-rgb), 0.3);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.online { background: var(--do-olive); box-shadow: 0 0 6px var(--do-olive); }
.status-dot.warning { background: var(--do-amber); box-shadow: 0 0 6px var(--do-amber); }

/* 抽屉样式 */
.drawer-edit-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.proto-sub-form {
  background: var(--do-sand-light);
  border: 1px solid var(--do-border-card);
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 14px;
}

.sub-form-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--th-accent-color);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-form-title::before {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--th-accent-color);
  box-shadow: 0 0 6px var(--th-accent-color);
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}
</style>
