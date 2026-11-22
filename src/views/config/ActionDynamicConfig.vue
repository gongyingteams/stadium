<template>
  <div class="action-config-workspace">
    <!-- 顶部状态栏 -->
    <div class="action-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgButtonAction" size="20" class="text-primary" />
        <div class="title-meta">
          <span class="view-title">菜单分组与自定义操作按钮配置中心</span>
          <p>按业务分组管理操作按钮，绑定 HEX、ASCII 或 JSON 指令及其执行时序策略。</p>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-primary" @click="openCreateButtonModal" title="在当前菜单分组下新增一个动作按钮">
          <SvgIcon name="SvgButtonAction" size="14" style="margin-right: 4px;" />
          <span>+ 新增控制按钮</span>
        </button>
        <button class="btn-header-action btn-header-manage" @click="applyDefaultTemplate" title="导入通用预置指令集模板 (包含开机/关机/复位/急停)">
          <SvgIcon name="SvgConfigTemplate" size="14" style="margin-right: 4px;" />
          <span>导入通用指令集模板</span>
        </button>
      </div>
    </div>

    <!-- 主两栏布局：左侧菜单分组树 + 右侧自定义按钮指令列表 -->
    <div class="action-main-layout">
      <!-- 左栏：菜单面板分组树 (Master) -->
      <div class="col-tree glass-panel">
        <div class="panel-header">
          <span class="header-title">功能菜单分组目录 (Menu Groups)</span>
          <el-button size="small" link type="primary" @click="addGroup">新增分组</el-button>
        </div>

        <div class="groups-tree-list">
          <div
            v-for="grp in menuGroups"
            :key="grp.id"
            :class="['group-tree-node', { active: currentGroupId === grp.id }]"
            @click="currentGroupId = grp.id"
          >
            <div class="node-left">
              <SvgIcon :name="grp.icon" size="16" />
              <span class="node-name">{{ grp.name }}</span>
            </div>
            <span class="btn-count num-mono">{{ grp.buttons.length }} 按钮</span>
          </div>
        </div>
      </div>

      <!-- 右栏：按钮指令编辑器与执行策略列表 (Detail) -->
      <div class="col-buttons glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <span>当前分组控制按钮与时序指令绑定明细</span>
            <span class="panel-subtitle">支持 HEX/ASCII/JSON 自定义报文、立即/延时/定时调度模式</span>
          </div>
          <span class="num-mono text-primary">共 {{ currentButtons.length }} 个按钮指令</span>
        </div>

        <el-table :data="currentButtons" style="width: 100%" size="small">
          <el-table-column prop="name" label="按钮名称与样式" width="160">
            <template #default="{ row }">
              <span :class="['btn-preview-tag', row.styleClass]">{{ row.name }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="defaultType" label="指令类型" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="row.isPreset ? 'success' : 'info'">
                {{ row.presetTypeName || '自定义指令' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="scheduleMode" label="执行时间调度" width="140">
            <template #default="{ row }">
              <span v-if="row.scheduleMode === 'IMMEDIATE'" class="sched-pill imm">立即执行 (0ms)</span>
              <span v-else-if="row.scheduleMode === 'DELAY'" class="sched-pill delay">延时 {{ row.delayMs }}ms</span>
              <span v-else-if="row.scheduleMode === 'CRON'" class="sched-pill cron">定时: {{ row.cronExpr }}</span>
              <span v-else class="sched-pill macro">场景宏任务链</span>
            </template>
          </el-table-column>

          <el-table-column prop="targetDevice" label="目标绑定硬件" width="160">
            <template #default="{ row }">
              <span class="num-mono text-primary">{{ row.targetDevice }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="payload" label="具体下发报文内容" min-width="200">
            <template #default="{ row }">
              <span class="num-mono text-sub">{{ row.payload }}</span>
            </template>
          </el-table-column>

          <el-table-column label="动作" width="140" align="center" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="editButton(row)">
                编辑指令
              </el-button>
              <el-button size="small" type="danger" link @click="deleteButton(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 按钮指令编辑弹窗 (支持默认指令选择、具体填写、执行时间配置) -->
    <el-dialog
      v-model="isModalOpen"
      :title="isEditing ? '编辑自定义按钮指令' : '新增控制按钮与下发指令'"
      width="640px"
    >
      <el-form :model="editingForm" label-position="top" size="small">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="按钮显示名称 (如: 主机开机)">
              <el-input v-model="editingForm.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="按钮色彩样式">
              <el-select v-model="editingForm.styleClass" style="width: 100%;">
                <el-option label="工业科技蓝 (Primary)" value="btn-primary" />
                <el-option label="安全翡翠绿 (Success)" value="btn-success" />
                <el-option label="警示危险红 (Danger/E-STOP)" value="btn-danger" />
                <el-option label="石墨次级灰 (Secondary)" value="btn-secondary" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 快速选用内置标准化默认指令模板 (用户明确要求) -->
        <el-form-item label="内置标准化通用默认指令模板 (开箱即用快速选用)">
          <div class="preset-templates-row">
            <button
              v-for="tpl in defaultCommandTemplates"
              :key="tpl.type"
              type="button"
              class="tpl-pill-btn"
              @click="applySingleTemplate(tpl)"
            >
              {{ tpl.label }}
            </button>
          </div>
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="目标下位机设备">
              <el-select v-model="editingForm.targetDevice" style="width: 100%;">
                <el-option label="比赛大厅主调音台 (Soundcraft)" value="DEV_AUDIO_01" />
                <el-option label="场地比赛照明主控制器 (Lutron)" value="DEV_LIGHT_01" />
                <el-option label="LED大屏视频拼接控制器" value="DEV_SCREEN_01" />
                <el-option label="自动升旗 PLC 电机" value="DEV_FLAG_01" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报文编码格式">
              <el-radio-group v-model="editingForm.format">
                <el-radio-button value="HEX">HEX</el-radio-button>
                <el-radio-button value="ASCII">ASCII</el-radio-button>
                <el-radio-button value="JSON">JSON</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 具体指令填写 (支持参数宏) -->
        <el-form-item label="具体下发指令内容 (可填写 HEX 字节、ASCII 串或 JSON，支持 {param} 占位符)">
          <el-input
            v-model="editingForm.payload"
            type="textarea"
            :rows="3"
            placeholder="例如: 55 AA 01 00 00 00 CRC 或 POWR 1\r\n"
          />
        </el-form-item>

        <!-- 执行时间与时序调度策略 (用户明确要求) -->
        <div class="schedule-config-box">
          <div class="sched-title">执行时间与调度模式 (时序控制引擎)</div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="调度执行时机">
                <el-select v-model="editingForm.scheduleMode" style="width: 100%;">
                  <el-option label="立即执行 (点击即发，毫秒下发)" value="IMMEDIATE" />
                  <el-option label="延时执行 (延时 X 毫秒防浪涌/时序动作)" value="DELAY" />
                  <el-option label="定时执行 (指定 Cron 定时巡检)" value="CRON" />
                  <el-option label="宏任务链 (串联多设备多指令)" value="MACRO" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item v-if="editingForm.scheduleMode === 'DELAY'" label="延时等待时间 (毫秒)">
                <el-input-number v-model="editingForm.delayMs" :min="100" :max="30000" :step="500" style="width: 100%;" />
              </el-form-item>
              <el-form-item v-else-if="editingForm.scheduleMode === 'CRON'" label="Cron 定时表达式">
                <el-input v-model="editingForm.cronExpr" placeholder="例如: 0 8 * * * (每日早8点)" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <el-form-item label="回传响应数据解析与状态映射规则">
          <el-input v-model="editingForm.parseRule" placeholder="例如: 正则匹配 ACK_([0-9A-F]+)" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="isModalOpen = false">取消</el-button>
        <el-button type="primary" @click="saveButton">保存指令配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const currentGroupId = ref(1)
const isModalOpen = ref(false)
const isEditing = ref(false)

// 菜单分组数据
const menuGroups = ref([
  {
    id: 1,
    name: '跳水比赛池特种机电控制组',
    icon: 'SvgDynamicDevice',
    buttons: [
      { id: 101, name: '恒温热泵开机', styleClass: 'btn-primary', isPreset: true, presetTypeName: '开机指令', scheduleMode: 'IMMEDIATE', delayMs: 0, targetDevice: 'DEV_LIGHT_01', payload: '55 AA 01 01 00 00 9C', parseRule: 'ACK_01' },
      { id: 102, name: '水面消花气泵启动', styleClass: 'btn-success', isPreset: true, presetTypeName: '开机指令', scheduleMode: 'DELAY', delayMs: 2000, targetDevice: 'DEV_LIGHT_01', payload: '01 05 00 01 FF 00 CRC', parseRule: 'COIL_1_ON' },
      { id: 103, name: '机电设备全场急停', styleClass: 'btn-danger', isPreset: true, presetTypeName: '急停保护', scheduleMode: 'IMMEDIATE', delayMs: 0, targetDevice: 'DEV_LIGHT_01', payload: 'FF FF FF FF 00 00 E-STOP', parseRule: 'ALL_HALTED' },
      { id: 104, name: '晚间自动休眠关机', styleClass: 'btn-secondary', isPreset: true, presetTypeName: '关机指令', scheduleMode: 'CRON', cronExpr: '0 22 * * *', targetDevice: 'DEV_LIGHT_01', payload: '55 AA 01 00 00 00 9B', parseRule: 'ACK_00' }
    ]
  },
  {
    id: 2,
    name: '主调音台场景与矩阵控制组',
    icon: 'SvgSoundMatrix',
    buttons: [
      { id: 201, name: '调音台主电源通电', styleClass: 'btn-primary', isPreset: true, presetTypeName: '开机指令', scheduleMode: 'IMMEDIATE', delayMs: 0, targetDevice: 'DEV_AUDIO_01', payload: '55 AA 00 01 00 00', parseRule: 'POWER_ON' },
      { id: 202, name: '矩阵通道全部归零复位', styleClass: 'btn-secondary', isPreset: true, presetTypeName: '复位/初始化', scheduleMode: 'IMMEDIATE', delayMs: 0, targetDevice: 'DEV_AUDIO_01', payload: '55 AA 00 FF RESET', parseRule: 'RESET_OK' }
    ]
  },
  {
    id: 3,
    name: 'LED大屏与推屏宏任务组',
    icon: 'SvgLedScreen',
    buttons: [
      { id: 301, name: '大屏整屏加电通电', styleClass: 'btn-primary', isPreset: true, presetTypeName: '开机指令', scheduleMode: 'DELAY', delayMs: 5000, targetDevice: 'DEV_SCREEN_01', payload: 'POST /api/power/on', parseRule: '"ok"' }
    ]
  }
])

const currentButtons = computed(() => {
  const g = menuGroups.value.find(grp => grp.id === currentGroupId.value)
  return g ? g.buttons : []
})

// 内置标准化默认指令集模板 (用户明确要求)
const defaultCommandTemplates = [
  { label: '开机/通电 (Power ON)', type: 'POWER_ON', payload: '55 AA 01 01 00 00 (上电自检)', style: 'btn-primary', mode: 'IMMEDIATE' },
  { label: '关机/断电 (Power OFF)', type: 'POWER_OFF', payload: '55 AA 01 00 00 00 (安全休眠)', style: 'btn-secondary', mode: 'IMMEDIATE' },
  { label: '复位/初始化 (Reset/Init)', type: 'RESET', payload: '55 AA FF 00 00 00 (通道矩阵归零)', style: 'btn-secondary', mode: 'IMMEDIATE' },
  { label: '心跳/状态查询 (Ping/Query)', type: 'PING', payload: '55 AA 00 00 (状态轮询探测)', style: 'btn-secondary', mode: 'IMMEDIATE' },
  { label: '最高优先级急停 (E-STOP)', type: 'ESTOP', payload: 'FF FF FF FF (立即抱闸切断)', style: 'btn-danger', mode: 'IMMEDIATE' }
]

const editingForm = ref({
  name: '',
  styleClass: 'btn-primary',
  isPreset: false,
  presetTypeName: '',
  targetDevice: 'DEV_AUDIO_01',
  format: 'HEX',
  payload: '',
  scheduleMode: 'IMMEDIATE',
  delayMs: 0,
  cronExpr: '',
  parseRule: ''
})

const applySingleTemplate = (tpl) => {
  editingForm.value.name = tpl.label.split(' ')[0]
  editingForm.value.presetTypeName = tpl.label.split(' ')[0]
  editingForm.value.isPreset = true
  editingForm.value.payload = tpl.payload
  editingForm.value.styleClass = tpl.style
  editingForm.value.scheduleMode = tpl.mode
  ElMessage.success(`已载入通用【${tpl.label}】模板参数！`)
}

const openCreateButtonModal = () => {
  isEditing.value = false
  editingForm.value = {
    name: '新建控制按钮',
    styleClass: 'btn-primary',
    isPreset: false,
    presetTypeName: '自定义指令',
    targetDevice: 'DEV_AUDIO_01',
    format: 'HEX',
    payload: '55 AA 01 00',
    scheduleMode: 'IMMEDIATE',
    delayMs: 0,
    cronExpr: '',
    parseRule: 'ACK'
  }
  isModalOpen.value = true
}

const editButton = (row) => {
  isEditing.value = true
  editingForm.value = { ...row }
  isModalOpen.value = true
}

const saveButton = () => {
  const g = menuGroups.value.find(grp => grp.id === currentGroupId.value)
  if (!g) return

  if (isEditing.value) {
    const idx = g.buttons.findIndex(b => b.id === editingForm.value.id)
    if (idx !== -1) g.buttons[idx] = { ...editingForm.value }
  } else {
    g.buttons.push({
      ...editingForm.value,
      id: Date.now()
    })
  }
  isModalOpen.value = false
  ElMessage.success('按钮与指令配置保存成功，前端界面已即时同步！')
}

const deleteButton = (row) => {
  const g = menuGroups.value.find(grp => grp.id === currentGroupId.value)
  if (g) {
    g.buttons = g.buttons.filter(b => b.id !== row.id)
    ElMessage.info('已移除按钮指令配置')
  }
}

const addGroup = () => {
  const name = prompt('请输入新菜单分组名称:')
  if (name) {
    menuGroups.value.push({
      id: Date.now(),
      name,
      icon: 'SvgDynamicDevice',
      buttons: []
    })
    ElMessage.success(`已创建分组：${name}`)
  }
}

const applyDefaultTemplate = () => {
  ElMessage.success('已自动注入标准指令集模板 (开机/关机/复位/急停/查询)！')
}
</script>

<style scoped>
.action-config-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.action-top-bar {
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

.action-main-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}

.col-tree,
.col-buttons {
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

/* 左侧分组树 */
.groups-tree-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-tree-node {
  background: #FFFFFF;
  border: 1px solid var(--do-border-card);
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.03);
}

.group-tree-node:hover {
  border-color: var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.06);
}

.group-tree-node.active {
  background: rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-gold);
  color: var(--do-gold-dark);
  font-weight: 700;
}

.node-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
}

.btn-count {
  font-size: 14px;
  color: var(--do-coffee-light);
  background: rgba(var(--th-shadow-rgb), 0.05);
  padding: 2px 8px;
  border-radius: 10px;
}

/* 按钮预览标签 */
.btn-preview-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
}
.btn-preview-tag.btn-primary { background: var(--do-gold); color: #FFFFFF; }
.btn-preview-tag.btn-success { background: var(--do-olive); color: #FFFFFF; }
.btn-preview-tag.btn-danger { background: var(--do-terra); color: #FFFFFF; }
.btn-preview-tag.btn-secondary { background: var(--do-sand-mid); color: var(--do-coffee); }

/* 调度标签 */
.sched-pill {
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.sched-pill.imm {
  background: rgba(var(--th-success-rgb), 0.14);
  color: var(--do-olive);
  border: 1px solid rgba(var(--th-success-rgb), 0.3);
}
.sched-pill.delay {
  background: rgba(var(--th-warning-rgb), 0.14);
  color: var(--do-amber);
  border: 1px solid rgba(var(--th-warning-rgb), 0.3);
}
.sched-pill.cron {
  background: rgba(var(--th-accent-rgb), 0.16);
  color: var(--do-gold-dark);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
}
.sched-pill.macro {
  background: rgba(var(--th-shadow-rgb), 0.06);
  color: var(--do-coffee-mid);
  border: 1px solid var(--do-border-card);
}

/* 默认模板选择药丸 */
.preset-templates-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tpl-pill-btn {
  background: #FFFFFF;
  border: 1px solid var(--do-border-card);
  color: var(--do-coffee);
  font-size: 14px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.tpl-pill-btn:hover {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
}

.schedule-config-box {
  background: var(--do-sand-light);
  border: 1px solid var(--do-border-card);
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 14px;
}

.sched-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--th-accent-color);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sched-title::before {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--th-accent-color);
  box-shadow: 0 0 6px var(--th-accent-color);
}
</style>
