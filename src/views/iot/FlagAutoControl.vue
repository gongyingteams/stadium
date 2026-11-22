<template>
  <div class="flag-workspace">
    <!-- 顶部状态栏：与大屏调度、计时计分页面保持一致的页面级标题区 -->
    <section class="flag-top-bar page-header glass-panel">
      <div class="top-left page-heading">
        <div class="page-icon">
          <SvgIcon name="SvgFlagSystem" size="28" />
        </div>
        <div class="title-meta">
          <div class="title-row">
            <h1 class="view-title">智能升旗·音画同步控制台</h1>
          </div>
          <p>国家、国歌、国旗已经内置，点击旗帜更换国家数据，操作前请检查设置连接状态。</p>
        </div>
      </div>

      <div class="top-right header-status">
        <div class="flag-header-status" @click="requestWsRefresh" style="cursor: pointer;"
          :title="wsConnected ? 'WebSocket 实时状态流已连接（点击立即刷新）' : 'WebSocket 重连中，当前使用 HTTP 兜底'">
          <span :class="['status-dot', wsConnected ? 'online' : 'warning']"></span>
          <strong>{{ wsConnected ? 'WS 实时' : 'WS 重连中' }}</strong>
          <span>{{ lastHwOnline ? '网关在线' : '网关待检' }}</span>
        </div>
        <div class="flag-header-status">
          <span
            :class="['status-dot', flagStatus === 'ESTOPPED' ? 'danger' : flagStatus === 'IDLE' ? 'muted' : 'online']"></span>
          <strong>{{ flagStatus }}</strong>
          <span>仪式状态</span>
        </div>
        <button class="btn-industrial btn-top-manage" @click="goCountryLibrary">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>国家资料录入与编辑</span>
        </button>
        <!-- 1. 一键获取硬件设备 -->
        <button class="btn-industrial btn-gold btn-fetch-hardware" :disabled="isFetchingDevices"
          @click="fetchHardwareDevices" title="扫描现场升旗控制器与通信总线节点，自动回读设备状态与寄存器参数">
          <SvgIcon name="SvgRefresh" size="14" :class="{ 'spin-icon': isFetchingDevices }" style="margin-right: 4px;" />
          <span>{{ isFetchingDevices ? '正在扫描设备与参数...' : '一键获取硬件设备' }}</span>
        </button>

        <!-- 2. 设备管理入口（默认固定为指令下发控制模式，不可切换） -->
        <div class="mode-toggle-group">
          <button class="mode-tab-btn mode-tab-device" @click="openDeviceManager"
            title="设备管理：添加/修改旗杆参数（IP、端口、从站ID、行程），全部入库">
            <span>设备管理</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 主三栏布局：数据呈现看板 (左) + 升旗动力学矢量视窗 (中) + 综合操控界面 (右) -->
    <div :class="['flag-main-layout', { 'is-sim-fullscreen': isSimFull }]">
      <!-- 1. 左栏：参与联动设备 (最多三台) · 状态与参数读取看板 -->
      <div v-show="!isSimFull" class="col-data glass-panel">
        <div class="panel-header">
          <div class="header-left">
            <span class="header-title">参与联动设备 (被控机组)</span>
          </div>
          <div class="header-right">
            <span class="dev-badge num-mono">
              {{ `已选被控: ${checkedIds.length}/${devices.length}` }}
            </span>
            <el-checkbox v-model="allChecked" :indeterminate="isIndeterminate" class="select-all-cb">全选</el-checkbox>
          </div>
        </div>

        <div class="data-present-body">
          <!-- 1.1 运行状态提示条 -->
          <div class="mode-hint-alert cmd_control">
            <SvgIcon name="SvgCpu" size="14" />
            <span>当前受控中设备数量 {{ checkedIds.length }} 套。</span>
          </div>

          <!-- 1.2 参与联动设备卡片 (显示：设备名称、类型、IP地址、状态) -->
          <div class="linked-devices-container">
            <div v-for="(dev, idx) in devices" :key="dev.id" :class="['hardware-dev-detail-card', {
              'is-selected': isDeviceSelected(dev.id),
              'is-offline': dev.status === 'OFFLINE'
            }]" @click="onCardClick(dev.id)">
              <!-- 设备卡片头部：设备名称 与 受控勾选 -->
              <div class="hdd-head">
                <div class="hdd-identity">
                  <span class="hdd-order-tag">设备{{ CHINESE_NUMS[idx] || (idx + 1) }}</span>
                  <span class="hdd-name" :title="dev.name">{{ dev.name }}</span>
                </div>
                <div class="hdd-head-right">
                  <div class="hdd-ctrl-check" @click.stop>
                    <el-checkbox :model-value="checkedIds.includes(dev.id)" :disabled="dev.status === 'OFFLINE'"
                      @change="toggleDevice(dev.id)">
                      <span :class="['hdd-ctrl-txt', { active: checkedIds.includes(dev.id) }]">
                        {{ checkedIds.includes(dev.id) ? '受控中' : '未受控' }}
                      </span>
                    </el-checkbox>
                  </div>
                </div>
              </div>

              <!-- 类型独占一行 -->
              <div class="hdd-meta-row hdd-single-row">
                <span class="hdd-field-lbl">设备类型:</span>
                <span class="hdd-type-badge">{{ dev.poleType === 'horizontal' ? '横向单杆' : '纵向三杆' }}</span>
              </div>

              <!-- IP地址独占一行 -->
              <div class="hdd-meta-row hdd-single-row">
                <span class="hdd-field-lbl">IP地址:</span>
                <span class="hdd-ip-text num-mono" :title="dev.ipAddress || dev.port">
                  {{ dev.ipAddress || dev.host || dev.port }}
                </span>
              </div>

              <!-- 状态独占一行 -->
              <div class="hdd-meta-row hdd-single-row">
                <span class="hdd-field-lbl">状态:</span>
                <div class="hdd-setting-wrap">
                  <span
                    :class="['hdd-setting-val', dev.status === 'OFFLINE' ? 'text-danger' : dev.status === 'ESTOP' ? 'text-warning' : 'text-success']">
                    <span class="setting-dot"></span>
                    {{ dev.settingStatus || devStatusText(dev) }}
                  </span>
                </div>
              </div>
            </div>
          </div>


        </div>
      </div>

      <!-- 2. 中栏：升旗动力学矢量视窗 (竖向三杆 / 横向单杆直接来自读取到的设备数据，无需人工改变) -->
      <div class="col-sim glass-panel">
        <div class="panel-header">
          <div class="header-left">
            <span class="header-title">升旗动力学矢量仿真视窗</span>
          </div>

          <div class="header-right-meta"></div>
        </div>

        <div class="canvas-stage">
          <!-- 仿真模拟台视窗：横向铺满父级容器，略留边距即可 -->
          <div class="sim-stage-viewport">
            <svg viewBox="0 0 880 480" preserveAspectRatio="xMidYMid meet" class="flag-sim-svg"
              aria-label="升旗动力学矢量仿真视窗">
              <defs>
                <!-- 视窗天空渐变 (明朗高质感，绝无蓝紫泛滥) -->
                <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#EBF1F6" />
                  <stop offset="45%" stop-color="#F4F8FA" />
                  <stop offset="100%" stop-color="#DFE7EE" />
                </linearGradient>

                <!-- 冠军黄金旗杆金属拉丝渐变 -->
                <linearGradient id="goldPoleGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stop-color="#FFF6D3" />
                  <stop offset="25%" stop-color="#E5B958" />
                  <stop offset="70%" stop-color="#B8860B" />
                  <stop offset="100%" stop-color="#D9A74A" />
                </linearGradient>

                <!-- 亚军/季军精钢旗杆金属渐变 -->
                <linearGradient id="silverPoleGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stop-color="#FFFFFF" />
                  <stop offset="30%" stop-color="#E2E8F0" />
                  <stop offset="75%" stop-color="#94A3B8" />
                  <stop offset="100%" stop-color="#CBD5E1" />
                </linearGradient>

                <!-- 顶端金球立体高光径向渐变 -->
                <radialGradient id="goldSphereGrad" cx="35%" cy="35%" r="65%">
                  <stop offset="0%" stop-color="#FFFBEB" />
                  <stop offset="35%" stop-color="#F59E0B" />
                  <stop offset="100%" stop-color="#92400E" />
                </radialGradient>

                <!-- 顶端银球立体高光径向渐变 -->
                <radialGradient id="silverSphereGrad" cx="35%" cy="35%" r="65%">
                  <stop offset="0%" stop-color="#FFFFFF" />
                  <stop offset="45%" stop-color="#94A3B8" />
                  <stop offset="100%" stop-color="#475569" />
                </radialGradient>

                <!-- 工业基座分层渐变 -->
                <linearGradient id="baseLayer1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#2D3B4C" />
                  <stop offset="100%" stop-color="#1B2531" />
                </linearGradient>
                <linearGradient id="baseLayer2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#415267" />
                  <stop offset="100%" stop-color="#283647" />
                </linearGradient>
              </defs>

              <!-- 1. 天空渐层背景 (横向完整铺满) -->
              <rect x="0" y="0" width="880" height="480" fill="url(#skyGrad)" />

              <!-- 2. A 模式 · 竖向三杆 (并排竖立 · 冠军居中 · 整体略偏左腾出右侧控制区) -->
              <g v-if="currentPoleMode === 'vertical'" class="sim-mode-vertical">
                <!-- 基座下层台阶 (台阶下移 36px，高度增加到旗杆：y=424, 高度 18, 底部 442) -->
                <rect x="60" y="424" width="760" height="18" fill="url(#baseLayer1)" rx="2" />
                <!-- 基座上层台阶 (y=412, 高度 12, 旗杆底部基准线 412) -->
                <rect x="100" y="412" width="680" height="12" fill="url(#baseLayer2)" rx="2" />
                <line x1="101" y1="412" x2="779" y2="412" stroke="rgba(255,255,255,0.22)" stroke-width="1" />

                <!-- 竖向三根旗杆与旗帜 (杆身加长 36px，全银色精钢杆体 · 居中对称) -->
                <g v-for="p in verticalPoles" :key="p.key">
                  <!-- 金属旗杆柱体 (全银色高质感精钢拉丝 · 加长至底部 412) -->
                  <rect :x="p.x - 2.5" :y="p.poleTop" width="5" :height="vertPolesConfig.poleBottom - p.poleTop"
                    fill="url(#silverPoleGrad)" rx="1" />

                  <!-- 顶端金属球 (银色立体精钢球) -->
                  <circle :cx="p.x" :cy="p.poleTop - 7" r="6.5" fill="url(#silverSphereGrad)" />

                  <!-- 升降吊绳虚线 -->
                  <line :x1="p.x + 3" :y1="p.poleTop" :x2="p.x + 3" :y2="vertPolesConfig.poleBottom"
                    stroke="rgba(200,164,92,0.5)" stroke-width="1" stroke-dasharray="3,3" />

                  <!-- 飘扬旗帜 (响应式动态位置 + 真实微风波浪 · 支持点击更换国家) -->
                  <g :class="['flag-clickable-item', { 'can-change': isAtLowerZero }]"
                    :transform="`translate(${p.x + 3}, ${p.flagY})`" @click="handleFlagClick(p.key)"
                    :title="flagClickTitle(p.key)">
                    <rect x="0" y="0" width="80" height="54" fill="transparent" pointer-events="all" />
                    <FlagFabricSvg :country="p.country" :width="80" :height="54" :phase="wavePhase + p.phaseOffset"
                      :clip-id="`clip-vert-${p.key}`" />
                  </g>

                  <!-- 旗杆底部文字标签 (名次 + 国家名合并为一行 · 点击亦可更换国家) -->
                  <text :class="['flag-clickable-label', { 'can-change': isAtLowerZero }]" :x="p.x" y="464"
                    text-anchor="middle" @click="handleFlagClick(p.key)" :title="flagClickTitle(p.key)">
                    <tspan font-size="22" font-weight="bold" :fill="p.gold ? '#B45309' : '#1E293B'">{{ p.label }}
                    </tspan>
                    <tspan dx="10" font-size="18" font-weight="500" fill="#475569">{{ p.country ? p.country.nameCn :
                      '未选定' }}</tspan>
                  </text>
                </g>
              </g>

              <!-- 3. B 模式 · 横向单杆 (一根横梁挂三面旗 · 横杆整体升降 · 旗杆高度同步加长) -->
              <g v-else class="sim-mode-singlebar">
                <!-- 顶部场馆建筑钢架吊索 (随三杆中心居中对应：230, 440, 650) -->
                <line x1="230" y1="0" x2="230" :y2="singleBarBeamY" stroke="rgba(200,164,92,0.85)" stroke-width="1.5"
                  stroke-dasharray="3,2" />
                <line x1="440" y1="0" x2="440" :y2="singleBarBeamY" stroke="rgba(200,164,92,0.85)" stroke-width="1.5"
                  stroke-dasharray="3,2" />
                <line x1="650" y1="0" x2="650" :y2="singleBarBeamY" stroke="rgba(200,164,92,0.85)" stroke-width="1.5"
                  stroke-dasharray="3,2" />

                <!-- 横向单杆主横梁 (高质感精钢横梁 · 随电机吊索整体升降 · 居中 x=440) -->
                <rect x="110" :y="singleBarBeamY" width="660" height="14" fill="url(#silverPoleGrad)" rx="3" />
                <line x1="110" :y1="singleBarBeamY + 1" x2="770" :y2="singleBarBeamY + 1"
                  stroke="rgba(255,255,255,0.45)" stroke-width="1" />
                <line x1="110" :y1="singleBarBeamY + 14" x2="770" :y2="singleBarBeamY + 14" stroke="rgba(15,23,42,0.4)"
                  stroke-width="1.5" />
                <!-- 左右两端固定法兰端盖 -->
                <rect x="102" :y="singleBarBeamY - 4" width="8" height="22" fill="#1E293B" rx="2" />
                <rect x="770" :y="singleBarBeamY - 4" width="8" height="22" fill="#1E293B" rx="2" />

                <!-- 横梁随动技术标牌 (居中 x=440，带半透垫片清晰展示) -->
                <rect :x="440 - 200" :y="singleBarBeamY - 20" width="400" height="16" fill="rgba(255,255,255,0.85)"
                  rx="3" />
                <text x="440" :y="singleBarBeamY - 8" text-anchor="middle" font-size="12" font-weight="600"
                  fill="#64748B" class="num-mono">
                  场馆吊挂横向单杆 (一杆挂三旗 · 横杆与旗帜相对静止整体升降)
                </text>

                <!-- 地面底座水平基准台阶 (下移 36px 增加行程) -->
                <rect x="60" y="424" width="760" height="18" fill="url(#baseLayer1)" rx="2" />
                <rect x="100" y="412" width="680" height="12" fill="url(#baseLayer2)" rx="2" />
                <line x1="101" y1="412" x2="779" y2="412" stroke="rgba(255,255,255,0.22)" stroke-width="1" />

                <!-- 从左到右一根杆挂 3 面国旗：亚军(左 230) · 冠军(中 440) · 季军(右 650) -->
                <g v-for="d in singleBarPoles" :key="d.key">
                  <!-- 主横梁下挂专用定滑轮卡扣 -->
                  <rect :x="d.x - 14" :y="singleBarBeamY + 14" width="28" height="12" fill="#1E293B" rx="2" />
                  <circle :cx="d.x" :cy="singleBarBeamY + 20" r="3.5" fill="#94A3B8" />

                  <!-- 垂直悬吊固定钢丝绳 (固定连接，相对横杆长度恒定不变) -->
                  <line :x1="d.x - 8" :y1="singleBarBeamY + 20" :x2="d.x - 8" :y2="d.flagY - 2"
                    stroke="rgba(200,164,92,0.7)" stroke-width="1.2" stroke-dasharray="3,2" />
                  <line :x1="d.x + 8" :y1="singleBarBeamY + 20" :x2="d.x + 8" :y2="d.flagY - 2"
                    stroke="rgba(200,164,92,0.7)" stroke-width="1.2" stroke-dasharray="3,2" />

                  <!-- 旗帜顶端金属吊挂横撑杆 (保持国旗舒展受力平衡) -->
                  <rect :x="d.x - 43" :y="d.flagY - 4" width="86" height="5" fill="url(#silverPoleGrad)" rx="1.5" />
                  <circle :cx="d.x - 43" :cy="d.flagY - 1.5" r="2.5" fill="#94A3B8" />
                  <circle :cx="d.x + 43" :cy="d.flagY - 1.5" r="2.5" fill="#94A3B8" />

                  <!-- 室内吊挂平整旗帜 (横向单杆模式 · 支持点击更换国家) -->
                  <g :class="['flag-clickable-item', { 'can-change': isAtLowerZero }]"
                    :transform="`translate(${d.x - 40}, ${d.flagY})`" @click="handleFlagClick(d.key)"
                    :title="flagClickTitle(d.key)">
                    <rect x="0" y="0" width="80" height="54" fill="transparent" pointer-events="all" />
                    <FlagFabricSvg :country="d.country" :width="80" :height="54" :static="true"
                      :clip-id="`clip-singlebar-${d.key}`" />
                  </g>

                  <!-- 底部名次与国家名标签 (名次 + 国家名合并单行 · 点击亦可更换国家) -->
                  <text :class="['flag-clickable-label', { 'can-change': isAtLowerZero }]" :x="d.x" y="464"
                    text-anchor="middle" @click="handleFlagClick(d.key)" :title="flagClickTitle(d.key)">
                    <tspan font-size="22" font-weight="bold" :fill="d.gold ? '#B45309' : '#1E293B'">{{ d.label }}
                    </tspan>
                    <tspan dx="10" font-size="18" font-weight="500" fill="#475569">{{ d.country ? d.country.nameCn :
                      '未选定' }}</tspan>
                  </text>
                </g>
              </g>
            </svg>

            <!-- 升旗台画布右下角：铺满与缩小操作按钮组 (等比例自适应，不拉伸变形) -->
            <div class="viewport-zoom-ctrl">
              <button :class="['zoom-btn', { active: isSimFull }]" @click="toggleSimFull(true)"
                title="铺满展示：隐藏左侧机组看板，全宽等比放大升旗台">
                <svg class="zoom-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="15 3 21 3 21 9" />
                  <polyline points="9 21 3 21 3 15" />
                  <line x1="21" y1="3" x2="14" y2="10" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
                <span>铺满</span>
              </button>
              <button :class="['zoom-btn', { active: !isSimFull }]" @click="toggleSimFull(false)"
                title="缩小还原：恢复左侧数据看板与标准双栏布局">
                <svg class="zoom-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="10" y1="14" x2="3" y2="21" />
                </svg>
                <span>缩小</span>
              </button>
            </div>
          </div>

          <!-- 升旗台下方：横向 5 个操作控制卡片 (紧急停止、颁奖升旗、上复位、下复位、升旗演练) -->
          <div class="viewport-hud-actions">
            <div class="hud-actions-head">
              <div class="hud-head-lbl">
                <SvgIcon name="SvgCpu" size="14" />
                <span>升旗控制指令组</span>
              </div>
              <div class="hud-head-right">
                <button class="btn-industrial btn-mini-tool" :disabled="isRunning" @click="promptSetManualRpm"
                  title="写入寄存器 0x01：设置手动点动/上下复位电机转速 (0.1~3000 RPM)">
                  手动转速 {{ lastManualRpm ?? '--' }} RPM
                </button>
                <button class="btn-industrial btn-mini-tool" :disabled="isRunning" @click="triggerAutoMeasure"
                  title="写入寄存器 0x09：触发自动测距（需电机停止且处于最高点限位）">
                  自动测距
                </button>
                <span class="mode-badge-mini cmd_control">可控状态</span>
              </div>
            </div>

            <!-- 横向 5 个卡片 (紧急停止、颁奖升旗、上复位、下复位、升旗演练) -->
            <div class="hud-cmd-list">
              <!-- 1. 紧急停止 (第一位 · 最高安全级) -->
              <button class="cmd-card estop-card hud-card" @click="handleEmergencyStop()"
                title="最高优先级急停：电机毫秒刹车断电，国歌即刻切断">
                <div class="cmd-card-inner">
                  <div class="cmd-icon-wrap estop-icon-wrap">
                    <svg class="estop-svg-icon" viewBox="0 0 24 24" width="28" height="28" fill="none"
                      aria-hidden="true">
                      <path d="M8.4 2.6h7.2l5.8 5.8v7.2l-5.8 5.8H8.4l-5.8-5.8V8.4z" fill="#FFFDF9" />
                      <rect x="7.6" y="10.2" width="8.8" height="3.6" rx="1.2" fill="#A0522D" />
                    </svg>
                  </div>
                  <div class="cmd-texts">
                    <span class="cmd-title text-danger">紧急停止</span>
                    <span class="cmd-desc">抱闸断电·停乐</span>
                  </div>
                </div>
              </button>

              <!-- 2. 颁奖升旗 (第二位) -->
              <button class="cmd-card official-card hud-card" :disabled="isRunning || !isAtLowerZero"
                @click="!isRunning && isAtLowerZero && confirmOfficialCeremony()"
                :title="!isAtLowerZero ? '旗面未归位：当前国旗不在“下复位”基准点，无法执行颁奖升旗，请先点击【下复位】平稳降旗归位' : '颁奖升旗：下发正式颁奖指令 (国歌音画同步联动)'">
                <div class="cmd-card-inner">
                  <div class="cmd-icon-wrap official-icon-wrap">
                    <SvgIcon name="SvgFlagSystem" size="24" />
                  </div>
                  <div class="cmd-texts">
                    <span class="cmd-title text-primary">颁奖升旗</span>
                    <span v-if="!isAtLowerZero && !isRunning" class="cmd-desc text-warning">旗面未归位·需下复位</span>
                    <span v-else class="cmd-desc">国歌同步·二次确认</span>
                  </div>
                </div>
              </button>

              <!-- 3. 上复位 (第三位) -->
              <button class="cmd-card top-card hud-card" :disabled="isRunning || isAtUpperTop"
                @click="!isRunning && !isAtUpperTop && moveToUpperZero()"
                :title="isAtUpperTop ? '旗帜已处于杆顶（上零位），不可重复执行上复位' : '上复位：升至最高限位 (上复位基准)'">
                <div class="cmd-card-inner">
                  <div class="cmd-icon-wrap top-icon-wrap">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.2"
                      stroke-linecap="round" stroke-linejoin="round">
                      <line x1="4" y1="5" x2="20" y2="5" />
                      <polyline points="7 14 12 9 17 14" />
                      <line x1="12" y1="9" x2="12" y2="19" />
                    </svg>
                  </div>
                  <div class="cmd-texts">
                    <span class="cmd-title text-info">上复位</span>
                    <span v-if="isAtUpperTop && !isRunning" class="cmd-desc">已在杆顶·无需复位</span>
                    <span v-else class="cmd-desc">平稳升顶·上限位</span>
                  </div>
                </div>
              </button>

              <!-- 4. 下复位 (第四位) -->
              <button class="cmd-card lower-card hud-card" :disabled="isRunning || isAtLowerZero"
                @click="!isRunning && !isAtLowerZero && startLowerFlag()"
                :title="isAtLowerZero ? '旗帜已处于底部起始位置（下零位），不可重复执行下复位' : '下复位：平稳降旗收回机械底端原点 (下复位)'">
                <div class="cmd-card-inner">
                  <div class="cmd-icon-wrap lower-icon-wrap">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.2"
                      stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="5" />
                      <line x1="4" y1="19" x2="20" y2="19" />
                    </svg>
                  </div>
                  <div class="cmd-texts">
                    <span class="cmd-title">下复位</span>
                    <span v-if="isAtLowerZero && !isRunning" class="cmd-desc">已在底原点·无需复位</span>
                    <span v-else class="cmd-desc">平稳降回·底原点</span>
                  </div>
                </div>
              </button>

              <!-- 5. 升旗演练 (第五位) -->
              <button class="cmd-card simulate-card hud-card" :disabled="isRunning || !isAtLowerZero"
                @click="!isRunning && isAtLowerZero && runCeremony('simulate')"
                :title="!isAtLowerZero ? '旗面未归位：当前国旗不在“下复位”基准点，无法执行升旗演练，请先点击【下复位】平稳降旗归位' : '升旗演练：联调彩排并同步下发自动升旗指令'">
                <div class="cmd-card-inner">
                  <div class="cmd-icon-wrap gold-icon-wrap">
                    <SvgIcon name="SvgTrophy" size="24" />
                  </div>
                  <div class="cmd-texts">
                    <span class="cmd-title text-gold">升旗演练</span>
                    <span v-if="!isAtLowerZero && !isRunning" class="cmd-desc text-warning">旗面未归位·需下复位</span>
                    <span v-else class="cmd-desc">联调彩排·音画同步</span>
                  </div>
                </div>
              </button>
            </div>
          </div>
          <div class="height-overlay num-mono">
            <template v-if="currentPoleMode === 'horizontal'">
              <span>横梁吊升行程: {{ championH.toFixed(2) }}m / 12.0m ({{ progressPct }}%)</span>
              <span>三旗相对横梁静止升空 · 吊升速度: {{ calculatedSpeed }} m/s</span>
            </template>
            <template v-else>
              <span>冠军杆: {{ championH.toFixed(2) }}m / {{ championTotalM.toFixed(1) }}m ({{ progressPct }}%)</span>
              <span>亚军杆: {{ runnerUpH.toFixed(2) }}m / {{ runnerUpTotalM.toFixed(1) }}m</span>
              <span>季军杆: {{ thirdH.toFixed(2) }}m / {{ thirdTotalM.toFixed(1) }}m</span>
            </template>
            <span class="flag-motion-status-item">
              <span class="motion-lbl">旗杆/旗帜 状态: </span>
              <span :class="['motion-val font-bold', flagMotionType]">{{ flagMotionText }}</span>
            </span>
          </div>

        </div>
      </div>
    </div>

    <!-- 国家选定模态框 (点击旗位卡片弹出 · 区域分组 / 模糊搜索 · 高保真卡片与即时试听) -->
    <el-dialog v-model="showCountryModal" width="1060px" append-to-body destroy-on-close
      class="country-picker-dialog modern-flag-picker" :show-close="true"
      :before-close="(done) => { handleCloseCountryModal(); done(); }">
      <template #header>
        <div class="modal-custom-header">
          <div class="mch-left">
            <div class="mch-medal-tag" :class="assignTarget">
              <span class="mch-medal-icon">{{ assignTarget === 'champion' ? '🥇' : assignTarget === 'runnerUp' ? '🥈' :
                '🥉' }}</span>
              <span class="mch-medal-title">{{ assignTargetLabel }}</span>
              <span class="mch-pole-badge">{{ assignTarget === 'champion' ? '1号主旗杆 (12.0m)' : assignTarget ===
                'runnerUp' ? '2号左旗杆 (10.5m)' : '3号右旗杆 (10.5m)' }}</span>
            </div>
            <div class="mch-titles">
              <h3 class="mch-main-title">指派【{{ assignTargetLabel }}】所属参赛国家与代表团</h3>
              <p class="mch-sub-title">收录全球 200 国及地区标准矢量国旗与权威国歌，点击卡片即刻同步更换</p>
            </div>
          </div>

          <!-- 席位快捷切换器 -->
          <div class="mch-slot-switch">
            <button v-for="s in slotDefs" :key="s.key" type="button" class="slot-switch-btn"
              :class="[s.key, { 'is-active': assignTarget === s.key }]" @click="switchAssignTargetInModal(s.key)">
              <span class="sw-icon">{{ s.key === 'champion' ? '🥇' : s.key === 'runnerUp' ? '🥈' : '🥉' }}</span>
              <span class="sw-label">{{ s.label.split(' ')[0] }}</span>
              <span v-if="slotCountry(s.key)" class="sw-curr-code num-mono">({{ slotCountry(s.key).code }})</span>
            </button>
          </div>
        </div>
      </template>

      <div class="dialog-country-content">
        <!-- 顶部工具条：搜索输入 + 快捷推荐 + 当前席位预显 -->
        <div class="picker-toolbar-panel">
          <div class="pt-top-row">
            <!-- 搜索框 -->
            <div class="pt-search-box">
              <el-input v-model="countrySearchKeyword" placeholder="搜索国家中文名、英文名、代码 (如 CN/CHN/USA/FRA) 或国歌..." clearable
                class="modern-search-input">
                <template #prefix>
                  <el-icon class="search-lens-icon">
                    <Search />
                  </el-icon>
                </template>
              </el-input>
            </div>

            <!-- 当前已指派展示 -->
            <div class="pt-current-assigned" v-if="currentSlotCountry">
              <span class="ca-label">当前席位:</span>
              <span class="ca-flag" :style="flagStyle(currentSlotCountry)"></span>
              <span class="ca-name">{{ currentSlotCountry.nameCn }}</span>
              <span class="ca-code num-mono">[{{ currentSlotCountry.code }} / {{ currentSlotCountry.codeAlpha3 ||
                currentSlotCountry.code }}]</span>
              <span class="ca-anthem-chip num-mono">🎵 {{ currentSlotCountry.anthemDuration }}s</span>
            </div>
          </div>

          <!-- 热门快速选择标签 -->
          <div class="pt-hot-tags">
            <span class="hot-tag-title">常用/代表团快捷定位:</span>
            <button v-for="hcode in ['CN', 'US', 'FR', 'JP', 'GB', 'AU', 'DE', 'IT', 'KR', 'BR', 'CA', 'ES']"
              :key="hcode" type="button" class="quick-country-chip"
              :class="{ 'is-active': currentSlotCountry?.code === hcode }" @click="quickSelectCountryByCode(hcode)">
              <span class="q-flag-dot" :style="flagStyle(getCountryByCode(hcode))"></span>
              <span class="q-name">{{ getCountryByCode(hcode)?.nameCn }}</span>
              <span class="q-code num-mono">{{ hcode }}</span>
            </button>
          </div>
        </div>

        <!-- 区域大洲分类 Tab 切换 -->
        <div class="dialog-region-bar modern-pill-tabs">
          <button v-for="r in regionTabs" :key="r" :class="['d-region-pill', { active: regionFilter === r }]"
            @click="regionFilter = r">
            <span class="pill-text">{{ r }}</span>
            <span class="pill-count num-mono">{{ regionCounts[r] || 0 }}</span>
          </button>
        </div>

        <!-- 国家卡片列表网格 -->
        <div class="dialog-country-grid modern-grid">
          <div v-for="c in filteredModalCountries" :key="c.id" :class="[
            'd-country-card',
            { 'is-selected': isCurrentSlotCountry(c.id) },
            { 'is-other-assigned': getOtherAssignedSlot(c.id) }
          ]" @click="confirmAssignCountry(c)">
            <!-- 左侧国旗预览区 (高度与右侧两行完全齐平等高) -->
            <div class="card-flag-stage">
              <span class="card-flag-img" :style="flagStyle(c)"></span>
              <span class="card-iso-tag num-mono">{{ c.codeAlpha3 || c.code }}</span>
            </div>

            <!-- 右侧两行信息区 -->
            <div class="card-info-stage">
              <!-- 第1行：国家中文名 + 英文名 (字号更小紧随其后) + 二字代码 -->
              <div class="card-title-line">
                <div class="card-names-wrap">
                  <span class="card-name-cn" :title="c.nameCn">{{ c.nameCn }}</span>
                  <span class="card-name-en-inline" :title="c.nameEn">{{ c.nameEn }}</span>
                </div>
                <span class="card-code-pill num-mono">{{ c.code }}</span>
              </div>

              <!-- 第2行：试听按钮 + 国歌名称 + 时长 -->
              <div class="card-anthem-row">
                <button type="button" class="anthem-audition-btn" :class="{ 'is-playing': modalPlayingCode === c.code }"
                  :title="modalPlayingCode === c.code ? '停止试听' : '点击试听国歌音频'"
                  @click.stop="togglePlayModalAnthem($event, c)">
                  <span v-if="modalPlayingCode === c.code" class="aud-icon">⏹</span>
                  <span v-else class="aud-icon">▶</span>
                  <span class="aud-label">{{ modalPlayingCode === c.code ? '暂停' : '试听' }}</span>
                </button>
                <div class="anthem-name-strip" :title="c.anthemName">
                  {{ c.anthemName || '国歌' }}
                </div>
                <span class="anthem-sec-badge num-mono">{{ c.anthemDuration }}s</span>
              </div>
            </div>

            <!-- 角标状态 -->
            <div v-if="isCurrentSlotCountry(c.id)" class="card-badge current-badge" :class="assignTarget">
              ✓ 当前{{ assignTargetLabel.split(' ')[0] }}
            </div>
            <div v-else-if="getOtherAssignedSlot(c.id)" class="card-badge other-badge">
              已指派为 {{ getOtherAssignedSlot(c.id) }}
            </div>
          </div>

          <div v-if="!filteredModalCountries.length" class="modern-dialog-empty">
            <div class="empty-icon-box">🔍</div>
            <p class="empty-main">未找到符合条件的国家或代表团</p>
            <p class="empty-sub">可尝试缩减搜索词或切换大洲分类，您也可前往国家资料库录入新增</p>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-meta modern-footer">
          <div class="d-foot-info-box">
            <span class="foot-count-tag">
              在库筛选: <strong class="num-mono">{{ filteredModalCountries.length }}</strong> / {{ countries.length }} 国
            </span>
            <span class="foot-tip-tag">点选卡片直接指派，国旗与国歌音画同步立即生效</span>
          </div>
          <div class="d-foot-actions">
            <el-button @click="goCountryLibrary">
              <el-icon style="margin-right: 4px;">
                <Edit />
              </el-icon>
              管理国家资料库
            </el-button>
            <el-button type="primary" @click="handleCloseCountryModal">关闭窗口</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 页面底部：PLC 硬件执行回执与升旗仪式总线指令日志 (全宽底栏) -->
    <div class="flag-receipt-layout glass-panel">
      <!-- 1. PLC 硬件执行回执 (Receipt) 移动至页面底部全宽呈现 -->
      <div class="receipt-section-block bottom-full-receipt">
        <div class="action-block-head">
          <span class="group-label">
            <SvgIcon name="SvgCpu" size="14" />
            <span>PLC 硬件执行回执 (Hardware Receipt)</span>
          </span>
          <div class="receipt-status-wrap">
            <span class="receipt-pulse-dot"></span>
            <span class="receipt-status-code num-mono">{{ deviceReceipt }}</span>
          </div>
        </div>

        <div class="receipt-summary-block num-mono">
          <div class="rs-grid">
            <div class="rs-item">
              <span class="rs-lbl">最近下发动作:</span>
              <span class="rs-val text-gold font-bold">{{ lastActionText }}</span>
            </div>
            <div class="rs-item">
              <span class="rs-lbl">PLC 执行代码:</span>
              <span class="rs-val text-success font-bold">{{ deviceReceipt }}</span>
            </div>
            <div class="rs-item">
              <span class="rs-lbl">回执响应时间:</span>
              <span class="rs-val text-primary">{{ lastActionTime }}</span>
            </div>
            <div class="rs-item">
              <span class="rs-lbl">联动受控机组:</span>
              <span class="rs-val text-primary rs-dev-val" :title="checkedIds.join(' , ')">
                {{ checkedIds.length ? checkedIds.join(' , ') : '未勾选受控设备' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. 升旗仪式运行与通信总线指令日志 (Live Bus Run Log) -->
      <div class="panel-header log-header">
        <div class="header-left">
          <SvgIcon name="SvgSerialPort" size="16" class="text-gold" />
          <span class="header-title">升旗仪式运行与通信总线指令日志 (Live Bus Run Log)</span>
        </div>
        <div class="header-right">
          <span :class="['receipt-pulse-dot', { offline: !wsConnected && !lastHwOnline }]"></span>
          <span class="receipt-status-code num-mono">
            {{ wsConnected ? (lastHwOnline ? 'WS 实时通道在线 · 网关数据同步中' : 'WS 实时通道已连接 · 等待网关响应') : 'WS 重连中 · HTTP 兜底模式' }}
          </span>
        </div>
      </div>

      <div class="receipt-bottom-body single-log">
        <!-- 仪式运行与通信日志流 (全宽铺开) -->
        <div class="receipt-log-block num-mono">
          <div class="rs-log-scroll">
            <p v-for="(line, idx) in runLog" :key="idx" class="log-entry">{{ line }}</p>
            <p v-if="!runLog.length" class="text-secondary">暂无总线执行记录</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ===== 设备管理弹窗（参数全部入库）===== -->
  <el-dialog v-model="deviceManagerVisible" title="旗杆设备管理" width="960px">
    <div class="dev-mgr-head">
      <span>设备参数全部存入后台数据库（flag_devices 表），不硬编码。</span>
      <button class="dev-mgr-btn primary" @click="newDeviceForm">+ 新增设备</button>
    </div>
    <el-table :data="deviceRows" size="small" style="width:100%" empty-text="暂无设备">
      <el-table-column prop="device_id" label="设备ID" width="105" />
      <el-table-column prop="name" label="设备名称" width="145" show-overflow-tooltip />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          <span>{{ row.pole_type === 'horizontal' ? '横向单杆' : '纵向三杆' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="IP地址" width="155">
        <template #default="{ row }">{{ row.host }}:{{ row.port }}</template>
      </el-table-column>
      <el-table-column prop="unit_id" label="从站" width="54" />
      <el-table-column label="行程" width="80">
        <template #default="{ row }">{{ row.total_stroke_mm ? (row.total_stroke_mm / 1000).toFixed(2) + 'm' : '--'
        }}</template>
      </el-table-column>
      <el-table-column label="在线" width="66">
        <template #default="{ row }">
          <span :class="row.status && row.status.online ? 'tag-safe' : 'tag-danger'">
            {{ row.status && row.status.online ? '在线' : '离线' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130">
        <template #default="{ row }">
          <button class="dev-mgr-btn" @click="editDeviceForm(row)">编辑</button>
          <button class="dev-mgr-btn danger" @click="removeDevice(row)">删除</button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="deviceFormVisible" class="dev-form">
      <div class="dev-form-title">{{ deviceForm.device_id ? '编辑设备' : '新增设备' }}</div>
      <div class="dev-form-grid">
        <label>设备ID</label><input v-model="deviceForm.device_id" placeholder="FLG-01" />
        <label>名称</label><input v-model="deviceForm.name" placeholder="主体育场旗杆" />
        <label>机构模式</label>
        <select v-model="deviceForm.pole_type">
          <option value="vertical">纵向三杆（三杆并排）</option>
          <option value="horizontal">横向单杆（一杆挂三旗）</option>
        </select>
        <label>所属区域</label><input v-model="deviceForm.region" placeholder="主体育场·领奖台" />
        <label>网关 IP</label><input v-model="deviceForm.host" placeholder="192.168.0.7" />
        <label>Modbus 端口</label><input v-model.number="deviceForm.port" type="number" />
        <label>从站 ID</label><input v-model.number="deviceForm.unit_id" type="number" />
        <label>超时(秒)</label><input v-model.number="deviceForm.timeout_s" type="number" step="0.5" />
        <label>标称高度(m)</label><input v-model.number="deviceForm.pole_height_m" type="number" step="0.1" />
        <label>实测行程(mm)</label><input v-model.number="deviceForm.total_stroke_mm" type="number" />
        <label>每米脉冲</label><input v-model.number="deviceForm.pulses_per_meter" type="number" />
        <label>运行上限(s)</label><input v-model.number="deviceForm.max_moving_seconds" type="number" step="5" />
        <label>心跳超时(s)</label><input v-model.number="deviceForm.heartbeat_timeout_s" type="number" step="10" />
      </div>
      <div class="dev-form-actions">
        <button class="dev-mgr-btn" @click="testDeviceConnection" :disabled="deviceTesting">
          {{ deviceTesting ? '测试中...' : '测试连接' }}
        </button>
        <button class="dev-mgr-btn primary" @click="saveDevice">保存</button>
        <button class="dev-mgr-btn" @click="deviceFormVisible = false">取消</button>
      </div>
      <div v-if="deviceTestResult" class="dev-test-result" :class="deviceTestResult.reachable ? 'ok' : 'fail'">
        {{ deviceTestResult.reachable ? '连接成功' : '连接失败' }}
        <template v-if="deviceTestResult.reachable"> 延迟 {{ deviceTestResult.latency_ms }}ms</template>
        <template v-else> {{ deviceTestResult.error || deviceTestResult.hint }}</template>
      </div>
    </div>
  </el-dialog>

</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Edit } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { useFlagCountriesStore, REGIONS, flagStyle } from '@/stores/flagCountries'
import { api } from '@/services/api'
import FlagFabricSvg from './components/FlagFabricSvg.vue'

/* ============================================================
 * 一、国家资料库 (区域分组 / 国旗 / 国歌 绑定)
 *    资料录入与编辑已迁移至独立路由页 /iot/flag/countries,
 *    控制台与资料页共享 useFlagCountriesStore 同一实例, 增删改即时同步
 * ============================================================ */
const router = useRouter()
const route = useRoute()
const countriesStore = useFlagCountriesStore()
const countries = computed(() => countriesStore.countries)

function goCountryLibrary() {
  router.push('/iot/flag/countries')
}

// 冠军 / 亚军 / 季军 三档位
const championId = ref('CN')
const runnerUpId = ref('JP')
const thirdId = ref('KR')
const assignTarget = ref('champion')

const champion = computed(() => countries.value.find(c => c.id === championId.value) || null)
const runnerUp = computed(() => countries.value.find(c => c.id === runnerUpId.value) || null)
const third = computed(() => countries.value.find(c => c.id === thirdId.value) || null)

// 一行三个卡片从左到右：亚军 (银牌) · 冠军 (金牌) · 季军 (铜牌)
const slotDefs = [
  { key: 'runnerUp', label: '亚军 (银牌)' },
  { key: 'champion', label: '冠军 (金牌)' },
  { key: 'third', label: '季军 (铜牌)' }
]

function slotCountry(key) {
  return key === 'champion' ? champion.value : key === 'runnerUp' ? runnerUp.value : third.value
}

const assignTargetLabel = computed(() => {
  const f = slotDefs.find(s => s.key === assignTarget.value)
  return f ? f.label : '冠军'
})

// 国家选定模态框状态与逻辑
// 升旗台视窗铺满状态 (铺满模式下隐藏左侧机组看板，col-sim 全宽等比放大展示)
const isSimFull = ref(false)

function toggleSimFull(val) {
  if (typeof val === 'boolean') {
    isSimFull.value = val
  } else {
    isSimFull.value = !isSimFull.value
  }
}

// 支持 ESC 键便捷退出铺满模式
function handleEscKey(e) {
  if (e.key === 'Escape' && isSimFull.value) {
    isSimFull.value = false
  }
}

const showCountryModal = ref(false)
const countrySearchKeyword = ref('')

// 判断当前是否处于“下复位”待机静止状态 (硬件处于下零位或高度归零且无动作运行)
const isAtLowerZero = computed(() => {
  if (isRunning.value || flagStatus.value === 'RISING' || flagStatus.value === 'LOWERING') {
    return false
  }
  const snap = lastHardwareSnapshot.value
  if (snap && snap.run_status === 0) {
    if (snap.limit_bottom !== 0) return true
    if (snap.limit_top !== 0) return false
  }
  return championH.value <= 0.05 &&
    runnerUpH.value <= 0.05 &&
    thirdH.value <= 0.05
})

// 判断当前是否处于“杆顶/上复位”静止状态 (硬件处于上零位或高度已达杆顶)
const isAtUpperTop = computed(() => {
  if (isRunning.value || flagStatus.value === 'RISING' || flagStatus.value === 'LOWERING') {
    return false
  }
  const snap = lastHardwareSnapshot.value
  if (snap && snap.run_status === 0) {
    if (snap.limit_top !== 0) return true
    if (snap.limit_bottom !== 0) return false
  }
  return championH.value >= championTotalM - 0.05 &&
    runnerUpH.value >= runnerUpTotalM - 0.05 &&
    thirdH.value >= thirdTotalM - 0.05
})

// 旗帜悬浮提示文案
function flagClickTitle(key) {
  const labelMap = { champion: '冠军', runnerUp: '亚军', third: '季军' }
  const label = labelMap[key] || '旗位'
  if (isAtLowerZero.value) {
    return `点击更换【${label}】所属国家与旗帜`
  }
  if (isRunning.value) {
    return '升旗仪式执行中，不可更换国家与旗帜'
  }
  return '仅允许在“下复位”待机状态下更换国家，请先点击【下复位】归零'
}

// 点击升旗台界面上的旗帜或标签更换国家 (只能在“下复位”状态下，升旗过程中不能更换)
function handleFlagClick(key) {
  // 1. 严格安全拦截：升旗过程中不能更换
  if (isRunning.value) {
    ElMessage.warning('升旗仪式正在执行中，严禁更换国家与旗帜！')
    return
  }

  // 2. 严格安全拦截：只能在“下复位”状态下更换
  if (!isAtLowerZero.value) {
    ElMessage.warning('仅允许在“下复位”静止待机状态下更换国家和旗帜！当前旗帜尚未归位，请先点击【下复位】。')
    return
  }

  // 3. 满足条件：打开国家选择模态框
  openCountrySelectModal(key)
}

function openCountrySelectModal(key) {
  assignTarget.value = key
  countrySearchKeyword.value = ''
  showCountryModal.value = true
}

const actualAnthemDurationSec = ref(null)

const selectedAudio = computed(() => {
  const c = champion.value
  if (!c) return { name: '尚未选定冠军国家 · 请点击冠军卡片选择国家', durationMs: 48560, durationSec: 48.56 }
  const sec = actualAnthemDurationSec.value || c.anthemDurationPrecise || c.anthemDuration || 48.56
  return {
    name: `${c.nameCn}国歌 · 《${c.anthemName}》`,
    durationMs: Math.round(sec * 1000),
    durationSec: sec
  }
})

const regionTabs = ['全部', ...REGIONS]
const regionFilter = ref('全部')

const regionCounts = computed(() => {
  const map = { '全部': countries.value.length }
  for (const r of REGIONS) {
    map[r] = countries.value.filter(c => c.region === r).length
  }
  return map
})

const currentSlotCountry = computed(() => {
  return slotCountry(assignTarget.value)
})

function getCountryByCode(code) {
  return countries.value.find(c => c.code === code) || null
}

function quickSelectCountryByCode(code) {
  const c = getCountryByCode(code)
  if (c) {
    confirmAssignCountry(c)
  }
}

function switchAssignTargetInModal(key) {
  assignTarget.value = key
}

function getOtherAssignedSlot(id) {
  if (assignTarget.value !== 'champion' && championId.value === id) return '冠军'
  if (assignTarget.value !== 'runnerUp' && runnerUpId.value === id) return '亚军'
  if (assignTarget.value !== 'third' && thirdId.value === id) return '季军'
  return null
}

const modalPlayingCode = ref(null)
let modalAudioPlayer = null

function togglePlayModalAnthem(e, c) {
  if (e && e.stopPropagation) e.stopPropagation()
  if (modalPlayingCode.value === c.code) {
    if (modalAudioPlayer) {
      modalAudioPlayer.pause()
      modalAudioPlayer = null
    }
    modalPlayingCode.value = null
    return
  }
  if (modalAudioPlayer) {
    modalAudioPlayer.pause()
    modalAudioPlayer = null
  }
  const audioSrc = c.anthemUrl || `/uploads/audio/${c.code}.mp3`
  try {
    modalAudioPlayer = new Audio(audioSrc)
    modalAudioPlayer.play().then(() => {
      modalPlayingCode.value = c.code
    }).catch(() => {
      modalPlayingCode.value = null
      ElMessage.warning(`国歌《${c.anthemName}》加载失败`)
    })
    modalAudioPlayer.onended = () => {
      modalPlayingCode.value = null
    }
    modalAudioPlayer.onerror = () => {
      modalPlayingCode.value = null
      ElMessage.warning(`国歌《${c.anthemName}》播放异常`)
    }
  } catch (err) {
    modalPlayingCode.value = null
  }
}

function handleCloseCountryModal() {
  if (modalAudioPlayer) {
    modalAudioPlayer.pause()
    modalAudioPlayer = null
  }
  modalPlayingCode.value = null
  showCountryModal.value = false
}

const filteredModalCountries = computed(() => {
  let list = countries.value
  if (regionFilter.value && regionFilter.value !== '全部') {
    list = list.filter(c => c.region === regionFilter.value)
  }
  const kw = countrySearchKeyword.value.trim().toLowerCase()
  if (kw) {
    list = list.filter(c =>
      (c.nameCn && c.nameCn.toLowerCase().includes(kw)) ||
      (c.nameEn && c.nameEn.toLowerCase().includes(kw)) ||
      (c.code && c.code.toLowerCase().includes(kw)) ||
      (c.codeAlpha3 && c.codeAlpha3.toLowerCase().includes(kw)) ||
      (c.region && c.region.toLowerCase().includes(kw)) ||
      (c.anthemName && c.anthemName.toLowerCase().includes(kw)) ||
      (c.anthemEn && c.anthemEn.toLowerCase().includes(kw))
    )
  }
  return list
})

function confirmAssignCountry(c) {
  if (modalAudioPlayer) {
    modalAudioPlayer.pause()
    modalAudioPlayer = null
  }
  modalPlayingCode.value = null
  assignCountry(c)
  showCountryModal.value = false
}

function isCurrentSlotCountry(id) {
  const current = slotCountry(assignTarget.value)
  return current?.id === id
}

function assignCountry(c) {
  const targetIdRef = assignTarget.value === 'champion' ? championId : assignTarget.value === 'runnerUp' ? runnerUpId : thirdId
  const label = assignTargetLabel.value
  targetIdRef.value = c.id
  actualAnthemDurationSec.value = null
  ElMessage.success(`${label}已设定为「${c.nameCn} (${c.code})」，国旗与国歌《${c.anthemName}》已就绪！`)
  logLine(`国家指派：${label} → ${c.nameCn} (${c.code}) · 国歌:《${c.anthemName}》`)
  if (!isRunning.value) stopAnthem()
}

/* ============================================================
 * 二、升旗动力学状态与音画同步参数
 * 规范：冠军旗杆维持最高(12.0m)，亚军与季军高度完全相同(10.5m)
 * 国歌演奏完毕时，三面旗帜自适应各自行程速度，同步全部升顶！
 * ============================================================ */
const championTotalM = 12.0
const runnerUpTotalM = 10.5
const thirdTotalM = 10.5 // 亚军与季军高度相同，冠军维持最高

const championH = ref(0)
const runnerUpH = ref(0)
const thirdH = ref(0)
const motorRpm = ref(0)
const isRunning = ref(false)
const flagStatus = ref('IDLE') // IDLE / RISING / LOWERING / ESTOPPED / COMPLETED
const playTimeMs = ref(0)

let animTimer = null
let activeDeviceId = null

const calculatedSpeed = computed(() =>
  (championTotalM / Math.max(1, selectedAudio.value.durationSec)).toFixed(4)
)

const progressPct = computed(() =>
  Math.min(100, Math.floor((championH.value / championTotalM) * 100))
)

// 旗杆/旗帜实时运动状态 (上升中、下降中、静止)
const flagMotionType = computed(() => {
  if (flagStatus.value === 'RISING') return 'status-rising'
  if (flagStatus.value === 'LOWERING') return 'status-lowering'
  return 'status-forbidden'
})

const flagMotionText = computed(() => {
  if (flagStatus.value === 'RISING') return '上升中'
  if (flagStatus.value === 'LOWERING') return '下降中'
  return '静止'
})

const lastActionText = ref('未执行')
const deviceReceipt = ref('PLC_STATUS_READY')
const lastActionTime = ref('--:--:--')
const runLog = ref([])

function nowStr() {
  return new Date().toLocaleTimeString()
}

function logLine(text) {
  runLog.value.unshift(`${nowStr()}  ${text}`)
  if (runLog.value.length > 10) runLog.value.pop()
}

/* ============================================================
 * 三、SVG 动力学矢量仿真视窗 (竖向三杆 / 横向单杆) · 严格由读取到的设备数据决定
 * ============================================================ */
const activeReadDeviceId = ref('FLG-POLE-01')

const currentReadingDevice = computed(() =>
  devices.value.find(d => d.id === activeReadDeviceId.value) || devices.value[0]
)

// 中间升旗台机构类型（横向单杆还是竖向三杆），直接来自于读取到的设备信息
const currentPoleMode = computed(() => {
  return currentReadingDevice.value?.poleType || 'vertical'
})

const wavePhase = ref(0)
let waveAnimId = null

function isDeviceSelected(id) {
  return checkedIds.value.includes(id)
}

function onCardClick(id) {
  toggleDevice(id)
  activeReadDeviceId.value = id
}

function startWaveLoop() {
  let lastTime = performance.now()
  const loop = (now) => {
    const dt = (now - lastTime) / 1000
    lastTime = now
    // 微风起伏速率 (配合 1.8 m/s 微风联动)
    wavePhase.value += dt * 2.2
    waveAnimId = requestAnimationFrame(loop)
  }
  waveAnimId = requestAnimationFrame(loop)
}

function stopWaveLoop() {
  if (waveAnimId) {
    cancelAnimationFrame(waveAnimId)
    waveAnimId = null
  }
}

// A 模式: 竖向三杆动力学高度与位置计算 (880 x 480 宽幅)
// 奥运/亚运颁奖礼仪物理标准：冠军杆最高 (poleTop: 44, 行程 12.0m)
// 亚军杆略低 (poleTop: 88, 行程 10.5m)
// 季军杆与亚军等高 (poleTop: 88, 行程 10.5m)
const vertPolesConfig = {
  poleBottom: 412 // 增加 36px 高度至旗杆 (基座下移后杆身伸长)
}

const verticalPoles = computed(() => {
  const hChampion = championH.value
  const hRunner = runnerUpH.value
  const hThird = thirdH.value

  const calcFlagY = (h, poleTop, totalStroke, bottomGap = 16) => {
    const f = Math.max(0, Math.min(1, h / totalStroke))
    const baseBottomY = vertPolesConfig.poleBottom - 54 - bottomGap // 底部初始静止位置：冠军距底部旗台 36px，亚军与季军距底部 16px
    const travel = baseBottomY - poleTop // 升至杆顶的实际总像素行程
    return baseBottomY - f * travel
  }

  return [
    {
      key: 'runnerUp',
      label: '亚军',
      x: 230, // 左右完美居中对称：亚军 230 (距左 230)
      gold: false,
      country: runnerUp.value,
      poleTop: 88, // 亚军旗杆 (行程 10.5m)
      totalStroke: runnerUpTotalM,
      currentH: hRunner,
      flagY: calcFlagY(hRunner, 88, runnerUpTotalM, 16),
      phaseOffset: 230 * 0.05
    },
    {
      key: 'champion',
      label: '冠军',
      x: 440, // 视窗绝对中心线 (880/2 = 440)
      gold: true,
      country: champion.value,
      poleTop: 44, // 冠军旗杆最高 (行程 12.0m)
      totalStroke: championTotalM,
      currentH: hChampion,
      flagY: calcFlagY(hChampion, 44, championTotalM, 36),
      phaseOffset: 440 * 0.05
    },
    {
      key: 'third',
      label: '季军',
      x: 650, // 左右完美居中对称：季军 650 (距右 230)
      gold: false,
      country: third.value,
      poleTop: 88, // 季军旗杆 (与亚军等高: 10.5m)
      totalStroke: thirdTotalM,
      currentH: hThird,
      flagY: calcFlagY(hThird, 88, thirdTotalM, 16),
      phaseOffset: 650 * 0.05
    }
  ]
})

// B 模式: 横向单杆 (一杆挂三旗 · 亚军和季军高度相同处于同一水平线，冠军略高，高差等同于竖向三杆模式 44px / 1.5m)
// 升旗全程三面旗帜与横梁保持刚性相对静止，升旗完毕后相对距离恒定不变
const singleBarConfig = {
  beamTopY: 46,      // 升顶到位时横梁顶Y坐标
  beamBottomY: 258   // 初始待机时横梁顶Y坐标同步下移 36px，旗杆与行程加长
}

const singleBarBeamY = computed(() => {
  const h = championH.value
  const f = Math.max(0, Math.min(1, h / championTotalM))
  return singleBarConfig.beamBottomY - f * (singleBarConfig.beamBottomY - singleBarConfig.beamTopY)
})

const singleBarPoles = computed(() => {
  const beamY = singleBarBeamY.value

  return [
    {
      key: 'runnerUp',
      label: '亚军',
      x: 230, // 左右完美居中对称：亚军 230
      gold: false,
      country: runnerUp.value,
      flagY: beamY + 84,
      phaseOffset: 230 * 0.05
    },
    {
      key: 'champion',
      label: '冠军',
      x: 440, // 视窗绝对中心线 (440)
      gold: true,
      country: champion.value,
      flagY: beamY + 40,
      phaseOffset: 440 * 0.05
    },
    {
      key: 'third',
      label: '季军',
      x: 650, // 左右完美居中对称：季军 650
      gold: false,
      country: third.value,
      flagY: beamY + 84,
      phaseOffset: 650 * 0.05
    }
  ]
})

/* ============================================================
 * 四、国歌音频播放 (上传音频真实播放 / 无文件时 WebAudio 合成)
 * ============================================================ */
let audioCtx = null
let masterGain = null
let synthTimer = null
let anthemEl = null

function hashInt(s) {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return h
}

function playAnthem(onPlayStarted = null, onPlayEnded = null) {
  stopAnthem()
  const c = champion.value
  if (!c) return
  // 优先播放上传绑定的国歌音频文件
  if (c.anthemUrl) {
    try {
      anthemEl = new Audio(c.anthemUrl)
      anthemEl.volume = 0.9
      anthemEl.currentTime = 0

      // 实时获取真实解码物理时长
      anthemEl.addEventListener('loadedmetadata', () => {
        if (anthemEl.duration && !isNaN(anthemEl.duration) && anthemEl.duration > 0) {
          actualAnthemDurationSec.value = anthemEl.duration
        }
      })

      // 真正开始发声时才回调通知启动升旗
      let started = false
      const triggerStart = () => {
        if (!started) {
          started = true
          if (onPlayStarted) {
            const finalDur = (anthemEl && anthemEl.duration && !isNaN(anthemEl.duration) && anthemEl.duration > 0)
              ? anthemEl.duration
              : (c.anthemDurationPrecise || c.anthemDuration || 48.56)
            onPlayStarted(finalDur)
          }
        }
      }

      anthemEl.addEventListener('playing', triggerStart)

      // 自然演奏完毕
      anthemEl.addEventListener('ended', () => {
        if (onPlayEnded) onPlayEnded()
      })

      anthemEl.play().catch(() => {
        ElMessage.warning('音频播放被浏览器拦截，请点击页面任意处激活音频')
        triggerStart()
      })
    } catch (e) {
      if (onPlayStarted) onPlayStarted(c.anthemDurationPrecise || c.anthemDuration || 48.56)
    }
    return
  }
  // 无音频文件: WebAudio 合成国歌旋律 (仪式仿真用)
  try {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) {
      if (onPlayStarted) onPlayStarted(c.anthemDuration || 46)
      return
    }
    audioCtx = audioCtx || new AC()
    if (audioCtx.state === 'suspended') audioCtx.resume()
    masterGain = audioCtx.createGain()
    masterGain.gain.value = 0.08
    masterGain.connect(audioCtx.destination)
  } catch (e) {
    if (onPlayStarted) onPlayStarted(c.anthemDuration || 46)
    return
  }
  const scale = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25]
  const seed = hashInt(c.code || 'XX')
  let idx = 0
  synthTimer = setInterval(() => {
    if (!masterGain || !audioCtx) return
    const t = audioCtx.currentTime
    const o = audioCtx.createOscillator()
    const g = audioCtx.createGain()
    o.type = 'triangle'
    o.frequency.value = scale[(seed + idx * 3 + (idx % 2) * 2) % scale.length]
    g.gain.setValueAtTime(0.0001, t)
    g.gain.exponentialRampToValueAtTime(0.9, t + 0.05)
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.6)
    o.connect(g)
    g.connect(masterGain)
    o.start(t)
    o.stop(t + 0.65)
    idx++
  }, 400)

  if (onPlayStarted) {
    onPlayStarted(c.anthemDurationPrecise || c.anthemDuration || 46)
  }
}

function stopAnthem() {
  if (anthemEl) {
    try { anthemEl.pause(); anthemEl.currentTime = 0 } catch (e) { }
    anthemEl = null
  }
  if (synthTimer) {
    clearInterval(synthTimer)
    synthTimer = null
  }
  if (masterGain) {
    try { masterGain.disconnect() } catch (e) { }
    masterGain = null
  }
}

/* ============================================================
 * 五、升旗动作: 模拟颁奖 / 正式颁奖 / 半旗 / 降旗 / 校准 / 强制升顶
 * ============================================================ */
function estimateManualMotionMs(hw, ratio = 1) {
  const turns = hw?.total_turns || (hw?.total_pulses && hw?.pulses_per_rev ? hw.total_pulses / hw.pulses_per_rev : 0)
  const rpm = hw?.manual_rpm || 1000
  const fullTravelMs = turns > 0 && rpm > 0 ? Math.round((turns / (rpm / 60)) * 1000) : 36000
  return Math.max(3000, Math.round(fullTravelMs * Math.max(0.15, Math.min(1, ratio))))
}

function tweenHeights(to, durationMs, onDone, options = {}) {
  const from = { c: championH.value, r: runnerUpH.value, t: thirdH.value }
  const start = performance.now()
  const isLinear = !!options.linear
  const waitForHardware = !!options.waitForHardware
  clearInterval(animTimer)
  isRunning.value = true
  animTimer = setInterval(() => {
    const rawK = Math.min(1, (performance.now() - start) / durationMs)
    const k = waitForHardware ? Math.min(0.98, rawK) : rawK
    const e = isLinear ? k : (1 - Math.pow(1 - k, 3))
    championH.value = +(from.c + (to.c * championTotalM - from.c) * e).toFixed(2)
    runnerUpH.value = +(from.r + (to.r * runnerUpTotalM - from.r) * e).toFixed(2)
    thirdH.value = +(from.t + (to.t * thirdTotalM - from.t) * e).toFixed(2)
    syncDevicesLive()
    if (!waitForHardware && rawK >= 1) {
      clearInterval(animTimer)
      animTimer = null
      isRunning.value = false
      if (onDone) onDone()
    }
  }, 50)
}

let actionLaunching = false
let estopLatched = false
let receiptLockUntil = 0

function setLockedReceipt(code, lockMs = 5000) {
  deviceReceipt.value = code
  receiptLockUntil = Date.now() + lockMs
}

// 模拟颁奖 / 正式颁奖: 升旗全程自动播放冠军国家国歌 (音画与硬件闭环同步)
async function runCeremony(kind) {
  if (actionLaunching || isRunning.value) {
    ElMessage.warning('动作正在启动或进行中，请等待完成或先触发急停')
    return
  }
  if (!isAtLowerZero.value) {
    ElMessage.warning('当前国旗不在“下复位”状态（旗面未归位），无法启动升旗！请先点击【下复位】使旗帜平稳降至底端原点后，再执行升旗。')
    return
  }
  const c = champion.value
  if (!c) {
    ElMessage.warning('请先点击冠军卡片选定冠军国家')
    return
  }

  actionLaunching = true
  isRunning.value = true
  estopLatched = false
  try {
    // 启动前先核对真实硬件状态：若已在最高点限位或正在运行，直接拦截提示
    const preHw = await syncFlagHardwareStatus(true)
    if (preHw && preHw.run_status !== 0) {
      isRunning.value = false
      ElMessage.warning(`现场硬件正在运行（${preHw.run_status_text}），请先点击【紧急停止】`)
      return
    }
    if (preHw && preHw.limit_top !== 0) {
      isRunning.value = false
      ElMessage.warning(`现场硬件当前已处于最高点（${preHw.limit_top_text}），无法再次升旗！请先点击【下复位】降旗归零。`)
      logLine(`升旗拦截：硬件当前处于${preHw.limit_top_text}，请先下复位`)
      return
    }
  } finally {
    actionLaunching = false
  }
  const isSim = kind === 'simulate'
  flagStatus.value = 'RISING'
  motorRpm.value = 1450
  playTimeMs.value = 0
  championH.value = 0
  runnerUpH.value = 0
  thirdH.value = 0
  lastActionText.value = isSim ? '升旗演练 (联调彩排)' : '正式颁奖 (音画同步)'
  lastActionTime.value = nowStr()
  deviceReceipt.value = isSim ? 'PLC_DRILL_CEREMONY_ACK (20ms)' : 'PLC_OFFICIAL_CEREMONY_ACK (20ms)'
  devices.value.forEach(d => {
    if (d.status !== 'OFFLINE' && (checkedIds.value.includes(d.id) || d.id === activeDeviceId)) {
      d.status = 'BUSY'
      d.lastCmd = isSim ? '升旗演练' : '正式颁奖'
      d.updated = nowStr()
    }
  })

  // 升旗仪式完成时的收尾处理 (确保国歌结束且硬件真正停机到位)
  let ceremonyCompleted = false
  const completeUI = (reasonText = '') => {
    if (ceremonyCompleted) return
    ceremonyCompleted = true
    stopMotionPolling()
    if (animTimer) {
      clearInterval(animTimer)
      animTimer = null
    }
    isRunning.value = false
    motorRpm.value = 0
    flagStatus.value = 'COMPLETED'
    championH.value = championTotalM
    runnerUpH.value = runnerUpTotalM
    thirdH.value = thirdTotalM
    syncDevicesLive()
    activeDeviceId = null
    devices.value.forEach(d => {
      if (d.status === 'BUSY') { d.status = 'ONLINE'; d.updated = nowStr() }
    })
    deviceReceipt.value = 'PLC_LIMIT_TOP_REACHED'
    setLockedReceipt('PLC_LIMIT_TOP_REACHED', 5000)
    ElMessage.success(reasonText || `【${isSim ? '升旗演练' : '正式颁奖'}】国歌演奏完毕，硬件已升顶到位！`)
    const isHoriz = currentPoleMode.value === 'horizontal'
    if (isHoriz) {
      logLine(`国歌演奏完毕 · 吊挂主横梁升顶到位 (12m) · 冠军高差1.5m · 亚军季军等高(10.5m)相对静止 · ${isSim ? '升旗演练' : '正式颁奖'}圆满完成`)
    } else {
      logLine(`国歌演奏完毕 · 冠军旗(12m最高)、亚军旗(10.5m)、季军旗(10.5m等高)全部到位 · ${isSim ? '升旗演练' : '正式颁奖'}圆满完成`)
    }
  }

  const finishCeremony = async () => {
    if (ceremonyCompleted) return
    if (animTimer) {
      clearInterval(animTimer)
      animTimer = null
    }
    // 检查真实硬件是否已停机或到达上限位
    const hw = await syncFlagHardwareStatus(true)
    if (!hw || hw.run_status === 0 || hw.limit_top !== 0) {
      if (hw && hw.run_status !== 0 && hw.limit_top !== 0) {
        await dispatchFlagHardwareCommand('estop', {}, '升顶到达上限位自动停机 (0x0A=1)')
      }
      completeUI()
      return
    }
    // 若国歌已播完但电机仍在转动收尾，继续轮询等待硬件停机（最多10秒保护）
    logLine('国歌已播完，等待硬件电机升顶停机...')
    ElMessage.info('国歌已播完，等待现场硬件升顶到位停机...')
    startLimitStopPolling({
      target: 'top',
      maxMs: 10000,
      onDone: (reason) => {
        if (reason === 'TIMEOUT') {
          completeUI('国歌已播完，已向硬件下发停机保护并完成升顶！')
        } else {
          completeUI()
        }
      }
    })
  }

  isRunning.value = true
  ElMessage.success(`${isSim ? '升旗演练' : '正式颁奖'}启动：正在加载国歌音频并同步硬件...`)

  // 启动国歌，并在音频真正发出声音且拿到真实时长时同步下发硬件自动升旗指令
  playAnthem(
    (realDurSec) => {
      const durSec = Math.max(1, +(realDurSec || selectedAudio.value.durationSec || 46).toFixed(1))
      const durMs = durSec * 1000
      const startedAt = Date.now()
      let seenHwRunning = false

      // 使用真实音频物理时长下发 0x02(国歌时长) + 0x08=1(自动升旗)，确保音画与机器同刻启动、同长运行
      dispatchFlagHardwareCommand(
        'auto_raise',
        { anthem_duration_sec: durSec },
        isSim ? '升旗演练自动升旗' : '正式颁奖自动升旗'
      ).then((cmdRes) => {
        if (!cmdRes && !ceremonyCompleted && isRunning.value) {
          stopAnthem()
          stopMotionPolling()
          if (animTimer) { clearInterval(animTimer); animTimer = null }
          isRunning.value = false
          motorRpm.value = 0
          flagStatus.value = 'IDLE'
        }
      })

      // 升旗过程中实时轮询硬件状态：若现场机器已先到达最高点并停机，页面与国歌同步收尾
      stopMotionPolling()
      let syncInFlight = false
      motionPollTimer = setInterval(async () => {
        if (ceremonyCompleted || !isRunning.value || syncInFlight) return
        syncInFlight = true
        try {
          const hw = await api.flagStatus(1)
          if (!hw || ceremonyCompleted || !isRunning.value) return
          applyHardwareStatus(hw)
          if (hw.run_status !== 0) seenHwRunning = true
          const elapsed = Date.now() - startedAt
          if (elapsed >= 1500 && (hw.limit_top !== 0 || (seenHwRunning && hw.run_status === 0))) {
            stopAnthem()
            completeUI(`【${isSim ? '升旗演练' : '正式颁奖'}】现场硬件已升顶停机，页面与国歌已同步完成！`)
          }
        } catch {
          // 忽略单次网络波动
        } finally {
          syncInFlight = false
        }
      }, 400)

      logLine(`【${isSim ? '升旗演练' : '正式颁奖'}】冠军 ${c.nameCn} (${c.code}) · 奏《${c.anthemName}》${durSec.toFixed(1)}s · 冠/亚/季速度: ${(championTotalM / durSec).toFixed(4)}/${(runnerUpTotalM / durSec).toFixed(4)}/${(thirdTotalM / durSec).toFixed(4)} m/s`)

      const stepMs = 50
      const startWallTime = performance.now()
      clearInterval(animTimer)

      animTimer = setInterval(() => {
        if (!isRunning.value) {
          clearInterval(animTimer)
          animTimer = null
          return
        }

        let progressRatio = 0
        // 若使用真实 Audio 对象播放，以音频硬件时间戳为绝对 Master Clock 驱动
        if (anthemEl && anthemEl.duration && !isNaN(anthemEl.duration) && anthemEl.duration > 0) {
          playTimeMs.value = Math.round(anthemEl.currentTime * 1000)
          const cur = anthemEl.currentTime
          const total = anthemEl.duration
          // 在音频未完全触发 ended 结束前，高度平滑逼近顶端但保留毫厘，绝不提前判定完成或掐断音频
          progressRatio = Math.min(0.999, cur / total)
        } else {
          const elapsed = performance.now() - startWallTime
          playTimeMs.value = Math.min(durMs, elapsed)
          progressRatio = Math.min(1, elapsed / durMs)
        }

        championH.value = +(championTotalM * progressRatio).toFixed(2)
        runnerUpH.value = +(runnerUpTotalM * progressRatio).toFixed(2)
        thirdH.value = +(thirdTotalM * progressRatio).toFixed(2)
        syncDevicesLive()

        // 仅在无真实音频文件（纯合成或离线降级）时依靠定时器结束
        if (!anthemEl && playTimeMs.value >= durMs) {
          finishCeremony()
        }
      }, stepMs)
    },
    // 音频自然播放完毕 (ended) 回调：旗帜正好达到 100% 满格 12m
    () => {
      finishCeremony()
    }
  )
}

function confirmOfficialCeremony() {
  if (isRunning.value) {
    ElMessage.warning('动作进行中，请等待完成或先触发急停')
    return
  }
  if (!isAtLowerZero.value) {
    ElMessage.warning('当前国旗不在“下复位”状态（旗面未归位），无法启动颁奖升旗！请先点击【下复位】使旗帜平稳降至底端原点后，再执行升旗。')
    return
  }
  const c = champion.value
  if (!c) {
    ElMessage.warning('请先点击冠军卡片选定冠军国家')
    return
  }
  ElMessageBox.confirm(
    `将正式执行颁奖仪式：冠军「${c.nameCn} (${c.code})」，奏《${c.anthemName}》并同步升旗。是否确认？`,
    '正式颁奖二次确认',
    { type: 'warning', confirmButtonText: '确认执行', cancelButtonText: '取消' }
  ).then(() => runCeremony('official')).catch(() => { })
}

let motionPollTimer = null
let activeLimitWaiter = null

function stopMotionPolling() {
  activeLimitWaiter = null
  if (motionPollTimer) {
    clearInterval(motionPollTimer)
    motionPollTimer = null
  }
}

async function evaluateLimitWaiter(hw) {
  const waiter = activeLimitWaiter
  if (!waiter || waiter.finished || !hw) return
  const hitLimit = waiter.target === 'bottom' ? hw.limit_bottom !== 0 : hw.limit_top !== 0
  const elapsed = Date.now() - waiter.startedAt

  if (hitLimit) {
    waiter.finished = true
    stopMotionPolling()
    await dispatchFlagHardwareCommand('estop', {}, waiter.target === 'bottom' ? '到达最低点自动停机 (0x0A=1)' : '到达最高点自动停机 (0x0A=1)')
    waiter.onDone?.('LIMIT_REACHED', hw)
  } else if (hw.run_status === 0 && elapsed >= 1200) {
    waiter.finished = true
    stopMotionPolling()
    waiter.onDone?.('HARDWARE_STOPPED_UNEXPECTED', hw)
  } else if (elapsed >= waiter.maxMs) {
    waiter.finished = true
    stopMotionPolling()
    await dispatchFlagHardwareCommand('estop', {}, '动作超时保护停机 (0x0A=1)')
    waiter.onDone?.('TIMEOUT', hw)
  }
}

function startLimitStopPolling({ target, maxMs = 65000, onDone }) {
  stopMotionPolling()
  const startedAt = Date.now()
  activeLimitWaiter = { target, maxMs, startedAt, onDone, finished: false }
  let inFlight = false

  // WebSocket 在线时由后端主动 0.3s 推送驱动 evaluateLimitWaiter；仅在 WS 断开或超时边界时用 HTTP 兜底
  motionPollTimer = setInterval(async () => {
    const waiter = activeLimitWaiter
    if (!waiter || waiter.finished) return
    const elapsed = Date.now() - startedAt
    if (elapsed >= maxMs) {
      waiter.finished = true
      stopMotionPolling()
      await dispatchFlagHardwareCommand('estop', {}, '动作超时保护停机 (0x0A=1)')
      onDone?.('TIMEOUT', null)
      return
    }
    if (wsConnected.value || inFlight) return
    inFlight = true
    try {
      const hw = await api.flagStatus(1)
      if (hw) {
        applyHardwareStatus(hw)
        await evaluateLimitWaiter(hw)
      }
    } catch {
      // 忽略单次轮询波动，等待下次轮询或手动急停
    } finally {
      inFlight = false
    }
  }, 600)
}

async function startLowerFlag() {
  if (actionLaunching || isRunning.value) {
    ElMessage.warning('动作正在启动或进行中，请等待完成或先触发急停')
    return
  }
  actionLaunching = true
  estopLatched = false
  stopAnthem()
  let hw = null
  let cmdRes = null
  try {
    hw = await syncFlagHardwareStatus(true)
    if (hw && hw.limit_bottom !== 0) {
      championH.value = 0
      runnerUpH.value = 0
      thirdH.value = 0
      motorRpm.value = 0
      playTimeMs.value = 0
      flagStatus.value = 'IDLE'
      syncDevicesLive()
      ElMessage.success(`硬件已处于最低点（${hw.limit_bottom_text}），已完成下复位归零！`)
      logLine(`下复位检查：硬件已处于${hw.limit_bottom_text}，无需再次启动反转`)
      return
    }

    cmdRes = await dispatchFlagHardwareCommand('manual_reverse', {}, '平稳降旗 (0x07=1)')
    if (!cmdRes) {
      isRunning.value = false
      flagStatus.value = 'IDLE'
      return
    }
  } finally {
    actionLaunching = false
  }

  flagStatus.value = 'LOWERING'
  motorRpm.value = Math.round(hw?.manual_rpm || 1000)
  lastActionText.value = '平稳降旗归位'
  lastActionTime.value = nowStr()

  const startRatio = championTotalM > 0 ? Math.max(0.2, championH.value / championTotalM) : 1
  const dur = estimateManualMotionMs(hw, startRatio)
  logLine(`下复位启动：硬件预计耗时 ${(dur / 1000).toFixed(1)}s (手动转速 ${hw?.manual_rpm || 1000} RPM · 总转数 ${hw?.total_turns || '--'})，画面与硬件同步下降中...`)
  tweenHeights({ c: 0, r: 0, t: 0 }, dur, null, { linear: true, waitForHardware: true })

  startLimitStopPolling({
    target: 'bottom',
    maxMs: Math.max(65000, dur + 15000),
    onDone: (reason) => {
      if (animTimer) { clearInterval(animTimer); animTimer = null }
      isRunning.value = false
      motorRpm.value = 0
      playTimeMs.value = 0
      flagStatus.value = 'IDLE'
      if (reason === 'LIMIT_REACHED') {
        championH.value = 0
        runnerUpH.value = 0
        thirdH.value = 0
        syncDevicesLive()
        setLockedReceipt('PLC_HOME_POSITION_OK', 5000)
        ElMessage.success('下复位完成，硬件已到达最低点并停机！')
        logLine('下复位完成：已到达最低点限位并自动停机')
      } else if (reason === 'HARDWARE_STOPPED_UNEXPECTED') {
        syncDevicesLive()
        setLockedReceipt('PLC_LOWER_STOPPED_MIDWAY', 5000)
        ElMessage.warning('电机已中途停止，但未检测到最低点限位信号，请检查机械或重新下复位！')
        logLine('下复位异常：电机中途停止且未到达最低点限位，已保留当前高度')
      } else {
        syncDevicesLive()
        setLockedReceipt('PLC_LOWER_TIMEOUT_ESTOP', 5000)
        ElMessage.warning('下复位超时未检测到最低点限位，已自动触发停机保护！')
        logLine('下复位超时：已自动下发 0x0A=1 停机保护')
      }
    }
  })
}

// 上复位：三杆平稳上升至最高限位 (上复位基准)
async function moveToUpperZero() {
  if (actionLaunching || isRunning.value) {
    ElMessage.warning('动作正在启动或进行中，请等待完成或先触发急停')
    return
  }
  actionLaunching = true
  estopLatched = false
  let hw = null
  let cmdRes = null
  try {
    hw = await syncFlagHardwareStatus(true)
    if (hw && hw.limit_top !== 0) {
      championH.value = championTotalM
      runnerUpH.value = runnerUpTotalM
      thirdH.value = thirdTotalM
      motorRpm.value = 0
      flagStatus.value = 'COMPLETED'
      syncDevicesLive()
      ElMessage.success(`硬件已处于最高点（${hw.limit_top_text}），已完成上复位！`)
      logLine(`上复位检查：硬件已处于${hw.limit_top_text}，无需再次启动正转`)
      return
    }

    cmdRes = await dispatchFlagHardwareCommand('manual_forward', {}, '上升至上复位 (0x06=1)')
    if (!cmdRes) {
      isRunning.value = false
      return
    }
  } finally {
    actionLaunching = false
  }

  flagStatus.value = 'RISING'
  motorRpm.value = Math.round(hw?.manual_rpm || 1000)
  lastActionText.value = '上升至上复位 (杆顶上限位)'
  lastActionTime.value = nowStr()
  setLockedReceipt('PLC_UPPER_ZERO_ACK', 3000)
  logLine('指令下发：平稳升至上复位 (上限位)')
  devices.value.forEach(d => {
    if (d.status !== 'OFFLINE' && checkedIds.value.includes(d.id)) {
      d.lastCmd = '上升至上复位'
      d.updated = nowStr()
    }
  })
  const remainRatio = championTotalM > 0 ? Math.max(0.2, (championTotalM - championH.value) / championTotalM) : 1
  const dur = estimateManualMotionMs(hw, remainRatio)
  logLine(`上复位启动：硬件预计耗时 ${(dur / 1000).toFixed(1)}s (手动转速 ${hw?.manual_rpm || 1000} RPM)，画面与硬件同步上升中...`)
  tweenHeights({ c: 1, r: 1, t: 1 }, dur, null, { linear: true, waitForHardware: true })

  startLimitStopPolling({
    target: 'top',
    maxMs: Math.max(65000, dur + 15000),
    onDone: (reason) => {
      if (animTimer) { clearInterval(animTimer); animTimer = null }
      isRunning.value = false
      motorRpm.value = 0
      if (reason === 'LIMIT_REACHED') {
        championH.value = championTotalM
        runnerUpH.value = runnerUpTotalM
        thirdH.value = thirdTotalM
        flagStatus.value = 'COMPLETED'
        syncDevicesLive()
        setLockedReceipt('PLC_LIMIT_TOP_REACHED', 5000)
        ElMessage.success('上复位完成，硬件已到达最高点并停机！')
        logLine('上复位就绪：已到达最高点限位并自动停机')
      } else if (reason === 'HARDWARE_STOPPED_UNEXPECTED') {
        flagStatus.value = 'IDLE'
        syncDevicesLive()
        setLockedReceipt('PLC_UPPER_STOPPED_MIDWAY', 5000)
        ElMessage.warning('电机已中途停止，但未检测到最高点限位信号，请检查机械或重新上复位！')
        logLine('上复位异常：电机中途停止且未到达最高点限位，已保留当前高度')
      } else {
        flagStatus.value = 'IDLE'
        syncDevicesLive()
        setLockedReceipt('PLC_UPPER_TIMEOUT_ESTOP', 5000)
        ElMessage.warning('上复位超时未检测到最高点限位，已自动触发停机保护！')
        logLine('上复位超时：已自动下发 0x0A=1 停机保护')
      }
    }
  })
}

// 最高优先级急停 (E-STOP): 不弹普通确认弹窗, 毫秒立即执行
function handleEmergencyStop() {
  stopMotionPolling()
  clearInterval(animTimer)
  animTimer = null
  stopAnthem()
  estopLatched = true
  devices.value.forEach(d => {
    if (d._t) { clearInterval(d._t); d._t = null }
    if (d.status !== 'OFFLINE') {
      d.status = 'ESTOP'
      d.rpm = 0
      d.lastCmd = '紧急停止 (E-STOP)'
      d.updated = nowStr()
    }
  })
  isRunning.value = false
  motorRpm.value = 0
  flagStatus.value = 'ESTOPPED'
  lastActionText.value = '最高优先级急停 (E-STOP)'
  lastActionTime.value = nowStr()
  setLockedReceipt('PLC_BRAKE_LOCKED_IMMEDIATE', 10000)
  logLine('【E-STOP】电机抱闸断电、国歌音频即刻切断')
  dispatchFlagHardwareCommand('estop', {}, '最高优先级急停 (0x0A=1)')
  ElMessage.error('【最高优先级急停触发】已瞬间向 PLC 电机下发抱闸断电指令，国歌播放即刻切断！')
}

/* ============================================================
 * 六、WebSocket 实时状态流 + 升旗设备列表（默认固定为指令下发控制模式）
 * ============================================================ */
const wsConnected = ref(false)
const lastHwOnline = ref(false)
const lastManualRpm = ref(null)
const lastHardwareSnapshot = ref(null)

let flagWs = null
let wsReconnectTimer = null
let wsPingTimer = null
let wsReconnectDelayMs = 1500
let wsManualClosed = false
let readSyncPollTimer = null

function buildFlagWsUrl(unitId = 1) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const token = localStorage.getItem('venue_access_token') || ''
  return `${proto}//${window.location.host}/api/flag/ws?unit_id=${encodeURIComponent(unitId)}&token=${encodeURIComponent(token)}`
}

function connectFlagWs() {
  if (wsManualClosed) return
  if (flagWs && (flagWs.readyState === WebSocket.OPEN || flagWs.readyState === WebSocket.CONNECTING)) {
    return
  }
  const token = localStorage.getItem('venue_access_token')
  if (!token) return

  try {
    flagWs = new WebSocket(buildFlagWsUrl(1))
  } catch {
    scheduleWsReconnect()
    return
  }

  flagWs.onopen = () => {
    wsConnected.value = true
    wsReconnectDelayMs = 1500
    if (wsPingTimer) clearInterval(wsPingTimer)
    wsPingTimer = setInterval(() => {
      if (flagWs && flagWs.readyState === WebSocket.OPEN) {
        flagWs.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
  }

  flagWs.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data)
      if (!msg || msg.type !== 'flag_status') return
      if (msg.online && msg.data) {
        lastHwOnline.value = true
        applyHardwareStatus(msg.data)
        evaluateLimitWaiter(msg.data)
      } else {
        lastHwOnline.value = false
        if (devices.value[0]) {
          devices.value[0].status = 'OFFLINE'
          devices.value[0].settingStatus = '网关通信中断'
          devices.value[0].updated = nowStr()
        }
      }
    } catch {
      // 忽略异常消息帧
    }
  }

  flagWs.onclose = () => {
    wsConnected.value = false
    if (wsPingTimer) { clearInterval(wsPingTimer); wsPingTimer = null }
    flagWs = null
    if (!wsManualClosed) scheduleWsReconnect()
  }

  flagWs.onerror = () => {
    wsConnected.value = false
  }
}

function scheduleWsReconnect() {
  if (wsReconnectTimer || wsManualClosed) return
  wsReconnectTimer = setTimeout(() => {
    wsReconnectTimer = null
    wsReconnectDelayMs = Math.min(10000, Math.round(wsReconnectDelayMs * 1.5))
    connectFlagWs()
  }, wsReconnectDelayMs)
}

function disconnectFlagWs() {
  wsManualClosed = true
  if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null }
  if (wsPingTimer) { clearInterval(wsPingTimer); wsPingTimer = null }
  if (flagWs) {
    try { flagWs.close() } catch { }
    flagWs = null
  }
  wsConnected.value = false
}

function requestWsRefresh() {
  if (flagWs && flagWs.readyState === WebSocket.OPEN) {
    flagWs.send(JSON.stringify({ type: 'refresh' }))
    ElMessage.success('已请求网关立即刷新状态')
  } else {
    syncFlagHardwareStatus(false)
    connectFlagWs()
  }
}

function startReadSyncPolling() {
  stopReadSyncPolling()
  readSyncPollTimer = setInterval(() => {
    // WebSocket 在线时不再重复发 HTTP 轮询串口，仅在 WS 断线时兜底
    if (!wsConnected.value) {
      syncFlagHardwareStatus(true)
    }
  }, 2000)
}

function stopReadSyncPolling() {
  if (readSyncPollTimer) {
    clearInterval(readSyncPollTimer)
    readSyncPollTimer = null
  }
}

function applyHardwareStatus(hw) {
  if (!hw || typeof hw !== 'object') return
  lastHardwareSnapshot.value = hw
  lastHwOnline.value = hw.online !== false
  if (hw.manual_rpm != null) {
    lastManualRpm.value = hw.manual_rpm
  }
  const t = nowStr()
  const primary = devices.value[0]
  if (primary) {
    if (estopLatched && hw.run_status === 0) {
      primary.status = 'ESTOP'
    } else {
      primary.status = hw.run_status === 0 ? 'ONLINE' : 'BUSY'
    }
    primary.rpm = hw.run_status === 0 ? 0 : (hw.auto_rpm || hw.manual_rpm || 0)
    primary.settingStatus = `${hw.run_status_text || '待机'} | ${hw.limit_top_text || ''} / ${hw.limit_bottom_text || ''}`
    primary.lastCmd = `脉冲:${hw.total_pulses ?? 0} | 国歌:${hw.anthem_duration_sec ?? '--'}s`
    primary.totalPulses = hw.total_pulses ?? null
    primary.updated = t

    // 位置：只显示硬件实测的真实值，不做任何推算
    primary.positionState = hw.position_state || 'IDLE_UNKNOWN'
    primary.positionText = hw.position_text || '位置未知'
    primary.heightExact = hw.height_exact === true
    primary.movingSeconds = hw.moving_seconds ?? null
    primary.positionNote = hw.position_note || ''
    // 仅在精确时赋值高度，否则置 null
    primary.heightM = primary.heightExact && hw.height_m != null ? hw.height_m : null
    primary.liveCounter = hw.live_counter ?? null
  }
  // 其他共挂或待独立配置的设备同步网关在线状态，不保留虚构仿真值
  devices.value.slice(1).forEach((d) => {
    if (d.status !== 'OFFLINE') {
      d.status = estopLatched && hw.run_status === 0 ? 'ESTOP' : (hw.run_status === 0 ? 'ONLINE' : 'BUSY')
      d.rpm = primary ? primary.rpm : 0
      d.settingStatus = hw.run_status === 0 ? '随主网关联动待机' : '随主网关联动运行'
      d.updated = t
    }
  })
  if (!isRunning.value) {
    motorRpm.value = hw.run_status === 0 ? 0 : Math.round(hw.auto_rpm || hw.manual_rpm || 0)
    // 当页面未在执行动画时，根据硬件上下限位自动同步模拟台旗帜位置（上零位→杆顶，下零位→底端）
    if (hw.run_status === 0) {
      if (hw.limit_top && hw.limit_top !== 0) {
        if (Math.abs(championH.value - championTotalM) > 0.05 || flagStatus.value !== 'COMPLETED') {
          championH.value = championTotalM
          runnerUpH.value = runnerUpTotalM
          thirdH.value = thirdTotalM
          flagStatus.value = 'COMPLETED'
        }
      } else if (hw.limit_bottom && hw.limit_bottom !== 0) {
        if (championH.value > 0.05 || flagStatus.value !== 'IDLE') {
          championH.value = 0
          runnerUpH.value = 0
          thirdH.value = 0
          flagStatus.value = 'IDLE'
        }
      }
    }
  }
  if (Date.now() >= receiptLockUntil) {
    deviceReceipt.value = `MODBUS_OK (${hw.elapsed_ms ?? 0}ms) | 脉冲:${hw.total_pulses ?? 0} | ${hw.limit_top_text || ''}`
  }
}

async function syncFlagHardwareStatus(silent = false) {
  try {
    const res = await api.flagStatus(1)
    if (res && res.online) {
      applyHardwareStatus(res)
      if (!silent) {
        logLine(`【真实硬件读取】192.168.0.7:20108 状态=${res.run_status_text} · 手动转速=${res.manual_rpm}RPM · 自动转速=${res.auto_rpm}RPM · 国歌时长=${res.anthem_duration_sec}s · 限位=(${res.limit_top_text}/${res.limit_bottom_text}) · 总脉冲=${res.total_pulses} (${res.elapsed_ms}ms)`)
      }
      return res
    }
  } catch (err) {
    lastHwOnline.value = false
    if (!silent) {
      ElMessage.warning(`读取升旗网关失败: ${err?.message || '网关连接异常'}`)
    }
    logLine(`【硬件读取异常】${err?.message || '无法连接 192.168.0.7:20108'}`)
  }
  return null
}

async function promptSetManualRpm() {
  if (isRunning.value) {
    ElMessage.warning('动作进行中，请等待完成或先触发急停')
    return
  }
  try {
    const { value } = await ElMessageBox.prompt(
      '请输入手动模式电机转速 (范围 0.1 ~ 3000.0 RPM，对应寄存器 0x01)',
      '设置手动转速 (0x01)',
      {
        confirmButtonText: '写入寄存器',
        cancelButtonText: '取消',
        inputValue: String(lastManualRpm.value || 1000),
        inputPattern: /^\d+(\.\d{1})?$/,
        inputErrorMessage: '请输入合法数字（最多保留 1 位小数）',
      }
    )
    const rpm = parseFloat(value)
    if (isNaN(rpm) || rpm < 0.1 || rpm > 3000) {
      ElMessage.warning('手动转速必须在 0.1 ~ 3000 RPM 之间')
      return
    }
    const res = await dispatchFlagHardwareCommand('set_manual_rpm', { manual_rpm: rpm }, `设置手动转速 ${rpm} RPM (0x01)`)
    if (res) {
      ElMessage.success(`手动转速已写入: ${rpm.toFixed(1)} RPM`)
    }
  } catch {
    // 取消输入
  }
}

async function triggerAutoMeasure() {
  if (isRunning.value) {
    ElMessage.warning('动作进行中，请等待完成或先触发急停')
    return
  }
  const hw = await syncFlagHardwareStatus(true)
  if (!hw) return
  if (hw.run_status !== 0) {
    ElMessage.warning(`当前电机状态为「${hw.run_status_text}」，自动测距需电机处于停止状态`)
    return
  }
  if (hw.limit_top === 0) {
    ElMessage.warning('自动测距要求旗帜处于最高点限位（0x0B != 0），请先执行【上复位】到达最高点后再测距')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确认向寄存器 0x09 写入 1 触发自动测距？（将重新标定总行程脉冲数 0x0D/0x0E）',
      '自动测距确认',
      { type: 'warning', confirmButtonText: '确认触发', cancelButtonText: '取消' }
    )
    const res = await dispatchFlagHardwareCommand('auto_measure', {}, '触发自动测距 (0x09=1)')
    if (res) {
      ElMessage.success('自动测距指令已下发，可通过日志与总脉冲数观察标定结果')
    }
  } catch {
    // 取消
  }
}

async function dispatchFlagHardwareCommand(action, payload = {}, label = '') {
  try {
    const res = await api.flagCommand(action, payload)
    if (res && res.status) {
      applyHardwareStatus(res.status)
    }
    const tx = res?.steps?.map(s => `${s.register}=${s.value} [${s.tx_hex}]`).join(' ; ') || action
    logLine(`【硬件指令下发成功】${label || action} -> ${tx} · ${res?.message || ''}`)
    return res
  } catch (err) {
    const msg = err?.message || '硬件指令下发失败'
    logLine(`【硬件指令下发失败】${label || action}: ${msg}`)
    ElMessage.warning(`硬件指令 (${label || action}): ${msg}`)
    return null
  }
}

const CHINESE_NUMS = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

const isFetchingDevices = ref(false)

async function fetchHardwareDevices() {
  if (isFetchingDevices.value) return
  isFetchingDevices.value = true
  ElMessage.info('正在扫描现场升旗控制器 (192.168.0.7:20108 Modbus TCP)...')
  logLine('发起现场硬件设备扫描握手 (USR-K7 192.168.0.7:20108 Modbus TCP)')
  await loadDeviceRows()
  const hw = await syncFlagHardwareStatus(false)
  requestWsRefresh()
  isFetchingDevices.value = false
  if (hw) {
    const curDev = currentReadingDevice.value
    ElMessage.success(`扫描完成！已成功读取 192.168.0.7:20108 真实数据：${hw.run_status_text} · 国歌 ${hw.anthem_duration_sec}s · 总脉冲 ${hw.total_pulses} (${hw.elapsed_ms}ms)`)
    logLine(`硬件设备状态回读完成：当前监视「${curDev.aliasName}」`)
  } else if (devices.value[0]) {
    devices.value[0].status = 'OFFLINE'
    devices.value[0].settingStatus = '网关通信中断'
  }
}

function devStatusText(dev) {
  if (dev.status === 'OFFLINE') return '离线中断'
  if (dev.status === 'ESTOP') return '急停抱闸'
  if (dev.status === 'BUSY') return '升降运行中'
  return '在线待机'
}

// 参与联动设备（完全由后端 /api/flag/devices 真实入库数据驱动，不硬编码假设备）
const devices = ref([])
let devicesInitialized = false

const checkedIds = ref([])

const allChecked = computed({
  get: () => devices.value.length > 0 && checkedIds.value.length === devices.value.filter(d => d.status !== 'OFFLINE').length,
  set: v => {
    checkedIds.value = v ? devices.value.filter(d => d.status !== 'OFFLINE').map(d => d.id) : []
  }
})

const isIndeterminate = computed(() => {
  const selectable = devices.value.filter(d => d.status !== 'OFFLINE').length
  return checkedIds.value.length > 0 && checkedIds.value.length < selectable
})

function toggleDevice(id) {
  const i = checkedIds.value.indexOf(id)
  if (i > -1) checkedIds.value.splice(i, 1)
  else checkedIds.value.push(id)
}

// 仪式运行时: 对应旗杆的高度实时回读
function syncDevicesLive() {
  const t = nowStr()
  devices.value.forEach((d, idx) => {
    if (d.status === 'OFFLINE') return
    if (idx === 0) {
      d.heightM = +championH.value.toFixed(2)
    } else if (idx === 1) {
      d.heightM = +runnerUpH.value.toFixed(2)
    } else if (idx === 2) {
      d.heightM = +thirdH.value.toFixed(2)
    }
    d.rpm = motorRpm.value
    d.updated = t
  })
}

/* ============================================================
 * 七、生命周期
 * ============================================================ */

/* ============================================================
 * 设备管理（参数入库，不硬编码）
 * ============================================================ */
const deviceManagerVisible = ref(false)
const deviceRows = ref([])
const deviceFormVisible = ref(false)
const deviceTesting = ref(false)
const deviceTestResult = ref(null)
const deviceForm = ref(makeEmptyDeviceForm())

function makeEmptyDeviceForm() {
  return {
    device_id: '',
    name: '',
    pole_type: 'vertical',
    host: '192.168.0.7',
    port: 20108,
    unit_id: 1,
    timeout_s: 3.0,
    pole_height_m: 12.0,
    total_stroke_mm: 12000,
    pulses_per_meter: 498000,
    max_pulses: null,
    allow_write: true,
    max_moving_seconds: 75,
    heartbeat_timeout_s: 120,
    region: '',
    remark: '',
  }
}

async function loadDeviceRows() {
  try {
    const res = await api.flagDevices()
    const items = (res && res.items) || []
    deviceRows.value = items
    const prevMap = new Map(devices.value.map(d => [d.id, d]))
    devices.value = items.map((row) => {
      const old = prevMap.get(row.device_id)
      const st = row.status || {}
      const online = st.online !== false
      const motorStatus = st.motor_status ?? 0
      return {
        id: row.device_id,
        name: row.name || row.device_id,
        aliasName: `${row.name || row.device_id} (${row.pole_height_m || 12.0}m)`,
        region: row.region || '主体育场',
        poleType: row.pole_type === 'horizontal' ? 'horizontal' : 'vertical',
        protocol: 'Modbus TCP (USR-K7)',
        host: row.host || '',
        ipAddress: row.host ? `${row.host}:${row.port}` : '',
        port: `${row.host}:${row.port} (UID:${row.unit_id || 1})`,
        status: !online ? 'OFFLINE' : (estopLatched && motorStatus === 0 ? 'ESTOP' : (motorStatus === 0 ? 'ONLINE' : 'BUSY')),
        settingStatus: online ? `${st.motor_status_text || '待机'} | ${st.limit_forward_text || ''} / ${st.limit_reverse_text || ''}` : '离线中断',
        heightM: st.height_exact && st.height_m != null ? st.height_m : (old?.heightM ?? null),
        rpm: motorStatus === 0 ? 0 : (st.auto_rpm || st.manual_rpm || 0),
        totalStroke: Number(row.pole_height_m || 12.0),
        limitTop: Number(row.pole_height_m || 12.0),
        totalPulses: st.total_pulses ?? null,
        positionState: st.position_state || 'IDLE_UNKNOWN',
        positionText: st.position_text || '位置未知',
        heightExact: st.height_exact === true,
        lastCmd: st.total_pulses != null ? `脉冲:${st.total_pulses} | 国歌:${st.anthem_duration_s ?? '--'}s` : '待机就绪',
        updated: nowStr(),
        loading: false,
      }
    })
    const validIds = new Set(devices.value.filter(d => d.status !== 'OFFLINE').map(d => d.id))
    if (!devicesInitialized) {
      checkedIds.value = Array.from(validIds)
      devicesInitialized = true
    } else {
      checkedIds.value = checkedIds.value.filter(id => validIds.has(id))
    }
    if (!devices.value.some(d => d.id === activeReadDeviceId.value)) {
      activeReadDeviceId.value = devices.value[0]?.id || ''
    }
  } catch (e) {
    ElMessage.warning('设备列表读取失败: ' + (e?.message || e))
    deviceRows.value = []
    devices.value = []
    checkedIds.value = []
  }
}

async function openDeviceManager() {
  deviceManagerVisible.value = true
  deviceFormVisible.value = false
  await loadDeviceRows()
}

function newDeviceForm() {
  deviceForm.value = makeEmptyDeviceForm()
  deviceTestResult.value = null
  deviceFormVisible.value = true
}

function editDeviceForm(row) {
  deviceForm.value = {
    ...makeEmptyDeviceForm(),
    ...row,
    allow_write: row.allow_write === true,
  }
  deviceTestResult.value = null
  deviceFormVisible.value = true
}

async function testDeviceConnection() {
  const f = deviceForm.value
  if (!f.host) { ElMessage.warning('请先填写网关 IP'); return }
  deviceTesting.value = true
  deviceTestResult.value = null
  try {
    const res = await api.flagProbe({
      device_id: f.device_id || '__probe__',
      name: f.name || 'probe',
      host: f.host,
      port: f.port,
      unit_id: f.unit_id,
      timeout_s: f.timeout_s,
      allow_write: false,
    })
    deviceTestResult.value = res
    if (res?.reachable) {
      ElMessage.success('连接成功')
    } else {
      ElMessage.error('连接失败: ' + (res?.error || res?.hint || ''))
    }
  } catch (e) {
    deviceTestResult.value = { reachable: false, error: e?.message || String(e) }
    ElMessage.error('测试失败: ' + (e?.message || e))
  } finally {
    deviceTesting.value = false
  }
}

async function saveDevice() {
  const f = deviceForm.value
  if (!f.device_id || !f.name || !f.host) {
    ElMessage.warning('设备ID、名称、网关IP 为必填项')
    return
  }
  try {
    await api.flagSaveDevice({ ...f, allow_write: true })
    ElMessage.success('已保存到数据库')
    deviceFormVisible.value = false
    await loadDeviceRows()
    await syncFlagHardwareStatus(true)
  } catch (e) {
    ElMessage.error('保存失败: ' + (e?.message || e))
  }
}

async function removeDevice(row) {
  try {
    await ElMessageBox.confirm(`确认删除设备 ${row.device_id}？`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await api.flagDeleteDevice(row.device_id)
    ElMessage.success('已删除')
    await loadDeviceRows()
  } catch (e) {
    ElMessage.error('删除失败: ' + (e?.message || e))
  }
}


onMounted(() => {
  window.addEventListener('keydown', handleEscKey)
  startWaveLoop()
  loadDeviceRows()
  syncFlagHardwareStatus(true)
  wsManualClosed = false
  connectFlagWs()
  if (route.query.select) {
    openCountrySelectModal(route.query.select)
  }
})

onUnmounted(() => {
  disconnectFlagWs()
  stopWaveLoop()
  stopReadSyncPolling()
  stopMotionPolling()
  if (animTimer) clearInterval(animTimer)
  stopAnthem()
  if (modalAudioPlayer) {
    modalAudioPlayer.pause()
    modalAudioPlayer = null
  }
  if (audioCtx) {
    try { audioCtx.close() } catch { }
    audioCtx = null
  }
  devices.value.forEach(d => { if (d._t) clearInterval(d._t) })
})
</script>

<style scoped>
.flag-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.flag-top-bar {
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
  gap: 10px;
}

/* ============================================================
 * 顶部 4 个按钮的统一基准规范（以“国家资料录入与编辑”为绝对标准）
 * 包含：国家资料录入与编辑、一键获取硬件设备、数据读取同步模式、指令下发控制模式
 * ============================================================ */
.btn-top-manage,
.btn-fetch-hardware,
.mode-tab-btn {
  height: 30px !important;
  padding: 0 14px !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  /* 按钮主体文字字重统一为 400，严禁加粗 */
  line-height: 28px !important;
  border-radius: 4px !important;
  box-sizing: border-box !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-top-manage *,
.btn-fetch-hardware *,
.mode-tab-btn *,
.btn-top-manage span,
.btn-fetch-hardware span,
.mode-tab-btn span {
  font-weight: 400 !important;
  /* 内部文字所有元素统一不加粗 */
}

/* 按钮 1：国家资料录入与编辑 (基准样式) */
.btn-top-manage {
  border: 1px solid rgba(217, 119, 6, 0.55) !important;
  color: var(--do-gold) !important;
  background: rgba(217, 119, 6, 0.1) !important;
}

.btn-top-manage:hover {
  background: rgba(217, 119, 6, 0.2) !important;
  border-color: var(--do-gold) !important;
}

/* 按钮 2：一键获取硬件设备 */
.btn-fetch-hardware {
  border: 1px solid var(--do-gold-deep) !important;
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%) !important;
  color: #FFFFFF !important;
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.25);
}

.btn-fetch-hardware:hover:not(:disabled) {
  filter: brightness(1.05);
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35);
}

.btn-fetch-hardware:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 按钮 3 & 4：模式切换容器与按钮 */
.mode-toggle-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  padding: 0;
}

.mode-tab-btn {
  border: 1px solid var(--do-border) !important;
  color: var(--do-text-secondary) !important;
  background: var(--do-bg-card) !important;
}

.mode-tab-btn:hover {
  color: var(--do-gold) !important;
  border-color: var(--do-gold) !important;
}

.mode-tab-btn.active {
  color: #FFFFFF !important;
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%) !important;
  border-color: var(--do-gold-deep) !important;
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.35);
}



/* 主布局: 严格按 25% 和 75% 比例划分左右两侧 (左侧设备 25% : 右侧升旗大台 75%) */
.flag-main-layout {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 3fr) !important;
  gap: 16px !important;
  align-items: start !important;
  width: 100% !important;
}

/* min-width: 0 精确分配比例, 不被子元素撑开破裂 */
.flag-main-layout>* {
  min-width: 0;
}

/* 第二行: 冠军国家选定 (全宽) */
.flag-secondary-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
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
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-text-secondary);
}

/* ---------- 音画时间轴 (沿用) ---------- */
.timeline-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.audio-asset-card {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.asset-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.asset-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.asset-spec {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.asset-hint {
  font-size: 14px;
  color: var(--do-gold-deep);
}

.calc-speed-box {
  text-align: right;
  flex-shrink: 0;
}

.calc-lbl {
  font-size: 14px;
  color: var(--do-text-secondary);
  display: block;
}

.calc-val {
  font-size: 20px;
  font-weight: bold;
  color: var(--do-warning);
}

.waveform-box {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px 14px;
}

.waveform-header {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--do-text-secondary);
  margin-bottom: 12px;
  font-weight: 500;
}

.waveform-bars-wrap {
  height: 80px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  position: relative;
  overflow: hidden;
}

.wave-bar {
  width: 4px;
  background: var(--do-border);
  border-radius: 2px;
  transition: background 0.1s;
}

.wave-bar.active {
  background: var(--do-gold);
  box-shadow: 0 0 6px rgba(var(--th-accent-rgb), 0.5);
}

.scrubber-cursor {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--do-danger);
  box-shadow: 0 0 6px var(--do-danger);
  z-index: 5;
  transition: left 0.1s linear;
}

.flag-params-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.param-box {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.p-lbl {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.p-val {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

/* ---------- Canvas 仿真视窗 ---------- */
.mode-toggle-bar {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  background: var(--do-bg-sunken);
  border-bottom: 1px solid var(--do-border-light);
}

.mode-btn {
  flex: 1;
  padding: 8px 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-secondary);
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.mode-btn:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.mode-btn.active {
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%);
  border-color: var(--do-gold-deep);
  color: #FFFFFF;
  box-shadow: 0 1px 4px rgba(var(--th-accent-deep-rgb), 0.3);
}

.canvas-stage {
  padding: 12px 14px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  background: var(--do-bg-card);
  border-radius: 0 0 6px 6px;
  width: 100%;
  box-sizing: border-box;
}

.sim-stage-viewport {
  width: 100%;
  /* 模拟台界面背景色横向铺满父级容器 (略留边距即可) */
  background: linear-gradient(180deg, #EBF1F6 0%, #F5F8FA 45%, #DFE7EE 100%);
  border: 1px solid var(--do-border);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 1px 4px rgba(15, 23, 42, 0.04);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flag-sim-svg {
  width: 100%;
  height: auto;
  max-height: 680px;
  aspect-ratio: 880 / 480;
  display: block;
  user-select: none;
}

/* 升旗台下方横向 5 个操作控制卡片面板 */
.viewport-hud-actions {
  width: 100%;
  margin-top: 10px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
}

.hud-actions-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--do-border-light);
  flex-shrink: 0;
}

.hud-head-lbl {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.hud-head-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-badge-mini {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 700;
}

.mode-badge-mini.cmd_control {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.mode-badge-mini.read_sync {
  background: rgba(148, 163, 184, 0.2);
  color: #64748B;
}

.hud-locked-hint {
  font-size: 11px;
  color: #D97706;
  background: rgba(245, 158, 11, 0.12);
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  line-height: 1.25;
  flex-shrink: 0;
}

.hud-cmd-list {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.hud-card {
  width: 100% !important;
  min-height: 58px;
  padding: 8px 10px !important;
  border-radius: 6px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  text-align: left !important;
  background: var(--do-bg-card);
  border: 1.5px solid var(--do-border);
  cursor: pointer;
  transition: all 0.2s ease;
}

.hud-card:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  filter: grayscale(0.4);
}

.hud-card:not(:disabled):hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.hud-card .cmd-card-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-width: 0;
}

.hud-card .cmd-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hud-card .cmd-texts {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  overflow: hidden;
}

.hud-card .cmd-title {
  font-family: SimHei, "Microsoft YaHei", "PingFang SC", sans-serif;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hud-card .cmd-desc {
  font-size: 14px !important;
  color: var(--do-text-secondary);
  font-weight: 500;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hud-card.top-card .top-icon-wrap {
  background: rgba(2, 132, 199, 0.12);
  color: #0284C7;
}

.hud-card.lower-card .lower-icon-wrap {
  background: rgba(100, 116, 139, 0.14);
  color: #475569;
}

@media (max-width: 1024px) {
  .hud-cmd-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .hud-cmd-list {
    grid-template-columns: 1fr;
  }
}

.height-overlay {
  width: 100%;
  margin-top: 10px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  padding: 8px 12px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  font-size: 14px;
  color: var(--do-gold-deep);
  font-weight: 700;
  text-align: center;
}

.height-overlay.read-mode-overlay {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 12px 18px;
  border-left: 3px solid var(--do-gold);
  background: var(--do-gold-wash);
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  color: var(--do-text-primary);
}

.header-right-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dev-switch-pills {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--do-bg-sunken);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--do-border);
}

.dev-switch-lbl {
  font-size: 13px;
  color: var(--do-text-secondary);
}

.dev-pill-btn {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--do-text-secondary);
  cursor: pointer;
  transition: var(--transition-fast);
}

.dev-pill-btn:hover {
  color: var(--do-text-primary);
}

.dev-pill-btn.active {
  background: var(--do-gold-deep);
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

/* ---------- 升旗台下方: 颁奖旗位指派 ---------- */
.podium-assign {
  width: 100%;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--do-border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.podium-assign-label {
  display: flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-secondary);
}

/* ---------- 右栏动作与急停 ---------- */
.col-actions {
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: calc(100vh - 200px);
}

.actions-body {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.flag-status-pill {
  font-size: 14px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.flag-status-pill.RISING {
  background: rgba(var(--th-accent-rgb), 0.2);
  color: var(--do-gold-deep);
}

.flag-status-pill.LOWERING {
  background: var(--do-warning-bg);
  color: var(--do-warning-deep);
}

.flag-status-pill.ESTOPPED {
  background: var(--do-danger-bg);
  color: var(--do-danger);
  font-weight: bold;
}

.flag-status-pill.COMPLETED {
  background: var(--do-success-bg);
  color: var(--do-success);
}

.flag-status-pill.IDLE {
  background: var(--do-border-lighter);
  color: var(--do-text-secondary);
}

.estop-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.btn-estop {
  width: 100%;
  padding: 16px 14px;
  background: linear-gradient(180deg, #B0593230 0%, var(--do-danger) 100%);
  background-color: var(--do-danger);
  border: 1px solid var(--do-danger-deep);
  border-radius: var(--radius-md);
  color: #FFFFFF;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(var(--th-danger-rgb), 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.16);
  transition: var(--transition-fast);
}

.btn-estop:hover {
  background: var(--do-danger-deep);
  border-color: var(--do-danger-deep);
  box-shadow: 0 6px 20px rgba(var(--th-danger-rgb), 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.22);
  transform: translateY(-1px);
}

.btn-estop:active {
  background: var(--do-danger-deep);
  transform: translateY(1px);
  box-shadow: 0 2px 8px rgba(var(--th-danger-rgb), 0.4);
}

.estop-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.estop-icon {
  width: 26px;
  height: 26px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.estop-title {
  font-size: var(--fs-h2);
  font-weight: 800;
  letter-spacing: 0.5px;
}

.estop-desc {
  font-size: var(--fs-sm);
  color: rgba(255, 253, 249, 0.86);
}

.estop-hint {
  font-size: var(--fs-sm);
  color: var(--do-text-secondary);
  text-align: center;
  line-height: var(--lh-loose);
}

.routine-actions-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-gold-deep);
}

.act-btn {
  height: 38px;
  width: 100%;
}

.receipt-box {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px 14px;
  font-size: 14px;
  color: var(--do-text-secondary);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.receipt-title {
  color: var(--do-gold-deep);
  font-weight: 700;
  margin-bottom: 2px;
}

.run-log {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--do-text-regular);
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 150px;
  overflow-y: auto;
}

/* ---------- 冠军国家选定面板 ---------- */
.country-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}


.slot-target-row {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: stretch !important;
  gap: 12px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.slot-card {
  flex: 1 1 0 !important;
  width: 0 !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--do-bg-input);
  border: 1.5px solid var(--do-border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.slot-card:hover {
  border-color: var(--do-gold);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.slot-card.active {
  border-color: var(--do-gold);
  background: var(--do-gold-wash);
  box-shadow: 0 0 0 2px rgba(var(--th-accent-rgb), 0.2);
}

.slot-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.slot-capsule-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1.5px solid var(--do-gold);
  background: rgba(var(--th-accent-rgb), 0.08);
  color: var(--do-gold-deep);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1.4;
  outline: none;
  user-select: none;
}

.slot-card:hover .slot-capsule-btn {
  background: var(--do-gold);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(var(--th-accent-rgb), 0.35);
}

.capsule-swap-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.slot-card-mid {
  display: flex;
  align-items: stretch;
  gap: 10px;
}

.slot-swatch {
  height: auto;
  align-self: stretch;
  aspect-ratio: 3 / 2;
  border-radius: 3px;
  border: 1px solid rgba(15, 23, 42, 0.25);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.slot-meta {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.slot-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slot-code {
  font-size: 12px;
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slot-card-bot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 12px;
  padding-top: 6px;
  border-top: 1px dashed rgba(148, 163, 184, 0.3);
}

.slot-anthem-text {
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.slot-linked-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.slot-linked-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10B981;
}

.slot-rank {
  font-size: 13px;
  font-weight: 800;
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 4px;
  color: #FFFFFF;
}

.slot-rank.champion {
  background: #D97706;
}

.slot-rank.runnerUp {
  background: #64748B;
}

.slot-rank.third {
  background: #B45309;
}

/* ---------- 国家选定模态框 (点击旗位卡片弹出) ---------- */
/* ============================================================
 * 现代高保真国家选定弹窗样式
 * ============================================================ */
::v-deep(.modern-flag-picker .el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.22);
  background: var(--do-bg-card, #FFFFFF);
  border: 1px solid var(--do-border, #E2E8F0);
}

::v-deep(.modern-flag-picker .el-dialog__header) {
  padding: 16px 20px;
  margin-right: 0;
  border-bottom: 1px solid var(--do-border, #E2E8F0);
  background: rgba(var(--th-shadow-rgb, 15, 23, 42), 0.02);
}

::v-deep(.modern-flag-picker .el-dialog__body) {
  padding: 16px 20px 10px;
}

::v-deep(.modern-flag-picker .el-dialog__footer) {
  padding: 12px 20px 16px;
  border-top: 1px solid var(--do-border, #E2E8F0);
  background: var(--do-bg-sunken, #F8FAFC);
}

.modal-custom-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.mch-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mch-medal-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  background: #F8FAFC;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.mch-medal-tag.champion {
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  border-color: #F59E0B;
  color: #92400E;
}

.mch-medal-tag.runnerUp {
  background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
  border-color: #94A3B8;
  color: #334155;
}

.mch-medal-tag.third {
  background: linear-gradient(135deg, #FFEDD5 0%, #FED7AA 100%);
  border-color: #EA580C;
  color: #9A3412;
}

.mch-medal-icon {
  font-size: 18px;
  line-height: 1;
}

.mch-medal-title {
  font-size: 14px;
  font-weight: 700;
}

.mch-pole-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.08);
}

.mch-titles {
  display: flex;
  flex-direction: column;
}

.mch-main-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--do-font-primary, #0F172A);
}

.mch-sub-title {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--do-font-secondary, #64748B);
}

/* 席位切换 Pill 选项卡 */
.mch-slot-switch {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #F1F5F9;
  padding: 3px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  margin-right: 32px;
}

.slot-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.slot-switch-btn:hover {
  color: #0F172A;
  background: rgba(255, 255, 255, 0.6);
}

.slot-switch-btn.is-active {
  background: #FFFFFF;
  color: #0F172A;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-color: #CBD5E1;
}

.slot-switch-btn.is-active.champion {
  border-color: #F59E0B;
  color: #B45309;
}

.slot-switch-btn.is-active.runnerUp {
  border-color: #64748B;
  color: #334155;
}

.slot-switch-btn.is-active.third {
  border-color: #EA580C;
  color: #C2410C;
}

.sw-curr-code {
  font-size: 11px;
  opacity: 0.85;
}

/* 顶部搜索与推荐工具栏 */
.picker-toolbar-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--do-bg-sunken, #F8FAFC);
  border: 1px solid var(--do-border, #E2E8F0);
}

.pt-top-row {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
}

.pt-search-box {
  flex: 1;
}

.modern-search-input {
  width: 100%;
}

.pt-current-assigned {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border-radius: 6px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.ca-label {
  font-size: 12px;
  color: #64748B;
}

.ca-flag {
  width: 24px;
  height: 16px;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.ca-name {
  font-size: 13px;
  font-weight: 700;
  color: #0F172A;
}

.ca-code {
  font-size: 12px;
  font-weight: 600;
  color: #2563EB;
}

.ca-anthem-chip {
  font-size: 11px;
  color: #D97706;
  background: #FEF3C7;
  padding: 1px 5px;
  border-radius: 3px;
}

/* 热门快捷定位标签 */
.pt-hot-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.hot-tag-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  margin-right: 2px;
}

.quick-country-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid #E2E8F0;
  background: #FFFFFF;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
  transition: all 0.18s ease;
}

.quick-country-chip:hover {
  border-color: #2563EB;
  color: #2563EB;
  background: #EFF6FF;
  transform: translateY(-1px);
}

.quick-country-chip.is-active {
  border-color: #F59E0B;
  background: #FFFBEB;
  color: #B45309;
  font-weight: 600;
}

.q-flag-dot {
  width: 16px;
  height: 12px;
  border-radius: 1px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.q-code {
  font-size: 10px;
  color: #64748B;
  font-weight: 600;
}

/* 大洲筛选 Pill Tabs */
.modern-pill-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.d-region-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #E2E8F0;
  background: #FFFFFF;
  font-size: 13px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.d-region-pill:hover {
  border-color: #2563EB;
  color: #2563EB;
  background: #F8FAFC;
}

.d-region-pill.active {
  background: #2563EB;
  border-color: #2563EB;
  color: #FFFFFF;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.d-region-pill .pill-count {
  font-size: 11px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.06);
  color: inherit;
  font-weight: 600;
}

.d-region-pill.active .pill-count {
  background: rgba(255, 255, 255, 0.25);
  color: #FFFFFF;
}

/* 国家卡片网格系统 */
.dialog-country-grid.modern-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(295px, 1fr));
  gap: 12px;
  max-height: 480px;
  overflow-y: auto;
  padding: 4px 2px;
  margin-top: 6px;
}

/* 自定义纤细滚动条 */
.dialog-country-grid.modern-grid::-webkit-scrollbar {
  width: 6px;
}

.dialog-country-grid.modern-grid::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 3px;
}

.dialog-country-grid.modern-grid::-webkit-scrollbar-track {
  background: #F1F5F9;
}

/* 国家卡片主体 */
.d-country-card {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 10px 12px;
  border: 1.5px solid #E2E8F0;
  border-radius: 8px;
  background: #FFFFFF;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.d-country-card:hover {
  border-color: #2563EB;
  background: #F8FAFC;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.12);
}

.d-country-card.is-selected {
  border-color: #F59E0B;
  background: #FFFDF5;
  box-shadow: 0 0 0 1px #F59E0B, 0 4px 14px rgba(245, 158, 11, 0.18);
}

.d-country-card.is-other-assigned {
  opacity: 0.88;
  border-style: dashed;
}

/* 左侧国旗预览区域 (严格等高于右侧国家名称+试听按钮两行的高度) */
.card-flag-stage {
  position: relative;
  height: 48px;
  width: 64px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.16);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  background: #F8FAFC;
}

.card-flag-img {
  display: block;
  width: 100%;
  height: 100%;
}

.card-iso-tag {
  position: absolute;
  bottom: 0;
  right: 0;
  background: rgba(15, 23, 42, 0.82);
  color: #FFFFFF;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-top-left-radius: 4px;
  letter-spacing: 0.3px;
  line-height: 1.1;
}

/* 右侧两行信息区域 (高度与左侧国旗48px严格齐平，两端对齐排列两行) */
.card-info-stage {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
  flex: 1;
  height: 48px;
}

/* 第1行：国家中文名 + 英文名(字号更小紧随其后) + 二字代码 */
.card-title-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  height: 22px;
  line-height: 22px;
}

.card-names-wrap {
  display: flex;
  align-items: baseline;
  gap: 6px;
  overflow: hidden;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.card-name-cn {
  font-size: 14.5px;
  font-weight: 700;
  color: #0F172A;
  white-space: nowrap;
  flex-shrink: 0;
  letter-spacing: 0.2px;
}

.card-name-en-inline {
  font-size: 11.5px;
  font-weight: normal;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-code-pill {
  font-size: 11px;
  font-weight: 700;
  color: #2563EB;
  background: #EFF6FF;
  padding: 0 5px;
  border-radius: 3px;
  border: 1px solid #DBEAFE;
  height: 18px;
  line-height: 18px;
  flex-shrink: 0;
}

/* 第2行：试听按钮 + 国歌名称 + 时长 */
.card-anthem-row {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 22px;
  line-height: 22px;
}

.anthem-audition-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 0 8px;
  height: 20px;
  box-sizing: border-box;
  border-radius: 10px;
  border: 1px solid #CBD5E1;
  background: #F8FAFC;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
  line-height: 1;
  vertical-align: middle;
}

.anthem-audition-btn:hover {
  background: #2563EB;
  border-color: #2563EB;
  color: #FFFFFF;
}

.anthem-audition-btn.is-playing {
  background: #DC2626;
  border-color: #DC2626;
  color: #FFFFFF;
}

.aud-icon {
  font-size: 8px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transform: translateY(-0.5px);
}

.aud-label {
  font-size: 11px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.anthem-name-strip {
  font-size: 11px;
  color: #B45309;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.anthem-sec-badge {
  font-size: 11px;
  font-weight: 600;
  color: #64748B;
  background: #F1F5F9;
  padding: 1px 5px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* 卡片角标 */
.card-badge {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-bottom-left-radius: 8px;
  letter-spacing: 0.3px;
}

.card-badge.current-badge.champion {
  background: #F59E0B;
  color: #FFFFFF;
}

.card-badge.current-badge.runnerUp {
  background: #64748B;
  color: #FFFFFF;
}

.card-badge.current-badge.third {
  background: #EA580C;
  color: #FFFFFF;
}

.card-badge.other-badge {
  background: #94A3B8;
  color: #FFFFFF;
}

/* 空状态 */
.modern-dialog-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 50px 20px;
}

.empty-icon-box {
  font-size: 36px;
  margin-bottom: 8px;
  opacity: 0.6;
}

.empty-main {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  margin: 0 0 4px;
}

.empty-sub {
  font-size: 13px;
  color: #94A3B8;
  margin: 0;
}

/* 弹窗底栏 */
.dialog-footer-meta.modern-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.d-foot-info-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.foot-count-tag {
  font-size: 13px;
  color: #0F172A;
  font-weight: 500;
}

.foot-count-tag strong {
  color: #2563EB;
}

.foot-tip-tag {
  font-size: 12px;
  color: #64748B;
}

.d-foot-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-select {
  flex: 1;
}

.search-hint {
  font-size: 14px;
  color: var(--do-text-secondary);
  flex-shrink: 0;
}

.region-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.region-chip {
  padding: 4px 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-secondary);
  background: var(--do-bg-input);
  border: 1px solid var(--do-border);
  border-radius: 999px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.region-chip:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.region-chip.active {
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%);
  border-color: var(--do-gold-deep);
  color: #FFFFFF;
}

.country-chips {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
  gap: 8px;
  max-height: 172px;
  overflow-y: auto;
  padding: 2px;
}

.country-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition-fast);
  min-width: 0;
}

.country-chip:hover {
  border-color: var(--do-gold);
  background: var(--do-gold-wash);
}

.country-chip.is-champion {
  border-color: var(--do-warning);
  background: var(--do-warning-bg);
}

.cc-swatch {
  width: 22px;
  height: 15px;
  border-radius: 2px;
  border: 1px solid rgba(15, 23, 42, 0.22);
  flex-shrink: 0;
}

.cc-code {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-gold-deep);
  flex-shrink: 0;
}

.cc-name {
  font-size: 14px;
  color: var(--do-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-tip {
  grid-column: 1 / -1;
  font-size: 14px;
  color: var(--do-text-secondary);
  text-align: center;
  padding: 16px 0;
}

.champion-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.06) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: 6px;
  padding: 10px 14px;
}

.cs-swatch {
  width: 44px;
  height: 30px;
  border-radius: 3px;
  border: 1px solid rgba(15, 23, 42, 0.22);
  flex-shrink: 0;
}

.cs-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.cs-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.cs-anthem {
  font-size: 14px;
  color: var(--do-text-secondary);
}

/* ============================================================
 * 左栏：参与联动设备 (最多3台) 状态与参数读取看板
 * ============================================================ */
.col-data {
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: calc(100vh - 190px);
}

.data-present-body {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.mode-hint-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
}

.mode-hint-alert.cmd_control {
  background: var(--do-gold-wash);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  color: var(--do-gold-deep);
}

.mode-hint-alert.read_sync {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  color: var(--do-text-secondary);
}

.linked-devices-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hardware-dev-detail-card {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-light);
  /* 默认浅色边框 */
  border-radius: 6px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.hardware-dev-detail-card:hover {
  border-color: rgba(var(--th-accent-rgb), 0.45);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

/* 选中后主题色边框 */


.hardware-dev-detail-card.is-offline {
  opacity: 0.55;
  background: var(--do-bg-sunken);
  cursor: not-allowed;
}

.hdd-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hdd-head-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 读取状态单选胶囊 (读取中 / 未读取) */
.read-status-chip {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--do-bg-sunken);
  color: var(--do-text-secondary);
  border: 1px solid var(--do-border);
  transition: var(--transition-fast);
}

.read-status-chip.active {
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  border-color: rgba(var(--th-accent-rgb), 0.4);
  font-weight: 700;
}

.read-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--do-text-secondary);
}

.read-status-chip.active .read-dot,
.is-reading-row .read-dot {
  background: var(--do-gold-deep);
}

.read-dot.pulse {
  animation: pulse-slow 1.6s infinite ease-in-out;
}

.is-reading-row {
  border-left: 3px solid var(--do-gold);
}

.read-mode-bottom-hint {
  font-size: 13px;
  color: var(--do-text-secondary);
  padding: 5px 8px;
  text-align: center;
  background: var(--do-bg-input);
  border-radius: 4px;
}

.hdd-identity {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
}

.hdd-order-tag {
  font-size: 12px;
  font-weight: 700;
  color: #FFFFFF;
  background: var(--do-gold-deep);
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
  line-height: 1.2;
}

.hdd-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--do-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.hdd-ctrl-check :deep(.el-checkbox__label) {
  font-weight: normal !important;
}

.hdd-ctrl-txt {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: normal !important;
}

.hdd-ctrl-txt.active {
  color: var(--do-gold-deep);
  font-weight: normal !important;
}

/* 基础信息行：所在位置与设置状态 */
.hdd-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 13.5px;
  padding-top: 6px;
  border-top: 1px dashed var(--do-border-light);
  min-width: 0;
}

.hdd-loc-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  flex: 1 1 auto;
  color: var(--do-text-secondary);
  overflow: hidden;
}

.hdd-loc-group .loc-icon {
  flex-shrink: 0;
  color: var(--do-gold-deep);
}

.hdd-type-badge {
  font-size: 11px;
  font-weight: 600;
  color: #0369A1;
  background: rgba(2, 132, 199, 0.1);
  border: 1px solid rgba(2, 132, 199, 0.25);
  border-radius: 3px;
  padding: 1px 6px;
  flex-shrink: 0;
}

.hdd-single-row {
  justify-content: flex-start;
  gap: 8px;
}

.hdd-field-lbl {
  font-size: 11px;
  color: var(--do-text-muted);
  flex-shrink: 0;
  min-width: 52px;
}

.hdd-ip-text {
  font-size: 11px;
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hdd-loc-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hdd-setting-wrap {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  flex-shrink: 0;
}

.hdd-setting-lbl {
  color: var(--do-text-secondary);
}

.hdd-setting-val {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--do-success);
}

.setting-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 6px rgba(var(--th-success-rgb), 0.6);
  flex-shrink: 0;
}

.hdd-telemetry-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--do-bg-sunken);
  border-radius: 4px;
  padding: 8px 10px;
}

.h-meter-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.h-meter-lbl {
  font-size: 13px;
  color: var(--do-text-secondary);
  flex-shrink: 0;
}

.h-bar-track {
  flex: 1;
  height: 8px;
  background: var(--do-border);
  border-radius: 3px;
  overflow: hidden;
}

.h-bar-fill {
  height: 100%;
  background: var(--do-gold);
  border-radius: 3px;
  transition: width 0.2s ease-out;
}

.h-meter-val {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--do-gold-deep);
  width: 56px;
  text-align: right;
  flex-shrink: 0;
}

.h-telemetry-sub {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--do-text-secondary);
}

.hdd-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* ============================================================
 * 右栏：区域一 2x2 指令卡片 + 区域二 已选被控设备
 * ============================================================ */
.action-section-block,
.selected-control-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 12px;
}

.action-block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mode-badge {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.mode-badge.cmd_control {
  background: var(--do-success-bg);
  color: var(--do-success);
  border: 1px solid rgba(var(--th-success-rgb), 0.3);
}

.mode-badge.read_sync {
  background: var(--do-bg-input);
  color: var(--do-text-secondary);
  border: 1px solid var(--do-border);
}

/* 升旗视窗下方的一行 4 个核心操作指令卡片 (横向平铺均分) */
.stage-actions-row {
  margin-top: 14px;
  padding: 12px 14px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stage-actions-row .action-block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cmd-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr) !important;
  gap: 12px !important;
  width: 100%;
}

.cmd-card {
  padding: 14px 10px;
  border-radius: 6px;
  border: 1px solid var(--do-border);
  background: var(--do-bg-card);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: left;
  transition: var(--transition-fast);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

.cmd-card:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
}

.cmd-card:active:not(:disabled) {
  transform: translateY(0);
}

.cmd-card:disabled {
  opacity: 0.52;
  cursor: not-allowed !important;
  filter: grayscale(0.45);
  box-shadow: none;
  pointer-events: auto;
}

.cmd-card .cmd-desc.text-warning {
  color: #D97706 !important;
  font-weight: 600;
}

.cmd-card-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.cmd-icon-wrap {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.estop-icon-wrap {
  background: rgba(var(--th-danger-rgb), 0.14);
  color: var(--do-danger);
}

.estop-svg-icon {
  width: 34px;
  height: 34px;
}

.gold-icon-wrap {
  background: rgba(var(--th-accent-rgb), 0.15);
  color: var(--do-gold-deep);
}

.neutral-icon-wrap {
  background: rgba(100, 116, 139, 0.15);
  color: #475569;
}

.official-icon-wrap {
  background: rgba(30, 41, 59, 0.1);
  color: var(--do-text-primary);
}

.cmd-texts {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.cmd-title {
  font-size: 15px;
  font-weight: 700;
}

.cmd-desc {
  font-size: 13px;
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 紧急停止卡片特别高亮样式 */
.estop-card:not(:disabled) {
  border-color: rgba(var(--th-danger-rgb), 0.5);
  background: linear-gradient(180deg, var(--do-bg-card) 0%, rgba(var(--th-danger-rgb), 0.08) 100%);
}

.estop-card:hover:not(:disabled) {
  border-color: var(--do-danger);
  background: rgba(var(--th-danger-rgb), 0.12);
}

.cmd-mode-locked-hint {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: var(--do-warning-deep);
  background: var(--do-warning-bg);
  border: 1px solid rgba(var(--th-warning-rgb), 0.3);
  border-radius: 4px;
  padding: 8px 12px;
  line-height: 1.5;
}

/* 右侧区域二：已选被控设备 (一行一个，简略呈现，快捷X掉) */
.selected-device-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.selected-dev-compact-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-light);
  border-radius: 5px;
  transition: var(--transition-fast);
}

.selected-dev-compact-row:hover {
  border-color: var(--do-gold);
}

.s-dev-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.s-dev-tag {
  font-size: 13px;
  font-weight: 700;
  color: #FFFFFF;
  background: var(--do-gold-deep);
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.s-dev-id {
  font-size: 13px;
  color: var(--do-text-secondary);
  flex-shrink: 0;
}

.s-dev-region {
  font-size: 13px;
  color: var(--do-text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.s-dev-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  padding-right: 6px;
}

.s-dev-stxt {
  font-size: 13px;
  color: var(--do-text-secondary);
}

.btn-remove-chip {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid var(--do-border);
  background: transparent;
  color: var(--do-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: var(--transition-fast);
}

.btn-remove-chip:hover {
  background: var(--do-danger-bg);
  border-color: var(--do-danger);
  color: var(--do-danger);
}

.empty-controlled-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 10px;
  color: var(--do-text-secondary);
  font-size: 13px;
  text-align: center;
}

.selected-batch-action-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 10px;
  margin-top: 6px;
  border-top: 1px dashed var(--do-border-light);
}

.btn-batch-mini {
  flex: 1;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 4px;
  box-sizing: border-box;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.btn-batch-restore {
  background: rgba(var(--th-accent-rgb), 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  color: var(--do-gold-deep);
}

.btn-batch-restore:hover {
  background: rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  box-shadow: 0 2px 8px rgba(var(--th-accent-rgb), 0.2);
  transform: translateY(-1px);
}

.btn-batch-restore:active {
  transform: translateY(0);
  background: rgba(var(--th-accent-rgb), 0.22);
}

.btn-batch-clear {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  color: var(--do-text-secondary);
}

.btn-batch-clear:hover {
  background: var(--do-danger-bg);
  border-color: rgba(var(--th-danger-rgb), 0.45);
  color: var(--do-danger);
  box-shadow: 0 2px 8px rgba(var(--th-danger-rgb), 0.15);
  transform: translateY(-1px);
}

.btn-batch-clear:active {
  transform: translateY(0);
  background: rgba(var(--th-danger-rgb), 0.15);
}

/* ============================================================
 * 第三行：PLC 硬件执行回执与运行日志 (放到页面底部全宽)
 * ============================================================ */

.bottom-full-receipt {
  border-bottom: 1px solid var(--do-border-light);
  border-radius: 6px 6px 0 0;
  padding: 14px 18px;
  background: rgba(var(--th-accent-rgb), 0.02);
}

.bottom-full-receipt .rs-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.bottom-full-receipt .rs-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.bottom-full-receipt .rs-lbl {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.bottom-full-receipt .rs-val {
  font-size: 14px;
  max-width: 100%;
  text-align: left;
}

.receipt-status-wrap {
  display: flex;
  align-items: center;
}

.receipt-section-block .receipt-summary-block {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-light);
  border-radius: 5px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.receipt-section-block .rs-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  line-height: 1.4;
}

.receipt-section-block .rs-lbl {
  color: var(--do-text-secondary);
  flex-shrink: 0;
}

.receipt-section-block .rs-dev-val {
  max-width: 190px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}

.receipt-bottom-body.single-log {
  grid-template-columns: 1fr;
  padding: 12px 16px;
}

.receipt-bottom-body.single-log .receipt-log-block {
  min-height: 90px;
}

.receipt-bottom-body.single-log .rs-log-scroll {
  max-height: 120px;
}

.flag-receipt-layout {
  display: flex;
  flex-direction: column;
  margin-top: 14px;
}

.receipt-pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--do-success);
  display: inline-block;
  box-shadow: 0 0 0 3px rgba(var(--th-success-rgb), 0.2);
  margin-right: 6px;
}

.receipt-status-code {
  font-size: 13.5px;
  color: var(--do-success);
  font-weight: 700;
}

.receipt-bottom-body {
  padding: 14px 16px;
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 14px;
}

.receipt-summary-block {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rs-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-gold-deep);
}

.rs-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rs-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13.5px;
}

.rs-lbl {
  color: var(--do-text-secondary);
}

.receipt-log-block {
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 120px;
}

.rs-log-scroll {
  flex: 1;
  max-height: 120px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-entry {
  font-size: 13px;
  color: var(--do-text-regular);
  line-height: 1.6;
}

@media (max-width: 1500px) {

  .receipt-bottom-body {
    grid-template-columns: 1fr;
  }

  /* 窄屏时设备行按钮回到两列, 避免挤压 */
  .dev-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ============================================================================
 * 统一控制台视觉与响应式增强
 * 参照“大屏调度”和“计时计分”页面，保留原有工业控制交互
 * ============================================================================ */
.flag-workspace {
  width: 100%;
  min-width: 0;
  color: var(--do-text-primary);
}

.flag-top-bar {
  align-items: center;
  gap: 20px;
  min-width: 0;
  padding: 18px 22px;
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
  flex-wrap: wrap;
}

.top-left {
  min-width: 0;
  flex: 1 1 360px;
  gap: 14px;
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

.title-meta {
  min-width: 0;
}

.title-row {
  min-width: 0;
  gap: 10px;
}

.view-title {
  min-width: 0;
  overflow: hidden;
  color: var(--do-text-primary);
  font-size: 21px;
  font-weight: 700;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-meta p {
  margin: 5px 0 0;
  overflow: hidden;
  color: var(--do-text-secondary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}



.top-right {
  min-width: 0;
  flex: 1 1 640px;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.header-status {
  color: var(--do-text-secondary);
  font-size: 13px;
}

.flag-header-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 30px;
  padding: 0 10px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border);
  border-radius: 5px;
  white-space: nowrap;
}

.flag-header-status strong {
  color: var(--do-text-primary);
  font-family: var(--font-mono, Consolas, monospace);
  font-size: 13px;
}

.flag-header-status .status-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: currentColor;
}

.flag-header-status .status-dot.online {
  color: var(--do-success);
  box-shadow: 0 0 7px currentColor;
}

.flag-header-status .status-dot.danger {
  color: var(--do-danger);
  box-shadow: 0 0 7px currentColor;
}

.flag-header-status .status-dot.muted {
  color: var(--do-text-placeholder);
}

.mode-toggle-group {
  min-width: 0;
  flex-wrap: wrap;
}

.panel-header {
  min-width: 0;
  gap: 10px;
  flex-wrap: wrap;
}

.panel-header>.header-left,
.panel-header>.header-right,
.panel-header>.header-right-meta {
  min-width: 0;
}

.panel-header>.header-left {
  flex: 1 1 auto;
}

.header-title,
.panel-subtitle {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-title {
  line-height: 1.35;
}

.header-right,
.header-right-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.header-right-meta {
  flex: 1 1 300px;
}

.flag-main-layout {
  grid-template-columns: minmax(0, 1fr) minmax(0, 3fr) !important;
  min-width: 0;
}

.flag-main-layout>*,
.flag-secondary-layout>* {
  min-width: 0;
}

.col-data,
.col-sim,
.col-actions,
.col-country {
  min-width: 0;
  width: 100%;
}

.data-present-body,
.actions-body,
.country-body,
.canvas-stage {
  min-width: 0;
}

.hdd-head,
.hdd-meta-row,
.h-meter-row,
.h-telemetry-sub,
.action-block-head,
.selected-dev-compact-row,
.receipt-status-wrap {
  min-width: 0;
  gap: 8px;
}

.hdd-head {
  flex-wrap: wrap;
}

.hdd-identity {
  min-width: 0;
  flex: 1 1 180px;
}

.hdd-head-right {
  min-width: 0;
  flex: 0 1 auto;
}

.hdd-alias,
.hdd-id,
.hdd-name,
.hdd-loc,
.hp-val {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hdd-alias,
.hdd-name,
.hdd-loc {
  white-space: nowrap;
}

.hdd-meta-row {
  flex-wrap: nowrap;
}

.hdd-loc-group {
  flex: 1 1 auto;
  min-width: 0;
}

.hdd-setting-wrap {
  flex-shrink: 0;
}

.h-telemetry-sub {
  justify-content: flex-start;
  flex-wrap: wrap;
  row-gap: 5px;
  column-gap: 12px;
}

.hdd-status-badge {
  margin-left: auto;
  flex: 0 0 auto;
}

.sim-stage-viewport {
  min-width: 0;
  max-width: 100%;
}

.flag-sim-svg {
  max-width: 100%;
  max-height: 680px;
}

.height-overlay {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.height-overlay>span,
.height-overlay.read-mode-overlay>span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.read-mode-overlay {
  align-items: flex-start;
}

.dev-switch-pills {
  min-width: 0;
  max-width: 100%;
  flex-wrap: wrap;
}

.dev-switch-lbl,
.dev-pill-btn {
  flex: 0 0 auto;
}

.podium-assign-label {
  min-width: 0;
}

.podium-assign-label span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cmd-cards-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.slot-card,
.cmd-card,
.cmd-card-inner,
.cmd-texts,
.action-section-block,
.receipt-section-block {
  min-width: 0;
}

.cmd-card-inner {
  overflow: hidden;
}

.cmd-title,
.cmd-desc {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-block-head {
  flex-wrap: wrap;
}

.group-label {
  min-width: 0;
}

.group-label>span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-device-list {
  min-width: 0;
}

.selected-dev-compact-row {
  overflow: hidden;
}

.s-dev-main {
  min-width: 0;
  overflow: hidden;
}

.s-dev-region {
  min-width: 0;
  flex: 1 1 80px;
}

.s-dev-status {
  flex: 0 0 auto;
  min-width: 0;
}

.selected-batch-action-bar {
  flex-wrap: wrap;
}

.btn-batch-mini {
  min-width: 0;
  flex: 1 1 140px;
}

.receipt-status-wrap {
  max-width: 52%;
  overflow: hidden;
}

.receipt-status-code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.receipt-section-block .rs-item {
  min-width: 0;
  gap: 10px;
  flex-wrap: wrap;
}

.receipt-section-block .rs-val {
  min-width: 0;
  max-width: 66%;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-row {
  min-width: 0;
  flex-wrap: wrap;
}

.search-select {
  min-width: min(300px, 100%);
  flex: 1 1 360px;
}

.search-hint {
  min-width: 0;
  flex: 1 1 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.country-body,
.country-chips,
.region-chips,
.champion-summary {
  min-width: 0;
}

.cs-info,
.cs-anthem {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 900px) {
  .flag-main-layout {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  .col-data,
  .col-sim {
    max-height: none;
  }

  .actions-body,
  .data-present-body {
    overflow: visible;
  }

  .flag-top-bar {
    align-items: flex-start;
  }

  .top-right {
    flex-basis: 100%;
    justify-content: flex-start;
  }

  .height-overlay {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .receipt-status-wrap {
    max-width: 100%;
  }

  .cmd-cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 760px) {
  .flag-top-bar {
    padding: 14px;
  }

  .top-left {
    align-items: flex-start;
    flex-basis: 100%;
  }

  .page-icon {
    width: 44px;
    height: 44px;
  }

  .view-title {
    font-size: 18px;
    white-space: normal;
  }

  .title-meta p {
    white-space: normal;
  }

  .title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .top-right {
    width: 100%;
  }

  .flag-header-status {
    width: 100%;
    justify-content: flex-start;
  }

  .mode-toggle-group {
    width: 100%;
  }

  .mode-tab-btn {
    min-width: 0;
    flex: 1 1 180px;
  }

  .header-right,
  .header-right-meta {
    width: 100%;
    justify-content: flex-start;
  }

  .header-title,
  .panel-subtitle {
    white-space: normal;
  }

  .hdd-loc {
    justify-content: flex-start;
  }

  .hdd-status-badge {
    margin-left: 0;
  }

  .height-overlay.read-mode-overlay {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .height-overlay.read-mode-overlay>span {
    white-space: normal;
  }

  .cmd-cards-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .cmd-card {
    min-height: 66px;
  }

  .s-dev-main {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .s-dev-status {
    margin-left: 0;
  }

  .receipt-section-block .rs-val {
    max-width: 100%;
    width: 100%;
    text-align: left;
  }

  .search-hint {
    white-space: normal;
  }

  .country-chips {
    max-height: 220px;
  }
}

@media (max-width: 520px) {

  .top-right>.btn-top-manage,
  .top-right>.btn-fetch-hardware {
    flex: 1 1 100%;
  }

  .mode-tab-btn {
    flex-basis: 100%;
  }

  .hdd-params-grid,
  .height-overlay,
  .height-overlay.read-mode-overlay {
    grid-template-columns: minmax(0, 1fr);
  }

  .height-overlay>span,
  .height-overlay.read-mode-overlay>span {
    white-space: normal;
  }

  .search-select {
    min-width: 100%;
  }

  .selected-batch-action-bar {
    flex-direction: column;
  }

  .btn-batch-mini {
    width: 100%;
    flex-basis: auto;
  }
}

/* 升旗台旗帜点击更换国家交互 */
.flag-clickable-item,
.flag-clickable-label {
  transition: transform 0.18s ease, filter 0.18s ease;
  user-select: none;
}

.flag-clickable-item.can-change,
.flag-clickable-label.can-change {
  cursor: pointer;
}

.flag-clickable-item.can-change:hover {
  filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.55)) brightness(1.05);
}

.flag-clickable-label.can-change:hover {
  filter: drop-shadow(0 2px 4px rgba(15, 23, 42, 0.18));
  opacity: 0.88;
}

.flag-clickable-item:not(.can-change),
.flag-clickable-label:not(.can-change) {
  cursor: not-allowed;
}

/* 升旗台视窗铺满与缩小样式控制 (保持 viewBox 宽高比不变形) */
.flag-main-layout {
  transition: all 0.28s ease-in-out;
}

.flag-main-layout.is-sim-fullscreen {
  grid-template-columns: minmax(0, 1fr) !important;
}

.flag-main-layout.is-sim-fullscreen .col-sim {
  width: 100% !important;
}

.flag-main-layout.is-sim-fullscreen .sim-stage-viewport {
  max-width: 100%;
}

.flag-main-layout.is-sim-fullscreen .flag-sim-svg {
  max-height: 760px;
}

/* 升旗台画布右下角：铺满与缩小浮动控制按钮组 */
.viewport-zoom-ctrl {
  position: absolute;
  right: 14px;
  bottom: 14px;
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.45);
  border-radius: 6px;
  padding: 3px;
  gap: 3px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
  z-index: 15;
  user-select: none;
}

.zoom-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: #475569;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  line-height: 1;
}

.zoom-btn:hover {
  background: rgba(241, 245, 249, 0.95);
  color: #0F172A;
}

.zoom-btn.active {
  background: var(--do-gold-deep, #B45309);
  color: #FFFFFF;
  border-color: rgba(180, 83, 9, 0.3);
  box-shadow: 0 2px 4px rgba(180, 83, 9, 0.25);
}

.zoom-btn.active:hover {
  background: #92400E;
}

.zoom-icon {
  width: 13.5px;
  height: 13.5px;
  flex-shrink: 0;
}

/* ============================================================
 * 旗杆/旗帜状态指示样式 (上升中、下降中、静止 · 鲜明三态色)
 * ============================================================ */
.flag-motion-status-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.flag-motion-status-item .motion-lbl {
  color: var(--do-text-secondary, #64748b);
  font-weight: 500;
}

.flag-motion-status-item .motion-val {
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 1. 上升中 (工控鲜绿) */
.flag-motion-status-item .motion-val.status-rising {
  color: #16A34A !important;
}

/* 2. 下降中 (琥珀暖橙) */
.flag-motion-status-item .motion-val.status-lowering {
  color: #EA580C !important;
}

/* 3. 静止 (警示正红) */
.flag-motion-status-item .motion-val.status-forbidden {
  color: #DC2626 !important;
}

/* ===== 设备管理弹窗 ===== */
.mode-tab-device {
  border-left: 1px solid var(--do-border, #334155) !important;
  margin-left: 6px;
}

.dev-mgr-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #475569;
}

.dev-mgr-btn {
  height: 28px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid #CBD5E1;
  background: #FFFFFF;
  color: #1E293B;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dev-mgr-btn+.dev-mgr-btn {
  margin-left: 6px;
}

.dev-mgr-btn:hover:not(:disabled) {
  background: #F1F5F9;
  border-color: #94A3B8;
}

.dev-mgr-btn.primary {
  background: #0EA5E9;
  border-color: #0EA5E9;
  color: #FFFFFF;
}

.dev-mgr-btn.primary:hover:not(:disabled) {
  background: #0284C7;
  border-color: #0284C7;
}

.dev-mgr-btn.danger {
  background: #FFF5F5;
  border-color: #FCA5A5;
  color: #DC2626;
}

.dev-mgr-btn.danger:hover:not(:disabled) {
  background: #FEE2E2;
  border-color: #EF4444;
}

.dev-mgr-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tag-safe {
  color: #16A34A;
  font-weight: 600;
}

.tag-danger {
  color: #DC2626;
  font-weight: 600;
}

.dev-form {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  background: #F8FAFC;
}

.dev-form-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #0F172A;
}

.dev-form-grid {
  display: grid;
  grid-template-columns: 105px 1fr 105px 1fr;
  gap: 10px 16px;
  align-items: center;
  font-size: 13px;
}

.dev-form-grid label {
  color: #334155;
  font-weight: 500;
  text-align: right;
}

.dev-form-grid input,
.dev-form-grid select {
  height: 32px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid #CBD5E1;
  background: #FFFFFF;
  color: #0F172A;
  font-size: 13px;
  width: 100%;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.dev-form-grid input::placeholder {
  color: #94A3B8;
}

.dev-form-grid input:focus,
.dev-form-grid select:focus {
  border-color: #0EA5E9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.16);
}

.dev-form-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #E2E8F0;
}

.dev-form-actions .dev-mgr-btn+.dev-mgr-btn {
  margin-left: 0;
}

.dev-test-result {
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.dev-test-result.ok {
  background: rgba(22, 163, 74, 0.15);
  color: #16A34A;
}

.dev-test-result.fail {
  background: rgba(220, 38, 38, 0.15);
  color: #DC2626;
}

.pos-exact-tag {
  display: inline-block;
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 3px;
  background: rgba(22, 163, 74, 0.18);
  color: #16A34A;
  font-size: 10px;
  font-weight: 600;
}

.btn-mini-tool {
  height: 24px;
  padding: 0 8px;
  font-size: 11px;
  border-radius: 5px;
  line-height: 22px;
}

.receipt-pulse-dot.offline {
  background: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.22);
}
</style>
