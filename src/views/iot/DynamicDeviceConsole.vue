<template>
  <div class="dynamic-console-workspace">
    <!-- 顶部状态栏 -->
    <div class="dynamic-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgDynamicDevice" size="20" class="text-primary" />
        <div class="title-meta">
          <span class="view-title">动态低代码通用设备控制台</span>
          <p>根据后台 JSON Schema 动态生成设备控件和操作面板，无需为每类设备重复开发页面。</p>
        </div>
        <span class="group-tag">当前分组: {{ currentGroup.name }} ({{ currentGroup.code }})</span>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-manage" @click="isDrawerOpen = true" title="查看并在线调试控件 JSON Schema 元数据">
          <SvgIcon name="SvgLowCodeConfig" size="14" style="margin-right: 4px;" />
          <span>查看/调试组件元数据</span>
        </button>
        <button class="btn-header-action btn-header-primary" @click="refreshMetadata" title="重新从后台服务拉取最新控件动态渲染元数据">
          <SvgIcon name="SvgRefresh" size="14" style="margin-right: 4px;" />
          <span>重新拉取元数据</span>
        </button>
      </div>
    </div>

    <!-- 主操作区：动态渲染画布 + 右侧元数据抽屉 -->
    <div class="dynamic-canvas glass-panel">
      <div class="panel-header">
        <div class="header-title">
          <span>元数据自适应渲染工作区 (Metadata-Driven Canvas)</span>
          <span class="panel-subtitle">此面板所有按钮、滑块、开关完全由后台 JSON Schema 动态生成，零硬编码</span>
        </div>
        <span class="num-mono text-primary">已加载 {{ schemaWidgets.length }} 个动态控件组件</span>
      </div>

      <!-- 动态控件渲染流 -->
      <div class="widgets-flow-grid">
        <div
          v-for="widget in schemaWidgets"
          :key="widget.id"
          class="widget-card glass-panel"
        >
          <div class="widget-head">
            <span class="widget-name">{{ widget.label }}</span>
            <span class="widget-proto num-mono">{{ widget.protocol }}</span>
          </div>

          <!-- 控件类型1: 脉冲动作按钮 -->
          <div v-if="widget.type === 'PULSE_BUTTON'" class="widget-body">
            <p class="widget-desc">{{ widget.desc }}</p>
            <button
              :class="['btn-industrial', widget.btnClass, 'btn-control-action']"
              @click="triggerAction(widget)"
            >
              {{ widget.btnText }}
            </button>
          </div>

          <!-- 控件类型2: 双向状态微动开关 -->
          <div v-else-if="widget.type === 'TOGGLE_SWITCH'" class="widget-body">
            <p class="widget-desc">{{ widget.desc }}</p>
            <div class="switch-row">
              <span class="switch-state-text">{{ widget.state ? widget.onText : widget.offText }}</span>
              <el-switch v-model="widget.state" @change="triggerSwitch(widget)" />
            </div>
          </div>

          <!-- 控件类型3: 模拟量调节滑块 -->
          <div v-else-if="widget.type === 'ANALOG_SLIDER'" class="widget-body">
            <div class="slider-header-row">
              <span class="widget-desc">{{ widget.desc }}</span>
              <span class="slider-cur-val num-mono font-bold text-primary">{{ widget.value }} {{ widget.unit }}</span>
            </div>
            <el-slider
              v-model="widget.value"
              :min="widget.min"
              :max="widget.max"
              :step="widget.step"
              @change="triggerSlider(widget)"
            />
          </div>

          <!-- 控件类型4: 数值步进输入 -->
          <div v-else-if="widget.type === 'NUMBER_INPUT'" class="widget-body">
            <p class="widget-desc">{{ widget.desc }}</p>
            <el-input-number
              v-model="widget.value"
              :min="widget.min"
              :max="widget.max"
              size="small"
              @change="triggerNumber(widget)"
            />
          </div>

          <!-- 底部指令摘要 -->
          <div class="widget-foot-cmd num-mono">
            <span>指令报文: {{ widget.cmdPayload }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧 JSON 元数据实时对照抽屉 -->
    <el-drawer
      v-model="isDrawerOpen"
      title="动态面板 JSON 元数据驱动字典 (Button & Input Schema)"
      size="520px"
      direction="rtl"
    >
      <div class="drawer-schema-box">
        <p class="schema-desc">
          前端通过读取该元数据字典，动态映射组件树、协议类型与通信报文。运维人员可直接在配置中心修改此 Schema，无需前端重新打包即可实现新硬件秒级热上线：
        </p>
        <pre class="schema-json-code num-mono">{{ JSON.stringify(schemaWidgets, null, 2) }}</pre>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const isDrawerOpen = ref(false)

const currentGroup = ref({
  code: 'GROUP_DIVING_SPECIAL',
  name: '跳水比赛池特种机电控制组'
})

// 动态控件元数据定义
const schemaWidgets = ref([
  {
    id: 'w1',
    label: '水面水花消除造浪气泵',
    type: 'TOGGLE_SWITCH',
    protocol: 'MODBUS_TCP',
    desc: '向跳水池水面释放压缩微气泡，消除水面反光镜面感',
    state: true,
    onText: '气泵强劲鼓泡中',
    offText: '气泵停止',
    cmdPayload: '01 05 00 01 FF 00 (Coil 1)'
  },
  {
    id: 'w2',
    label: '跳台喷淋花洒温水阀',
    type: 'TOGGLE_SWITCH',
    protocol: 'SERIAL_RS485',
    desc: '运动员起跳前冲淋温水防抽筋',
    state: false,
    onText: '温水喷淋开启',
    offText: '喷淋阀门关闭',
    cmdPayload: '55 AA 03 01 01 9A'
  },
  {
    id: 'w3',
    label: '跳水池恒温热泵水温设定',
    type: 'ANALOG_SLIDER',
    protocol: 'MODBUS_RTU',
    desc: '比赛标准水温: 26.0℃ ~ 28.0℃',
    value: 27.5,
    min: 24,
    max: 32,
    step: 0.5,
    unit: '℃',
    cmdPayload: '02 06 00 10 01 13 (Reg 16)'
  },
  {
    id: 'w4',
    label: '池底循环水流流速调节',
    type: 'ANALOG_SLIDER',
    protocol: 'TCP_SOCKET',
    desc: '变频循环水泵转速控制 (0~100%)',
    value: 65,
    min: 0,
    max: 100,
    step: 5,
    unit: '%',
    cmdPayload: 'SET_PUMP_SPEED:65'
  },
  {
    id: 'w5',
    label: '水质余氯自动投药加注脉冲',
    type: 'PULSE_BUTTON',
    btnText: '单次加注 50ml',
    btnClass: 'btn-primary',
    protocol: 'HTTP_POST',
    desc: '触发自动计量泵单次定量投药',
    cmdPayload: 'POST /api/v1/dosing/feed {amount: 50}'
  },
  {
    id: 'w6',
    label: '循环过滤砂缸反冲洗排污',
    type: 'PULSE_BUTTON',
    btnText: '一键启动反冲洗 (历时180s)',
    btnClass: 'btn-danger',
    protocol: 'SERIAL_RS485',
    desc: '高压反洗泳池多介质石英砂过滤器',
    cmdPayload: '55 AA 05 01 FF E3'
  }
])

const triggerAction = (widget) => {
  ElMessage.success(`已下发指令：【${widget.label}】 -> ${widget.cmdPayload}`)
}

const triggerSwitch = (widget) => {
  ElMessage.info(`已切换【${widget.label}】状态为：${widget.state ? '开启' : '关闭'}`)
}

const triggerSlider = (widget) => {
  ElMessage.info(`【${widget.label}】已调节设定值为：${widget.value} ${widget.unit}`)
}

const triggerNumber = (widget) => {
  ElMessage.info(`【${widget.label}】数值已更新为：${widget.value}`)
}

const refreshMetadata = () => {
  ElMessage.success('已重新从元数据驱动中心同步最新 Schema！')
}
</script>

<style scoped>
.dynamic-console-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.dynamic-top-bar {
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

.group-tag {
  font-size: 14px;
  color: var(--do-gold-dark);
  background: rgba(var(--th-accent-rgb), 0.15);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.top-right {
  display: flex;
  gap: 12px;
}

.dynamic-canvas {
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

.widgets-flow-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.widget-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #FFFFFF;
  border: 1px solid var(--do-border-card);
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(var(--th-shadow-rgb), 0.04);
  transition: all 0.2s ease;
}

.widget-card:hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 12px rgba(var(--th-accent-rgb), 0.15);
}

.widget-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
}

.widget-proto {
  font-size: 14px;
  color: var(--do-gold-dark);
  background: rgba(var(--th-accent-rgb), 0.15);
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.widget-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.widget-desc {
  font-size: 14px;
  color: var(--do-coffee-light);
  line-height: 1.5;
  margin: 0;
}

.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--do-sand-light);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.5);
}

.switch-state-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-coffee);
}

.slider-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-foot-cmd {
  font-size: 14px;
  color: var(--do-coffee-mid);
  background: var(--do-sand-light);
  padding: 6px 10px;
  border-radius: 4px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
}

.drawer-schema-box {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.schema-desc {
  font-size: 14px;
  color: var(--do-coffee-light);
  line-height: 1.6;
}

.schema-json-code {
  background: var(--do-sand-light);
  border: 1px solid var(--do-border-card);
  border-radius: 6px;
  padding: 14px;
  font-size: 14px;
  color: var(--do-coffee);
  overflow-x: auto;
  max-height: 520px;
}
</style>
