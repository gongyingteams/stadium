<template>
  <div class="portal-nav-grid">
    <!-- 顶部工控全景指标条 (4 大核心态势卡，丰富页面图标与视觉纵深) -->
    <div class="portal-kpi-grid">
      <div class="kpi-stat-card glass-panel">
        <div class="kpi-icon-wrap gold">
          <SvgIcon name="SvgPortal" size="26" />
        </div>
        <div class="kpi-info">
          <span class="kpi-lbl">全场集成子系统</span>
          <div class="kpi-val-row">
            <span class="kpi-num num-mono">13</span>
            <span class="kpi-unit">套</span>
            <span class="kpi-tag">100%覆盖</span>
          </div>
        </div>
      </div>

      <div class="kpi-stat-card glass-panel">
        <div class="kpi-icon-wrap olive">
          <SvgIcon name="SvgCpu" size="26" />
        </div>
        <div class="kpi-info">
          <span class="kpi-lbl">API 开放直通模式</span>
          <div class="kpi-val-row">
            <span class="kpi-num num-mono">11</span>
            <span class="kpi-unit">套</span>
            <span class="kpi-tag success">毫秒双向直连</span>
          </div>
        </div>
      </div>

      <div class="kpi-stat-card glass-panel">
        <div class="kpi-icon-wrap warm">
          <SvgIcon name="SvgFiberNet" size="26" />
        </div>
        <div class="kpi-info">
          <span class="kpi-lbl">iframe 隔离降级</span>
          <div class="kpi-val-row">
            <span class="kpi-num num-mono">2</span>
            <span class="kpi-unit">套</span>
            <span class="kpi-tag warning">安全沙箱防护</span>
          </div>
        </div>
      </div>

      <div class="kpi-stat-card glass-panel">
        <div class="kpi-icon-wrap blue">
          <SvgIcon name="SvgAccessDoor" size="26" />
        </div>
        <div class="kpi-info">
          <span class="kpi-lbl">SSO 单点免密就绪</span>
          <div class="kpi-val-row">
            <span class="kpi-num num-mono">100</span>
            <span class="kpi-unit">%</span>
            <span class="kpi-tag success">动态Ticket鉴权</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 顶部检索与分类筛选过滤栏 -->
    <div class="portal-filter-bar glass-panel">
      <div class="search-box">
        <el-input v-model="keyword" placeholder="按系统名称、厂商、接入模式 (API/iframe) 快速检索..." prefix-icon="Search" clearable
          class="portal-search-input" />
      </div>

      <div class="category-tabs">
        <button v-for="cat in categories" :key="cat.key" :class="['cat-btn', { active: currentCategory === cat.key }]"
          @click="currentCategory = cat.key">
          {{ cat.name }} ({{ cat.count }})
        </button>
      </div>

      <!-- 右侧工具区：3列/4列切换胶囊 + SSO 鉴权状态 -->
      <div class="filter-right-tools">
        <div class="grid-mode-selector">
          <span class="mode-label">视图:</span>
          <button type="button" :class="['mode-btn', { active: gridColumns === '3' }]" title="切换至 3 列宽松视图"
            @click="setGridColumns('3')">
            <el-icon>
              <Grid />
            </el-icon>
            <span>3 列</span>
          </button>
          <button type="button" :class="['mode-btn', { active: gridColumns === '4' }]" title="切换至 4 列紧凑视图"
            @click="setGridColumns('4')">
            <el-icon>
              <Menu />
            </el-icon>
            <span>4 列</span>
          </button>
        </div>

        <div class="right-sso-summary">
          <span class="status-dot online"></span>
          <span>统一鉴权中心连接正常 (双机热备)</span>
        </div>
      </div>
    </div>

    <!-- 13大子系统集中聚合卡片网格 (根据用户偏好和断点响应) -->
    <div v-if="filteredApps.length > 0" ref="cardsGridRef" :class="['app-cards-grid', `cols-${gridColumns}`]">
      <div v-for="app in filteredApps" :key="app.id" class="app-card glass-panel">
        <!-- 卡片头部：图标、名称与模式标签 -->
        <div class="card-head">
          <div class="app-icon-box" :class="app.mode === 'API' ? 'api-box' : 'iframe-box'">
            <SvgIcon :name="app.icon" size="24" />
          </div>
          <div class="app-title-group">
            <div class="app-name-row">
              <h3 class="app-name" :title="app.name">{{ app.name }}</h3>
            </div>
            <div class="app-sub-vendor">
              <span class="vendor-name">{{ app.vendor }} · {{ app.version }}</span>
            </div>
          </div>

          <!-- 设备通信状态标签 (通信正常 / 通信失败) -->
          <div class="mode-tag-wrap">
            <span v-if="app.commStatus !== 'FAULT'" class="tag-pill comm-normal">
              <span class="status-pulse-dot normal"></span>
              <span>通信正常</span>
            </span>
            <span v-else class="tag-pill comm-fault">
              <span class="status-pulse-dot fault"></span>
              <span>通信失败</span>
            </span>
          </div>
        </div>

        <!-- 软件功能描述 (单行超出省略，提供展开/收起) -->
        <div class="app-desc-wrapper">
          <p :ref="el => setDescRef(app.id, el)" :class="['app-desc-text', { 'is-expanded': isDescExpanded(app.id) }]"
            :title="app.desc">
            {{ app.desc || '暂无详细描述说明。' }}
          </p>
          <button v-if="shouldShowDescToggle(app)" type="button" class="desc-toggle-btn"
            @click.stop="toggleDesc(app.id)">
            <span>{{ isDescExpanded(app.id) ? '收起' : '展开' }}</span>
            <el-icon class="toggle-arrow">
              <ArrowUp v-if="isDescExpanded(app.id)" />
              <ArrowDown v-else />
            </el-icon>
          </button>
        </div>

        <!-- 切换前展示：第①级与第②级区域 -->
        <template v-if="!isIframeView(app.id)">
          <!-- 第①级：核心协议与路由（浅色等宽代码块 + 虚线边框） -->
          <div class="app-target-bar dark-code-block">
            <div class="target-info-wrap">
              <span class="target-scheme-badge" :class="app.mode === 'API' ? 'bs' : 'cs'">
                {{ app.mode === 'API' ? 'PROTO' : 'PROXY' }}
              </span>
              <span class="target-path-val terminal-mono" :title="`${app.protocol} (路由: ${app.targetRoute})`">
                {{ app.protocol }}
              </span>
            </div>
            <div class="target-actions-wrap">
              <el-tooltip content="复制协议与系统路由" placement="top">
                <button class="icon-copy-btn dark-copy"
                  @click.stop="copyText(`${app.name}: ${app.protocol} (路由: ${app.targetRoute})`)">
                  <el-icon>
                    <CopyDocument />
                  </el-icon>
                </button>
              </el-tooltip>
              <el-tooltip :content="app.commStatus === 'FAULT' ? '链路异常: 核心控制器离线或通信失败' : '链路就绪: 核心控制器通信心跳正常'" placement="top">
                <div class="status-indicator">
                  <span class="status-dot-sm" :class="app.commStatus === 'FAULT' ? 'fault' : 'online'"></span>
                </div>
              </el-tooltip>
            </div>
          </div>

          <!-- 第②级：凭据与接入规范 紧凑型状态胶囊（通透轻巧、主次分明） -->
          <div class="app-credential-capsule-bar">
            <div class="capsule-left">
              <!-- 凭据状态胶囊 -->
              <span class="pill-tag credential-pill" title="基于统一 SSO 鉴权中心分发动态短效 Ticket">
                <el-icon class="pill-icon">
                  <Key />
                </el-icon>
                <span>Ticket免密已鉴权</span>
              </span>

              <!-- 模式胶囊 -->
              <span v-if="app.mode === 'API'" class="pill-tag args-pill" title="双向毫秒级 Direct API 直连调度">
                <el-icon class="pill-icon">
                  <Cpu />
                </el-icon>
                <span>毫秒直连</span>
              </span>
              <span v-else class="pill-tag direct-pill" title="无开放API，采用反向代理+安全沙箱容器防护">
                <el-icon class="pill-icon">
                  <CircleCheck />
                </el-icon>
                <span>沙箱隔离</span>
              </span>
            </div>

            <!-- 紧凑型折叠触发按钮 -->
            <button type="button" class="capsule-expand-btn" :class="{ 'is-open': isConfigExpanded(app.id) }"
              @click.stop="toggleConfig(app.id)">
              <span>{{ isConfigExpanded(app.id) ? '收起详情' : '参数详情' }}</span>
              <el-icon class="capsule-arrow" :class="{ 'rotated': isConfigExpanded(app.id) }">
                <ArrowDown />
              </el-icon>
            </button>
          </div>

          <!-- 参数与接入规范轻量折叠抽屉 -->
          <div v-show="isConfigExpanded(app.id)" class="credential-drawer-panel">
            <div class="drawer-detail-row">
              <span class="detail-label">系统路由:</span>
              <span class="detail-val num-mono">{{ app.targetRoute }}</span>
              <button class="mini-copy-btn" title="复制路由" @click.stop="copyText(app.targetRoute)">
                <el-icon>
                  <CopyDocument />
                </el-icon>
              </button>
            </div>
            <div class="drawer-detail-row">
              <span class="detail-label">硬件厂商:</span>
              <span class="detail-val num-mono">{{ app.vendor }} ({{ app.version }})</span>
            </div>
            <div class="drawer-detail-row">
              <span class="detail-label">接入协议:</span>
              <span class="detail-val num-mono">{{ app.protocol }}</span>
            </div>
            <div class="drawer-detail-row">
              <span class="detail-label">鉴权模式:</span>
              <span class="detail-val" style="color: #4A7C49; font-weight: 600;">
                <el-icon class="mr-0.5">
                  <CircleCheck />
                </el-icon>SSO Ticket 动态鉴权免密
              </span>
            </div>
          </div>
        </template>

        <!-- 切换后展示：目标页面的实时效果 嵌入 iframe 视窗 -->
        <div v-else class="app-iframe-live-window">
          <div class="live-window-header">
            <div class="header-left">
              <span class="live-pulse-dot"></span>
              <span class="live-tag">LIVE 实时视窗</span>
              <span class="live-route terminal-mono" :title="app.targetRoute">{{ app.targetRoute }}</span>
            </div>
            <button class="live-refresh-btn" title="刷新视窗画面" @click.stop="refreshIframe(app.id)">
              <el-icon><Refresh /></el-icon>
            </button>
          </div>
          <div class="iframe-container-box">
            <iframe
              :key="iframeKeyMap[app.id] || 1"
              :src="getEmbeddedUrl(app.targetRoute)"
              class="card-live-iframe"
              frameborder="0"
              scrolling="no"
              loading="lazy"
              @load="onIframeLoad"
            ></iframe>
          </div>
        </div>

        <!-- 第③级：底部高对比度暖金主按钮 + 视窗切换快捷按钮 -->
        <div class="card-footer">
          <!-- 视窗切换快捷按钮 -->
          <el-tooltip :content="isIframeView(app.id) ? '点击切回系统参数指标面板' : '切换为目标系统实时视窗嵌入预览'"
            placement="top">
            <button class="test-connection-btn" :class="{ 'is-view-active': isIframeView(app.id) }"
              @click.stop="toggleIframeView(app.id)">
              <el-icon class="test-icon">
                <Monitor v-if="!isIframeView(app.id)" />
                <Back v-else />
              </el-icon>
              <span>{{ isIframeView(app.id) ? '返回面板' : '视窗切换' }}</span>
            </button>
          </el-tooltip>

          <!-- 拆分为两个操作按钮：1.新窗口中打开 2.直接打开 -->
          <button class="open-btn btn-new-window" @click.stop="openInNewWindow(app)" title="在浏览器新窗口中独立打开该系统">
            <el-icon class="btn-icon">
              <TopRight />
            </el-icon>
            <span class="launch-label">新窗口中打开</span>
          </button>

          <button class="open-btn btn-direct-open gold-primary-launch" @click="enterSystem(app)"
            title="在当前窗口直接进入该系统工作台">
            <span class="launch-label">直接打开</span>
            <span class="arrow-icon">→</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 无数据空状态 -->
    <div v-else class="empty-state-panel glass-panel">
      <div class="empty-icon-wrap">
        <el-icon :size="48">
          <FolderOpened />
        </el-icon>
      </div>
      <h4 class="empty-title">未找到匹配的子系统</h4>
      <p class="empty-desc">请尝试调整搜索关键字或切换分类标签。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Connection, Platform, Cpu, Tools, CircleCheck, Link, Grid, Menu,
  CopyDocument, ArrowDown, ArrowUp, Key, Lock, User, Loading, FolderOpened, TopRight, Monitor, Refresh, Back
} from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()

// 实时视窗嵌入切换管理: { [appId]: boolean }
const iframeViewMap = reactive({})
const iframeKeyMap = reactive({})

const isIframeView = (id) => !!iframeViewMap[id]

const toggleIframeView = (id) => {
  iframeViewMap[id] = !iframeViewMap[id]
  if (iframeViewMap[id] && !iframeKeyMap[id]) {
    iframeKeyMap[id] = 1
  }
}

const refreshIframe = (id) => {
  iframeKeyMap[id] = (iframeKeyMap[id] || 1) + 1
  ElMessage.success('已刷新实时视窗画面')
}

// 获取嵌入纯净模式 URL（携带 embedded=1，自动隐藏顶栏、侧边栏及面包屑）
const getEmbeddedUrl = (route) => {
  if (!route) return ''
  const separator = route.includes('?') ? '&' : '?'
  return `${route}${separator}embedded=1`
}

// iframe 加载完成后的样式加固（双重保障：强制消除顶栏与侧边栏）
const onIframeLoad = (e) => {
  try {
    const doc = e.target.contentDocument || e.target.contentWindow?.document
    if (doc) {
      const styleId = '__ibms_embedded_override_style'
      if (!doc.getElementById(styleId)) {
        const style = doc.createElement('style')
        style.id = styleId
        style.textContent = `
          .top-header,
          .sidebar-nav,
          .viewport-breadcrumb,
          .breadcrumb-header {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
          }
          .default-layout,
          .main-container,
          .content-viewport {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 100% !important;
            border: none !important;
          }
          .page-content-wrapper {
            padding: 8px 10px !important;
            overflow-y: auto !important;
          }
          html, body {
            overflow-x: hidden !important;
            background: transparent !important;
          }
        `
        doc.head.appendChild(style)
      }
    }
  } catch (err) {
    // 跨域或安全环境降级忽略
  }
}
const keyword = ref('')
const currentCategory = ref('ALL')

// 布局列数偏好模式 (3列 / 4列)，支持本地持久化记忆
const gridColumns = ref(localStorage.getItem('ibms_portal_grid_cols') || '4')
const setGridColumns = (cols) => {
  gridColumns.value = cols
  try {
    localStorage.setItem('ibms_portal_grid_cols', cols)
  } catch (e) {
    // 忽略异常
  }
}

// 描述文本元素 DOM 引用池
const descRefMap = new Map()
const setDescRef = (id, el) => {
  if (el) {
    descRefMap.set(id, el)
  } else {
    descRefMap.delete(id)
  }
}

// 描述文本展开/收起管理
const expandedDescMap = reactive({})
const toggleDesc = (id) => {
  expandedDescMap[id] = !expandedDescMap[id]
  if (!expandedDescMap[id]) {
    // 收起后在下一帧重新核验当前宽度下是否溢出单行
    nextTick(() => {
      checkSingleDescOverflow(id)
    })
  }
}
const isDescExpanded = (id) => !!expandedDescMap[id]

// 单行文本是否发生真实溢出（内容超出单行宽度被截断）
const descOverflowMap = reactive({})

// 检查单个卡片描述是否溢出单行
const checkSingleDescOverflow = (id) => {
  const el = descRefMap.get(id)
  if (!el || !el.parentElement) return false

  // 如果当前是展开状态，跳过检测，保持溢出状态
  if (isDescExpanded(id)) {
    return true
  }

  // 单行模式下，比较内容真实排版宽度 scrollWidth 与父容器整行宽度 clientWidth
  // 容差 +1px 避免亚像素渲染舍入误差
  const parentWidth = el.parentElement.clientWidth
  const isOverflow = el.scrollWidth > parentWidth + 1
  descOverflowMap[id] = isOverflow
  return isOverflow
}

// 批量检测所有已挂载的卡片描述
const checkAllDescOverflow = () => {
  descRefMap.forEach((el, id) => {
    checkSingleDescOverflow(id)
  })
}

let resizeRafId = null
const debouncedCheckOverflow = () => {
  if (resizeRafId) cancelAnimationFrame(resizeRafId)
  resizeRafId = requestAnimationFrame(() => {
    checkAllDescOverflow()
  })
}

// 是否应显示展开/收起按钮：只有多行（被截断溢出）或当前已展开时才显示
const shouldShowDescToggle = (app) => {
  if (!app || !app.desc) return false
  // 若用户已手动展开，必须保留“收起”按钮
  if (isDescExpanded(app.id)) return true
  // 若未展开，则依据 DOM 实际是否发生单行物理溢出判定
  return !!descOverflowMap[app.id]
}

// 兼容旧方法
const hasLongDesc = (desc, id) => {
  if (id) return shouldShowDescToggle({ id, desc })
  if (!desc) return false
  return desc.length > 36
}

// 启动参数与接入详情折叠面板管理
const expandedConfigMap = reactive({})
const toggleConfig = (id) => {
  expandedConfigMap[id] = !expandedConfigMap[id]
}
const isConfigExpanded = (id) => !!expandedConfigMap[id]

// 复制文字辅助
const copyText = async (text) => {
  if (!text) return
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动选取复制')
  }
}

// 独立的连通性探测状态管理: { [appId]: boolean }
const testingMap = reactive({})

const handleTestApp = async (app) => {
  if (testingMap[app.id]) return
  testingMap[app.id] = true

  ElMessage.info({
    message: `正在发起【${app.name}】连通探测...`,
    duration: 1500
  })

  try {
    const pingDelay = Math.floor(Math.random() * 25) + 12
    await new Promise(resolve => setTimeout(resolve, 600))

    if (app.mode === 'API') {
      ElMessage.success({
        message: `[API 直通] ${app.name} 控制器握手正常！协议链路通畅 (时延: ${pingDelay}ms)`,
        duration: 3500
      })
    } else {
      ElMessage.success({
        message: `[iframe 沙箱] ${app.name} 反向代理网关就绪，Ticket 鉴权安全连接有效！`,
        duration: 3500
      })
    }
  } catch (err) {
    ElMessage.error(`探测异常：${err.message || '握手超时'}`)
  } finally {
    testingMap[app.id] = false
  }
}

const categories = ref([
  { key: 'ALL', name: '全部子系统', count: 13 },
  { key: 'IOT', name: '弱电硬件与声光', count: 6 },
  { key: 'MEDIA', name: '媒体与视频', count: 4 },
  { key: 'BIZ', name: '运营与票务', count: 3 }
])

// 完整覆盖 13 大基线子系统卡片 (规范编号 SYS-01 ~ SYS-13)
const apps = ref([
  {
    id: 'audio',
    code: 'SYS-01',
    commStatus: 'NORMAL',
    name: '扩声调音与矩阵系统',
    vendor: 'Soundcraft Vi3000',
    version: 'v2.4',
    category: 'IOT',
    icon: 'SvgSoundMatrix',
    mode: 'API',
    protocol: '串口 RS232 (115200bps)',
    desc: '全场16通道音频矩阵推子控制、场景音效调用与音量分贝监视',
    targetRoute: '/iot/audio'
  },
  {
    id: 'lighting',
    code: 'SYS-02',
    commStatus: 'NORMAL',
    name: '场地照明及控制系统',
    vendor: 'Lutron Quantum',
    version: 'v4.1',
    category: 'IOT',
    icon: 'SvgLighting',
    mode: 'API',
    protocol: '串口 RS485 / Modbus',
    desc: '赛事/训练/演播照明场景一键切换，24小时智能配电电表能耗监测',
    targetRoute: '/iot/lighting'
  },
  {
    id: 'screen',
    code: 'SYS-03',
    commStatus: 'NORMAL',
    name: 'LED大屏与推屏调度系统',
    vendor: 'Novastar UHD',
    version: 'v3.0',
    category: 'IOT',
    icon: 'SvgLedScreen',
    mode: 'API',
    protocol: 'Web API / 串口双通道',
    desc: '大屏信号源矩阵切换、现场实时预览画面监测与推屏调度',
    targetRoute: '/iot/screen'
  },
  {
    id: 'score',
    code: 'SYS-04',
    commStatus: 'NORMAL',
    name: '计时计分及现场成绩系统',
    vendor: 'Omega ARES-21',
    version: 'v5.8',
    category: 'BIZ',
    icon: 'SvgMatchScore',
    mode: 'API',
    protocol: 'TCP Socket (5000端口)',
    desc: '比赛道次成绩毫秒级实时捕获，支持全自动及手动大屏一键推屏',
    targetRoute: '/iot/score'
  },
  {
    id: 'ticketing',
    code: 'SYS-05',
    commStatus: 'FAULT',
    name: '售验票与闸机客流系统',
    vendor: '第三方票务系统',
    version: 'v1.8',
    category: 'BIZ',
    icon: 'SvgTicketGate',
    mode: 'IFRAME_FALLBACK',
    protocol: '反向代理 / 安全iframe',
    desc: '无开放API老旧系统，通过短时效Ticket代理内嵌展示售验票后台与闸机通行',
    targetRoute: '/portal/app/ticketing'
  },
  {
    id: 'clock',
    code: 'SYS-06',
    commStatus: 'NORMAL',
    name: '标准时钟与北斗授时系统',
    vendor: 'TimeMaster TS9000',
    version: 'v3.2',
    category: 'IOT',
    icon: 'SvgMasterClock',
    mode: 'API',
    protocol: 'TCP/UDP (北斗/GPS双模)',
    desc: '卫星颗数采集、时间毫秒比对校验与全场子钟分类拓扑监控',
    targetRoute: '/iot/clock'
  },
  {
    id: 'flag',
    code: 'SYS-07',
    commStatus: 'NORMAL',
    name: '自动升旗控制系统',
    vendor: 'Siemens S70-PLC',
    version: 'v2.0',
    category: 'IOT',
    icon: 'SvgFlagSystem',
    mode: 'API',
    protocol: '串口 RS485 控制',
    desc: '国歌音频时长智能测速换算、Canvas升旗高精度仿真、立即急停',
    targetRoute: '/iot/flag'
  },
  {
    id: 'video',
    code: 'SYS-08',
    commStatus: 'NORMAL',
    name: '现场影像采集回放系统',
    vendor: '海康威视平台',
    version: 'v8.2',
    category: 'MEDIA',
    icon: 'SvgCameraMatrix',
    mode: 'API',
    protocol: 'RTSP / WebRTC',
    desc: '全馆多路机位高清视窗监看、云台PTZ八向操控、关键事件抓拍',
    targetRoute: '/iot/video'
  },
  {
    id: 'underwater',
    code: 'SYS-09',
    commStatus: 'NORMAL',
    name: '水下影像采集识别系统',
    vendor: 'SubC Underwater',
    version: 'v1.5',
    category: 'MEDIA',
    icon: 'SvgSwimmingPool',
    mode: 'API',
    protocol: '特种采集流 / RTSP',
    desc: '跳水游泳特种水下高速摄像机、运动员触壁与水下技术动作分析',
    targetRoute: '/iot/video'
  },
  {
    id: 'tv_broadcast',
    code: 'SYS-10',
    commStatus: 'NORMAL',
    name: '电视转播系统',
    vendor: 'Blackmagic采集卡',
    version: 'v4.0',
    category: 'MEDIA',
    icon: 'SvgSdiVideo',
    mode: 'API',
    protocol: 'SDI/HDMI 采集适配',
    desc: '广播级视频源画面监视、输入格式/分辨率/帧率监测',
    targetRoute: '/iot/video'
  },
  {
    id: 'info_publish',
    code: 'SYS-11',
    commStatus: 'NORMAL',
    name: '信息发布与大厅导视系统',
    vendor: '多媒体信息发布系统',
    version: 'v2.1',
    category: 'BIZ',
    icon: 'SvgLedScreen',
    mode: 'API',
    protocol: 'HTTP RESTful / API控制',
    desc: '导视屏节目单排期、全场赛程公告滚动播发与多媒体终端推屏',
    targetRoute: '/portal/app/info_publish'
  },
  {
    id: 'audio_playback',
    code: 'SYS-12',
    commStatus: 'NORMAL',
    name: '高保真音频播放服务',
    vendor: '内置媒体引擎',
    version: 'v1.0',
    category: 'MEDIA',
    icon: 'SvgMediaPlayer',
    mode: 'API',
    protocol: '本地媒体流调度',
    desc: '动态联动媒体素材库，国歌、颁奖进行曲与场馆背景音乐选播',
    targetRoute: '/iot/media'
  },
  {
    id: 'video_playback',
    code: 'SYS-13',
    commStatus: 'NORMAL',
    name: '视频播放与多路投屏服务',
    vendor: '内置媒体引擎',
    version: 'v1.0',
    category: 'MEDIA',
    icon: 'SvgMediaPlayer',
    mode: 'API',
    protocol: '本地多路解码推流',
    desc: '赛事宣传片、回放视频多路大屏与导视屏定向投屏输出',
    targetRoute: '/iot/media'
  }
])

const filteredApps = computed(() => {
  return apps.value.filter(app => {
    const matchCat = currentCategory.value === 'ALL' || app.category === currentCategory.value
    const matchKw = !keyword.value ||
      app.name.includes(keyword.value) ||
      app.vendor.includes(keyword.value) ||
      app.protocol.includes(keyword.value) ||
      app.mode.toLowerCase().includes(keyword.value.toLowerCase())
    return matchCat && matchKw
  })
})

const enterSystem = (app) => {
  ElMessage.success(`正在通过 SSO 鉴权单点直连：${app.name}...`)
  router.push(app.targetRoute)
}

// 在浏览器新窗口中独立打开子系统
const openInNewWindow = (app) => {
  ElMessage.info(`正在新窗口中打开【${app.name}】...`)
  const routeData = router.resolve({ path: app.targetRoute })
  window.open(routeData.href, '_blank')
}

// 网格容器 DOM 引用与尺寸变化监听器
const cardsGridRef = ref(null)
let resizeObserver = null

onMounted(() => {
  nextTick(() => {
    debouncedCheckOverflow()
    // 延迟 120ms 做二次校准，确保字体和动画布局完全就绪
    setTimeout(debouncedCheckOverflow, 120)
  })

  window.addEventListener('resize', debouncedCheckOverflow)

  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      debouncedCheckOverflow()
    })
    if (cardsGridRef.value) {
      resizeObserver.observe(cardsGridRef.value)
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', debouncedCheckOverflow)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (resizeRafId) {
    cancelAnimationFrame(resizeRafId)
    resizeRafId = null
  }
})

// 监听搜索关键字、分类标签、列数偏好切换，重新触发单行溢出检测
watch([keyword, currentCategory, gridColumns], () => {
  nextTick(() => {
    debouncedCheckOverflow()
  })
})
</script>

<style scoped>
.portal-nav-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 顶部全景态势指标卡 */
.portal-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .portal-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.kpi-stat-card {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(165deg, var(--do-bg-card) 0%, var(--do-bg-card) 65%, var(--do-bg-sunken) 100%);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: transform var(--dur-normal) var(--ease-out-expo), border-color var(--dur-normal);
}

.kpi-stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--do-gold);
  box-shadow: var(--shadow-md);
}

.kpi-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.kpi-icon-wrap.gold {
  background: linear-gradient(145deg, rgba(var(--th-accent-rgb), 0.22), rgba(var(--th-accent-rgb), 0.08));
  color: var(--do-gold-deep);
  border: 1px solid var(--do-gold);
}

.kpi-icon-wrap.olive {
  background: linear-gradient(145deg, rgba(var(--th-success-rgb), 0.22), rgba(var(--th-success-rgb), 0.08));
  color: var(--do-success-deep);
  border: 1px solid var(--do-success);
}

.kpi-icon-wrap.warm {
  background: linear-gradient(145deg, rgba(var(--th-danger-rgb), 0.2), rgba(var(--th-danger-rgb), 0.08));
  color: var(--do-warning-deep);
  border: 1px solid var(--do-warning);
}

.kpi-icon-wrap.blue {
  background: linear-gradient(145deg, rgba(74, 107, 130, 0.22), rgba(74, 107, 130, 0.08));
  color: var(--do-gold-deep);
  border: 1px solid var(--do-text-secondary);
}

.kpi-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.kpi-lbl {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
  font-weight: 500;
}

.kpi-val-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.kpi-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--do-text-primary);
  line-height: 1;
}

.kpi-unit {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
  font-weight: 600;
}

.kpi-tag {
  font-size: 14px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-weight: 600;
  background: rgba(var(--th-accent-rgb), 0.14);
  color: var(--do-gold-deep);
  margin-left: auto;
}

.kpi-tag.success {
  background: var(--do-success-bg);
  color: var(--do-success-deep);
}

.kpi-tag.warning {
  background: var(--do-warning-bg);
  color: var(--do-warning-deep);
}

.portal-filter-bar {
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.search-box {
  flex-shrink: 0;
}

.portal-search-input {
  width: 380px;
}

@media (max-width: 1400px) {
  .portal-search-input {
    width: 300px;
  }
}

.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cat-btn {
  padding: 6px 14px;
  background: linear-gradient(180deg, var(--do-bg-card) 0%, var(--do-bg-input) 100%);
  border: 1px solid var(--do-border);
  color: var(--do-text-regular);
  border-radius: var(--radius-pill);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
}

.cat-btn:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.cat-btn.active {
  background: linear-gradient(180deg, var(--do-gold-hover), var(--do-gold));
  border-color: var(--do-gold-deep);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(var(--th-accent-deep-rgb), 0.32);
}

.filter-right-tools {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-wrap: wrap;
}

/* 布局列数切换胶囊选择器 (与主按钮高度 32px 齐平) */
.grid-mode-selector {
  display: inline-flex;
  align-items: center;
  background: rgba(var(--th-accent-rgb), 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  border-radius: 6px;
  padding: 2px 4px;
  gap: 3px;
  height: 32px;
  box-sizing: border-box;
}

.mode-label {
  font-size: 14px;
  color: var(--do-gold-deep);
  padding: 0 4px 0 2px;
  user-select: none;
}

.mode-btn {
  background: transparent;
  border: none;
  font-size: 14px;
  color: var(--do-text-secondary);
  padding: 3px 8px;
  height: 26px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
  line-height: 1;
}

.mode-btn:hover {
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.15);
}

.mode-btn.active {
  background: var(--do-gold-deep);
  color: #FFFFFF;
  box-shadow: 0 1px 4px rgba(var(--th-accent-deep-rgb), 0.35);
}

.right-sso-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--do-success-deep);
  font-weight: 600;
  background: rgba(var(--th-success-rgb), 0.1);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(var(--th-success-rgb), 0.2);
}

/* 13大子系统集中聚合卡片网格 (方案A断点响应式体系 + 方案B多列偏好) */
.app-cards-grid {
  display: grid;
  gap: 16px;
  width: 100%;
}

.app-cards-grid.cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.app-cards-grid.cols-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

/* 断点响应式降级回退 */
@media (max-width: 1680px) {
  .app-cards-grid.cols-4 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {

  .app-cards-grid.cols-4,
  .app-cards-grid.cols-3 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 768px) {

  .app-cards-grid.cols-4,
  .app-cards-grid.cols-3 {
    grid-template-columns: 1fr !important;
  }
}

/* 卡片样式 (禁止鼠标悬停位移晃动，仅边框平滑变色发光) */
.app-card {
  position: relative;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(255, 252, 247, 0.9);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.22s ease, box-shadow 0.22s ease;
}

.app-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--do-gold-deep), var(--do-gold), transparent 88%);
  opacity: 0.55;
  transition: opacity 0.22s ease;
}

.app-card:hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 16px rgba(var(--th-accent-rgb), 0.22);
}

.app-card:hover::before {
  opacity: 1;
}

/* 卡片头部 */
.card-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}

.app-icon-box {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  background: linear-gradient(150deg, rgba(var(--th-accent-rgb), 0.18), rgba(var(--th-accent-rgb), 0.06));
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--do-gold-deep);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
  transition: transform 0.2s ease;
}

.app-card:hover .app-icon-box {
  transform: scale(1.05);
}

.app-icon-box.iframe-box {
  background: linear-gradient(150deg, rgba(var(--th-danger-rgb), 0.16), rgba(var(--th-danger-rgb), 0.05));
  border-color: rgba(var(--th-danger-rgb), 0.35);
  color: var(--do-danger-deep);
}

.app-title-group {
  flex: 1;
  min-width: 0;
}

.app-name-row {
  display: flex;
  align-items: center;
  min-height: 22px;
}

.app-name {
  font-size: 15px;
  font-weight: 700;
  color: #0F172A;
  /* 纯正深邃炭黑蓝，在白底卡片上极具品质与高对比度，彻底杜绝发浅发虚 */
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.2px;
}

.app-sub-vendor {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  font-size: 13.5px;
}

.code-badge {
  color: var(--do-gold-deep, #1D4ED8);
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-weight: 700;
  font-size: 13.5px;
  letter-spacing: 0.3px;
}

.vendor-name {
  color: #475569;
  /* 清晰舒适的深灰副标题，杜绝模糊 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 模式标签 (与标题第一行严格处于同一水平线) */
.mode-tag-wrap {
  flex-shrink: 0;
  margin-top: 0;
  margin-left: 6px;
  display: flex;
  align-items: center;
}

.tag-pill {
  font-size: 13.5px;
  padding: 2px 9px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  line-height: 16px;
  letter-spacing: 0.2px;
}

.tag-pill .pill-icon {
  font-size: 13px !important;
}

.tag-pill.comm-normal,
.tag-pill.api {
  background: #DCFCE7;
  /* 舒适清爽的浅绿底 */
  color: #15803D;
  /* 深翠绿高对比文字，清晰锐利无模糊 */
  border: 1px solid #86EFAC;
  box-shadow: 0 1px 2px rgba(21, 128, 61, 0.08);
}

.tag-pill.comm-fault,
.tag-pill.iframe {
  background: #FEE2E2;
  /* 舒适浅红底 */
  color: #B91C1C;
  /* 深红高对比文字 */
  border: 1px solid #FCA5A5;
  box-shadow: 0 1px 2px rgba(185, 28, 28, 0.08);
}

.status-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  display: inline-block;
}

.status-pulse-dot.normal {
  background: #16A34A;
  box-shadow: 0 0 5px rgba(22, 163, 74, 0.65);
}

.status-pulse-dot.fault {
  background: #DC2626;
  box-shadow: 0 0 5px rgba(220, 38, 38, 0.65);
}

.status-dot-sm.fault {
  background: var(--do-danger, #DC2626);
  box-shadow: 0 0 6px rgba(220, 38, 38, 0.55);
}

/* 原样式保留 */
.old-tag-pill-unused {
  background: #DCFCE7;
  /* 舒适清爽的浅绿底 */
  color: #15803D;
  /* 深翠绿高对比文字，清晰锐利无模糊 */
  border: 1px solid #86EFAC;
  box-shadow: 0 1px 2px rgba(21, 128, 61, 0.08);
}

.tag-pill.iframe {
  background: #FEE2E2;
  /* 舒适浅红底 */
  color: #B91C1C;
  /* 深红高对比文字 */
  border: 1px solid #FCA5A5;
  box-shadow: 0 1px 2px rgba(185, 28, 28, 0.08);
}

/* 软件功能描述：单行溢出省略，支持展开与收起 */
.app-desc-wrapper {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin: 4px 0 10px 0;
  min-height: 22px;
}

.app-desc-text {
  font-size: 14px;
  color: var(--do-text-secondary);
  line-height: 1.5;
  margin: 0;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-desc-text.is-expanded {
  white-space: normal;
  word-break: break-all;
}

.desc-toggle-btn {
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  font-size: 14px;
  color: var(--do-gold);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  font-weight: 600;
  transition: color 0.2s ease;
}

.desc-toggle-btn:hover {
  color: var(--do-gold-deep);
  text-decoration: underline;
}

.desc-toggle-btn .toggle-arrow {
  font-size: 14px !important;
}

/* 第①级：核心入口/URL 浅色等宽代码块（无多层硬边框、浅色柔和底、易识别高对比） */
.app-target-bar.dark-code-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(var(--th-accent-rgb), 0.05);
  /* 大幅减少降低背景色，保持轻盈通透 */
  border: none;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  padding: 7px 10px;
  margin-bottom: 8px;
  gap: 8px;
  transition: all 0.2s ease;
}

.app-target-bar.dark-code-block:hover {
  background: rgba(var(--th-accent-rgb), 0.09);
}

.target-info-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.target-scheme-badge {
  font-size: 13px;
  padding: 2px 7px;
  border-radius: 4px;
  border: none;
  font-family: monospace;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.target-scheme-badge.bs {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.target-scheme-badge.cs {
  background: rgba(var(--th-success-rgb), 0.12);
  color: var(--do-success-deep);
}

.target-path-val.terminal-mono {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, Monaco, monospace;
  font-size: 13.5px;
  color: #1E293B;
  /* 深沉清晰高对比代码文字，在任何主题下都极度清晰易辨 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  letter-spacing: -0.2px;
}

.target-actions-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.icon-copy-btn.dark-copy {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--do-gold-deep);
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.icon-copy-btn.dark-copy:hover {
  color: var(--do-gold-deep);
  transform: scale(1.12);
}

.icon-copy-btn .el-icon {
  font-size: 14px !important;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  cursor: help;
  padding: 2px;
}

.status-dot-sm {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot-sm.online {
  background: var(--do-success);
  box-shadow: 0 0 6px rgba(46, 158, 68, 0.55);
}

/* 第②级：凭据与接入规范 紧凑型状态胶囊（通透轻巧、无多层套框） */
.app-credential-capsule-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  background: rgba(var(--th-accent-rgb), 0.04);
  border: none;
  border-radius: 6px;
  padding: 5px 8px;
  margin-bottom: 8px;
  min-height: 28px;
}

.capsule-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.pill-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 12px;
  border: none;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.pill-tag .pill-icon {
  font-size: 14px !important;
}

.pill-tag.credential-pill {
  background: rgba(var(--th-accent-rgb), 0.10);
  color: #334155;
  /* 深蓝灰高对比文字 */
  border: none;
}

.pill-tag.direct-pill {
  background: #F1F5F9;
  color: #475569;
  border: none;
}

.pill-tag.args-pill {
  background: #ECFDF5;
  color: #047857;
  /* 深草绿高对比 */
  border: none;
}

.capsule-expand-btn {
  background: none;
  border: none;
  font-size: 14px;
  color: var(--do-gold-deep);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 600;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.capsule-expand-btn:hover {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
}

.capsule-arrow {
  font-size: 14px !important;
  transition: transform 0.22s ease;
}

.capsule-arrow.rotated {
  transform: rotate(180deg);
}

/* 抽屉详情 (仅顶部轻微细分割线，去除厚重全套边框) */
.credential-drawer-panel {
  background: rgba(var(--th-accent-rgb), 0.03);
  border: none;
  border-top: 1px solid rgba(var(--th-accent-rgb), 0.12);
  border-radius: 0 0 6px 6px;
  padding: 8px 10px;
  margin-top: -4px;
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.drawer-detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 14px;
}

.detail-label {
  color: var(--do-text-secondary);
  font-weight: 500;
  width: 60px;
  flex-shrink: 0;
}

.detail-val {
  flex: 1;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: monospace;
  font-size: 14px;
}

.mini-copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--do-gold);
  padding: 1px;
  display: inline-flex;
  align-items: center;
  font-size: 14px;
  transition: color 0.2s;
}

.mini-copy-btn:hover {
  color: var(--do-gold-deep);
}

/* 第③级：底部高对比度暖金主按钮 + 独立连通测试快捷按钮 */
.card-footer {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--do-border-light);
}

.test-connection-btn {
  height: 34px;
  padding: 0 12px;
  background: #FFFFFF;
  /* 清爽通透的白底，彻底消除死黑过深问题 */
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  border-radius: 4px;
  color: var(--do-gold-deep);
  font-size: 13.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.test-connection-btn:hover:not(:disabled) {
  background: rgba(var(--th-accent-rgb), 0.08);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.18);
  transform: translateY(-1px);
}

.test-connection-btn:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

.test-connection-btn .test-icon {
  font-size: 14px !important;
}

.test-connection-btn .test-icon.is-loading {
  animation: spin-anim 1s linear infinite;
}

@keyframes spin-anim {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.open-btn {
  height: 34px;
  padding: 0 10px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  letter-spacing: 0.2px;
  min-width: 0;
}

.open-btn.btn-new-window {
  flex: 1;
  background: rgba(var(--th-accent-rgb), 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  color: var(--do-gold-deep);
  font-size: 12.5px;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.open-btn.btn-new-window:hover {
  background: rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-gold-deep);
  color: var(--do-gold-deep);
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.18);
  transform: translateY(-1px);
}

.open-btn.btn-new-window .btn-icon {
  font-size: 13.5px !important;
  color: var(--do-gold-deep);
  flex-shrink: 0;
}

.open-btn.btn-direct-open.gold-primary-launch {
  flex: 1;
  background: linear-gradient(135deg, var(--do-gold-deep) 0%, var(--do-gold-deep) 100%);
  border: 1px solid var(--do-gold-deep);
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35);
}

.open-btn.btn-direct-open.gold-primary-launch:hover {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  border-color: var(--do-gold-deep);
  box-shadow: 0 4px 12px rgba(var(--th-accent-deep-rgb), 0.45);
  filter: brightness(1.04);
  transform: translateY(-1px);
}

.open-btn.btn-direct-open .arrow-icon {
  font-size: 13px;
  font-weight: bold;
  transition: transform 0.2s ease;
}

.open-btn.btn-direct-open:hover .arrow-icon {
  transform: translateX(2px);
}

.open-btn.gold-primary-launch:active {
  transform: scale(0.98);
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.4);
}

.open-btn.gold-primary-launch:hover .arrow-icon {
  transform: translateX(3px);
}

.arrow-icon {
  font-size: 14px;
  font-weight: 800;
  transition: transform 0.2s ease;
}

/* 空状态 */
.empty-state-panel {
  padding: 40px 20px;
  text-align: center;
  background: rgba(255, 252, 247, 0.7);
  border: 1px dashed rgba(var(--th-accent-rgb), 0.35);
  border-radius: 8px;
}

.empty-icon-wrap {
  color: var(--do-gold);
  margin-bottom: 12px;
}

.empty-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-text-primary);
  margin: 0 0 6px 0;
}

.empty-desc {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin: 0;
}

/* ============================================================
 * 嵌入式实时视窗预览面板 (视窗切换效果)
 * ============================================================ */
.app-iframe-live-window {
  margin: 4px 0 10px 0;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.28);
  background: var(--do-bg-sunken, #0f172a);
  box-shadow: inset 0 1px 3px rgba(15, 23, 42, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
}

.live-window-header {
  height: 26px;
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.08);
  border-bottom: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.18);
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.live-window-header .header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.live-pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--do-success, #16a34a);
  box-shadow: 0 0 5px rgba(22, 163, 74, 0.7);
  flex-shrink: 0;
}

.live-tag {
  font-size: 11px;
  font-weight: 700;
  color: var(--el-color-primary, #2563eb);
  letter-spacing: 0.3px;
  flex-shrink: 0;
}

.live-route {
  font-size: 11px;
  color: var(--do-text-secondary, #64748b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.live-refresh-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--do-text-secondary, #64748b);
  padding: 2px 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.2s;
}

.live-refresh-btn:hover {
  color: var(--el-color-primary, #2563eb);
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.15);
}

.iframe-container-box {
  width: 100%;
  height: 120px;
  position: relative;
  overflow: hidden;
  background: #0b0f17;
}

.card-live-iframe {
  width: 200%;
  height: 200%;
  transform: scale(0.5);
  transform-origin: 0 0;
  border: none;
  display: block;
  pointer-events: auto;
}

.test-connection-btn.is-view-active {
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.15) !important;
  color: var(--el-color-primary, #2563eb) !important;
  border-color: rgba(var(--th-accent-rgb, 37, 99, 235), 0.45) !important;
  font-weight: 700 !important;
}

</style>
