<template>
  <div class="lighting-page">
    <section class="lighting-header glass-panel">
      <div class="lighting-title-block">
        <div class="lighting-icon"><SvgIcon name="SvgLighting" size="28" /></div>
        <div>
          <div class="title-line">
            <h1>场地照明控制与能耗监测</h1>
            <span class="system-badge">LIGHTING CONTROL</span>
          </div>
          <p>切换赛事照明场景，监测灯具分区、智能电表能耗和配电回路运行状态。</p>
        </div>
      </div>
      <div class="header-status">
        <div class="status-item"><span class="status-dot online"></span>总控箱通信正常</div>
        <div class="status-item"><strong class="num-mono">{{ activeFixtureCount }}/{{ fixtures.length }}</strong> 组灯具点亮</div>
        <div class="status-item"><strong class="num-mono">{{ closedCircuitCount }}/{{ circuits.length }}</strong> 回路接通</div>
        <button class="btn-header-action btn-header-danger" @click="handleAllOffConfirm" title="急停操作：切断场地所有照明配电回路并紧急全灭">
          <SvgIcon name="SvgEmergencyHalt" size="14" style="margin-right: 4px;" />
          <span>照明紧急全灭</span>
        </button>
      </div>
    </section>

    <section class="metric-grid">
      <div class="metric-card glass-panel">
        <span>当前运行场景</span>
        <strong>{{ currentSceneName }}</strong>
        <em>预设照度 {{ currentSceneLux }} Lux</em>
      </div>
      <div class="metric-card glass-panel">
        <span>场地中心照度</span>
        <strong class="num-mono">{{ currentLuxVal }} Lux</strong>
        <em>赛事目标 2000 Lux</em>
      </div>
      <div class="metric-card glass-panel">
        <span>当前瞬时功率</span>
        <strong class="num-mono">142.8 kW</strong>
        <em>电表实时采集</em>
      </div>
      <div class="metric-card glass-panel">
        <span>今日累计用电</span>
        <strong class="num-mono">864.2 kWh</strong>
        <em>昨日同期 840.5 kWh</em>
      </div>
    </section>

    <section class="control-grid">
      <div class="scene-panel glass-panel">
        <div class="panel-heading">
          <div><h2>一键场景模式</h2><p>响应 FINA 照度标准，选择后立即下发照明场景</p></div>
          <span class="panel-code num-mono">PRESET SCENES</span>
        </div>
        <div class="scene-list">
          <button
            v-for="sc in scenes"
            :key="sc.id"
            type="button"
            :class="['scene-card', { active: currentScene === sc.id }]"
            @click="switchLightingScene(sc)"
          >
            <div class="scene-card-head">
              <div class="scene-name"><SvgIcon :name="sc.icon" size="19" /><strong>{{ sc.name }}</strong></div>
              <span class="scene-lux num-mono">{{ sc.lux }} Lux</span>
            </div>
            <p>{{ sc.desc }}</p>
            <div class="scene-card-foot"><span class="num-mono">预估 {{ sc.power }} kW</span><span v-if="currentScene === sc.id" class="active-label">当前运行</span></div>
          </button>
        </div>
      </div>

      <div class="topology-panel glass-panel">
        <div class="panel-heading">
          <div><h2>灯具分区拓扑</h2><p>48 组专业泛光灯具实时状态</p></div>
          <span class="lux-reading"><span>中心照度</span><strong class="num-mono">{{ currentLuxVal }} Lux</strong></span>
        </div>
        <div class="topology-legend"><span><i class="legend-dot on"></i>点亮 {{ activeFixtureCount }}</span><span><i class="legend-dot off"></i>关闭 {{ fixtures.length - activeFixtureCount }}</span><span class="num-mono">12 × 4 阵列</span></div>
        <div class="fixtures-grid">
          <div v-for="fix in fixtures" :key="fix.code" :class="['fixture-cell', { on: fix.isOn }]" :title="`${fix.name} - 状态: ${fix.isOn ? '开启 (100%)' : '关闭'}`">
            <div class="fix-bulb"></div><span class="fix-code num-mono">{{ fix.code }}</span>
          </div>
        </div>
        <div class="topology-note"><span class="status-dot online"></span>灯具拓扑为控制状态视图，具体亮度以电表与照度传感器采集值为准</div>
      </div>

      <div class="energy-panel glass-panel">
        <div class="panel-heading">
          <div><h2>能耗趋势分析</h2><p>智能电表近 24 小时负荷功率</p></div>
          <span class="panel-code num-mono">POWER MONITOR</span>
        </div>
        <div class="energy-kpi-row">
          <div><span>瞬时功率</span><strong class="num-mono warning-value">142.8 <small>kW</small></strong></div>
          <div><span>电费评估</span><strong class="num-mono">¥1,037</strong></div>
        </div>
        <div class="chart-wrap">
          <svg viewBox="0 0 420 170" class="energy-chart-svg" role="img" aria-label="近24小时照明负荷功率曲线">
            <line v-for="y in [20, 60, 100, 140]" :key="y" x1="50" :y1="y" x2="400" :y2="y" class="chart-grid-line" />
            <text x="44" y="24" class="chart-axis num-mono">200kW</text><text x="44" y="64" class="chart-axis num-mono">150kW</text><text x="44" y="104" class="chart-axis num-mono">100kW</text><text x="44" y="144" class="chart-axis num-mono">0kW</text>
            <polygon class="chart-area" points="50,135 80,130 110,128 140,125 170,85 200,80 230,85 260,55 290,50 320,55 350,90 400,50 400,140 50,140" />
            <polyline class="chart-line" points="50,135 80,130 110,128 140,125 170,85 200,80 230,85 260,55 290,50 320,55 350,90 400,50" />
            <text x="50" y="160" class="chart-axis num-mono">00:00</text><text x="170" y="160" class="chart-axis num-mono">08:00</text><text x="260" y="160" class="chart-axis num-mono">14:00</text><text x="375" y="160" class="chart-axis num-mono">当前</text>
          </svg>
        </div>
        <div class="energy-foot"><span>昨日同期 <strong class="num-mono">840.5 kWh</strong></span><span class="trend-up">较昨日 +2.8%</span></div>
      </div>
    </section>

    <section class="circuits-panel glass-panel">
      <div class="panel-heading">
        <div><h2>智能配电回路实时监测</h2><p>监测支路电流、负载率、过载预警及脱扣状态</p></div>
        <div class="circuit-summary"><span class="status-dot online"></span><strong class="num-mono">{{ closedCircuitCount }}/{{ circuits.length }}</strong> 回路接通</div>
      </div>
      <el-table :data="circuits" style="width: 100%" size="small" stripe>
        <el-table-column prop="circuitNo" label="回路编号" width="120" />
        <el-table-column prop="areaName" label="配电受控区域" min-width="190" />
        <el-table-column prop="phase" label="供电相别" width="100" />
        <el-table-column prop="ratedCurrent" label="额定电流" width="105"><template #default="{ row }"><span class="num-mono">{{ row.ratedCurrent }}A</span></template></el-table-column>
        <el-table-column prop="currentA" label="实测电流" width="110"><template #default="{ row }"><strong class="num-mono">{{ row.currentA }}A</strong></template></el-table-column>
        <el-table-column prop="loadRate" label="负载率" width="130"><template #default="{ row }"><el-progress :percentage="row.loadRate" :color="row.loadRate > 80 ? 'var(--do-danger)' : 'var(--do-success)'" :stroke-width="7" /></template></el-table-column>
        <el-table-column prop="status" label="开关状态" width="115"><template #default="{ row }"><span :class="['table-status', row.status === 'CLOSED' ? 'closed' : 'open']"><i></i>{{ row.status === 'CLOSED' ? '合闸接通' : '分闸断电' }}</span></template></el-table-column>
        <el-table-column label="动作控制" width="140" align="center"><template #default="{ row }"><el-button size="small" :type="row.status === 'CLOSED' ? 'danger' : 'primary'" link @click="toggleCircuit(row)">{{ row.status === 'CLOSED' ? '断开回路' : '闭合送电' }}</el-button></template></el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import SvgIcon from '@/components/SvgIcon.vue'

const currentScene = ref('HD_BROADCAST')
const currentLuxVal = ref(2045)

const scenes = ref([
  { id: 'HD_BROADCAST', name: '赛事高清转播模式', icon: 'SvgSdiVideo', lux: 2000, power: 142.8, desc: '4K/8K 慢动作超高清电视转播，主泳道垂直照度最大化，全开泛光' },
  { id: 'PROFESSIONAL_MATCH', name: '专业竞技比赛模式', icon: 'SvgTrophy', lux: 1500, power: 110.5, desc: '符合国际泳联正赛要求，消除眩光与水面反光，重点覆盖泳池区' },
  { id: 'DAILY_TRAINING', name: '日常体校训练模式', icon: 'SvgSwimmingPool', lux: 750, power: 58.2, desc: '满足运动员日常游泳与跳水起跳训练要求，节能巡航运行' },
  { id: 'CLEANING_STANDBY', name: '场馆保洁维护模式', icon: 'SvgPower', lux: 200, power: 18.0, desc: '夜间泳池清扫、水质药剂投放及基础安防地灯低功耗照明' }
])

const fixtures = ref(Array.from({ length: 48 }, (_, i) => ({
  code: `L${(i + 1).toString().padStart(2, '0')}`,
  name: `顶棚${Math.floor(i / 12) + 1}排-${(i % 12) + 1}号大功率投光灯`,
  isOn: true
})))

const circuits = ref([
  { circuitNo: 'AL-1-01', areaName: '泳池主赛道 1~4道 顶棚主投光', phase: 'L1', ratedCurrent: 63, currentA: 42.5, loadRate: 67, status: 'CLOSED' },
  { circuitNo: 'AL-1-02', areaName: '泳池主赛道 5~8道 顶棚主投光', phase: 'L2', ratedCurrent: 63, currentA: 43.1, loadRate: 68, status: 'CLOSED' },
  { circuitNo: 'AL-1-03', areaName: '跳水台 10米高台垂直立体补光', phase: 'L3', ratedCurrent: 32, currentA: 21.0, loadRate: 65, status: 'CLOSED' },
  { circuitNo: 'AL-2-01', areaName: '东看台 观众区环境漫射照明', phase: 'L1', ratedCurrent: 32, currentA: 18.2, loadRate: 56, status: 'CLOSED' },
  { circuitNo: 'AL-2-02', areaName: '西看台 贵宾主席台重点照明', phase: 'L2', ratedCurrent: 32, currentA: 14.5, loadRate: 45, status: 'CLOSED' },
  { circuitNo: 'AL-3-01', areaName: '热身副馆 25米过渡泳池常规灯', phase: 'L3', ratedCurrent: 40, currentA: 24.8, loadRate: 62, status: 'CLOSED' }
])

const activeFixtureCount = computed(() => fixtures.value.filter(fixture => fixture.isOn).length)
const closedCircuitCount = computed(() => circuits.value.filter(circuit => circuit.status === 'CLOSED').length)
const currentSceneName = computed(() => scenes.value.find(scene => scene.id === currentScene.value)?.name || '未选择场景')
const currentSceneLux = computed(() => scenes.value.find(scene => scene.id === currentScene.value)?.lux || '—')

const switchLightingScene = (sc) => {
  currentScene.value = sc.id
  currentLuxVal.value = sc.lux + Math.floor(Math.random() * 50 - 25)
  if (sc.id === 'CLEANING_STANDBY') fixtures.value.forEach((fixture, index) => (fixture.isOn = index % 3 === 0))
  else if (sc.id === 'DAILY_TRAINING') fixtures.value.forEach((fixture, index) => (fixture.isOn = index % 2 === 0))
  else fixtures.value.forEach(fixture => (fixture.isOn = true))
  ElMessage.success(`已下发串口指令，切换照明为：【${sc.name}】(${sc.lux} Lux)`)
}

const handleAllOffConfirm = () => {
  ElMessageBox.confirm('【高危操作防呆】此操作将瞬间关闭全场全部比赛区与看台照明，将导致现场处于黑暗状态，请确认现场赛事已结束！', '紧急照明全灭防误触确认', { confirmButtonText: '确认全灭', cancelButtonText: '取消', type: 'warning' }).then(() => {
    fixtures.value.forEach(fixture => (fixture.isOn = false))
    currentLuxVal.value = 0
    ElMessage.error('已下发指令：全场场地照明紧急全灭！')
  }).catch(() => {})
}

const toggleCircuit = (row) => {
  row.status = row.status === 'CLOSED' ? 'OPEN' : 'CLOSED'
  ElMessage.info(`回路 ${row.circuitNo} 已切换为：${row.status === 'CLOSED' ? '合闸' : '分闸'}`)
}
</script>

<style scoped>
.lighting-page { display:flex; flex-direction:column; gap:14px; min-width:0; color:var(--do-text-primary); }
.glass-panel { background:var(--do-bg-card); border:1px solid var(--do-border); border-radius:10px; box-shadow:var(--shadow-sm); }
.lighting-header,.lighting-title-block,.title-line,.header-status,.status-item,.panel-heading,.scene-card-head,.scene-card-foot,.topology-legend,.energy-foot,.circuit-summary { display:flex; align-items:center; }
.lighting-header { justify-content:space-between; gap:20px; padding:18px 22px; }
.lighting-title-block { gap:14px; min-width:0; }.lighting-icon { width:52px; height:52px; display:grid; place-items:center; flex-shrink:0; color:var(--do-gold); background:var(--do-gold-wash); border:1px solid var(--do-border-dark); border-radius:12px; }
h1,h2,h3,p { margin:0; } h1 { font-size:21px; line-height:1.3; } h2 { font-size:16px; line-height:1.35; }
.title-line { gap:10px; flex-wrap:wrap; }.lighting-title-block p,.panel-heading p { margin-top:5px; color:var(--do-text-secondary); font-size:13px; }.system-badge,.panel-code { padding:4px 8px; color:var(--do-gold-deep); background:var(--do-gold-wash); border:1px solid var(--do-border-dark); border-radius:5px; font-size:13px; font-weight:700; }.panel-code { padding:3px 7px; }
.header-status { justify-content:flex-end; gap:16px; flex-wrap:wrap; color:var(--do-text-secondary); font-size:13px; }.status-item { gap:6px; white-space:nowrap; }.status-item strong { color:var(--do-text-primary); font-size:15px; }.status-dot { width:8px; height:8px; flex:0 0 auto; border-radius:50%; background:currentColor; }.status-dot.online { color:var(--do-success); box-shadow:0 0 7px currentColor; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(160px,1fr)); gap:12px; }.metric-card { min-width:0; padding:15px; }.metric-card span,.metric-card em { color:var(--do-text-secondary); font-size:13px; }.metric-card strong { display:block; margin-top:8px; overflow:hidden; color:var(--do-text-primary); font-size:17px; text-overflow:ellipsis; white-space:nowrap; }.metric-card em { display:block; margin-top:5px; overflow:hidden; font-style:normal; text-overflow:ellipsis; white-space:nowrap; }
.control-grid { display:grid; grid-template-columns:minmax(330px,1fr) minmax(380px,1.18fr) minmax(300px,.86fr); gap:14px; align-items:stretch; }.scene-panel,.topology-panel,.energy-panel,.circuits-panel { min-width:0; padding:18px; }.panel-heading { justify-content:space-between; gap:14px; min-width:0; }.panel-heading > div { min-width:0; }.panel-heading p { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.scene-list { display:grid; gap:9px; margin-top:16px; }.scene-card { width:100%; padding:12px 13px; color:inherit; text-align:left; background:var(--do-bg-sunken); border:1px solid var(--do-border); border-radius:8px; cursor:pointer; transition:border-color .2s, box-shadow .2s, background .2s; }.scene-card:hover,.scene-card.active { border-color:var(--do-gold); box-shadow:var(--shadow-hover); }.scene-card.active { background:var(--do-gold-wash); }.scene-card-head { justify-content:space-between; gap:10px; }.scene-name { display:flex; align-items:center; gap:8px; min-width:0; color:var(--do-text-primary); }.scene-name svg { flex-shrink:0; color:var(--do-gold); }.scene-name strong { overflow:hidden; font-size:14px; text-overflow:ellipsis; white-space:nowrap; }.scene-lux { flex-shrink:0; padding:3px 7px; color:var(--do-warning-deep); background:var(--do-warning-bg); border:1px solid var(--do-warning-border); border-radius:4px; font-size:13px; font-weight:700; }.scene-card p { margin-top:8px; color:var(--do-text-secondary); font-size:13px; line-height:1.5; }.scene-card-foot { justify-content:space-between; margin-top:9px; color:var(--do-text-secondary); font-size:13px; }.active-label { color:var(--do-success-deep); font-weight:700; }
.lux-reading { display:flex; flex-direction:column; align-items:flex-end; gap:3px; color:var(--do-text-secondary); font-size:13px; }.lux-reading strong { color:var(--do-gold-deep); font-size:15px; }.topology-legend { justify-content:space-between; gap:10px; margin-top:16px; color:var(--do-text-secondary); font-size:13px; }.topology-legend > span { display:flex; align-items:center; gap:5px; }.legend-dot { width:8px; height:8px; border-radius:50%; }.legend-dot.on { background:var(--do-success); box-shadow:0 0 6px var(--do-success); }.legend-dot.off { background:var(--do-text-placeholder); }.fixtures-grid { display:grid; grid-template-columns:repeat(12,minmax(24px,1fr)); gap:6px; margin-top:10px; padding:12px; background:var(--do-bg-sunken); border:1px solid var(--do-border-light); border-radius:8px; }.fixture-cell { display:flex; flex-direction:column; align-items:center; gap:4px; padding:7px 2px; background:var(--do-bg-card); border:1px solid var(--do-border-light); border-radius:5px; }.fix-bulb { width:10px; height:10px; border-radius:50%; background:var(--do-text-placeholder); }.fixture-cell.on { background:var(--do-success-bg); border-color:var(--do-success); }.fixture-cell.on .fix-bulb { background:var(--do-success); box-shadow:0 0 8px var(--do-success); }.fix-code { color:var(--do-text-secondary); font-size:13px; }.topology-note { display:flex; align-items:center; gap:7px; margin-top:12px; color:var(--do-text-secondary); font-size:13px; line-height:1.4; }
.energy-kpi-row { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-top:16px; }.energy-kpi-row > div { padding:10px 12px; background:var(--do-bg-sunken); border-radius:7px; }.energy-kpi-row span { display:block; color:var(--do-text-secondary); font-size:13px; }.energy-kpi-row strong { display:block; margin-top:6px; color:var(--do-text-primary); font-size:17px; }.energy-kpi-row small { font-size:13px; font-weight:400; }.warning-value { color:var(--do-warning-deep) !important; }.chart-wrap { margin-top:14px; }.energy-chart-svg { display:block; width:100%; height:auto; min-height:180px; background:var(--do-bg-sunken); border:1px solid var(--do-border-light); border-radius:7px; }.chart-grid-line { stroke:var(--do-border-light); stroke-width:1; }.chart-axis { fill:var(--do-text-secondary); font-size:13px; text-anchor:end; }.chart-axis:last-child { text-anchor:start; }.chart-area { fill:var(--do-gold-wash-strong); }.chart-line { fill:none; stroke:var(--do-gold); stroke-width:2.5; }.energy-foot { justify-content:space-between; gap:10px; margin-top:10px; color:var(--do-text-secondary); font-size:13px; }.energy-foot strong { color:var(--do-text-primary); }.trend-up { color:var(--do-warning-deep); }
.circuits-panel { padding-bottom:12px; }.circuit-summary { gap:7px; color:var(--do-success-deep); font-size:13px; white-space:nowrap; }.circuit-summary strong { font-size:15px; }.circuits-panel :deep(.el-table) { margin-top:16px; --el-table-header-bg-color:var(--do-bg-sunken); --el-table-row-hover-bg-color:var(--do-gold-wash); --el-table-border-color:var(--do-border-light); --el-table-text-color:var(--do-text-regular); --el-table-header-text-color:var(--do-text-secondary); }.circuits-panel :deep(.el-table th.el-table__cell) { font-size:13px; }.circuits-panel :deep(.el-table td.el-table__cell) { font-size:13px; }.table-status { display:inline-flex; align-items:center; gap:6px; padding:4px 8px; border-radius:12px; font-size:13px; font-weight:700; }.table-status i { width:7px; height:7px; border-radius:50%; background:currentColor; }.table-status.closed { color:var(--do-success-deep); background:var(--do-success-bg); }.table-status.open { color:var(--do-text-secondary); background:var(--do-bg-sunken); }
@media (max-width:1200px) { .control-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.scene-panel { grid-row:span 2; }.energy-panel { grid-column:2; } }
@media (max-width:900px) { .lighting-header { align-items:flex-start; flex-direction:column; }.header-status { justify-content:flex-start; }.metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.control-grid { grid-template-columns:1fr; }.scene-panel { grid-row:auto; }.energy-panel { grid-column:auto; }.fixtures-grid { grid-template-columns:repeat(8,minmax(24px,1fr)); } }
@media (max-width:600px) { .lighting-header,.scene-panel,.topology-panel,.energy-panel,.circuits-panel { padding:14px; }.lighting-title-block { align-items:flex-start; }.metric-grid { grid-template-columns:1fr; }.header-status { align-items:flex-start; flex-direction:column; gap:9px; }.panel-heading { align-items:flex-start; flex-direction:column; }.panel-code,.circuit-summary { align-self:flex-start; }.fixtures-grid { grid-template-columns:repeat(6,minmax(24px,1fr)); }.energy-kpi-row { grid-template-columns:1fr; }.energy-foot { align-items:flex-start; flex-direction:column; } }
</style>
