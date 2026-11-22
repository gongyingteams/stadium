<template>
  <div class="audio-control-workspace">
    <!-- 顶部状态栏 - 统一采用参考页面设计风格 -->
    <section class="page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon">
          <SvgIcon name="SvgSoundMatrix" size="28" />
        </div>
        <div>
          <div class="title-row">
            <h1>数字调音台推子矩阵与场景音效总控台</h1>
            <span class="device-tag">
              <el-icon class="mr-1">
                <Connection />
              </el-icon>
              <span v-if="selectedMixers.length === mixerDevices.length">
                广播控制全部 {{ mixerDevices.length }} 套调音台 (Soundcraft / Yamaha / A&H)
              </span>
              <span v-else-if="selectedMixers.length > 0">
                定向受控 {{ selectedMixers.length }} 套: {{selectedMixers.map(d => d.custom_no).join('、')}}
              </span>
              <span v-else class="text-danger">
                未指定受控设备 (下发已暂停)
              </span>
            </span>
          </div>
          <p>专业场馆扩声声学矩阵 · 毫秒级推子电平回读与场景一键召回</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-metric">
          <span :class="['status-dot', selectedMixers.length > 0 ? 'online' : 'muted']"></span>
          <span>{{ selectedMixers.length > 0 ? `链路正常 (${selectedMixers.length}套在线)` : '无目标设备' }}</span>
        </div>
        <div class="status-metric"><strong class="num-mono">+0.0 dB</strong> 主输出电平</div>
        <button class="btn-header-action btn-header-manage" @click="router.push('/config/devices')" title="跳转物联硬件设备管理与总控中台查看扩声矩阵台账">
          <SvgIcon name="SvgDeviceSetting" size="14" style="margin-right: 4px;" />
          <span>设备矩阵台账</span>
        </button>
        <button class="btn-header-action btn-header-danger" @click="confirmMuteAll" title="安全急停：全场所有调音台输出通道一键紧急静音">
          <SvgIcon name="SvgEmergencyHalt" size="14" style="margin-right: 4px;" />
          <span>全场静音 (MUTE ALL)</span>
        </button>
      </div>
    </section>

    <!-- 设备选择工具栏 - 统一采用参考页面设计风格 -->
    <section class="target-toolbar glass-panel">
      <div class="section-heading">
        <div>
          <h2>指令下发目标设备</h2>
          <span class="section-help">选择本次调度的目标调音台设备</span>
        </div>
        <span class="selection-count num-mono">已选 {{ selectedDeviceIds.length }} / {{ mixerDevices.length }} 套</span>
      </div>
      <div class="target-actions">
        <el-button size="small" @click="handleSelectAllChange(!isAllSelected)">{{ isAllSelected ? '取消全选' : '默认全选'
        }}</el-button>
        <el-button size="small" @click="selectOnlyPrimaryMixer">仅选主控机</el-button>
        <el-button size="small" @click="selectAllMixers">一键全选</el-button>
      </div>
    </section>

    <!-- 设备卡片网格 -->
    <section class="mixer-wall">
      <article v-for="dev in mixerDevices" :key="dev.id" class="mixer-card glass-panel"
        :class="{ selected: selectedDeviceIds.includes(dev.id) }" @click="toggleDeviceSelect(dev.id)">
        <div class="mixer-card-top">
          <div class="mixer-identity">
            <div class="mixer-icon">
              <SvgIcon name="SvgSoundMatrix" size="22" />
            </div>
            <div>
              <h3>{{ dev.device_name }}</h3>
              <span class="device-code num-mono">{{ dev.custom_no }}</span>
            </div>
          </div>
          <span :class="['mixer-status', dev.online_status?.toLowerCase() || 'offline']">
            {{ (dev.online_status?.toLowerCase() === 'online') ? '在线' : '离线' }}
          </span>
        </div>
        <div class="mixer-location">
          <div class="location-info">
            <el-icon>
              <Location />
            </el-icon>
            <span>{{ dev.region_name || '主赛场' }}</span>
          </div>
          <div class="mixer-conn">
            <span class="field-label">连接方式</span>
            <strong class="num-mono">{{ dev.connection_type === 'SERIAL' ? (dev.serial_port || 'COM3') : (dev.target_ip
              || 'TCP') }}</strong>
          </div>
        </div>
        <div class="mixer-card-footer">
          <span :class="['selection-state', { active: selectedDeviceIds.includes(dev.id) }]">
            <el-icon v-if="selectedDeviceIds.includes(dev.id)"><Select /></el-icon>
            {{ selectedDeviceIds.includes(dev.id) ? '已加入调度目标' : '点击选择目标' }}
          </span>
        </div>
      </article>
    </section>

    <!-- 主操作区 -->
    <div class="main-layout">
      <div class="main-left">
        <!-- 1. 虚拟数字调音台 12 通道推子矩阵 -->
        <div class="control-card glass-panel">
          <div class="panel-heading">
            <div>
              <h2>输入 / 输出通道音量数字推子 (Fader Matrix)</h2>
              <span class="section-help">支持电动推子物理回读、触控联动与多路监听</span>
            </div>
            <div class="panel-actions">
              <el-button size="small" @click="resetAllFadersToZero">
                <el-icon>
                  <Refresh />
                </el-icon>
                全通道归零 (0dB)
              </el-button>
              <el-button size="small" @click="unmuteAllChannels">
                <el-icon>
                  <CircleCheckFilled />
                </el-icon>
                解除全静音
              </el-button>
            </div>
          </div>

          <!-- 12 路专业推子通道条 (可横向自适应排开) -->
          <div class="faders-row">
            <div v-for="ch in channels" :key="ch.id"
              :class="['fader-strip', { 'is-muted': ch.isMuted, 'is-solo': ch.isSolo }]">
              <!-- 通道编号与硬件信号指示灯 -->
              <div class="strip-header">
                <div class="strip-header-top">
                  <div class="ch-meta-wrap">
                    <SvgIcon :name="getChannelIcon(ch)" size="15" class="ch-icon" />
                    <span class="ch-id num-mono">CH{{ ch.id.toString().padStart(2, '0') }}</span>
                  </div>
                  <!-- 信号灯：SIG(绿) / CLIP(红) -->
                  <div class="led-indicators">
                    <span class="sig-led" :class="{ active: !ch.isMuted && ch.currentVu > 10 }"
                      title="信号输入 (Signal Present)"></span>
                    <span class="clip-led" :class="{ active: !ch.isMuted && ch.gain >= 6 }"
                      title="过载削波 (Peak/Clip)"></span>
                  </div>
                </div>

                <!-- 硬件拟物控制键：MUTE / SOLO -->
                <div class="strip-buttons">
                  <button type="button" :class="['btn-mute', { active: ch.isMuted }]" title="静音开关"
                    @click="toggleMute(ch)">
                    MUTE
                  </button>
                  <button type="button" :class="['btn-solo', { active: ch.isSolo }]" title="独奏监听 (Solo/PFL)"
                    @click="toggleSolo(ch)">
                    SOLO
                  </button>
                </div>
              </div>

              <!-- 核心控制区：标尺刻度 + 动态跳动电平表 VU + 垂直金属推子 -->
              <div class="fader-core-area">
                <!-- 刻度尺 (dB Scale) -->
                <div class="fader-scale num-mono">
                  <span>+12</span>
                  <span>+6</span>
                  <span class="zero-db">0</span>
                  <span>-6</span>
                  <span>-12</span>
                  <span>-24</span>
                  <span>-40</span>
                  <span>-∞</span>
                </div>

                <!-- 左侧：左声道 L 动态彩色跳动竖线 -->
                <div class="vu-meter-col-track l-track" title="L 左声道实时电平">
                  <div class="vu-meter-bar" :style="{ height: getVuBarHeight(ch, 'L') }"></div>
                  <div class="vu-zero-mark"></div>
                </div>

                <!-- 中间：垂直推子滑道与金属推子帽 (Fader Slider) -->
                <div class="slider-slot-container">
                  <div class="fader-slot-zero-line"></div>
                  <el-slider v-model="ch.gain" vertical height="190px" :min="-60" :max="12" :step="1"
                    :disabled="ch.isMuted" :show-tooltip="false" @input="handleGainInput(ch)"
                    @change="handleGainChange(ch)" />
                </div>

                <!-- 右侧：右声道 R 动态彩色跳动竖线 -->
                <div class="vu-meter-col-track r-track" title="R 右声道实时电平">
                  <div class="vu-meter-bar" :style="{ height: getVuBarHeight(ch, 'R') }"></div>
                  <div class="vu-zero-mark"></div>
                </div>
              </div>

              <!-- 分贝数值液晶显示屏 (Fader dB Window) -->
              <div :class="['gain-display-box', 'num-mono', { muted: ch.isMuted }]">
                <span v-if="ch.isMuted">MUTED</span>
                <span v-else>{{ ch.gain > 0 ? '+' : '' }}{{ ch.gain.toFixed(1) }} dB</span>
              </div>

              <!-- 调音台涂鸦液晶条 (LCD Scribble Strip) - 完整呈现两行通道名，绝不省略号 -->
              <div class="scribble-strip" :title="`${ch.name} (${ch.type})`">
                <span class="scribble-type">{{ ch.type }}</span>
                <span class="scribble-name">{{ ch.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. 赛事场景音效一键调用网格 -->
        <div class="scenes-card glass-panel">
          <div class="panel-heading">
            <div>
              <h2>快捷场景混音与音效一键触发 (Scene Recall)</h2>
              <span class="section-help">下发预置混音矩阵参数、通道路由与侧链闪避配置</span>
            </div>
            <span class="active-scene-badge">当前模式: <strong>{{ getCurrentSceneTitle }}</strong></span>
          </div>

          <div class="scene-buttons-row">
            <div v-for="scene in sceneList" :key="scene.id"
              :class="['scene-tile', { active: currentSceneId === scene.id }]" @click="recallScene(scene)">
              <div class="scene-tile-badge num-mono">SCENE {{ scene.id.toString().padStart(2, '0') }}</div>

              <div class="scene-content">
                <div class="tile-icon-circle">
                  <SvgIcon :name="scene.icon" size="24" />
                </div>
                <div class="tile-meta">
                  <span class="tile-title">{{ scene.title }}</span>
                  <span class="tile-desc">{{ scene.desc }}</span>
                </div>
              </div>

              <div v-if="currentSceneId === scene.id" class="active-indicator">
                <span class="pulse-dot"></span>
                <span>当前激活运行</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：通信参数与下发流水日志 -->
      <aside class="comm-panel glass-panel">
        <!-- 下位机多链路通信参数面板 -->
        <div class="panel-heading comm-header">
          <div>
            <h2>下位机通信与多链路监视</h2>
            <span :class="['comm-badge num-mono', selectedMixers.length > 0 ? 'online' : '']">
              {{ selectedMixers.length > 1 ? `MULTI-LINK (${selectedMixers.length}路)` : (selectedMixers.length === 1 ?
                'ONLINE' : '暂无设备') }}
            </span>
          </div>
          <!-- 动态收发指示灯 -->
          <div class="comm-leds">
            <span class="comm-led-label">TX</span>
            <span :class="['traffic-led', 'tx-led', { active: isTxActive }]"></span>
            <span class="comm-led-label">RX</span>
            <span :class="['traffic-led', 'rx-led', { active: isRxActive }]"></span>
          </div>
        </div>

        <div class="comm-stats-box">
          <div class="stat-grid">
            <div class="stat-item">
              <span class="stat-lbl">受控设备链路</span>
              <span class="stat-val num-mono">{{ selectedMixers.length > 1 ? `已聚合并行 ${selectedMixers.length} 套` :
                (selectedMixers[0]?.connection_type === 'SERIAL' ? 'COM3 (RS-232)' : selectedMixers[0]?.target_ip ||
                  'COM3') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-lbl">下发工作模式</span>
              <span class="stat-val font-bold"
                :style="{ color: selectedMixers.length === mixerDevices.length ? 'var(--do-success)' : 'var(--do-gold-deep)' }">
                {{ selectedMixers.length === mixerDevices.length ? '全场广播同步' : selectedMixers.length > 0 ? `定向多播
                (${selectedMixers.length}套)` : '已挂起' }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-lbl">DSP处理核心</span>
              <span class="stat-val">Vi-Core / QL-DSP / XCVI</span>
            </div>
            <div class="stat-item">
              <span class="stat-lbl">音频网络协议</span>
              <span class="stat-val num-mono">Dante / AES67 (48kHz)</span>
            </div>
            <div class="stat-item">
              <span class="stat-lbl">传输报文校验</span>
              <span class="stat-val text-success font-bold num-mono">CRC16 (100% OK)</span>
            </div>
            <div class="stat-item">
              <span class="stat-lbl">双向通信延迟</span>
              <span class="stat-val text-success font-bold num-mono">18 ms</span>
            </div>
          </div>
        </div>

        <!-- 串口报文实时流水终端 (Console Terminal) -->
        <div class="console-section">
          <div class="console-toolbar">
            <span class="console-title">串口报文流水 (HEX / ASCII)</span>
            <div class="console-actions">
              <button type="button" class="console-btn" title="清空历史报文" @click="clearLogs">
                <el-icon>
                  <Delete />
                </el-icon>
                <span>清空</span>
              </button>
            </div>
          </div>

          <div class="comm-log-scroll num-mono">
            <div v-for="(log, idx) in serialLogs" :key="idx" class="log-entry">
              <span class="log-t">{{ log.time }}</span>
              <span :class="['log-dir', log.dir]">{{ log.dir }}</span>
              <span class="log-msg">{{ log.msg }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  SwitchButton, Refresh, CircleCheckFilled, Delete, Setting, Connection, Select, Location
} from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { iotDeviceService } from '@/services/iotDeviceService'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 12 路典型场馆扩声通道 (包含信号类型、微电平跳动等拟真数据)
const channels = ref([
  { id: 1, name: '主席台麦克 1', type: 'MIC 1', gain: 0, isMuted: false, isSolo: false, currentVu: 45, currentVuL: 45, currentVuR: 43 },
  { id: 2, name: '主席台麦克 2', type: 'MIC 2', gain: -3, isMuted: false, isSolo: false, currentVu: 38, currentVuL: 38, currentVuR: 36 },
  { id: 3, name: '总裁判长麦克', type: 'REF MIC', gain: 2, isMuted: false, isSolo: false, currentVu: 55, currentVuL: 55, currentVuR: 53 },
  { id: 4, name: '现场解说播音', type: 'COMMENT', gain: 1, isMuted: false, isSolo: false, currentVu: 50, currentVuL: 50, currentVuR: 48 },
  { id: 5, name: '国歌/颁奖音源', type: 'CEREMONY', gain: 4, isMuted: false, isSolo: false, currentVu: 62, currentVuL: 62, currentVuR: 64 },
  { id: 6, name: '背景音乐 (BGM)', type: 'MEDIA', gain: -8, isMuted: false, isSolo: false, currentVu: 28, currentVuL: 28, currentVuR: 30 },
  { id: 7, name: '跳水发令提示音', type: 'START BEEP', gain: 3, isMuted: false, isSolo: false, currentVu: 58, currentVuL: 58, currentVuR: 56 },
  { id: 8, name: '泳池水下扬声器', type: 'UNDERWATER', gain: -2, isMuted: false, isSolo: false, currentVu: 40, currentVuL: 40, currentVuR: 38 },
  { id: 9, name: '东看台扩声组', type: 'EAST STAND', gain: 0, isMuted: false, isSolo: false, currentVu: 44, currentVuL: 44, currentVuR: 45 },
  { id: 10, name: '西看台扩声组', type: 'WEST STAND', gain: 0, isMuted: false, isSolo: false, currentVu: 44, currentVuL: 44, currentVuR: 43 },
  { id: 11, name: '热身副馆返听', type: 'AUX WARM', gain: -6, isMuted: false, isSolo: false, currentVu: 32, currentVuL: 32, currentVuR: 30 },
  { id: 12, name: '媒体转播混音', type: 'BROADCAST', gain: 0, isMuted: false, isSolo: false, currentVu: 46, currentVuL: 46, currentVuR: 48 }
])

// 通道硬件切片图标智能映射
const getChannelIcon = (ch) => {
  if (!ch || !ch.type) return 'SvgMicrophone'
  const t = ch.type.toUpperCase()
  if (t.includes('MIC') || t.includes('COMMENT')) return 'SvgMicrophone'
  if (t.includes('CEREMONY') || t.includes('MEDIA')) return 'SvgMusicNote'
  if (t.includes('BEEP')) return 'SvgWhistle'
  if (t.includes('UNDERWATER')) return 'SvgSwimmingPool'
  if (t.includes('AUX') || t.includes('BROADCAST')) return 'SvgRadio'
  return 'SvgSpeaker'
}

// ==============================================================================
// 同一类型多套硬件设备状态管理 (指定受控设备，默认全选)
// ==============================================================================
const mixerDevices = ref([])
const selectedDeviceIds = ref([])

// 加载当前系统中所有调音台设备
const loadMixerDevices = () => {
  const list = iotDeviceService.getDevices('AUDIO')
  // 筛选出调音台设备
  const mixers = list.filter(d => d.custom_no.includes('MIX') || d.device_name.includes('调音台'))
  mixerDevices.value = mixers.length > 0 ? mixers : list

  // 【核心要求】默认全选所有调音台设备！
  selectedDeviceIds.value = mixerDevices.value.map(d => d.id)
}

// 已选中的调音台列表对象
const selectedMixers = computed(() => {
  return mixerDevices.value.filter(d => selectedDeviceIds.value.includes(d.id))
})

// 全选双向绑定
const isAllSelected = computed({
  get: () => mixerDevices.value.length > 0 && selectedDeviceIds.value.length === mixerDevices.value.length,
  set: (val) => {
    if (val) {
      selectedDeviceIds.value = mixerDevices.value.map(d => d.id)
    } else {
      selectedDeviceIds.value = []
    }
  }
})

// 半选状态
const isIndeterminate = computed(() => {
  return selectedDeviceIds.value.length > 0 && selectedDeviceIds.value.length < mixerDevices.value.length
})

const handleSelectAllChange = (val) => {
  if (val) {
    selectedDeviceIds.value = mixerDevices.value.map(d => d.id)
    ElMessage.success(`已全选当前 ${mixerDevices.value.length} 套调音台设备 (全场广播模式)`)
  } else {
    selectedDeviceIds.value = []
    ElMessage.info('已取消所有设备勾选，发送指令前请先指定目标设备')
  }
}

// 切换单台设备的勾选状态
const toggleDeviceSelect = (id) => {
  const idx = selectedDeviceIds.value.indexOf(id)
  if (idx > -1) {
    selectedDeviceIds.value.splice(idx, 1)
  } else {
    selectedDeviceIds.value.push(id)
  }
}

// 快捷操作：一键全选
const selectAllMixers = () => {
  selectedDeviceIds.value = mixerDevices.value.map(d => d.id)
  ElMessage.success(`已恢复全选当前 ${mixerDevices.value.length} 套调音台设备`)
}

// 快捷操作：仅选主赛场核心调音台
const selectOnlyPrimaryMixer = () => {
  const primary = mixerDevices.value.find(d => d.custom_no === 'AUD-MIX-01') || mixerDevices.value[0]
  if (primary) {
    selectedDeviceIds.value = [primary.id]
    ElMessage.info(`已切换为仅定向受控：【${primary.custom_no}】${primary.device_name}`)
  }
}

// ==============================================================================
// 统一多播/定向指令发射引擎
// ==============================================================================
const dispatchAudioCommand = (actionName, cmdPayload, successMessage) => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return false
  }

  const targets = selectedMixers.value
  const targetLabel = targets.map(d => d.custom_no).join(', ')
  const isBroadcast = targets.length === mixerDevices.value.length

  triggerTxPulse()
  serialLogs.value.unshift({
    time: new Date().toLocaleTimeString(),
    dir: 'TX',
    msg: `[${isBroadcast ? '广播' : '定向'} -> ${targetLabel}] ${actionName}: ${cmdPayload}`
  })

  // 同步在统一物联服务中批量下发指令并生成审计回执
  // 注意：sendCommand 签名为 (targetDeviceIds: number[], commandPayload: string,
  //                            commandName: string, operator: string)
  iotDeviceService
    .sendCommand(
      targets.map(d => d.id),
      cmdPayload,
      actionName,
      userStore.currentUser?.username || 'admin'
    )
    .catch((e) => ElMessage.error(`指令下发失败：${e.message}`))

  setTimeout(() => {
    triggerRxPulse()
    targets.forEach(dev => {
      serialLogs.value.unshift({
        time: new Date().toLocaleTimeString(),
        dir: 'RX',
        msg: `[ACK <- ${dev.custom_no}] ${actionName} SYNC_ACK_OK`
      })
    })
  }, 40)

  if (successMessage) {
    ElMessage.success(successMessage)
  }
  return true
}

const currentSceneId = ref(1)

const sceneList = ref([
  { id: 1, title: '开幕仪式 / 升旗国歌', desc: '强化主席台与国歌主通道，看台立体声扩声全开', icon: 'SvgFlagSystem' },
  { id: 2, title: '常规竞赛 / 赛事进行', desc: '发令音高动态优先，背景音乐自动侧链混音闪避', icon: 'SvgMatchScore' },
  { id: 3, title: '颁奖加冕典礼', desc: '高保真进行曲音源与现场解说专业立体声混响', icon: 'SvgMediaPlayer' },
  { id: 4, title: '休赛撤场 / 保洁氛围', desc: '低照度轻柔环境轻音乐循环，看台组自动降噪', icon: 'SvgSoundMatrix' }
])

const serialLogs = ref([
  { time: '12:05:40', dir: 'TX', msg: '[广播 -> AUD-MIX-01, AUD-MIX-02, AUD-MIX-03] 55 AA 01 0B 00 24 CRC16_OK' },
  { time: '12:05:40', dir: 'RX', msg: '[ACK <- AUD-MIX-01] 55 AA 01 0B ACK FADER_CH05_GAIN_4DB' },
  { time: '12:05:41', dir: 'RX', msg: '[ACK <- AUD-MIX-02] 55 AA 01 0B ACK DANTE_GAIN_SYNC_OK' },
  { time: '12:05:43', dir: 'TX', msg: '[心跳轮询] 55 AA 00 00 PING_HEARTBEAT' },
  { time: '12:05:43', dir: 'RX', msg: '[心跳应答] 3 套调音台设备均在线正常' }
])

// 串口指示灯脉冲状态
const isTxActive = ref(false)
const isRxActive = ref(false)

const triggerTxPulse = () => {
  isTxActive.value = true
  setTimeout(() => { isTxActive.value = false }, 180)
}

const triggerRxPulse = () => {
  isRxActive.value = true
  setTimeout(() => { isRxActive.value = false }, 180)
}

const getCurrentSceneTitle = computed(() => {
  const current = sceneList.value.find(s => s.id === currentSceneId.value)
  return current ? current.title : '未知场景'
})

// 电平表动态微跳动定时器（模拟专业声学调音台真实现场声音波动）
let vuTimer = null

onMounted(() => {
  // 加载当前系统中所有调音台设备（默认全选）
  loadMixerDevices()

  vuTimer = setInterval(() => {
    channels.value.forEach(ch => {
      if (ch.isMuted) {
        ch.currentVu = 0
        ch.currentVuL = 0
        ch.currentVuR = 0
      } else {
        // 在推子当前 gain 基础上产生 L/R 独立微抖动
        const jitterL = (Math.random() - 0.45) * 10
        const jitterR = (Math.random() - 0.45) * 10
        const dynamicLevelL = Math.max(-60, Math.min(10, ch.gain + jitterL))
        const dynamicLevelR = Math.max(-60, Math.min(10, ch.gain + jitterR))
        const normalizedL = ((dynamicLevelL + 60) / 72) * 100
        const normalizedR = ((dynamicLevelR + 60) / 72) * 100
        ch.currentVuL = Math.min(96, Math.max(8, normalizedL))
        ch.currentVuR = Math.min(96, Math.max(8, normalizedR))
        ch.currentVu = (ch.currentVuL + ch.currentVuR) / 2
      }
    })
  }, 140)
})

onUnmounted(() => {
  if (vuTimer) clearInterval(vuTimer)
})

// 计算电平柱明确的像素高度 (总高度 184px，保底高度 10px 杜绝黑槽隐形)
const getVuBarHeight = (ch, side) => {
  if (ch.isMuted) return '0px'
  const val = side === 'L' ? (ch.currentVuL ?? ch.currentVu ?? 45) : (ch.currentVuR ?? ch.currentVu ?? 43)
  const num = typeof val === 'number' && !isNaN(val) ? val : 45
  const clamped = Math.max(8, Math.min(98, num))
  const px = Math.round((clamped / 100) * 184)
  return `${px}px`
}

// 滑块交互
const handleGainInput = (ch) => {
  if (!ch.isMuted) {
    const val = Math.min(95, Math.max(10, ((ch.gain + 60) / 72) * 100))
    ch.currentVu = val
    ch.currentVuL = val
    ch.currentVuR = Math.max(8, val - 3)
  }
}

const handleGainChange = (ch) => {
  const hexVal = (ch.gain + 60).toString(16).padStart(2, '0').toUpperCase()
  const payload = `HEX: 55 AA 02 ${ch.id} ${hexVal} (${ch.gain > 0 ? '+' : ''}${ch.gain.toFixed(1)}dB)`
  dispatchAudioCommand(`SET_FADER_CH${ch.id}`, payload, null)
}

// 静音切换
const toggleMute = (ch) => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return
  }
  ch.isMuted = !ch.isMuted
  const payload = ch.isMuted ? 'MUTE_ON' : 'MUTE_OFF'
  dispatchAudioCommand(
    `SET_MUTE_CH${ch.id}`,
    payload,
    `${ch.name} ${ch.isMuted ? '已静音' : '已恢复输出'} (已同步至 ${selectedMixers.value.length} 套设备)`
  )
}

// 独奏监听切换
const toggleSolo = (ch) => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return
  }
  ch.isSolo = !ch.isSolo
  const payload = ch.isSolo ? 'SOLO_ACTIVE' : 'SOLO_OFF'
  dispatchAudioCommand(`SET_SOLO_CH${ch.id}`, payload, ch.isSolo ? `已开启【${ch.name}】Solo 耳机监听` : null)
}

// 场景切换
const recallScene = (scene) => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return
  }
  currentSceneId.value = scene.id
  const payload = `0x55 AA SCENE_RECALL_ID_${scene.id}`
  dispatchAudioCommand(
    `RECALL_SCENE_${scene.id}`,
    payload,
    `已向选中的 ${selectedMixers.value.length} 套调音台设备同步召回：【${scene.title}】`
  )
}

// 全通道归零 (0dB)
const resetAllFadersToZero = () => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return
  }
  channels.value.forEach(c => (c.gain = 0))
  dispatchAudioCommand(
    'RESET_ALL_FADERS_0DB',
    '0x55 AA 00 00 FADER_RESET_ALL_0DB',
    `已将所有推子重置为 0dB (已同步至 ${selectedMixers.value.length} 套设备)`
  )
}

// 解除全场静音
const unmuteAllChannels = () => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return
  }
  channels.value.forEach(c => (c.isMuted = false))
  dispatchAudioCommand(
    'UNMUTE_ALL_CHANNELS',
    '0x55 AA 00 FF UNMUTE_ALL',
    `已解除全场静音 (已同步至 ${selectedMixers.value.length} 套设备)`
  )
}

// 确认全场静音
const confirmMuteAll = () => {
  if (selectedDeviceIds.value.length === 0) {
    ElMessage.warning('【操作已拦截】请先指定至少 1 套受控调音台设备！')
    return
  }
  ElMessageBox.confirm(
    `确认向当前已选中的【${selectedMixers.value.map(d => d.custom_no).join('、')}】（共 ${selectedMixers.value.length} 套设备）执行【全场紧急静音 (MUTE ALL)】吗？所有对应声学通道将瞬间静音。`,
    '全场紧急静音确认',
    {
      confirmButtonText: '立即全场静音',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    channels.value.forEach(c => (c.isMuted = true))
    dispatchAudioCommand(
      'EMERGENCY_MUTE_ALL',
      '0x55 AA FF FF EMERGENCY_MUTE_ALL',
      `已向选中的 ${selectedMixers.value.length} 套调音台设备执行全场紧急静音！`
    )
  }).catch(() => { })
}

// 清空报文
const clearLogs = () => {
  serialLogs.value = []
  ElMessage.info('已清空报文流水记录')
}
</script>

<style scoped>
.audio-control-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 顶部状态栏 */
.audio-top-bar {
  padding: 10px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
}

/* ==============================================================================
   受控设备多路目标分发条 (支持多套设备、默认全选、单选多选指定)
   ============================================================================== */
.target-device-bar {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.04);
}

.target-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.target-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.target-icon {
  color: var(--do-gold-deep);
  font-size: 15px;
}

.target-bar-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-bg-dark);
}

.target-count-badge {
  font-size: 14px;
  padding: 2px 8px;
  background: var(--do-gold-light);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  border-radius: 4px;
  color: var(--do-gold-deep);
  font-weight: 700;
}

.select-all-checkbox {
  margin-right: 0 !important;
}

.select-all-checkbox :deep(.el-checkbox__label) {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: var(--do-text-primary) !important;
}

/* 设备多路选择胶囊组 */
.target-device-chips {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  overflow-x: auto;
  padding: 4px 0;
}

.device-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  white-space: nowrap;
}

.device-chip:hover {
  background: var(--do-bg-input);
  border-color: var(--do-gold);
}

.device-chip.active {
  background: linear-gradient(180deg, var(--do-bg-card) 0%, var(--do-gold-light) 100%);
  border: 1.5px solid var(--do-gold);
  box-shadow: 0 1px 6px rgba(var(--th-accent-rgb), 0.25);
}

.chip-custom-no {
  font-size: 14px;
  font-weight: 700;
  padding: 2px 6px;
  background: rgba(var(--th-accent-rgb), 0.12);
  border: none;
  border-radius: 3px;
  color: var(--do-gold-deep);
}

.chip-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-region {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: rgba(var(--th-shadow-rgb), 0.05);
  padding: 2px 6px;
  border-radius: 3px;
}

.chip-conn {
  font-size: 14px;
  color: var(--do-gold-deep);
  font-weight: 600;
}

.chip-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--do-text-placeholder);
}

.chip-status-dot.online {
  background: var(--do-success);
  box-shadow: 0 0 0 2px rgba(var(--th-success-rgb), 0.2);
}

/* 右侧快捷按钮 */
.target-bar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.quick-select-btn {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-select-btn:hover {
  background: var(--do-bg-input);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.quick-select-btn.select-all-btn {
  background: linear-gradient(135deg, var(--do-bg-sunken) 0%, var(--do-bg-input) 100%);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.quick-select-btn.select-all-btn:hover {
  background: var(--do-gold);
  color: #fff;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-icon-circle {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--do-gold-light) 0%, var(--do-gold-hover) 100%);
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.08);
}

.title-meta-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.view-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.device-tag {
  font-size: 14px;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.12);
  border: none;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 600;
  font-family: var(--font-family-mono);
  display: inline-flex;
  align-items: center;
}

.title-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.master-bus-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border);
  padding: 4px 12px;
  border-radius: 4px;
}

.bus-lbl {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 700;
}

.bus-val {
  font-size: 14px;
  color: var(--do-gold-deep);
  font-weight: 700;
}

.port-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--do-success);
  font-weight: 600;
}

.status-dot-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 8px rgba(var(--th-success-rgb), 0.8);
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.95);
    opacity: 0.8;
  }

  50% {
    transform: scale(1.3);
    opacity: 1;
  }

  100% {
    transform: scale(0.95);
    opacity: 0.8;
  }
}

.btn-matrix-link {
  background: var(--do-bg-input);
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-matrix-link:hover {
  background: var(--do-gold);
  color: #fff;
}

.btn-mute-all {
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 1px 3px rgba(var(--th-danger-rgb), 0.2);
}

/* 主布局 */
.audio-main-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 14px;
}

.audio-left-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.fader-matrix-card,
.scenes-grid-card,
.audio-right-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
}

.panel-header {
  padding: 12px 18px;
  border-bottom: 1px solid var(--do-border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(var(--th-accent-rgb), 0.08) 0%, rgba(var(--th-accent-rgb), 0.02) 100%);
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-btn {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 14px;
  color: var(--do-text-primary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: var(--do-bg-input);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

/* 调音台推子行排版：12 通道等比自适应栅格，确保在任何屏幕分辨率与浏览器下一行整齐展示 12 个推子并完整铺满父级容器 */
.faders-row {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: clamp(4px, 0.5vw, 8px);
  padding: 14px 10px;
  width: 100%;
  box-sizing: border-box;
  background: var(--do-bg-input);
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
  overflow-x: hidden;
}

/* 单个推子条：精工调音台硬件拟物卡槽（百分比自适应，随父容器 12 等分完全铺满） */
.fader-strip {
  width: 100%;
  min-width: 0;
  max-width: none;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  border-radius: 8px;
  padding: 10px clamp(2px, 0.35vw, 6px) 8px clamp(2px, 0.35vw, 6px);
  box-shadow: 0 1px 4px rgba(var(--th-shadow-rgb), 0.06);
  position: relative;
  transition: all 0.2s ease;
}

.fader-strip:hover {
  border-color: var(--do-gold);
  box-shadow: 0 3px 8px rgba(var(--th-accent-rgb), 0.2);
}

.fader-strip.is-muted {
  background: var(--do-bg-sunken);
  border-color: var(--do-border);
}

.fader-strip.is-solo {
  box-shadow: 0 0 0 2px var(--do-gold);
}

/* 通道顶部指示与功能键 */
.strip-header {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(216, 202, 190, 0.6);
}

.strip-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1px;
}

.ch-meta-wrap {
  display: flex;
  align-items: center;
  gap: 3px;
  min-width: 0;
}

.ch-icon {
  color: var(--do-gold-deep);
  flex-shrink: 0;
}

.ch-id {
  font-size: clamp(11px, 0.8vw, 13px);
  color: var(--do-text-regular);
  font-weight: 700;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.led-indicators {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.sig-led,
.clip-led {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--do-border);
  transition: all 0.1s ease;
}

.sig-led.active {
  background: var(--do-success);
  box-shadow: 0 0 5px var(--do-success);
}

.clip-led.active {
  background: var(--do-danger);
  box-shadow: 0 0 5px var(--do-danger);
}

.strip-buttons {
  display: flex;
  gap: 3px;
  width: 100%;
}

.btn-mute,
.btn-solo {
  flex: 1;
  min-width: 0;
  height: 22px;
  border-radius: 4px;
  font-size: clamp(10px, 0.72vw, 12px);
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  border: 1px solid var(--do-border);
  background: linear-gradient(180deg, var(--do-bg-input) 0%, var(--do-gold-light) 100%);
  color: var(--do-text-secondary);
  padding: 0 1px;
  white-space: nowrap;
  letter-spacing: -0.2px;
}

.btn-mute:hover,
.btn-solo:hover {
  filter: brightness(1.05);
}

.btn-mute.active {
  background: linear-gradient(180deg, var(--do-danger) 0%, var(--do-danger-deep) 100%);
  border-color: var(--do-danger-deep);
  color: #FFFFFF;
  box-shadow: 0 0 6px rgba(var(--th-danger-rgb), 0.5);
}

.btn-solo.active {
  background: linear-gradient(180deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  border-color: var(--do-gold-deep);
  color: #FFFFFF;
  box-shadow: 0 0 6px rgba(212, 167, 71, 0.6);
}

/* 核心推子区域 (刻度 + VU表 + 滑块) */
.fader-core-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(2px, 0.25vw, 4px);
  height: 210px;
  padding: 6px 0;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

/* 刻度尺 (dB Scale) - 自适应字号与紧凑排版 */
.fader-scale {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 190px;
  font-size: clamp(10px, 0.7vw, 12px);
  line-height: 1;
  color: var(--do-text-secondary);
  text-align: right;
  padding-right: 2px;
  user-select: none;
  font-weight: 600;
  flex-shrink: 0;
}

.fader-scale .zero-db {
  color: var(--do-gold-deep);
  font-weight: 800;
}

/* 左右双声道立体声高亮动态电平跳动竖线 (工控黑底 + 绿黄红高对比度动态光柱) */
.vu-meter-col-track {
  width: 5px;
  height: 190px;
  background: var(--do-bg-dark);
  border-radius: 2px;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(var(--th-accent-rgb), 0.4);
  flex-shrink: 0;
}

.vu-meter-col-track .vu-meter-bar {
  display: block;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  min-height: 8px;
  background: linear-gradient(to top,
      var(--do-success) 0%,
      var(--do-success) 65%,
      var(--do-warning) 82%,
      var(--do-danger) 100%);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.85);
  transition: height 0.12s ease-out;
  z-index: 2;
}

.vu-zero-mark {
  position: absolute;
  top: 32px;
  /* 对应 0dB 处 */
  left: 0;
  right: 0;
  height: 1.5px;
  background: #FFFFFF;
  box-shadow: 0 0 3px rgba(255, 255, 255, 0.9);
  z-index: 3;
  pointer-events: none;
}

/* 垂直推子轨道与滑块 */
.slider-slot-container {
  width: clamp(24px, 1.8vw, 30px);
  height: 190px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.fader-slot-zero-line {
  position: absolute;
  top: 34px;
  left: -4px;
  right: -4px;
  height: 1px;
  border-top: 1px dashed rgba(var(--th-accent-rgb), 0.6);
  pointer-events: none;
  z-index: 1;
}

/* 调音台金属推子头 (Motorized Fader Knob) 拟物深度穿透定制 */
:deep(.el-slider.is-vertical) {
  margin: 0 !important;
  height: 190px !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  touch-action: none;
}

/* 垂直推子滑道：强制覆盖全局 height: 5px，彻底恢复 190px 全程垂直拖动手感 */
:deep(.el-slider.is-vertical .el-slider__runway) {
  width: 5px !important;
  height: 100% !important;
  margin: 0 !important;
  position: relative !important;
  background: var(--do-bg-header) !important;
  border-radius: 2px !important;
  border: 1px solid rgba(var(--th-accent-rgb), 0.3) !important;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4) !important;
  cursor: pointer !important;
}

:deep(.el-slider.is-vertical .el-slider__bar) {
  width: 5px !important;
  background: var(--do-gold) !important;
  border-radius: 2px !important;
  opacity: 0.6;
}

/* 专业调音台金属推子帽包围盒：严格左右居中对齐 runway 垂直轨道 */
:deep(.el-slider.is-vertical .el-slider__button-wrapper) {
  left: 50% !important;
  top: auto !important;
  transform: translate(-50%, 50%) !important;
  z-index: 2;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 36px !important;
  height: 36px !important;
  touch-action: none !important;
  user-select: none !important;
}

/* 专业调音台金属推子帽按钮本体：水平严格居中、丝滑上下拖拽手感 */
:deep(.el-slider.is-vertical .el-slider__button) {
  width: clamp(20px, 1.4vw, 24px) !important;
  height: 34px !important;
  margin: 0 auto !important;
  border-radius: 4px !important;
  background: linear-gradient(180deg, var(--do-bg-sunken) 0%, var(--do-border) 45%, var(--do-border) 55%, var(--do-gold-light) 100%) !important;
  border: 1px solid var(--do-text-secondary) !important;
  box-shadow: 0 2px 6px rgba(var(--th-shadow-rgb), 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
  position: relative;
  cursor: grab !important;
  cursor: -webkit-grab !important;
  touch-action: none !important;
  user-select: none !important;
}

:deep(.el-slider.is-vertical .el-slider__button:hover) {
  transform: scale(1.05);
  box-shadow: 0 3px 8px rgba(var(--th-shadow-rgb), 0.45), 0 0 0 1px var(--do-gold) !important;
}

:deep(.el-slider.is-vertical .el-slider__button:active) {
  cursor: grabbing !important;
  cursor: -webkit-grabbing !important;
}

/* 推子帽中央高精度定位白/金线 */
:deep(.el-slider.is-vertical .el-slider__button::before) {
  content: "";
  position: absolute;
  top: 50%;
  left: 2px;
  right: 2px;
  height: 2px;
  background: var(--do-bg-header);
  border-top: 1px solid rgba(255, 255, 255, 0.8);
  transform: translateY(-50%);
  pointer-events: none;
}

/* 静音态下推子头灰暗化 */
:deep(.el-slider.is-disabled .el-slider__button) {
  background: var(--do-border) !important;
  border-color: var(--do-text-secondary) !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
}

/* 分贝数值液晶读数窗 */
.gain-display-box {
  width: 100%;
  height: 22px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-gold-hover);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(11px, 0.78vw, 13px);
  font-weight: 700;
  color: var(--do-gold-deep);
  margin-top: 5px;
  box-sizing: border-box;
  white-space: nowrap;
}

.gain-display-box.muted {
  background: var(--do-danger-bg);
  border-color: var(--do-gold-hover);
  color: var(--do-danger);
}

/* 调音台涂鸦条 (LCD Scribble Strip) - 拟真液晶黑底高对比排版 */
.scribble-strip {
  width: 100%;
  height: 48px;
  background: var(--do-bg-dark);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  border-radius: 4px;
  margin-top: 5px;
  padding: 3px 2px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.5);
  box-sizing: border-box;
}

.scribble-type {
  font-size: clamp(10px, 0.7vw, 11px);
  color: var(--do-gold);
  font-weight: 700;
  letter-spacing: 0.3px;
  line-height: 1;
  margin-bottom: 2px;
  white-space: nowrap;
}

.scribble-name {
  font-size: clamp(10px, 0.78vw, 12px);
  color: var(--do-bg-card);
  line-height: 1.15;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

/* 2. 赛事场景音效卡片网格 */
.active-scene-summary {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.active-scene-summary strong {
  color: var(--do-gold-deep);
}

.scene-buttons-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 16px 18px;
}

.scene-tile {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 8px;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  min-height: 112px;
}

.scene-tile:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--th-shadow-rgb), 0.08);
}

.scene-tile.active {
  background: linear-gradient(180deg, var(--do-bg-input) 0%, var(--do-gold-light) 100%);
  border-color: var(--do-gold);
  box-shadow: 0 0 0 1.5px var(--do-gold), 0 4px 14px rgba(var(--th-accent-rgb), 0.2);
}

.scene-tile-badge {
  font-size: 14px;
  color: var(--do-text-placeholder);
  font-weight: 700;
  letter-spacing: 0.5px;
}

.scene-tile.active .scene-tile-badge {
  color: var(--do-gold-deep);
}

.scene-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tile-icon-circle {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--do-bg-input);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--do-gold-deep);
  flex-shrink: 0;
}

.scene-tile.active .tile-icon-circle {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
}

.tile-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tile-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
  line-height: 1.3;
}

.tile-desc {
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.active-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--do-success);
  font-weight: 700;
  padding-top: 5px;
  border-top: 1px dashed rgba(var(--th-accent-rgb), 0.4);
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 6px var(--do-success);
}

/* 右侧面板：串口通信与终端流水 */
.audio-right-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.comm-header {
  border-bottom: 1px solid var(--do-border-light);
}

.comm-badge {
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 700;
}

.comm-badge.online {
  background: rgba(var(--th-success-rgb), 0.15);
  color: var(--do-success);
  border: 1px solid rgba(var(--th-success-rgb), 0.4);
}

.comm-leds {
  display: flex;
  align-items: center;
  gap: 6px;
}

.comm-led-label {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-family: var(--font-family-mono);
  font-weight: 700;
}

.traffic-led {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--do-border);
  transition: all 0.1s;
}

.tx-led.active {
  background: var(--do-warning);
  box-shadow: 0 0 7px var(--do-warning);
}

.rx-led.active {
  background: var(--do-success);
  box-shadow: 0 0 7px var(--do-success);
}

.comm-stats-box {
  padding: 14px 16px;
  background: var(--do-bg-input);
  border-bottom: 1px solid var(--do-border-light);
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 14px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-lbl {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.stat-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
}

/* 终端流水控制区 */
.console-section {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.console-toolbar {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--do-gold-light);
  border-bottom: 1px solid var(--do-border-light);
}

.console-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.console-btn {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 14px;
  color: var(--do-text-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.console-btn:hover {
  color: var(--do-gold-deep);
  border-color: var(--do-gold);
}

/* 工控暗黑石金终端滚动区 */
.comm-log-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  line-height: 1.5;
  background: var(--do-bg-dark);
  min-height: 320px;
  max-height: 380px;
}

.log-entry {
  display: flex;
  gap: 8px;
  align-items: baseline;
  word-break: break-all;
}

.log-t {
  color: var(--do-text-secondary);
  flex-shrink: 0;
  font-size: 14px;
}

.log-dir {
  font-weight: 700;
  flex-shrink: 0;
  font-size: 14px;
  padding: 0 4px;
  border-radius: 2px;
}

.log-dir.TX {
  color: var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.15);
}

.log-dir.RX {
  color: var(--do-success);
  background: rgba(103, 194, 58, 0.15);
}

.log-msg {
  color: var(--do-gold-light);
}

/* ============================================================================
   统一控制台视觉与响应式布局
   参照大屏调度、计时计分页面，确保卡片不会撑破主容器
   ============================================================================ */
.audio-control-workspace {
  min-width: 0;
  color: var(--do-text-primary);
}

.glass-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
}

.page-header,
.page-heading,
.title-row,
.header-status,
.status-metric,
.target-toolbar,
.section-heading,
.target-actions,
.mixer-card-top,
.mixer-identity,
.mixer-location,
.mixer-card-footer,
.panel-heading,
.panel-actions,
.comm-leds {
  display: flex;
  align-items: center;
}

.page-header {
  justify-content: space-between;
  gap: 20px;
  padding: 18px 22px;
}

.page-heading {
  min-width: 0;
  gap: 14px;
}

.page-heading>div:last-child {
  min-width: 0;
}

.page-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  color: var(--do-gold);
  background: var(--do-gold-wash);
  border: 1px solid var(--do-border-dark);
  border-radius: 12px;
}

.page-header h1,
.control-card h2,
.scenes-card h2,
.comm-panel h2,
.target-toolbar h2,
.mixer-card h3 {
  margin: 0;
}

.page-header h1 {
  min-width: 0;
  overflow: hidden;
  font-size: 21px;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-header p,
.section-help {
  display: block;
  margin: 5px 0 0;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.title-row {
  min-width: 0;
  gap: 10px;
}

.device-tag {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  max-width: min(46vw, 520px);
  overflow: hidden;
  padding: 4px 8px;
  color: var(--do-gold-deep);
  background: var(--do-gold-wash);
  border: 1px solid var(--do-border-dark);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-status {
  justify-content: flex-end;
  flex: 0 0 auto;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.status-metric {
  gap: 6px;
  white-space: nowrap;
}

.status-metric strong {
  color: var(--do-text-primary);
  font-size: 15px;
}

.status-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: currentColor;
}

.status-dot.online {
  color: var(--do-success);
  box-shadow: 0 0 7px currentColor;
}

.status-dot.muted {
  color: var(--do-text-placeholder);
}

.btn-matrix-link {
  color: var(--do-gold-deep);
  background: var(--do-bg-input);
  border-color: var(--do-gold);
  font-weight: 600;
}

.btn-matrix-link:hover {
  color: #fff;
  background: var(--do-gold);
  border-color: var(--do-gold);
}

.btn-mute-all {
  font-weight: 700;
}

.target-toolbar {
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
}

.section-heading,
.panel-heading {
  justify-content: space-between;
  min-width: 0;
  gap: 12px;
}

.section-heading {
  flex: 1;
}

.target-toolbar h2,
.panel-heading h2 {
  font-size: 16px;
  line-height: 1.35;
}

.selection-count {
  color: var(--do-gold-deep);
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.target-actions,
.panel-actions {
  gap: 8px;
  flex-wrap: wrap;
}

.target-actions :deep(.el-button),
.panel-actions :deep(.el-button) {
  margin-left: 0;
}

.mixer-wall {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  min-width: 0;
}

.mixer-card {
  position: relative;
  min-width: 0;
  padding: 15px;
  cursor: pointer;
  transition: border-color .2s, box-shadow .2s, transform .2s;
}

.mixer-card:hover,
.mixer-card.selected {
  border-color: var(--do-gold);
  box-shadow: var(--shadow-hover, 0 4px 14px rgba(var(--th-accent-rgb), .18));
}

.mixer-card.selected {
  background: var(--do-gold-wash);
  box-shadow: 0 0 0 2px var(--do-gold-wash-strong, rgba(var(--th-accent-rgb), .12));
}

.mixer-card-top {
  justify-content: space-between;
  gap: 10px;
}

.mixer-identity {
  min-width: 0;
  gap: 9px;
}

.mixer-icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  color: var(--do-gold);
  background: var(--do-bg-sunken);
  border-radius: 8px;
}

.mixer-identity>div:last-child {
  min-width: 0;
}

.mixer-card h3 {
  overflow: hidden;
  font-size: 15px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-code {
  display: block;
  margin-top: 4px;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.mixer-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 13px;
  white-space: nowrap;
}

.mixer-status.online {
  color: var(--do-success-deep);
  letter-spacing: 3px;
  background: var(--do-success-bg);
}

.mixer-status.offline,
.mixer-status.fault,
.mixer-status.warning {
  color: var(--do-warning-deep);
  letter-spacing: 3px;
  background: var(--do-warning-bg);
}

.mixer-location {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
  margin: 14px 0 12px;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.location-info {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mixer-conn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  flex-shrink: 0;
}

.field-label {
  color: var(--do-text-secondary);
  font-size: 13px;
}

.mixer-conn strong {
  min-width: 0;
  color: var(--do-gold-deep);
  font-size: 13px;
  white-space: nowrap;
}

.mixer-card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 14px;
  padding-top: 11px;
  border-top: 1px solid var(--do-border-light);
}

.selection-state {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--do-text-secondary);
  font-size: 14px;
  margin-left: auto;
}

.selection-state.active {
  color: var(--do-gold-deep);
}

.main-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(310px, 340px);
  gap: 14px;
  align-items: start;
  min-width: 0;
}

.main-left {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.control-card,
.scenes-card,
.comm-panel {
  min-width: 0;
  overflow: hidden;
}

.control-card,
.scenes-card {
  padding: 0;
}

.control-card>.panel-heading,
.scenes-card>.panel-heading,
.comm-panel>.panel-heading {
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border-light);
  background: linear-gradient(180deg, rgba(var(--th-accent-rgb), .06), rgba(var(--th-accent-rgb), .015));
}

.panel-heading>div:first-child {
  min-width: 0;
}

.panel-heading h2 {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-actions {
  flex: 0 0 auto;
}

.active-scene-badge {
  flex: 0 0 auto;
  color: var(--do-text-secondary);
  font-size: 13px;
  white-space: nowrap;
}

.active-scene-badge strong {
  color: var(--do-gold-deep);
}

.faders-row {
  min-width: 0;
  padding: 16px 12px;
}

.scene-buttons-row {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.comm-panel {
  display: flex;
  flex-direction: column;
}

.comm-header {
  align-items: flex-start !important;
}

.comm-header>div:first-child {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.comm-header h2 {
  min-width: 0;
}

.comm-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  color: var(--do-text-secondary);
  border: 1px solid var(--do-border);
  border-radius: 5px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.comm-badge.online {
  color: var(--do-success-deep);
  background: var(--do-success-bg);
  border-color: var(--do-success-border, rgba(var(--th-success-rgb), .35));
}

.comm-leds {
  flex: 0 0 auto;
  gap: 6px;
  padding-top: 4px;
}

.comm-led-label {
  color: var(--do-text-secondary);
  font-family: var(--font-mono, Consolas, monospace);
  font-size: 12px;
  font-weight: 700;
}

.comm-stats-box {
  padding: 14px 16px;
}

.stat-grid {
  gap: 12px;
}

.stat-item {
  min-width: 0;
}

.stat-val {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.console-section {
  min-height: 0;
  border-top: 1px solid var(--do-border-light);
}

.console-toolbar {
  background: var(--do-bg-sunken);
}

.console-actions {
  display: flex;
  align-items: center;
}

.comm-log-scroll {
  min-height: 300px;
  max-height: 420px;
}

@media (max-width: 1360px) {
  .page-header {
    align-items: flex-start;
  }

  .page-header h1 {
    font-size: 19px;
  }

  .header-status {
    max-width: 46%;
  }

  .device-tag {
    max-width: 36vw;
  }

  .scene-buttons-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1180px) {
  .main-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .comm-panel {
    display: grid;
    grid-template-columns: minmax(250px, .8fr) minmax(0, 1.2fr);
    align-items: stretch;
  }

  .comm-panel>.panel-heading {
    grid-column: 1 / -1;
  }

  .comm-stats-box {
    border-right: 1px solid var(--do-border-light);
  }

  .console-section {
    border-top: 0;
  }
}

@media (max-width: 820px) {

  .page-header,
  .target-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-status {
    justify-content: flex-start;
    max-width: none;
  }

  .device-tag {
    max-width: 42vw;
  }

  .mixer-wall {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .comm-panel {
    display: flex;
  }

  .comm-stats-box {
    border-right: 0;
  }

  .console-section {
    border-top: 1px solid var(--do-border-light);
  }

  .panel-heading {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .panel-actions {
    width: 100%;
  }
}

@media (max-width: 560px) {

  .page-header,
  .target-toolbar,
  .control-card>.panel-heading,
  .scenes-card>.panel-heading,
  .comm-panel>.panel-heading {
    padding: 14px;
  }

  .page-heading {
    align-items: flex-start;
  }

  .page-icon {
    width: 44px;
    height: 44px;
  }

  .page-header h1 {
    font-size: 17px;
    white-space: normal;
  }

  .title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .device-tag {
    max-width: 100%;
  }

  .header-status,
  .target-actions,
  .panel-actions {
    width: 100%;
  }

  .header-status :deep(.el-button),
  .target-actions :deep(.el-button),
  .panel-actions :deep(.el-button) {
    flex: 1 1 auto;
  }

  .mixer-wall,
  .scene-buttons-row {
    grid-template-columns: 1fr;
  }

  .mixer-card {
    padding: 13px;
  }

  .comm-header>div:first-child {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }

  .faders-row {
    padding-inline: 8px;
  }
}
</style>
