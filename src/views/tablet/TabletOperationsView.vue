<template>
  <div class="tablet-operations-container">
    <!-- 平板快捷分类导航栏 (大触控靶心) -->
    <div class="tablet-cat-nav">
      <button
        v-for="cat in tabletTabs"
        :key="cat.key"
        :class="['tablet-nav-btn', { active: currentTab === cat.key }]"
        @click="currentTab = cat.key"
      >
        <SvgIcon :name="cat.icon" size="22" />
        <span>{{ cat.label }}</span>
      </button>

      <!-- 顶栏右侧醒目大急停按钮 (最高优先级) -->
      <button class="tablet-estop-btn" @click="handleTabletEstop">
        <svg class="estop-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.4 2.6h7.2l5.8 5.8v7.2l-5.8 5.8H8.4l-5.8-5.8V8.4z" fill="#FFFDF9" /><rect x="7.6" y="10.2" width="8.8" height="3.6" rx="1.2" fill="#A0522D" /></svg>
        现场紧急停止 (E-STOP)
      </button>
    </div>

    <!-- 主操作大触控卡片区 (自适应平铺网格) -->
    <div class="tablet-touch-canvas">
      <!-- 模块1: 一键照明场景大触控 -->
      <div v-if="currentTab === 'LIGHTING' || currentTab === 'ALL'" class="touch-section">
        <div class="section-title">
          <span>场地照明一键模式 (FINA 照度规范)</span>
          <span class="num-mono text-warning">当前瞬时负荷: 142.8 kW</span>
        </div>

        <div class="touch-cards-grid">
          <button
            class="big-touch-card primary"
            @click="triggerLighting('HD_BROADCAST', '赛事高清转播模式 (2000 Lux)')"
          >
            <div class="card-icon"><SvgIcon name="SvgLighting" size="26" /></div>
            <div class="card-content">
              <span class="c-title">赛事高清转播 (2000 Lux)</span>
              <span class="c-sub">4K/8K 摄像机全开泛光</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card"
            @click="triggerLighting('PROFESSIONAL_MATCH', '专业竞赛模式 (1500 Lux)')"
          >
            <div class="card-icon"><SvgIcon name="SvgLighting" size="26" /></div>
            <div class="card-content">
              <span class="c-title">专业竞赛模式 (1500 Lux)</span>
              <span class="c-sub">防眩光水面聚焦</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card"
            @click="triggerLighting('DAILY_TRAINING', '日常训练模式 (750 Lux)')"
          >
            <div class="card-icon"><SvgIcon name="SvgButtonAction" size="26" /></div>
            <div class="card-content">
              <span class="c-title">日常训练模式 (750 Lux)</span>
              <span class="c-sub">节能低负荷运行</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card danger"
            @click="confirmLightingAllOff"
          >
            <div class="card-icon"><SvgIcon name="SvgButtonAction" size="26" /></div>
            <div class="card-content">
              <span class="c-title">全场灯光全灭 (清场闭馆)</span>
              <span class="c-sub">防误触滑动/二次确认</span>
            </div>
            <span class="touch-indicator">高危操作</span>
          </button>
        </div>
      </div>

      <!-- 模块2: 自动升旗与国歌典礼 -->
      <div v-if="currentTab === 'FLAG' || currentTab === 'ALL'" class="touch-section">
        <div class="section-title">
          <span>自动升旗与颁奖典礼 (音画强同步)</span>
          <span class="num-mono text-primary">旗杆状态: {{ flagHeight }}m / 12.0m</span>
        </div>

        <div class="touch-cards-grid">
          <button
            class="big-touch-card primary"
            @click="triggerFlagRaise"
          >
            <div class="card-icon"><SvgIcon name="SvgFlagSystem" size="26" /></div>
            <div class="card-content">
              <span class="c-title">一键奏国歌升旗 (46秒)</span>
              <span class="c-sub">音画同步测速 0.2608 m/s</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card"
            @click="triggerFlagHalf"
          >
            <div class="card-icon"><SvgIcon name="SvgFlagSystem" size="26" /></div>
            <div class="card-content">
              <span class="c-title">升至半旗仪式</span>
              <span class="c-sub">升至杆顶后平稳回降1/3</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card"
            @click="triggerFlagLower"
          >
            <div class="card-icon"><SvgIcon name="SvgButtonAction" size="26" /></div>
            <div class="card-content">
              <span class="c-title">平稳降旗收回基座</span>
              <span class="c-sub">仪式完毕安全归零</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>
        </div>
      </div>

      <!-- 模块3: 现场音效与大屏推屏 -->
      <div v-if="currentTab === 'MEDIA' || currentTab === 'ALL'" class="touch-section">
        <div class="section-title">
          <span>现场音响与 LED 大屏推屏调度</span>
          <span class="num-mono text-success">推屏联动在线</span>
        </div>

        <div class="touch-cards-grid">
          <button
            class="big-touch-card success"
            @click="pushScoreScreen"
          >
            <div class="card-icon"><SvgIcon name="SvgMatchScore" size="26" /></div>
            <div class="card-content">
              <span class="c-title">推送最新赛事成绩至大屏</span>
              <span class="c-sub">男子100米自由泳榜单</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card"
            @click="playAwardMusic"
          >
            <div class="card-icon"><SvgIcon name="SvgSoundMatrix" size="26" /></div>
            <div class="card-content">
              <span class="c-title">播放奥运颁奖进行曲</span>
              <span class="c-sub">立体声加冕仪式曲目</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>

          <button
            class="big-touch-card"
            @click="switchCameraFeed"
          >
            <div class="card-icon"><SvgIcon name="SvgCameraMatrix" size="26" /></div>
            <div class="card-content">
              <span class="c-title">大屏切换为现场4K摄像机</span>
              <span class="c-sub">转播全景俯视角直播</span>
            </div>
            <span class="touch-indicator">点触执行</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 底部状态反馈条 -->
    <footer class="tablet-foot-feedback">
      <div class="fb-left">
        <span class="status-dot online"></span>
        <span class="fb-txt">最近指令回执: {{ lastReceipt }}</span>
      </div>
      <div class="fb-right num-mono">
        <span>操作员: 刘主管 (现场执勤) | 终端: 工控防爆平板</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const currentTab = ref('ALL')
const flagHeight = ref('0.00')
const lastReceipt = ref('就绪待命 (ACK_STANDBY)')

const tabletTabs = ref([
  { key: 'ALL', label: '全部常用', icon: 'SvgTablet' },
  { key: 'LIGHTING', label: '场地照明', icon: 'SvgLighting' },
  { key: 'FLAG', label: '自动升旗', icon: 'SvgFlagSystem' },
  { key: 'MEDIA', label: '音效大屏', icon: 'SvgLedScreen' }
])

const triggerLighting = (mode, name) => {
  lastReceipt.value = `下发照明指令【${name}】-> PLC_ACK_SUCCESS`
  ElMessage.success(`已切换场地照明：${name}`)
}

const confirmLightingAllOff = () => {
  ElMessageBox.confirm(
    '【高危操作】确定要关闭全场场地照明吗？',
    '照明全灭确认',
    { confirmButtonText: '确定关闭', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    lastReceipt.value = '下发场地照明紧急全灭 -> LIGHTS_OFF_OK'
    ElMessage.error('全场照明已安全关闭')
  }).catch(() => {})
}

const triggerFlagRaise = () => {
  flagHeight.value = '11.85'
  lastReceipt.value = '国歌升旗已启动 -> 速度:0.2608m/s (PLC_START)'
  ElMessage.success('已启动一键国歌升旗！')
}

const triggerFlagHalf = () => {
  flagHeight.value = '7.90'
  lastReceipt.value = '半旗指令已下发 -> PLC_HALF_MAST_OK'
  ElMessage.info('已下发半旗升降动作')
}

const triggerFlagLower = () => {
  flagHeight.value = '0.00'
  lastReceipt.value = '降旗指令下发 -> 回到底座归零位'
  ElMessage.success('降旗完毕')
}

// 最高优先级急停 (规范要求：毫秒立即执行，不弹阻滞确认框)
const handleTabletEstop = () => {
  flagHeight.value = '4.20'
  lastReceipt.value = '【最高优先级急停】电机毫秒刹车抱死 (E-STOP_TRIGGERED)'
  ElMessage.error('【现场紧急停止】已瞬间下发急停指令，断开现场电机与高危电源！')
}

const pushScoreScreen = () => {
  lastReceipt.value = '推屏指令 -> LED_SCREEN_DISP_SCORE_OK'
  ElMessage.success('男子100米自由泳决赛成绩已推送至 LED 大屏！')
}

const playAwardMusic = () => {
  lastReceipt.value = '扩声通道 -> 播发奥运颁奖进行曲 (AUDIO_START)'
  ElMessage.success('扩声系统已播发奥运颁奖进行曲！')
}

const switchCameraFeed = () => {
  lastReceipt.value = '大屏信号源切换 -> SDI 4K 摄像机直通'
  ElMessage.info('大屏已切换为主看台摄像机信号')
}
</script>

<style scoped>
.tablet-operations-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: var(--gap-section, 14px);
}

/* 顶部大触控分类栏 (大马士革白卡片材质) */
.tablet-cat-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--do-bg-card);
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--do-border);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}

.tablet-cat-nav::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--do-gold-deep), var(--do-gold), transparent 85%);
}

.tablet-nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  min-height: 48px;
  background: linear-gradient(180deg, var(--do-bg-card) 0%, var(--do-bg-input) 100%);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-md);
  color: var(--do-text-primary);
  font-size: var(--fs-body);
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-fast);
  box-shadow: var(--shadow-xs);
}

.tablet-nav-btn:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  transform: translateY(-1px);
}

.tablet-nav-btn.active {
  background: linear-gradient(180deg, var(--do-gold-hover), var(--do-gold));
  border-color: var(--do-gold-deep);
  color: #FFFFFF;
  font-weight: 700;
  box-shadow: 0 3px 10px rgba(var(--th-accent-deep-rgb), 0.32);
}

.tablet-nav-btn.active :deep(svg) {
  color: #FFFFFF;
}

/* 赭石沙漠棕色急停按钮 (var(--do-danger)) */
.tablet-estop-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  padding: 10px 24px;
  background: linear-gradient(180deg, var(--do-danger-deep) 0%, var(--do-danger) 100%);
  border: 1px solid var(--do-danger-deep);
  color: #FFFFFF;
  border-radius: var(--radius-md);
  font-size: var(--fs-h3);
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(var(--th-danger-rgb), 0.36), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  transition: var(--transition-fast);
}

.tablet-estop-btn:hover {
  background: var(--do-danger-deep);
  box-shadow: 0 6px 18px rgba(var(--th-danger-rgb), 0.46);
  transform: translateY(-1px);
}

.tablet-estop-btn:active {
  background: var(--do-danger-deep);
  transform: translateY(1px);
}

.estop-mark {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* 主大卡片触控区 (触控卡片高 > 48px，间距 > 16px) */
.tablet-touch-canvas {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-right: 4px;
}

.touch-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  font-weight: 600;
  color: var(--do-text-primary);
  gap: 8px;
}

.section-title::before {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--th-accent-color);
  box-shadow: 0 0 6px var(--th-accent-color);
  flex-shrink: 0;
}

.touch-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

/* 大马士革白触控大卡片 */
.big-touch-card {
  min-height: 88px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 8px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  position: relative;
  box-shadow: var(--shadow-card);
  transition: transform 0.15s, background 0.15s, border-color 0.15s, box-shadow 0.15s;
  text-align: left;
}

.big-touch-card:hover {
  border-color: var(--do-gold);
  background: var(--do-bg-card-hover);
  box-shadow: 0 4px 16px rgba(var(--th-accent-rgb), 0.2);
}

.big-touch-card:active {
  transform: scale(0.98);
  background: rgba(var(--th-accent-rgb), 0.1);
}

.big-touch-card.primary {
  border-color: var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.08);
}

.big-touch-card.success {
  border-color: var(--do-success-border);
  background: var(--do-success-bg);
}

.big-touch-card.danger {
  border-color: var(--do-danger-border);
  background: var(--do-danger-bg);
}

/* 卡片图标：暖色底衬 + 金色描边的工控徽章位 */
.card-icon {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: linear-gradient(150deg, var(--do-gold-light), rgba(var(--th-accent-rgb), 0.14));
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
  transition: transform var(--dur-normal) var(--ease-out-expo),
    box-shadow var(--dur-normal) var(--ease-out-expo);
}

.big-touch-card:hover .card-icon {
  transform: scale(1.06);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6), 0 4px 14px rgba(var(--th-accent-rgb), 0.34);
}

.big-touch-card.success .card-icon {
  background: linear-gradient(150deg, var(--do-success-bg), rgba(var(--th-success-rgb), 0.14));
  border-color: var(--do-success-border);
  color: var(--do-success-deep);
}

.big-touch-card.danger .card-icon {
  background: linear-gradient(150deg, var(--do-danger-bg), rgba(var(--th-danger-rgb), 0.14));
  border-color: var(--do-danger-border);
  color: var(--do-danger-deep);
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.c-title {
  font-size: var(--fs-h3);
  font-weight: 700;
  color: var(--do-text-primary);
  letter-spacing: 0.2px;
  padding-right: 72px;
}

.c-sub {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
}

.touch-indicator {
  position: absolute;
  top: 10px;
  right: 14px;
  font-size: var(--fs-sm);
  color: var(--do-text-placeholder);
  font-weight: 600;
  letter-spacing: 0.3px;
}

.big-touch-card.danger .touch-indicator {
  color: var(--do-danger-deep);
}

/* 底部反馈条 */
.tablet-foot-feedback {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 6px;
  padding: 10px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  box-shadow: var(--shadow-card);
}

.fb-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--do-text-primary);
}

.fb-right {
  color: var(--do-text-secondary);
}
</style>
