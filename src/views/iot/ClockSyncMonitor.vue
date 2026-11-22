<template>
  <div class="clock-monitor-workspace">
    <!-- 顶部状态栏：与智能升旗页面保持完全一致的页面级标题区 -->
    <section class="clock-top-bar page-header glass-panel">
      <div class="top-left page-heading">
        <div class="page-icon">
          <SvgIcon name="SvgMasterClock" size="28" />
        </div>
        <div class="title-meta">
          <div class="title-row">
            <h1 class="view-title">标准时钟卫星授时与子钟网络监测台</h1>
          </div>
          <p>
            实时监测卫星主母钟授时与全场子钟网络状态，执行全网校准。
          </p>
        </div>
      </div>

      <div class="top-right header-status">
        <div class="clock-header-status" title="WebSocket 实时状态流通道">
          <span :class="['status-dot', wsConnected ? 'online' : 'warning']"></span>
          <strong>{{ wsConnected ? 'WS 实时' : 'WS 重连中' }}</strong>
          <span>{{ masterOnline ? '母钟在线' : '母钟待检' }}</span>
        </div>
        <div class="clock-header-status" title="卫星授时接收状态">
          <span :class="['status-dot', masterOnline ? 'online' : 'muted']"></span>
          <strong>{{ masterOnline ? `${satelliteCount ?? '--'} 星` : 'OFFLINE' }}</strong>
          <span>卫星授时</span>
        </div>
        <button class="btn-industrial btn-top-manage" @click="refreshSubClocks" title="从 MySQL 台账刷新最新子钟列表">
          <SvgIcon name="SvgRefresh" size="14" style="margin-right: 4px;" />
          <span>刷新台账</span>
        </button>
        <button class="btn-industrial btn-gold btn-fetch-hardware" :disabled="isCalibrating" @click="calibrateNow"
          title="一键同步时钟：向母钟下发立即全网同步指令 (0x0D) + 校准间隔 (0x08) 并校准平台时间基准">
          <SvgIcon name="SvgRefresh" size="14" :class="{ 'spin-icon': isCalibrating }" style="margin-right: 4px;" />
          <span>{{ isCalibrating ? '全网时钟同步中...' : '一键同步时钟' }}</span>
        </button>
        <div class="mode-toggle-group">
          <button class="mode-tab-btn" @click="$router.push('/iot/clock/floorplan')"
            title="在 SVG 场馆平面图上拖拽安放全部子钟并查看状态点位">
            <span>平面图点位</span>
          </button>
          <button class="mode-tab-btn mode-tab-device" @click="openClockSettingsModal"
            title="对接设置：配置母钟 UDP 与子钟 MySQL 对接参数">
            <span>对接设置</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 顶部核心标准授时大盘 (3 列典雅工业仪表盘) -->
    <div class="master-clock-kpi glass-panel">
      <!-- 1. 北京时间基准视窗 -->
      <div class="kpi-block time-hero">
        <div class="block-head-row">
          <span class="time-lbl">国家授时中心 (NTSC) · 标准北京时间</span>
          <span class="ntsc-badge num-mono">{{ masterClockConfig.ip ? (masterClockConfig.port ? `${masterClockConfig.ip}:${masterClockConfig.port}` : masterClockConfig.ip) : 'IP待配置' }}</span>
        </div>
        <!-- 工业液晶高精度数码时钟视窗 -->
        <div class="digital-clock-screen">
          <div class="digital-time-display num-mono">
            <span class="time-main">{{ beijingTimeStr }}</span>
            <span class="time-millis">.{{ millisStr }}</span>
          </div>
          <div class="screen-corner-badge num-mono">{{ masterClockConfig.timeZoneStr || 'UTC+08:00' }}</div>
        </div>
        <div class="date-str-wrap">
          <span class="calendar-icon">📅</span>
          <span :class="['date-str', { 'is-disconnected': !masterOnline || dateStr.startsWith('未连接') }]">{{ dateStr
            }}</span>
          <span class="zone-pill num-mono" title="卫星主母钟网关设备型号">
            TS-9000-NTP 卫星主母钟
          </span>
        </div>
      </div>

      <!-- 2. 卫星捕获状态 -->
      <div class="kpi-block stat-item">
        <div class="block-head-row">
          <span class="block-lbl">北斗 / GPS 双模锁定卫星</span>
          <span class="sig-status text-success">信号质量 100% 优</span>
        </div>
        <div class="stat-main-row">
          <div class="stat-num num-mono text-primary">
            {{ satelliteCount ?? '--' }} <small>颗有效锁定</small>
          </div>
          <!-- 4格信号柱 -->
          <div class="signal-bars">
            <span class="s-bar b1 active"></span>
            <span class="s-bar b2 active"></span>
            <span class="s-bar b3 active"></span>
            <span class="s-bar b4 active"></span>
          </div>
        </div>
        <div class="sat-badges">
          <div class="sat-tag bd">
            <span class="sat-dot bd-dot"></span>
            <span class="sat-name">北斗/GPS 总星数</span>
            <span class="sat-count num-mono">{{ satelliteCount != null ? `${satelliteCount}` : '--' }}</span>
          </div>
          <div class="sat-tag gps">
            <span class="sat-dot gps-dot"></span>
            <span class="sat-name">链路状态</span>
            <span class="sat-count num-mono">{{ masterOnline ? '锁定正常' : '未连接' }}</span>
          </div>
        </div>
      </div>

      <!-- 3. 子钟网络在线情况 -->
      <div class="kpi-block stat-item">
        <div class="block-head-row">
          <span class="block-lbl">全场子钟网络在线情况</span>
          <span class="online-rate-pill num-mono">在线率 {{ onlineRate }}%</span>
        </div>
        <div class="stat-main-row">
          <div class="stat-num num-mono">
            <span class="text-success font-bold">{{ normalCount }}</span> <small>台正常</small>
            <span class="divider-slash">/</span>
            <span class="text-danger font-bold">{{ faultCount }}</span> <small>台异常</small>
          </div>
        </div>
        <div class="sub-clocks-type-pills">
          <span class="type-pill">数字单面 <b>{{ countByType('DS') }}</b></span>
          <span class="type-pill">数字双面 <b>{{ countByType('DD') }}</b></span>
          <span class="type-pill">倒计时 <b>{{ countByType('DC') }}</b></span>
          <span class="type-pill">机械时钟 <b>{{ countByType('M') }}</b></span>
        </div>
      </div>
    </div>

    <!-- 中下布局：左侧全场子钟阵列与运维管理，右侧历史漂移与真实UDP通信协议流水 -->
    <div class="clock-main-grid">
      <!-- 左侧：全场子钟分类网格阵列 -->
      <div class="sub-clocks-panel glass-panel">
        <!-- 面板顶栏与综合过滤栏 -->
        <div class="panel-header">
          <div class="header-title">
            <div class="title-row">
              <span class="title-txt">全场馆分布式子钟监控矩阵</span>
              <span class="title-tag num-mono">SUB-CLOCKS MATRIX</span>
              <span class="device-total-count">共 {{ filteredClocks.length }}/{{ subClocks.length }} 台设备</span>
            </div>
            <span class="panel-subtitle">台账数据实时读取自 MySQL（clock_view），支持按楼栋、楼层与总线链路检索及调控</span>
          </div>
          <div class="top-quick-actions">
            <button class="btn-mini-action" @click="refreshSubClocks">
              <span>🔄 刷新台账</span>
            </button>
            <button class="btn-mini-action" @click="openBroadcastTimingModal">
              <span>⏱ 赛事倒计时广播</span>
            </button>
            <button class="btn-mini-action" @click="toggleAllScreens">
              <span>💡 {{ isAllScreenOn ? '一键全屏熄屏' : '一键全屏点亮' }}</span>
            </button>
          </div>
        </div>

        <!-- 多维筛选与搜索工具条 -->
        <div class="filter-toolbar">
          <div class="filter-item">
            <span class="filter-lbl">场馆楼栋:</span>
            <el-select v-model="selectedBuild" size="small" class="filter-select" placeholder="全部楼栋">
              <el-option label="全部楼栋" value="ALL" />
              <el-option v-for="b in availableBuilds" :key="b" :label="b" :value="b" />
            </el-select>
          </div>

          <div class="filter-item">
            <span class="filter-lbl">楼层区域:</span>
            <el-select v-model="selectedFloor" size="small" class="filter-select" placeholder="全部楼层">
              <el-option label="全部楼层" value="ALL" />
              <el-option v-for="f in availableFloors" :key="f" :label="f" :value="f" />
            </el-select>
          </div>

          <div class="filter-item">
            <span class="filter-lbl">运行状态:</span>
            <el-select v-model="selectedStatus" size="small" class="filter-select" placeholder="全部状态">
              <el-option label="全部状态" value="ALL" />
              <el-option label="同步正常" value="正常" />
              <el-option label="偏差告警/离线" value="离线" />
            </el-select>
          </div>

          <div class="filter-item search-item">
            <el-input v-model="searchKeyword" size="small" placeholder="搜索房间、屏号(MAC)、型号..." clearable
              class="filter-search-input">
              <template #prefix>🔍</template>
            </el-input>
          </div>
        </div>

        <!-- 未配置 MySQL 空状态引导 -->
        <div v-if="!mysqlConfigured && subClocks.length === 0" class="clock-empty-guide">
          <div class="empty-guide-title">尚未配置子钟台账数据库</div>
          <div class="empty-guide-desc">请点击右上角【⚙ 对接设置】填写 MySQL 主机地址与只读账号（charset: gb18030），测试连通后即可加载真实子钟列表。</div>
          <button class="btn-header-action btn-header-primary" @click="openClockSettingsModal">⚙ 立即配置对接参数</button>
        </div>
        <div v-else-if="filteredClocks.length === 0" class="clock-empty-guide">
          <div class="empty-guide-title">暂无符合条件的子钟设备</div>
          <div class="empty-guide-desc">{{ mysqlLoadError ? `台账读取异常：${mysqlLoadError}` : '当前筛选条件下无子钟记录，请调整筛选条件或刷新台账。' }}
          </div>
        </div>

        <!-- 子钟卡片网格 -->
        <div v-else class="clocks-cards-grid">
          <div v-for="clk in filteredClocks" :key="clk.mac"
            :class="[
              'sub-clock-card',
              clk.status === '正常' ? 'normal' : 'fault',
              clk.status === '正常' ? (clk.screenPower === false ? 'is-screen-off' : 'is-screen-on') : ''
            ]">
            <!-- 1. 卡片顶栏：屏号、房间名称与实时状态 -->
            <div class="clk-card-header">
              <div class="code-box">
                <span class="clk-mac-badge num-mono">#{{ String(clk.mac).padStart(2, '0') }}</span>
                <span class="clk-loc-summary" :title="`${clk.build} · ${clk.floor} · ${clk.room}`">
                  {{ clk.room }}
                </span>
              </div>
              <span :class="['clk-status-badge', clk.status === '正常' ? 'normal' : 'fault']">
                <span class="badge-dot"></span>
                {{ clk.status === '正常' ? '在线正常' : (clk.status || '设备离线') }}
              </span>
            </div>

            <!-- 2. 空间归属与硬件型号规格标签 -->
            <div class="clk-location-details">
              <span class="loc-tag">🏢 {{ formatLoc(clk.build, '栋') }} · {{ formatLoc(clk.floor, '层') }}</span>
              <span class="loc-tag tag-model num-mono" :title="MODEL_DICT[clk.model]?.name || clk.model">{{ clk.model
              }}</span>
              <span class="loc-tag tag-link">{{ LINK_DICT[clk.link] || `链路${clk.link}` }}</span>
            </div>

            <!-- 4. 参数摘要行 (全部源自 MySQL clock_view 真实字段) -->
            <div class="clk-params-row num-mono">
              <div class="param-pill" :title="clk.brightRaw ? `时段策略: ${clk.brightRaw}` : ''">
                <span class="p-lbl">💡 亮度</span>
                <span class="p-val font-bold">{{ formatBright(clk.bright) }}</span>
              </div>
              <div class="param-pill-divider"></div>
              <div class="param-pill">
                <span class="p-lbl">🔊 音量</span>
                <span class="p-val font-bold">{{ clk.volume === 0 ? '静音' : `${clk.volume}档` }}</span>
              </div>
              <div class="param-pill-divider"></div>
              <div class="param-pill param-pill-time" :title="`最后更新时间: ${formatUpdateAt(clk.update_at)}`">
                <span class="p-lbl">更新时间：</span>
                <span class="p-val text-primary">{{ formatUpdateAt(clk.update_at) }}</span>
              </div>
            </div>

            <!-- 5. 故障警告提示条 (若有异常) -->
            <div v-if="clk.faultReason" class="clk-fault-box">
              <span class="fault-icon">⚠️</span>
              <span class="fault-txt">{{ clk.faultReason }}</span>
            </div>

            <!-- 6. 卡片底层操作工具栏 -->
            <div class="clk-card-actions">
              <button class="card-btn btn-control" @click="openClockControl(clk)" title="调控该子钟模式、参数或下发赛事计时">
                <span>⚙️ 调控/计时</span>
              </button>
              <button class="card-btn btn-power" @click="toggleClockScreen(clk)"
                :title="clk.screenPower ? '熄灭屏幕节能' : '点亮显示屏'">
                <span>{{ clk.screenPower ? '💡 熄屏' : '💡 亮屏' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：时钟漂移分析 与 真实通信协议流水 (双 Tab 切换) -->
      <div class="clock-sync-logs-panel glass-panel">
        <!-- 面板顶栏带 Tab 切换 -->
        <div class="panel-header-tabbed">
          <div class="tab-switch-group">
            <button :class="['tab-btn', { active: rightActiveTab === 'drift' }]" @click="rightActiveTab = 'drift'">
              <span>📊 漂移分析与审计</span>
            </button>
            <button :class="['tab-btn', { active: rightActiveTab === 'protocol' }]"
              @click="rightActiveTab = 'protocol'">
              <span>⚡ UDP 通信报文</span>
            </button>
          </div>
        </div>

        <!-- Tab 1: 漂移趋势与授时记录 -->
        <div v-show="rightActiveTab === 'drift'" class="tab-content-wrap">
          <!-- 漂移对比直方图 (具备 50ms 阈值准线) -->
          <div class="drift-bar-chart">
            <div class="chart-caption-row">
              <span class="chart-caption">各子钟时间漂移对比</span>
              <span class="chart-unit num-mono">基准规范: ≤50ms</span>
            </div>

            <div class="bars-container">
              <div class="threshold-guide-line"></div>
              <span class="threshold-corner-lbl num-mono">--- ≤50ms 规范线</span>

              <div v-for="clk in subClocks.slice(0, 8)" :key="clk.mac" class="bar-col">
                <div class="bar-fill-wrap" :title="`#${clk.mac} ${clk.room}: ${clk.driftMs ?? '--'}ms`">
                  <div :class="['bar-pillar', { alert: (clk.driftMs ?? 0) > 100 }]"
                    :style="{ height: calcBarHeight(clk.driftMs) + '%' }">
                    <span class="pillar-glow"></span>
                  </div>
                </div>
                <span class="bar-val num-mono" :class="{ 'text-danger': (clk.driftMs ?? 0) > 100 }">
                  {{ clk.driftMs ?? '--' }}
                </span>
                <span class="bar-lbl num-mono">#{{ clk.mac }}</span>
              </div>
            </div>
          </div>

          <!-- 平台与母钟时差采样流水 -->
          <div class="sync-logs-wrap">
            <div class="logs-header-row">
              <div class="logs-header-left">
                <span class="logs-header">平台与母钟时差采样流水</span>
                <span class="pulse-dot-mini"></span>
              </div>
              <span class="logs-count-badge num-mono">{{ syncLogs.length }} 条记录</span>
            </div>
            <div class="logs-list-scroll">
              <div v-for="(log, idx) in syncLogs" :key="idx" class="log-item-card">
                <div class="log-top-meta">
                  <div class="log-time-group">
                    <span class="log-bullet"></span>
                    <span class="log-time num-mono">{{ log.time }}</span>
                  </div>
                  <div class="log-badges-group">
                    <span class="log-sat-pill num-mono">🛰️ {{ log.sat }} 颗星</span>
                    <span class="log-status-badge" :class="log.type || 'ok'">{{ log.tag || '极优' }}</span>
                  </div>
                </div>
                <div class="log-bottom-desc">
                  <span class="log-res-code num-mono">{{ log.res }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 2: 真实通信协议报文流水 (Hex Debugger) -->
        <div v-show="rightActiveTab === 'protocol'" class="tab-content-wrap protocol-log-wrap">
          <div class="protocol-log-header">
            <span class="proto-title">母钟与子钟通信报文实时交互流</span>
            <button class="btn-clear-logs" @click="protocolLogs = []">清空日志</button>
          </div>
          <div class="protocol-logs-scroll">
            <div v-for="(pLog, pIdx) in protocolLogs" :key="pIdx" :class="['proto-item', pLog.direction]">
              <div class="proto-meta-row num-mono">
                <span :class="['proto-dir-tag', pLog.direction]">{{ pLog.direction === 'TX' ? '▲ 上位机发送' : '▼ 母钟应答'
                }}</span>
                <span class="proto-time">{{ pLog.time }}</span>
                <span class="proto-cmd-name">{{ pLog.cmdName }}</span>
              </div>
              <div class="proto-raw-hex num-mono">{{ pLog.rawHex }}</div>
              <div class="proto-desc">{{ pLog.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- 对话框 2：子钟参数调控与赛事倒计时 Dialog                     -->
    <!-- ============================================================ -->
    <el-dialog v-model="showControlModal" :title="`子钟调控中心 · #${selectedClock?.mac} ${selectedClock?.room}`"
      width="680px" class="custom-glass-dialog" destroy-on-close>
      <div v-if="selectedClock" class="control-dialog-body">
        <div class="clock-target-banner">
          <div class="target-info-row">
            <span class="target-title font-bold">{{ selectedClock.build }} · {{ selectedClock.floor }} · {{
              selectedClock.room }}</span>
            <span class="target-model-pill num-mono">{{ selectedClock.model }} ({{ MODEL_DICT[selectedClock.model]?.name
            }})</span>
          </div>
          <div class="target-meta-row num-mono">
            <span>物理链路: {{ LINK_DICT[selectedClock.link] }}</span>
            <span>屏号地址: 0x{{ Number(selectedClock.mac).toString(16).toUpperCase().padStart(2, '0') }} ({{
              selectedClock.mac
            }})</span>
            <span>当前模式: {{ selectedClock.mode === 'COUNTDOWN' ? '赛事倒计时' : (selectedClock.mode === 'COUNTUP' ? '正计时' :
              '标准时钟走时') }}</span>
          </div>
        </div>

        <el-tabs v-model="controlTab" class="control-tabs">
          <!-- Tab 1: 赛事正/倒计时控制 (功能码 0x01 / 0x0E / 0x0F) -->
          <el-tab-pane label="⏱ 赛事计时控制" name="timing">
            <div class="timing-control-pane">
              <div class="mode-select-row">
                <span class="pane-lbl">运行模式切换:</span>
                <el-radio-group v-model="timingForm.mode" size="default">
                  <el-radio-button label="CLOCK">恢复标准时钟走时</el-radio-button>
                  <el-radio-button label="COUNTDOWN">赛事倒计时模式</el-radio-button>
                  <el-radio-button label="COUNTUP">比赛正计时模式</el-radio-button>
                </el-radio-group>
              </div>

              <!-- 倒计时时间设置 -->
              <div v-if="timingForm.mode === 'COUNTDOWN'" class="time-set-box">
                <div class="pane-lbl">设置倒计时目标时长 (时:分:秒):</div>
                <div class="time-pick-row">
                  <div class="time-input-col">
                    <el-input-number v-model="timingForm.hours" :min="0" :max="99" controls-position="right" />
                    <span class="unit-txt">小时</span>
                  </div>
                  <span class="time-colon">:</span>
                  <div class="time-input-col">
                    <el-input-number v-model="timingForm.minutes" :min="0" :max="59" controls-position="right" />
                    <span class="unit-txt">分钟</span>
                  </div>
                  <span class="time-colon">:</span>
                  <div class="time-input-col">
                    <el-input-number v-model="timingForm.seconds" :min="0" :max="59" controls-position="right" />
                    <span class="unit-txt">秒</span>
                  </div>
                </div>

                <!-- 快捷预设按钮 -->
                <div class="preset-btn-row">
                  <span class="preset-lbl">常用赛事预设:</span>
                  <button class="preset-pill" @click="setCountdownPreset(0, 5, 0)">5 分钟</button>
                  <button class="preset-pill" @click="setCountdownPreset(0, 10, 0)">10 分钟</button>
                  <button class="preset-pill" @click="setCountdownPreset(0, 20, 0)">20 分钟 (篮球单节)</button>
                  <button class="preset-pill" @click="setCountdownPreset(0, 45, 0)">45 分钟 (足球半场)</button>
                </div>
              </div>

              <!-- 控制指令下发按钮区 -->
              <div class="timing-action-row">
                <button class="btn-timing-action primary" @click="applyTimingMode(selectedClock, false)">
                  <span>🚀 装载并定点下发 (单钟 0x0F)</span>
                </button>
                <button class="btn-timing-action warning" @click="applyTimingMode(selectedClock, true)">
                  <span>📢 装载并在所属总线全网广播发令 (0x0E)</span>
                </button>
              </div>
            </div>
          </el-tab-pane>

          <!-- Tab 2: 硬件参数与屏幕亮度 (功能码 0x04 / 0x06 / 0x07) -->
          <el-tab-pane label="💡 亮度/音量/屏幕电源" name="params">
            <div class="params-control-pane">
              <div class="param-form-item">
                <span class="item-label">屏幕电源状态 (功能码 0x04):</span>
                <el-switch v-model="selectedClock.screenPower" active-text="点亮开启" inactive-text="休眠熄屏"
                  @change="onScreenSwitchChange(selectedClock)" />
              </div>

              <div class="param-form-item">
                <span class="item-label">屏幕显示亮度 (功能码 0x06):</span>
                <div class="slider-with-val" style="width: 320px">
                  <el-slider v-model="selectedClock.bright" :min="1" :max="5" :step="1" show-stops
                    @change="onBrightChange(selectedClock)" />
                  <span class="slider-val-txt num-mono">{{ selectedClock.bright }} 档</span>
                </div>
              </div>

              <div class="param-form-item">
                <span class="item-label">提示音开关与音量 (功能码 0x07):</span>
                <div class="slider-with-val" style="width: 320px">
                  <el-slider v-model="selectedClock.volume" :min="0" :max="10" :step="1" show-stops
                    @change="onVolumeChange(selectedClock)" />
                  <span class="slider-val-txt num-mono">{{ formatVolume(selectedClock.volume) }}</span>
                </div>
              </div>

              <div class="param-footer-hint">
                <span>💡 每次拖动调节将自动向主母钟下发对应的 <code>0xDD</code> 报文，并可在右侧报文流视窗中实时比对十六进制帧。</span>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showControlModal = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- ============================================================ -->
    <!-- 对话框 3：全场赛事倒计时广播 Dialog                            -->
    <!-- ============================================================ -->
    <el-dialog v-model="showBroadcastModal" title="全馆赛事倒计时统一广播发布" width="560px" class="custom-glass-dialog"
      destroy-on-close>
      <div class="dialog-form-wrap">
        <div class="dialog-tips-box warning-box">
          <span>⚠️ 此操作将向所有 485 总线和 PowerBus 总线广播 <code>0x0E</code> 指令包，将所选场馆内的所有比赛计时钟同步切换至倒计时发令状态！</span>
        </div>
        <div class="time-set-box" style="margin-top: 14px;">
          <div class="pane-lbl">统一广播倒计时时长:</div>
          <div class="time-pick-row">
            <div class="time-input-col">
              <el-input-number v-model="broadcastTime.hours" :min="0" :max="99" controls-position="right" />
              <span class="unit-txt">小时</span>
            </div>
            <span class="time-colon">:</span>
            <div class="time-input-col">
              <el-input-number v-model="broadcastTime.minutes" :min="0" :max="59" controls-position="right" />
              <span class="unit-txt">分钟</span>
            </div>
            <span class="time-colon">:</span>
            <div class="time-input-col">
              <el-input-number v-model="broadcastTime.seconds" :min="0" :max="59" controls-position="right" />
              <span class="unit-txt">秒</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBroadcastModal = false">取消</el-button>
          <el-button type="warning" @click="executeBroadcastCountdown">广播发布全馆倒计时</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 弹窗 4: 时钟系统对接设置 (母钟 UDP + 子钟 MySQL) -->
    <el-dialog v-model="showSettingsModal" title="时钟系统对接设置" class="clock-settings-dialog" width="min(820px, 94vw)"
      align-center destroy-on-close>
      <el-form :model="settingsForm" label-position="top" size="default" class="clock-settings-form">
        <div class="settings-group-card">
          <div class="settings-section-title">① 母钟 UDP 协议参数（TimeMaster 0xDD/0xEE）</div>
          <div class="settings-grid settings-grid-2">
            <el-form-item label="母钟 IP 地址">
              <el-input v-model="settingsForm.masterIp" placeholder="192.168.7.2" />
            </el-form-item>
            <el-form-item label="母钟端口">
              <el-input-number v-model="settingsForm.masterPort" :min="1" :max="65535" controls-position="right"
                style="width:100%" />
            </el-form-item>
          </div>
        </div>

        <div class="settings-group-card">
          <div class="settings-section-title">② 子钟台账 MySQL 参数（只读 clock_view）</div>
          <div class="settings-grid settings-grid-2">
            <el-form-item label="MySQL 主机">
              <el-input v-model="settingsForm.mysqlHost" placeholder="如 192.168.7.10" />
            </el-form-item>
            <el-form-item label="端口">
              <el-input-number v-model="settingsForm.mysqlPort" :min="1" :max="65535" controls-position="right"
                style="width:100%" />
            </el-form-item>
            <el-form-item label="数据库名">
              <el-input v-model="settingsForm.mysqlDatabase" placeholder="clock" />
            </el-form-item>
            <el-form-item label="视图名称">
              <el-input v-model="settingsForm.mysqlView" placeholder="clock_view" />
            </el-form-item>
            <el-form-item label="只读账号">
              <el-input v-model="settingsForm.mysqlUser" placeholder="建议只读 SELECT 账号" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="settingsForm.mysqlPassword" type="password" show-password
                :placeholder="hasMysqlPassword ? '已加密保存，留空则不修改' : '请输入密码'" />
            </el-form-item>
          </div>
        </div>
      </el-form>

      <div v-if="settingsTestResult" class="settings-test-box">
        <div>
          <b>UDP 母钟探活：</b>
          <span :style="{ color: settingsTestResult.udp?.reachable ? '#16a34a' : '#dc2626' }">
            {{ settingsTestResult.udp?.reachable ? `在线 (${settingsTestResult.udp.latency_ms}ms · 卫星数
            ${settingsTestResult.udp.satellite_count ?? '--'})` : `失败 (${settingsTestResult.udp?.error || '超时'})` }}
          </span>
        </div>
        <div>
          <b>MySQL 台账：</b>
          <span
            :style="{ color: settingsTestResult.mysql?.reachable ? '#16a34a' : (settingsTestResult.mysql?.skipped ? '#64748b' : '#dc2626') }">
            {{ settingsTestResult.mysql?.reachable ? `连通成功 (${settingsTestResult.mysql.count} 条子钟记录)` :
              (settingsTestResult.mysql?.error || '未测试') }}
          </span>
        </div>
      </div>

      <template #footer>
        <div class="settings-dialog-footer">
          <el-button @click="testClockSettings" :loading="settingsTesting">测试连接</el-button>
          <div class="footer-right-actions">
            <el-button @click="showSettingsModal = false">取消</el-button>
            <el-button type="primary" @click="saveClockSettings" :loading="settingsSaving">保存并刷新台账</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>

const formatVolume = (vol) => {
  if (vol === 0 || vol === '0') return '静音'
  return `${vol} 档`
}

const formatLoc = (val, suffix) => {
  const s = String(val ?? '').trim()
  if (!s) return '--'
  return /^\d+$/.test(s) ? `${s}${suffix}` : s
}

const formatUpdateAt = (val, short = false) => {
  const s = String(val ?? '').trim()
  if (!s) return '--'
  const clean = s.replace('T', ' ').slice(0, 19)
  return short && clean.length >= 16 ? clean.slice(5, 16) : clean
}

const formatBright = (val) => {
  if (val === null || val === undefined || val === '') return '--'
  if (typeof val === 'number' && !Number.isNaN(val)) return `${val}档`
  const s = String(val).trim()
  if (/^\d+$/.test(s)) return `${s}档`
  const segs = [...s.matchAll(/(\d{2}:\d{2})-(\d{2}:\d{2})->(\d+)/g)]
  if (segs.length) {
    const now = new Date()
    const hhmm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
    for (const [, startHm, endHm, lvl] of segs) {
      if (startHm <= endHm ? (hhmm >= startHm && hhmm < endHm) : (hhmm >= startHm || hhmm < endHm)) {
        return `${lvl}档`
      }
    }
    return `${segs[0][3]}档`
  }
  const m = s.match(/(\d+)/)
  return m ? `${m[1]}档` : s
}

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/services/api'

// ============================================================================
// 1. 数据字典 (完全对标 标准时钟对接参数资料.md 与 clock_view 视图)
// ============================================================================
const MODEL_DICT = {
  DD54: { name: '5寸4位双面钟', desc: 'LED双面吊挂，走时' },
  DD56: { name: '5寸6位双面钟', desc: 'LED双面吊挂，时分秒/赛事计时' },
  DD34: { name: '3寸4位双面钟', desc: '走廊通道双面吊挂' },
  DD36: { name: '3寸6位双面钟', desc: '走廊通道时分秒双面' },
  DS54: { name: '5寸4位单面钟', desc: '会议室/发布厅壁挂' },
  DS56: { name: '5寸6位单面钟', desc: '指挥中心/转播室壁挂' },
  DS34: { name: '3寸4位单面钟', desc: '更衣室/休息室壁挂' },
  DS36: { name: '3寸6位单面钟', desc: '裁判室/药检室壁挂' },
  DC56: { name: '5寸6位倒计时钟', desc: '裁判席/终点计时倒正计时' },
  DC36: { name: '3寸6位倒计时钟', desc: '技术代表席/热身倒正计时' },
  DCS56: { name: '5寸6位单面倒计时钟', desc: '单面壁挂/赛事正倒计时' },
  DCD56: { name: '5寸6位双面倒计时钟', desc: '双面吊挂/赛事正倒计时' },
  MC400: { name: '400mm机械圆盘钟', desc: 'VIP厅/大堂机械指针式' },
  MR400: { name: '400mm机械方盘钟', desc: '陈列厅/贵宾室机械指针式' }
}

const LINK_DICT = {
  1: 'RS-485 第1路',
  2: 'RS-485 第2路',
  3: 'RS-485 第3路',
  4: 'RS-485 第4路',
  5: 'PowerBus 第1路',
  6: 'PowerBus 第2路',
  7: '以太网 (ETH)',
  8: 'LoRa 无线通信'
}

// 主母钟硬件配置与实时状态
const masterClockConfig = ref({
  ip: '192.168.7.2',
  port: 123,
  timeZone: 8,
  timeZoneStr: 'UTC+08:00 (北京时间)'
})

const masterOnline = ref(false)
const wsConnected = ref(false)
const mysqlConfigured = ref(false)
const mysqlLoadError = ref('')
const hasMysqlPassword = ref(false)

const beijingTimeStr = ref('--:--:--')
const millisStr = ref('000')
const dateStr = ref('等待母钟对时...')
const satelliteCount = ref(null)
const isCalibrating = ref(false)
const rightActiveTab = ref('drift') // 'drift' | 'protocol'
const isAllScreenOn = ref(true)

let clockTimer = null
let subclockPollTimer = null
let clockWs = null
let wsReconnectTimer = null
let wsPingTimer = null
let wsManualClosed = false
let masterTimeBaseMs = null
let masterSyncPerfMs = 0
let lastMasterUnixS = null

// ============================================================================
// 2. 子钟台账列表（完全源自后端 MySQL clock_view，不使用假数据）
// ============================================================================
const CLOCK_CACHE_KEY = 'stadium_clock_last_real_cache_v1'
const subClocks = ref([])

const saveLastRealCache = (items) => {
  try {
    localStorage.setItem(CLOCK_CACHE_KEY, JSON.stringify({ items, cachedAt: Date.now() }))
  } catch {
    // ignore
  }
}

const loadLastRealCache = () => {
  try {
    const raw = localStorage.getItem(CLOCK_CACHE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed?.items)) {
      return parsed.items.map(c => ({ ...c, status: '离线', faultReason: '台账缓存（当前离线）' }))
    }
  } catch {
    // ignore
  }
  return []
}

// 统计数据
const normalCount = computed(() => subClocks.value.filter(c => c.status === '正常').length)
const faultCount = computed(() => subClocks.value.filter(c => c.status !== '正常').length)
const onlineRate = computed(() => {
  if (subClocks.value.length === 0) return 0
  return Math.round((normalCount.value / subClocks.value.length) * 1000) / 10
})

const countByType = (prefix) => {
  return subClocks.value.filter(c => c.model.startsWith(prefix)).length
}

// 多维筛选选项列表
const availableBuilds = computed(() => Array.from(new Set(subClocks.value.map(c => c.build))).filter(Boolean))
const availableFloors = computed(() => Array.from(new Set(subClocks.value.map(c => c.floor))).filter(Boolean))

const selectedBuild = ref('ALL')
const selectedFloor = ref('ALL')
const selectedStatus = ref('ALL')
const searchKeyword = ref('')

const filteredClocks = computed(() => {
  return subClocks.value.filter(clk => {
    if (selectedBuild.value !== 'ALL' && clk.build !== selectedBuild.value) return false
    if (selectedFloor.value !== 'ALL' && clk.floor !== selectedFloor.value) return false
    if (selectedStatus.value !== 'ALL' && clk.status !== selectedStatus.value) return false
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.trim().toLowerCase()
      const matchRoom = clk.room && clk.room.toLowerCase().includes(kw)
      const matchMac = String(clk.mac).includes(kw) || (`#${clk.mac}`).includes(kw)
      const matchModel = clk.model && clk.model.toLowerCase().includes(kw)
      if (!matchRoom && !matchMac && !matchModel) return false
    }
    return true
  })
})

// ============================================================================
// 3. 真实通信日志、母钟基准走时与 WebSocket 实时推送
// ============================================================================
const syncLogs = ref([])
const protocolLogs = ref([])

const WEEK_DAYS = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']

const setMasterClockBase = (unixS) => {
  if (!unixS) return
  const numS = Number(unixS)
  if (numS === lastMasterUnixS) return
  lastMasterUnixS = numS
  masterTimeBaseMs = numS * 1000
  masterSyncPerfMs = performance.now()
}

const updateClock = () => {
  if (masterTimeBaseMs == null) {
    beijingTimeStr.value = '--:--:--'
    millisStr.value = '---'
    dateStr.value = '未连接母钟 · 请在【⚙ 对接设置】配置检查母钟参数和状态'
    return
  }
  const now = new Date(masterTimeBaseMs + (performance.now() - masterSyncPerfMs))
  const hours = now.getHours().toString().padStart(2, '0')
  const minutes = now.getMinutes().toString().padStart(2, '0')
  const seconds = now.getSeconds().toString().padStart(2, '0')
  const millis = now.getMilliseconds().toString().padStart(3, '0')

  beijingTimeStr.value = `${hours}:${minutes}:${seconds}`
  millisStr.value = millis
  dateStr.value = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 ${WEEK_DAYS[now.getDay()]}`
}

const showSettingsModal = ref(false)
const settingsTesting = ref(false)
const settingsSaving = ref(false)
const settingsTestResult = ref(null)
const settingsForm = ref({
  masterIp: '192.168.7.2',
  masterPort: 123,
  localPort: 0,
  timeoutS: 4.0,
  retries: 2,
  timezone: 8,
  mysqlHost: '',
  mysqlPort: 3306,
  mysqlDatabase: 'clock',
  mysqlView: 'clock_view',
  mysqlUser: '',
  mysqlPassword: '',
  keepExistingPassword: true,
})

const loadClockSettings = async () => {
  try {
    const cfg = await api.clockSettings()
    if (!cfg || cfg.__offline) return
    hasMysqlPassword.value = !!cfg.hasMysqlPassword
    mysqlConfigured.value = !!(cfg.mysqlHost && cfg.mysqlHost.trim())
    masterClockConfig.value = {
      ip: cfg.masterIp || '192.168.7.2',
      port: cfg.masterPort || 123,
      timeZone: cfg.timezone ?? 8,
      timeZoneStr: `UTC${(cfg.timezone ?? 8) >= 0 ? '+' : ''}${String(cfg.timezone ?? 8).padStart(2, '0')}:00`,
    }
    settingsForm.value = {
      masterIp: cfg.masterIp || '192.168.7.2',
      masterPort: cfg.masterPort || 123,
      localPort: cfg.localPort ?? 0,
      timeoutS: cfg.timeoutS ?? 4.0,
      retries: cfg.retries ?? 2,
      timezone: cfg.timezone ?? 8,
      mysqlHost: cfg.mysqlHost || '',
      mysqlPort: cfg.mysqlPort || 3306,
      mysqlDatabase: cfg.mysqlDatabase || 'clock',
      mysqlView: cfg.mysqlView || 'clock_view',
      mysqlUser: cfg.mysqlUser || '',
      mysqlPassword: '',
      keepExistingPassword: true,
    }
  } catch {
    // 忽略未登录或网络错误
  }
}

const openClockSettingsModal = async () => {
  settingsTestResult.value = null
  await loadClockSettings()
  showSettingsModal.value = true
}

const testClockSettings = async () => {
  settingsTesting.value = true
  settingsTestResult.value = null
  try {
    settingsTestResult.value = await api.testClockSettings(settingsForm.value)
  } catch (e) {
    ElMessage.error('测试失败: ' + (e?.message || e))
  } finally {
    settingsTesting.value = false
  }
}

const saveClockSettings = async () => {
  settingsSaving.value = true
  try {
    await api.saveClockSettings(settingsForm.value)
    ElMessage.success('时钟对接配置已保存')
    showSettingsModal.value = false
    await loadClockSettings()
    await loadClockStatus()
    await loadSubClocks()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e?.message || e))
  } finally {
    settingsSaving.value = false
  }
}

const loadClockStatus = async () => {
  try {
    const st = await api.clockStatus()
    if (!st || st.__offline) return
    masterOnline.value = !!st.online
    mysqlConfigured.value = !!st.mysqlConfigured
    if (st.satelliteCount != null) satelliteCount.value = st.satelliteCount
    if (st.masterUnixS) setMasterClockBase(st.masterUnixS)
    if (Array.isArray(st.protocolLogs)) protocolLogs.value = st.protocolLogs
    if (Array.isArray(st.driftHistory) && st.driftHistory.length) {
      syncLogs.value = st.driftHistory.slice().reverse().map(d => ({
        time: d.time,
        sat: d.sat ?? '--',
        res: `服务器-母钟时差 ${d.driftMs} ms`,
        tag: Math.abs(d.driftMs) <= 50 ? '极优' : '偏差',
        type: Math.abs(d.driftMs) <= 50 ? 'ok' : 'alert',
      }))
    }
  } catch {
    masterOnline.value = false
  }
}

const loadSubClocks = async () => {
  try {
    const res = await api.clockSubclocks()
    if (!res || res.__offline) return
    mysqlConfigured.value = !!res.configured
    if (!res.configured) {
      mysqlLoadError.value = ''
      subClocks.value = []
      return
    }
    if (res.online) {
      mysqlLoadError.value = ''
      subClocks.value = res.items || []
      saveLastRealCache(subClocks.value)
    } else {
      mysqlLoadError.value = res.error || 'MySQL 暂时不可达'
      subClocks.value = (res.items && res.items.length) ? res.items : loadLastRealCache()
    }
  } catch (e) {
    mysqlLoadError.value = e?.message || '台账加载失败'
  }
}

const connectClockWs = () => {
  if (wsManualClosed) return
  if (clockWs && (clockWs.readyState === WebSocket.OPEN || clockWs.readyState === WebSocket.CONNECTING)) return
  const token = localStorage.getItem('venue_access_token')
  if (!token) return
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  try {
    clockWs = new WebSocket(`${proto}//${window.location.host}/api/clock/ws?token=${encodeURIComponent(token)}`)
  } catch {
    return
  }
  clockWs.onopen = () => {
    wsConnected.value = true
    if (wsPingTimer) clearInterval(wsPingTimer)
    wsPingTimer = setInterval(() => {
      if (clockWs && clockWs.readyState === WebSocket.OPEN) {
        clockWs.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
  }
  clockWs.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data)
      if (!msg) return
      if (msg.type === 'clock_status') {
        masterOnline.value = !!msg.online
        if (msg.satelliteCount != null) satelliteCount.value = msg.satelliteCount
        if (msg.masterUnixS) setMasterClockBase(msg.masterUnixS)
      } else if (msg.type === 'clock_log' && msg.log) {
        protocolLogs.value.unshift(msg.log)
        if (protocolLogs.value.length > 60) protocolLogs.value.pop()
      } else if (msg.type === 'clock_event' && msg.event) {
        if (msg.log) {
          protocolLogs.value.unshift(msg.log)
          if (protocolLogs.value.length > 60) protocolLogs.value.pop()
        }
        if (msg.event.type === 'satellite_change') {
          satelliteCount.value = msg.event.satellite_count
        } else if (msg.event.type === 'subclock_fault') {
          const target = subClocks.value.find(c => c.mac === msg.event.mac)
          if (target) {
            target.status = msg.event.fault ? '离线' : '正常'
            target.faultReason = msg.event.fault ? `母钟主动上报故障 (总线 ${msg.event.bus})` : ''
          }
        }
      }
    } catch {
      // ignore
    }
  }
  clockWs.onclose = () => {
    wsConnected.value = false
    if (wsPingTimer) { clearInterval(wsPingTimer); wsPingTimer = null }
    clockWs = null
    if (!wsManualClosed && !wsReconnectTimer) {
      wsReconnectTimer = setTimeout(() => {
        wsReconnectTimer = null
        connectClockWs()
      }, 3000)
    }
  }
  clockWs.onerror = () => {
    wsConnected.value = false
  }
}

const disconnectClockWs = () => {
  wsManualClosed = true
  if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null }
  if (wsPingTimer) { clearInterval(wsPingTimer); wsPingTimer = null }
  if (clockWs) { try { clockWs.close() } catch { } clockWs = null }
  wsConnected.value = false
}

onMounted(async () => {
  updateClock()
  clockTimer = setInterval(updateClock, 50)
  wsManualClosed = false
  await loadClockSettings()
  await loadClockStatus()
  await loadSubClocks()
  connectClockWs()
  subclockPollTimer = setInterval(() => {
    if (mysqlConfigured.value) loadSubClocks()
  }, 60000)
})

onUnmounted(() => {
  disconnectClockWs()
  if (clockTimer) clearInterval(clockTimer)
  if (subclockPollTimer) clearInterval(subclockPollTimer)
})

const calcBarHeight = (ms) => {
  if (ms == null || isNaN(ms)) return 8
  if (ms <= 10) return Math.max(16, ms * 3.8)
  if (ms <= 50) return 38 + ((ms - 10) / 40) * 16
  if (ms <= 200) return 55 + ((ms - 50) / 150) * 20
  return Math.min(100, 80 + Math.min(20, (ms - 200) / 50))
}

// ============================================================================
// 5. 刷新数据库台账 (Read-only MySQL clock_view)
// ============================================================================
const refreshSubClocks = async () => {
  await loadSubClocks()
  if (!mysqlConfigured.value) {
    ElMessage.warning('尚未配置子钟 MySQL 数据库，请先点击【⚙ 对接设置】')
  } else if (mysqlLoadError.value) {
    ElMessage.error(`台账刷新失败: ${mysqlLoadError.value}`)
  } else {
    ElMessage.success(`已从数据库刷新 ${subClocks.value.length} 台子钟台账`)
  }
}

// ============================================================================
// 7. 单钟/全场调控中心与赛事计时联动 (Control Modal)
// ============================================================================
const showControlModal = ref(false)
const selectedClock = ref(null)
const controlTab = ref('timing')

const timingForm = ref({
  mode: 'CLOCK',
  hours: 0,
  minutes: 10,
  seconds: 0
})

const openClockControl = (clk) => {
  selectedClock.value = clk
  timingForm.value.mode = clk.mode || 'CLOCK'
  showControlModal.value = true
}

const setCountdownPreset = (h, m, s) => {
  timingForm.value.hours = h
  timingForm.value.minutes = m
  timingForm.value.seconds = s
}

const applyTimingMode = async (clk, isBroadcast) => {
  let modeCode = 0x03
  let desc = '恢复标准走时'
  if (timingForm.value.mode === 'COUNTDOWN') {
    modeCode = 0x02
    desc = `倒计时预设 (${timingForm.value.hours}:${timingForm.value.minutes}:${timingForm.value.seconds})`
  } else if (timingForm.value.mode === 'COUNTUP') {
    modeCode = 0x01
    desc = '正计时模式'
  }

  try {
    await api.clockCommand('set_timer', {
      addr: clk.mac,
      mode: modeCode,
      hours: timingForm.value.hours,
      minutes: timingForm.value.minutes,
      seconds: timingForm.value.seconds,
    })
    if (isBroadcast) {
      const busType = (clk.link >= 1 && clk.link <= 6) ? clk.link : 1
      await api.clockCommand('broadcast_timer', { bus_type: busType, start: modeCode !== 0x03 })
      ElMessage.success(`已向总线广播下发【${desc}】发令指令！`)
    } else {
      await api.clockCommand('point_timer', { addr: clk.mac, start: modeCode !== 0x03 })
      clk.mode = timingForm.value.mode
      ElMessage.success(`子钟 #${clk.mac} 已完成【${desc}】定点发令！`)
    }
    showControlModal.value = false
    await loadClockStatus()
  } catch (e) {
    ElMessage.error(`下发计时指令失败: ${e?.message || e}`)
  }
}

const onScreenSwitchChange = async (clk) => {
  try {
    await api.clockCommand('set_screen', { addr: clk.mac, on: !!clk.screenPower })
    ElMessage.info(`子钟 #${clk.mac} 屏幕已${clk.screenPower ? '点亮开启' : '休眠熄灭'}！`)
  } catch (e) {
    clk.screenPower = !clk.screenPower
    ElMessage.error(`屏幕控制失败: ${e?.message || e}`)
  }
}

const onBrightChange = async (clk) => {
  try {
    const lv = Math.max(1, Math.min(5, Number(clk.bright || 3)))
    await api.clockCommand('set_brightness', {
      addr: clk.mac,
      seg1: [6, 0, 18, 0, lv],
      seg2: [18, 0, 23, 59, lv],
    })
    ElMessage.success(`子钟 #${clk.mac} 亮度已设为 ${lv} 档`)
  } catch (e) {
    ElMessage.error(`亮度调节失败: ${e?.message || e}`)
  }
}

const onVolumeChange = async (clk) => {
  try {
    await api.clockCommand('set_audio', { addr: clk.mac, on: clk.volume > 0, volume: Math.max(1, Number(clk.volume || 8)) })
    ElMessage.success(`子钟 #${clk.mac} 音量已设为 ${clk.volume} 档`)
  } catch (e) {
    ElMessage.error(`音量调节失败: ${e?.message || e}`)
  }
}

const toggleClockScreen = (clk) => {
  clk.screenPower = !clk.screenPower
  onScreenSwitchChange(clk)
}

const toggleAllScreens = async () => {
  if (!subClocks.value.length) {
    ElMessage.warning('当前暂无子钟台账设备，无法执行全场屏幕控制')
    return
  }
  const target = !isAllScreenOn.value
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
  let okCount = 0
  const failedMacs = []
  for (const c of subClocks.value) {
    const addr = Number(c.mac)
    if (!addr || addr < 1 || addr > 254) continue
    let sent = false
    for (let attempt = 0; attempt < 2 && !sent; attempt++) {
      try {
        await api.clockCommand('set_screen', { addr, on: target })
        c.screenPower = target
        okCount++
        sent = true
      } catch {
        if (attempt === 0) await sleep(500)
      }
    }
    if (!sent) failedMacs.push(`#${addr}`)
    // 给母钟 RS-485 / 网络总线留出转发间隔，避免连续群发导致设备忙 (0x11)
    await sleep(350)
  }
  if (okCount > 0) {
    isAllScreenOn.value = target
    ElMessage.success(`已${target ? '点亮' : '熄灭'} ${okCount} 台子钟屏幕${failedMacs.length ? `（失败: ${failedMacs.join(', ')}）` : ''}`)
  } else {
    ElMessage.error('全场屏幕控制失败：子钟未响应')
  }
}

// ============================================================================
// 8. 全场倒计时统一下发弹窗
// ============================================================================
const showBroadcastModal = ref(false)
const broadcastTime = ref({
  hours: 0,
  minutes: 10,
  seconds: 0
})

const openBroadcastTimingModal = () => {
  showBroadcastModal.value = true
}

const executeBroadcastCountdown = async () => {
  if (!subClocks.value.length) {
    ElMessage.warning('当前暂无子钟台账设备，无法下发全场倒计时')
    return
  }
  let okCount = 0
  try {
    for (const c of subClocks.value) {
      if (!c.mac || c.mac < 1 || c.mac > 254) continue
      await api.clockCommand('set_timer', {
        addr: c.mac,
        mode: 2,
        hours: broadcastTime.value.hours,
        minutes: broadcastTime.value.minutes,
        seconds: broadcastTime.value.seconds,
      })
      c.mode = 'COUNTDOWN'
      okCount++
    }
    const has485 = subClocks.value.some(c => c.link >= 1 && c.link <= 4)
    const hasPbus = subClocks.value.some(c => c.link === 5 || c.link === 6)
    if (has485) await api.clockCommand('broadcast_timer', { bus_type: 1, start: true })
    if (hasPbus) await api.clockCommand('broadcast_timer', { bus_type: 5, start: true })
    showBroadcastModal.value = false
    ElMessage.success(`已向 ${okCount} 台子钟下发倒计时并广播发令！`)
    await loadClockStatus()
  } catch (e) {
    ElMessage.error(`广播倒计时失败: ${e?.message || e}`)
  }
}

// 立即触发比对与校准
const calibrateNow = async () => {
  isCalibrating.value = true
  try {
    const res = await api.clockSync()
    if (res?.master_unix_s) setMasterClockBase(res.master_unix_s)
    if (res?.satelliteCount != null) satelliteCount.value = res.satelliteCount
    ElMessage.success(`全网校准已下发！平台偏差 ${res?.drift_ms ?? '--'} ms`)
    await loadClockStatus()
    await loadSubClocks()
  } catch (e) {
    ElMessage.error(`全网对时校准失败: ${e?.message || e}`)
  } finally {
    isCalibrating.value = false
  }
}
</script>


<style scoped>
.clock-empty-guide {
  padding: 36px 20px;
  text-align: center;
  border: 1px dashed var(--do-border);
  border-radius: var(--radius-sm);
  background: rgba(15, 23, 42, 0.02);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.empty-guide-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.empty-guide-desc {
  font-size: 13px;
  color: var(--do-text-secondary);
  max-width: 520px;
  line-height: 1.6;
}

:deep(.clock-settings-dialog) {
  height: auto !important;
  max-height: 86vh !important;
  display: flex !important;
  flex-direction: column !important;
  margin: 0 auto !important;
  border-radius: 10px;
  overflow: hidden;
}

:deep(.clock-settings-dialog .el-dialog__header) {
  padding: 12px 20px !important;
  margin-right: 0;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

:deep(.clock-settings-dialog .el-dialog__body) {
  padding: 12px 20px !important;
  overflow-y: auto !important;
  flex: 0 1 auto !important;
  height: auto !important;
  min-height: 0;
}

:deep(.clock-settings-dialog .el-dialog__footer) {
  padding: 10px 20px !important;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  flex-shrink: 0;
}

.clock-settings-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.settings-group-card {
  padding: 10px 14px 4px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.settings-section-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid var(--do-gold, #2563eb);
}

.settings-grid {
  display: grid;
  gap: 0 14px;
}

.settings-grid-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

:deep(.clock-settings-form .el-form-item) {
  margin-bottom: 8px;
}

:deep(.clock-settings-form .el-form-item__label) {
  padding-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  line-height: 1.3;
}

.settings-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.footer-right-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 520px) {
  .settings-grid-2 {
    grid-template-columns: minmax(0, 1fr);
  }
  .settings-dialog-footer {
    justify-content: flex-end;
  }
}

.settings-test-box {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.clock-monitor-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 玻璃拟态卡片基础 */
.glass-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

/* ============================================================
 * 1. 顶部状态栏 (Title Bar)
 * ============================================================ */
.clock-top-bar {
  padding: 10px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--do-bg-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-box {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  background: rgba(var(--th-accent-rgb), 0.1);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.title-meta-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-text-primary);
  letter-spacing: 0.2px;
}

.device-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--do-text-secondary);
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  padding: 4px 12px;
  border-radius: 4px;
}

.dot-online {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--do-success);
}

.tag-divider {
  color: var(--do-border);
  font-size: 12px;
}

.ip-tag {
  color: var(--do-gold-deep);
  font-weight: 600;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.port-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: var(--do-success);
  font-weight: 500;
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  padding: 4px 12px;
  border-radius: 999px;
}

/* 脉冲雷达点 */
.pulse-radar-dot {
  position: relative;
  width: 8px;
  height: 8px;
}

.radar-core {
  position: absolute;
  top: 0;
  left: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--do-success);
}

.radar-ping {
  position: absolute;
  top: -4px;
  left: -4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(var(--th-success-rgb), 0.35);
  animation: radarPing 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes radarPing {
  0% {
    transform: scale(0.6);
    opacity: 1;
  }

  100% {
    transform: scale(1.6);
    opacity: 0;
  }
}

.btn-calibrate {
  height: 32px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 4px;
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%);
  border: 1px solid var(--do-gold-deep);
  color: #FFFFFF;
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.2);
  transition: all 0.2s;
}

.btn-calibrate:hover {
  background: var(--do-gold-deep);
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35);
}

.btn-inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #FFFFFF;
}

/* ============================================================
 * 2. 顶部标准授时大盘 (3 列典雅仪表盘)
 * ============================================================ */
.master-clock-kpi {
  display: grid;
  grid-template-columns: 2fr 1.15fr 1.15fr;
  gap: 16px;
  padding: 16px 20px;
  border-radius: var(--radius-sm);
}

.kpi-block {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
}

.time-hero {
  border-right: 1px solid var(--do-border-light);
  padding-right: 20px;
}

.block-head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-lbl,
.block-lbl {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--do-text-secondary);
}

.ntsc-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(var(--th-accent-rgb), 0.1);
  color: var(--do-gold-deep);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  border-radius: 4px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 专业数码时钟视窗 (与系统主色调高度契合的典雅浅色微晶凹槽，彻底告别黑色) */
.digital-clock-screen {
  background: linear-gradient(180deg, #F0F6FF 0%, #E6F0FD 100%);
  border: 1.5px solid rgba(37, 99, 235, 0.28);
  border-radius: 6px;
  padding: 10px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: inset 0 1px 3px rgba(37, 99, 235, 0.05);
}

.digital-time-display {
  display: flex;
  align-items: baseline;
  letter-spacing: 2px;
}

.time-main {
  font-size: 38px;
  font-weight: 800;
  color: #0F275A;
}

.time-millis {
  font-size: 20px;
  font-weight: 700;
  color: var(--do-primary, #2563EB);
  margin-left: 2px;
}

.screen-corner-badge {
  font-size: 11px;
  color: var(--do-primary, #2563EB);
  background: rgba(var(--th-accent-rgb), 0.1);
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: 1px;
  font-weight: 700;
}

.date-str-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: var(--do-text-secondary);
}

.date-str.is-disconnected {
  color: var(--do-danger, #dc2626);
  font-weight: 600;
}

.zone-pill {
  font-size: 12px;
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  padding: 2px 8px;
  border-radius: 3px;
  color: var(--do-text-primary);
  font-weight: 600;
}

/* 卫星与子钟卡片通用统计主体 */
.stat-main-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sig-status {
  font-size: 13px;
  font-weight: 600;
}

.stat-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--do-text-primary);
  line-height: 1;
}

.stat-num small {
  font-size: 13.5px;
  font-weight: normal;
  color: var(--do-text-secondary);
  margin-left: 2px;
}

.divider-slash {
  margin: 0 6px;
  color: var(--do-border);
  font-weight: normal;
}

/* 4格信号指示柱 */
.signal-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 20px;
  padding: 0 4px;
}

.s-bar {
  width: 4px;
  background: var(--do-border);
  border-radius: 1px;
}

.s-bar.b1 {
  height: 6px;
}

.s-bar.b2 {
  height: 10px;
}

.s-bar.b3 {
  height: 15px;
}

.s-bar.b4 {
  height: 20px;
}

.s-bar.active {
  background: var(--do-success);
  box-shadow: 0 0 4px rgba(var(--th-success-rgb), 0.4);
}

.sat-badges {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.sat-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 13px;
}

.sat-tag.bd {
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  color: var(--do-success);
}

.sat-tag.gps {
  background: rgba(var(--th-accent-rgb), 0.1);
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
  color: var(--do-gold-deep);
}

.sat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.bd-dot {
  background: var(--do-success);
}

.gps-dot {
  background: var(--do-gold-deep);
}

.sat-name {
  font-weight: 600;
}

.sat-count {
  margin-left: auto;
  font-weight: 700;
}

.online-rate-pill {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  border-radius: 999px;
  color: var(--do-success);
  font-weight: 700;
}

.sub-clocks-type-pills {
  display: flex;
  gap: 6px;
}

.type-pill {
  flex: 1;
  text-align: center;
  font-size: 12.5px;
  color: var(--do-text-secondary);
  background: var(--do-bg-sunken);
  border: 1px solid var(--do-border-light);
  padding: 5px 6px;
  border-radius: 4px;
}

.type-pill b {
  color: var(--do-text-primary);
  font-weight: 700;
  margin-left: 2px;
}

/* ============================================================
 * 3. 中下布局：左侧子钟网格与右侧分析
 * ============================================================ */
.clock-main-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
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
  gap: 3px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-txt {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.title-tag {
  font-size: 11px;
  padding: 1px 6px;
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  border-radius: 3px;
  font-weight: 600;
}

.panel-subtitle {
  font-size: 13px;
  color: var(--do-text-secondary);
}

.filter-radio-group {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--do-text-secondary);
}

.status-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.status-legend .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-legend .dot.normal {
  background: var(--do-success);
  box-shadow: 0 0 4px rgba(var(--th-success-rgb), 0.4);
}

.status-legend .dot.fault {
  background: var(--do-danger);
  box-shadow: 0 0 4px rgba(var(--th-danger-rgb), 0.4);
}

/* ============================================================
 * 4. 子钟分类卡片网格
 * ============================================================ */
.clocks-cards-grid {
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.sub-clock-card {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 6px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.sub-clock-card:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--th-accent-rgb), 0.45);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
}

/* 故障子钟：高优先级警戒样式 */
.sub-clock-card.fault {
  border: 1.5px solid var(--do-danger);
  background: rgba(220, 38, 38, 0.02);
  box-shadow: 0 0 12px rgba(var(--th-danger-rgb), 0.12);
}

.clk-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.code-box {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hardware-chip-icon {
  font-size: 14px;
}

.clk-code {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.clk-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.clk-status-badge.normal {
  background: var(--do-success-bg);
  color: var(--do-success);
  border: 1px solid var(--do-success-border);
}

.clk-status-badge.normal .badge-dot {
  background: var(--do-success);
}

.clk-status-badge.fault {
  background: var(--do-danger-bg);
  color: var(--do-danger);
  border: 1px solid var(--do-danger-border);
}

.clk-status-badge.fault .badge-dot {
  background: var(--do-danger);
  box-shadow: 0 0 4px rgba(var(--th-danger-rgb), 0.6);
}

.clk-type-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--do-text-secondary);
}

.ip-addr {
  font-weight: 600;
  color: var(--do-gold-deep);
}

.clk-location {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--do-text-secondary);
}

.loc-lbl {
  flex-shrink: 0;
}

.loc-val {
  color: var(--do-text-primary);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 嵌入式专业数码时钟液晶屏幕 (与主色调一致的浅色微晶凹槽，告别黑色) */
.clk-time-screen {
  border-radius: 4px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 2px 0;
  transition: all 0.2s;
}

.screen-label {
  font-size: 11px;
  color: var(--do-text-secondary);
  letter-spacing: 0.8px;
  font-weight: 500;
}

.screen-digits {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 2px;
}

.screen-status-led {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

/* 正常子钟：与主色调契合的科技浅蓝微凹底色 + 高对比度深蓝数字 */
.clk-time-screen.normal {
  background: linear-gradient(180deg, #F0F6FF 0%, #E8F2FE 100%);
  border: 1px solid rgba(37, 99, 235, 0.2);
  box-shadow: inset 0 1px 3px rgba(37, 99, 235, 0.05);
}

.clk-time-screen.normal .screen-digits {
  color: #1E3A8A;
}

.clk-time-screen.normal .screen-label {
  color: #3B82F6;
  font-weight: 600;
}

.clk-time-screen.normal .screen-status-led {
  background: var(--do-success);
  box-shadow: 0 0 5px rgba(var(--th-success-rgb), 0.6);
}

/* 故障子钟：警戒浅绯红背景 + 鲜红文字 (完全告别黑色) */
.clk-time-screen.fault {
  background: var(--do-danger-bg);
  border-color: rgba(var(--th-danger-rgb), 0.35);
}

.clk-time-screen.fault .screen-digits {
  color: var(--do-danger);
  text-shadow: 0 1px 1px rgba(var(--th-danger-rgb), 0.15);
}

.clk-time-screen.fault .screen-status-led {
  background: var(--do-danger);
  box-shadow: 0 0 6px rgba(var(--th-danger-rgb), 0.6);
}

.clk-time-screen.fault .screen-label {
  color: var(--do-danger);
  font-weight: 600;
}

.clk-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  margin-top: 2px;
}

.drift-label {
  color: var(--do-text-secondary);
}

.drift-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 18px;
  font-weight: 700;
}

.drift-tag.tag-good {
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  color: var(--do-success);
}

.drift-tag.tag-good small {
  font-weight: normal;
  color: var(--do-text-secondary);
}

.drift-tag.tag-alert {
  background: var(--do-danger-bg);
  border: 1px solid var(--do-danger-border);
  color: var(--do-danger);
}

.drift-tag.tag-alert small {
  font-weight: 600;
}

.clk-fault-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--do-danger-bg);
  border: 1px solid var(--do-danger);
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 13px;
  color: var(--do-danger);
  font-weight: 600;
  line-height: 1.4;
}

/* ============================================================
 * 5. 右侧柱状图与审计日志
 * ============================================================ */
.r-head-left {
  display: flex;
  align-items: center;
}

.header-title-txt {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.protocol-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--do-bg-sunken);
  color: var(--do-gold-deep);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  font-weight: 700;
}

.drift-bar-chart {
  padding: 14px 16px;
  border-bottom: 1px solid var(--do-border-light);
}

.chart-caption-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.chart-caption {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--do-text-primary);
  white-space: nowrap;
}

.chart-unit {
  font-size: 12px;
  color: var(--do-text-secondary);
  white-space: nowrap;
}

.threshold-corner-lbl {
  position: absolute;
  top: 8px;
  left: 10px;
  font-size: 11px;
  color: var(--do-gold-deep);
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.2);
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 600;
  pointer-events: none;
  z-index: 3;
}

.clock-sync-logs-panel {
  display: flex;
  flex-direction: column;
}

.bars-container {
  display: flex;
  justify-content: space-around;
  height: 140px;
  align-items: flex-end;
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.02) 0%, rgba(37, 99, 235, 0.06) 100%);
  border-radius: 6px;
  padding: 20px 8px 8px;
  border: 1px solid rgba(37, 99, 235, 0.16);
  position: relative;
}

/* 50ms 规范基准虚线 (轻盈通透贯穿，绝不遮挡任何柱子) */
.threshold-guide-line {
  position: absolute;
  top: 55%;
  left: 8px;
  right: 8px;
  border-top: 1px dashed rgba(37, 99, 235, 0.45);
  pointer-events: none;
}

.bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
  justify-content: flex-end;
  z-index: 2;
  cursor: pointer;
}

.bar-fill-wrap {
  width: 18px;
  height: 78px;
  display: flex;
  flex-direction: column-reverse;
}

.bar-pillar {
  width: 100%;
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%);
  border-radius: 3px 3px 1px 1px;
  transition: all 0.25s ease;
  position: relative;
}

.bar-pillar:hover {
  transform: scaleX(1.15);
  box-shadow: 0 0 8px rgba(var(--th-accent-rgb), 0.5);
}

.bar-pillar.alert {
  background: linear-gradient(180deg, #F87171 0%, var(--do-danger) 100%);
  box-shadow: 0 0 8px rgba(var(--th-danger-rgb), 0.4);
}

.bar-val {
  font-size: 13px;
  color: var(--do-text-primary);
  font-weight: 700;
}

.bar-lbl {
  font-size: 11.5px;
  color: var(--do-text-secondary);
  font-weight: 600;
}

/* 同步流水记录：弹性撑满高度，清爽微卡片流 */
.sync-logs-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 14px 16px;
  min-height: 0;
}

.logs-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.logs-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logs-header {
  font-size: 13.5px;
  color: var(--do-text-primary);
  font-weight: 700;
}

.pulse-dot-mini {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 4px rgba(var(--th-success-rgb), 0.5);
}

.logs-count-badge {
  font-size: 11px;
  padding: 1px 8px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--do-gold-deep);
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: 999px;
  font-weight: 600;
}

.logs-list-scroll {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  padding-right: 2px;
}

/* 纤细优雅滚动条 */
.logs-list-scroll::-webkit-scrollbar {
  width: 4px;
}

.logs-list-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.logs-list-scroll::-webkit-scrollbar-thumb {
  background: var(--do-border-light);
  border-radius: 4px;
}

.logs-list-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--do-gold);
}

/* 审计流水微卡片：两行舒展排版，彻底告别挤压 */
.log-item-card {
  background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.log-item-card:hover {
  background: linear-gradient(180deg, #F0F6FF 0%, #E8F2FE 100%);
  border-color: rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.08);
}

.log-top-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.log-time-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.log-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 4px rgba(var(--th-success-rgb), 0.5);
}

.log-time {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-text-primary);
  letter-spacing: 0.5px;
}

.log-badges-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.log-sat-pill {
  font-size: 11px;
  font-weight: 600;
  color: var(--do-gold-deep);
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.2);
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.log-status-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--do-success);
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.log-bottom-desc {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.log-res-code {
  font-size: 12px;
  font-weight: 600;
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ============================================================================
 * 统一控制台视觉与响应式增强
 * 对齐“大屏调度”和“计时计分”页面，保留实时钟面与校准交互
 * ============================================================================ */
.clock-monitor-workspace {
  width: 100%;
  min-width: 0;
  color: var(--do-text-primary);
}

.glass-panel {
  border-radius: var(--radius-lg, 10px);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(15, 23, 42, .05));
}

.clock-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-width: 0;
  padding: 18px 22px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: 10px;
  box-shadow: var(--shadow-sm, var(--shadow-card));
  flex-wrap: wrap;
}

.clock-top-bar .top-left {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1 1 360px;
  gap: 14px;
}

.clock-top-bar .page-icon {
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

.clock-top-bar .title-meta {
  min-width: 0;
}

.clock-top-bar .title-row {
  min-width: 0;
  gap: 10px;
}

.clock-top-bar .view-title {
  min-width: 0;
  overflow: hidden;
  color: var(--do-text-primary);
  font-size: 21px;
  font-weight: 700;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clock-top-bar .title-meta p {
  margin: 5px 0 0;
  overflow: hidden;
  color: var(--do-text-secondary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clock-top-bar .top-right {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1 1 640px;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.clock-top-bar .header-status {
  color: var(--do-text-secondary);
  font-size: 13px;
}

.clock-header-status {
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

.clock-header-status strong {
  color: var(--do-text-primary);
  font-family: var(--font-mono, Consolas, monospace);
  font-size: 13px;
}

.clock-header-status .status-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: currentColor;
}

.clock-header-status .status-dot.online {
  color: var(--do-success);
  box-shadow: 0 0 7px currentColor;
}

.clock-header-status .status-dot.warning {
  color: var(--do-warning, #f59e0b);
  box-shadow: 0 0 7px currentColor;
}

.clock-header-status .status-dot.muted {
  color: var(--do-text-placeholder);
}

.clock-top-bar .btn-top-manage,
.clock-top-bar .btn-fetch-hardware,
.clock-top-bar .mode-tab-btn {
  height: 30px !important;
  padding: 0 14px !important;
  font-size: 13px !important;
  font-weight: 400 !important;
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

.clock-top-bar .btn-top-manage *,
.clock-top-bar .btn-fetch-hardware *,
.clock-top-bar .mode-tab-btn *,
.clock-top-bar .btn-top-manage span,
.clock-top-bar .btn-fetch-hardware span,
.clock-top-bar .mode-tab-btn span {
  font-weight: 400 !important;
}

.clock-top-bar .btn-top-manage {
  border: 1px solid rgba(217, 119, 6, 0.55) !important;
  color: var(--do-gold) !important;
  background: rgba(217, 119, 6, 0.1) !important;
}

.clock-top-bar .btn-top-manage:hover {
  background: rgba(217, 119, 6, 0.2) !important;
  border-color: var(--do-gold) !important;
}

.clock-top-bar .btn-fetch-hardware {
  border: 1px solid var(--do-gold-deep) !important;
  background: linear-gradient(180deg, var(--do-gold-hover) 0%, var(--do-gold) 100%) !important;
  color: #FFFFFF !important;
  box-shadow: 0 1px 3px rgba(var(--th-accent-deep-rgb), 0.25);
}

.clock-top-bar .btn-fetch-hardware:hover:not(:disabled) {
  filter: brightness(1.05);
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35);
}

.clock-top-bar .btn-fetch-hardware:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.clock-top-bar .mode-toggle-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.clock-top-bar .mode-tab-btn {
  border: 1px solid var(--do-border) !important;
  color: var(--do-text-secondary) !important;
  background: var(--do-bg-card) !important;
}

.clock-top-bar .mode-tab-btn:hover {
  color: var(--do-gold) !important;
  border-color: var(--do-gold) !important;
}

.clock-top-bar .mode-tab-device {
  border-left: 1px solid var(--do-border, #334155) !important;
  margin-left: 6px;
}

.master-clock-kpi {
  grid-template-columns: minmax(0, 2fr) minmax(0, 1.15fr) minmax(0, 1.15fr);
  min-width: 0;
  padding: 18px 22px;
  border-radius: var(--radius-lg, 10px);
}

.master-clock-kpi>* {
  min-width: 0;
}

.kpi-block,
.time-hero,
.stat-item {
  min-width: 0;
}

/* 卫星捕获状态与子钟网络状态之间的视觉分区 */
.master-clock-kpi .stat-item + .stat-item {
  padding-left: 24px;
  border-left: 1px solid var(--do-border-light);
}

.time-hero {
  padding-right: 22px;
}

.block-head-row,
.stat-main-row,
.date-str-wrap,
.digital-clock-screen,
.chart-caption-row,
.logs-header-row,
.log-top-meta {
  min-width: 0;
}

.block-head-row {
  gap: 10px;
  flex-wrap: wrap;
}

.time-lbl,
.block-lbl,
.sig-status,
.online-rate-pill {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ntsc-badge,
.online-rate-pill,
.sig-status {
  flex: 0 0 auto;
}

.digital-clock-screen {
  gap: 10px;
  flex-wrap: wrap;
}

.digital-time-display {
  min-width: 0;
  max-width: 100%;
}

.time-main {
  font-size: clamp(30px, 3vw, 38px);
}

.screen-corner-badge {
  flex: 0 0 auto;
}

.date-str-wrap {
  flex-wrap: wrap;
}

.sat-badges {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.sat-tag,
.type-pill {
  min-width: 0;
  overflow: hidden;
}

.sat-name,
.type-pill {
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-clocks-type-pills {
  min-width: 0;
  flex-wrap: wrap;
}

.type-pill {
  min-width: 100px;
}

.clock-main-grid {
  grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);
  min-width: 0;
}

.clock-main-grid>* {
  min-width: 0;
}

.sub-clocks-panel,
.clock-sync-logs-panel {
  min-width: 0;
  overflow: hidden;
  border-radius: var(--radius-lg, 10px);
}

.sub-clocks-panel .panel-header,
.clock-sync-logs-panel .panel-header {
  min-width: 0;
  gap: 12px;
  flex-wrap: wrap;
}

.sub-clocks-panel .header-title,
.r-head-left,
.filter-radio-group {
  min-width: 0;
}

.sub-clocks-panel .header-title {
  flex: 1 1 360px;
}

.title-row {
  min-width: 0;
}

.title-txt,
.panel-subtitle,
.header-title-txt {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.panel-subtitle {
  white-space: nowrap;
}

.filter-radio-group {
  flex: 0 1 auto;
  flex-wrap: wrap;
}

.clocks-cards-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  min-width: 0;
}

.sub-clock-card {
  min-width: 0;
  border-radius: 8px;
}

.clk-card-header,
.clk-type-row,
.clk-footer,
.clk-location,
.clk-time-screen,
.clk-fault-box {
  min-width: 0;
}

.clk-card-header,
.clk-type-row,
.clk-footer {
  gap: 8px;
  flex-wrap: wrap;
}

.code-box,
.type-name,
.ip-addr,
.drift-label,
.drift-val {
  min-width: 0;
}

.code-box {
  flex: 1 1 120px;
  overflow: hidden;
}

.clk-code,
.type-name,
.ip-addr {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clk-status-badge {
  flex: 0 0 auto;
}

.clk-type-row .type-name {
  flex: 1 1 120px;
}

.clk-type-row .ip-addr {
  flex: 0 1 135px;
  text-align: right;
}

.clk-location {
  align-items: flex-start;
}

.loc-val {
  min-width: 0;
  flex: 1 1 auto;
}

.clk-time-screen {
  overflow: hidden;
}

.screen-digits {
  min-width: 0;
  overflow: hidden;
  font-size: clamp(21px, 2vw, 26px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drift-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drift-tag small {
  overflow: hidden;
  text-overflow: ellipsis;
}

.clk-fault-box {
  align-items: flex-start;
}

.fault-txt {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clock-sync-logs-panel .panel-header {
  justify-content: space-between;
}

.r-head-left {
  flex: 1 1 auto;
}

.protocol-badge {
  flex: 0 0 auto;
}

.drift-bar-chart {
  min-width: 0;
}

.chart-caption-row {
  gap: 10px;
  flex-wrap: wrap;
}

.chart-caption,
.chart-unit {
  min-width: 0;
}

.chart-caption {
  overflow: hidden;
  text-overflow: ellipsis;
}

.bars-container {
  min-width: 0;
  overflow: hidden;
}

.bar-col {
  min-width: 0;
  flex: 1 1 0;
}

.bar-lbl,
.bar-val {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sync-logs-wrap {
  min-width: 0;
}

.logs-header-row {
  gap: 8px;
  flex-wrap: wrap;
}

.logs-header-left,
.log-badges-group,
.log-time-group,
.log-bottom-desc {
  min-width: 0;
}

.logs-header-left {
  flex: 1 1 180px;
}

.logs-header,
.log-res-code {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logs-count-badge {
  flex: 0 0 auto;
}

.log-item-card {
  min-width: 0;
  border-radius: 8px;
}

.log-top-meta {
  gap: 8px;
  flex-wrap: wrap;
}

.log-time-group {
  flex: 1 1 90px;
}

.log-badges-group {
  flex: 0 1 auto;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.log-sat-pill,
.log-status-badge {
  flex: 0 0 auto;
}

@media (max-width: 1280px) {
  .clock-main-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .clock-sync-logs-panel {
    min-height: 420px;
  }

  .clocks-cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .clock-top-bar {
    align-items: flex-start;
  }

  .clock-top-bar .top-left,
  .clock-top-bar .top-right {
    flex-basis: 100%;
  }

  .clock-top-bar .top-right {
    justify-content: flex-start;
  }

  .master-clock-kpi {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .time-hero {
    grid-column: 1 / -1;
    padding-right: 0;
    padding-bottom: 16px;
    border-right: 0;
    border-bottom: 1px solid var(--do-border-light);
  }

  .master-clock-kpi .stat-item {
    padding-top: 2px;
  }

  .master-clock-kpi .stat-item + .stat-item {
    padding-left: 24px;
  }

  .panel-subtitle {
    white-space: normal;
  }
}

@media (max-width: 640px) {

  .clock-top-bar,
  .master-clock-kpi {
    padding: 14px;
  }

  .clock-top-bar .top-left {
    align-items: flex-start;
  }

  .clock-top-bar .page-icon,
  .clock-top-bar .header-icon-box {
    width: 44px;
    height: 44px;
  }

  .clock-top-bar .title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .clock-top-bar .view-title {
    font-size: 18px;
    white-space: normal;
  }

  .clock-top-bar .device-tag {
    width: 100%;
    white-space: normal;
  }

  .clock-top-bar .port-status,
  .btn-calibrate {
    width: 100%;
  }

  .clock-top-bar .port-status {
    justify-content: flex-start;
  }

  .btn-calibrate :deep(.el-button__text),
  .btn-calibrate .btn-inner {
    justify-content: center;
    width: 100%;
  }

  .master-clock-kpi {
    grid-template-columns: minmax(0, 1fr);
  }

  .time-hero {
    grid-column: auto;
  }

  .master-clock-kpi .stat-item {
    padding-top: 0;
    padding-bottom: 4px;
  }

  .master-clock-kpi .stat-item + .stat-item {
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid var(--do-border-light);
    padding-top: 16px;
    margin-top: 12px;
  }

  .sat-badges {
    grid-template-columns: minmax(0, 1fr);
  }

  .clocks-cards-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .sub-clocks-panel .panel-header,
  .clock-sync-logs-panel .panel-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .sub-clocks-panel .header-title,
  .filter-radio-group,
  .r-head-left {
    width: 100%;
  }

  .filter-radio-group {
    justify-content: flex-start;
  }

  .clk-type-row .ip-addr {
    flex-basis: 100%;
    text-align: left;
  }

  .clk-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .drift-tag {
    white-space: normal;
  }

  .chart-caption,
  .chart-unit {
    white-space: normal;
  }

  .log-badges-group {
    justify-content: flex-start;
  }
}

@media (max-width: 420px) {
  .clock-top-bar .device-tag {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .clock-top-bar .device-tag .tag-divider {
    display: none;
  }

  .clock-top-bar .device-tag .ip-tag {
    flex-basis: 100%;
  }

  .digital-clock-screen {
    align-items: flex-start;
    flex-direction: column;
  }

  .time-main {
    font-size: 30px;
  }

  .time-millis {
    font-size: 17px;
  }

  .sub-clocks-type-pills {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .type-pill {
    min-width: 0;
  }
}


/* ============================================================
 * 新增扩展样式：筛选栏、弹窗、操作按钮与真实协议流水
 * ============================================================ */
.header-btn-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-header-secondary {
  background: rgba(var(--th-accent-rgb), 0.12);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  color: var(--do-text-primary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-header-secondary:hover {
  background: rgba(var(--th-accent-rgb), 0.22);
  border-color: var(--do-primary);
}

.btn-icon-plus {
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
}

.device-total-count {
  font-size: 12px;
  color: var(--do-text-secondary);
  background: rgba(148, 163, 184, 0.12);
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 8px;
}

.top-quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-mini-action {
  background: rgba(var(--th-accent-rgb), 0.08);
  border: 1px solid var(--do-border);
  color: var(--do-text-primary);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-mini-action:hover {
  background: rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-primary);
}

.btn-mini-action.btn-add {
  background: var(--do-primary);
  color: #fff;
  border-color: var(--do-primary);
  font-weight: 600;
}

/* 过滤工具栏 */
.filter-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(15, 23, 42, 0.02);
  border-bottom: 1px solid var(--do-border);
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-lbl {
  font-size: 12.5px;
  color: var(--do-text-secondary);
  white-space: nowrap;
}

.filter-select {
  width: 130px;
}

.search-item {
  margin-left: auto;
}

.filter-search-input {
  width: 220px;
}

/* 子钟卡片强化样式 */
.clk-mac-badge {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-primary);
  background: rgba(var(--th-accent-rgb), 0.1);
  padding: 1px 6px;
  border-radius: 4px;
}

.clk-loc-summary {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--do-text-primary);
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-code {
  color: var(--do-primary);
  font-size: 13px;
  margin-right: 4px;
}

.model-desc {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.link-badge {
  font-size: 11px;
  background: rgba(100, 116, 139, 0.1);
  border: 1px solid rgba(100, 116, 139, 0.2);
  color: var(--do-text-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}

.clk-location-details {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--do-text-secondary);
}

.loc-tag {
  background: rgba(15, 23, 42, 0.03);
  padding: 1px 6px;
  border-radius: 3px;
}

/* 屏幕状态 */
.screen-off {
  background: #0f172a !important;
  color: #64748b !important;
  opacity: 0.65;
}

.screen-off-txt {
  font-size: 12px;
  letter-spacing: 1px;
}

.countdown-color {
  color: #f59e0b !important;
  text-shadow: 0 0 10px rgba(245, 158, 11, 0.5) !important;
}

.countup-color {
  color: #06b6d4 !important;
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.5) !important;
}

.screen-mode-tag {
  position: absolute;
  top: 4px;
  left: 8px;
  font-size: 10px;
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  padding: 1px 4px;
  border-radius: 2px;
}

.clk-params-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--do-text-secondary);
  padding: 4px 6px;
  background: rgba(15, 23, 42, 0.02);
  border-radius: 4px;
}

.clk-card-actions {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px dashed var(--do-border);
}

.card-btn {
  flex: 1;
  padding: 4px 0;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid var(--do-border);
  background: var(--do-bg-card);
  color: var(--do-text-primary);
}

.card-btn.btn-control:hover {
  border-color: var(--do-primary);
  color: var(--do-primary);
  background: rgba(var(--th-accent-rgb), 0.05);
}

.card-btn.btn-power:hover {
  border-color: #f59e0b;
  color: #f59e0b;
}

.card-btn.btn-delete:hover {
  border-color: var(--do-danger);
  color: var(--do-danger);
  background: rgba(220, 38, 38, 0.05);
}

/* 右侧 Tab 切换 */
.panel-header-tabbed {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--do-border);
}

.tab-switch-group {
  display: flex;
  background: rgba(15, 23, 42, 0.04);
  padding: 2px;
  border-radius: 6px;
}

.tab-btn {
  padding: 4px 12px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--do-text-secondary);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--do-bg-card);
  color: var(--do-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.protocol-log-wrap {
  padding: 12px;
  display: flex;
  flex-direction: column;
  height: 600px;
}

.protocol-log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.proto-title {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--do-text-secondary);
}

.btn-clear-logs {
  background: none;
  border: 1px solid var(--do-border);
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  cursor: pointer;
  color: var(--do-text-secondary);
}

.protocol-logs-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.proto-item {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--do-border);
  background: rgba(15, 23, 42, 0.02);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.proto-item.TX {
  border-left: 3px solid var(--do-primary);
}

.proto-item.RX {
  border-left: 3px solid var(--do-success);
}

.proto-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
}

.proto-dir-tag {
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 2px;
}

.proto-dir-tag.TX {
  color: var(--do-primary);
}

.proto-dir-tag.RX {
  color: var(--do-success);
}

.proto-time {
  color: var(--do-text-secondary);
}

.proto-cmd-name {
  color: var(--do-text-primary);
  font-weight: 600;
}

.proto-raw-hex {
  font-size: 12px;
  color: #0284c7;
  background: rgba(2, 132, 199, 0.06);
  padding: 4px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.proto-desc {
  font-size: 11.5px;
  color: var(--do-text-secondary);
}

/* 弹窗专用样式 */
.dialog-tips-box {
  background: rgba(var(--th-accent-rgb), 0.08);
  border: 1px solid rgba(var(--th-accent-rgb), 0.2);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12.5px;
  color: var(--do-text-primary);
  margin-bottom: 14px;
}

.dialog-tips-box.warning-box {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
}

.form-sub-hint {
  font-size: 11.5px;
  color: var(--do-text-secondary);
  display: block;
  margin-top: 4px;
}

.slider-with-val {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.slider-val-txt {
  font-size: 13px;
  font-weight: 600;
  color: var(--do-primary);
  width: 45px;
  text-align: right;
}

.clock-target-banner {
  background: rgba(var(--th-accent-rgb), 0.06);
  border: 1px solid rgba(var(--th-accent-rgb), 0.18);
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.target-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.target-title {
  font-size: 15px;
  color: var(--do-text-primary);
}

.target-model-pill {
  font-size: 12px;
  background: var(--do-primary);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
}

.target-meta-row {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--do-text-secondary);
}

.timing-control-pane {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 8px 0;
}

.mode-select-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pane-lbl {
  font-size: 13px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.time-set-box {
  background: rgba(15, 23, 42, 0.02);
  border: 1px solid var(--do-border);
  padding: 12px 16px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.time-pick-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-input-col {
  display: flex;
  align-items: center;
  gap: 6px;
}

.time-colon {
  font-size: 20px;
  font-weight: bold;
  color: var(--do-text-secondary);
}

.unit-txt {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.preset-btn-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-lbl {
  font-size: 12px;
  color: var(--do-text-secondary);
}

.preset-pill {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  color: var(--do-text-primary);
  transition: all 0.15s;
}

.preset-pill:hover {
  border-color: var(--do-primary);
  color: var(--do-primary);
}

.timing-action-row {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-timing-action {
  flex: 1;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-timing-action.primary {
  background: var(--do-primary);
  color: #fff;
}

.btn-timing-action.warning {
  background: #f59e0b;
  color: #fff;
}

.params-control-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 10px 0;
}

.param-form-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.item-label {
  width: 180px;
  font-size: 13px;
  color: var(--do-text-primary);
}

.param-footer-hint {
  font-size: 12px;
  color: var(--do-text-secondary);
  background: rgba(15, 23, 42, 0.02);
  padding: 8px 12px;
  border-radius: 4px;
}

.empty-clocks-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 8px;
}

.empty-icon {
  font-size: 40px;
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.empty-hint {
  font-size: 13px;
  color: var(--do-text-secondary);
}



/* 核心工业监视屏：采用纯净纯色微灰白背景与清爽边框，杜绝渐变与模糊发虚，极简护眼 */
.clk-status-screen {
  position: relative !important;
  min-height: 58px !important;
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
  padding: 10px 14px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

.clk-status-screen.normal {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
}

.clk-status-screen.fault {
  background: #fef2f2 !important;
  border: 1px solid #fecaca !important;
}

.clk-status-screen.screen-off {
  background: #f1f5f9 !important;
  border: 1px solid #e2e8f0 !important;
  opacity: 0.8 !important;
}

.screen-main-title {
  font-size: 14px !important;
  font-weight: 700 !important;
  color: #0f172a !important;
  letter-spacing: 0.2px !important;
}

.sync-tag-ok {
  font-size: 11px !important;
  font-weight: 600 !important;
  color: #047857 !important;
  background: #ecfdf5 !important;
  border: 1px solid #a7f3d0 !important;
  padding: 1px 6px !important;
  border-radius: 3px !important;
}

.screen-sub-desc {
  font-size: 12px !important;
  color: #475569 !important;
  font-weight: 500 !important;
}

.sync-pulse-dot {
  width: 7px !important;
  height: 7px !important;
  border-radius: 50% !important;
  background: #10b981 !important;
  box-shadow: 0 0 5px rgba(16, 185, 129, 0.6) !important;
  flex-shrink: 0 !important;
}

.screen-content-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.screen-content-box.sync-state {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.sync-state-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sync-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
  animation: pulseSyncDot 2s infinite ease-in-out;
}

@keyframes pulseSyncDot {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.4;
    transform: scale(0.85);
  }
}

.screen-state-text {
  font-size: 13px;
  color: #10b981;
  letter-spacing: 0.5px;
}

.sync-sub-desc {
  font-size: 11px;
  color: #6ee7b7;
  opacity: 0.85;
}

.mode-badge {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 700;
}

.cd-badge {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.cu-badge {
  background: rgba(6, 182, 212, 0.2);
  color: #06b6d4;
  border: 1px solid rgba(6, 182, 212, 0.4);
}

.screen-content-box.off-state .screen-state-text {
  color: #64748b;
  font-size: 12px;
}

.screen-content-box.fault-state .screen-state-text {
  color: #f87171;
  font-size: 12px;
}


/* ============================================================
 * 子钟监控卡片系统主题自适应样式 (跟随系统配置的主色调如经典商务蓝，呈现高雅科技质感)
 * ============================================================ */
.clocks-cards-grid {
  padding: 16px;
  display: grid !important;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)) !important;
  gap: 16px !important;
}

/* 正常状态子钟卡片：背景、边框、投影均自适应跟随系统主色调（商务蓝体系）微调 */
.sub-clock-card.normal,
.sub-clock-card {
  background: linear-gradient(180deg, var(--do-bg-card, #ffffff) 0%, rgba(var(--th-accent-rgb, 37, 99, 235), 0.045) 100%) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.22) !important;
  border-radius: 8px !important;
  padding: 16px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 3px 10px rgba(var(--th-accent-rgb, 37, 99, 235), 0.05) !important;
  transition: all 0.32s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* 在线亮屏状态：浅绿背景 */
.sub-clock-card.normal.is-screen-on {
  background: linear-gradient(180deg, #f7fef9 0%, #dcfce7 100%) !important;
  border-color: rgba(22, 163, 74, 0.36) !important;
}

/* 在线熄屏状态：浅灰背景 */
.sub-clock-card.normal.is-screen-off {
  background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
  border-color: rgba(100, 116, 139, 0.38) !important;
}

.sub-clock-card.normal:hover,
.sub-clock-card:hover {
  transform: translateY(-2px) !important;
  border-color: rgba(var(--th-accent-rgb, 37, 99, 235), 0.55) !important;
  box-shadow: 0 6px 22px rgba(var(--th-accent-rgb, 37, 99, 235), 0.16) !important;
}

/* 故障子钟卡片 */
.sub-clock-card.fault {
  border: 1.5px solid var(--do-danger, #ef4444) !important;
  background: linear-gradient(180deg, var(--do-bg-card, #ffffff) 0%, rgba(var(--th-danger-rgb, 220, 38, 38), 0.04) 100%) !important;
  box-shadow: 0 2px 10px rgba(var(--th-danger-rgb, 220, 38, 38), 0.10) !important;
}

/* 顶栏排版 */
.clk-card-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  gap: 8px !important;
}

.code-box {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  min-width: 0 !important;
  flex: 1 !important;
}

.clk-mac-badge {
  font-size: 13.5px !important;
  font-weight: 800 !important;
  color: var(--el-color-primary, #2563eb) !important;
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.10) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.25) !important;
  padding: 2px 7px !important;
  border-radius: 4px !important;
  flex-shrink: 0 !important;
}

.clk-loc-summary {
  font-size: 17px !important;
  font-weight: 800 !important;
  color: var(--do-text-primary, #1e293b) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

.clk-status-badge {
  display: inline-flex !important;
  align-items: center !important;
  gap: 5px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  padding: 3px 8px !important;
  border-radius: 4px !important;
  flex-shrink: 0 !important;
}

.clk-status-badge.normal {
  background: var(--do-success-bg, rgba(22, 163, 74, 0.12)) !important;
  color: var(--do-success-deep, #15803d) !important;
  border: 1px solid var(--do-success-border, #4ade80) !important;
}

.clk-status-badge.normal .badge-dot {
  background: var(--do-success, #16a34a) !important;
  box-shadow: 0 0 5px rgba(22, 163, 74, 0.8) !important;
}

.clk-status-badge.fault {
  background: var(--do-danger-bg, rgba(220, 38, 38, 0.12)) !important;
  color: var(--do-danger-deep, #b91c1c) !important;
  border: 1px solid var(--do-danger-border, #f87171) !important;
}

.clk-status-badge.fault .badge-dot {
  background: var(--do-danger, #dc2626) !important;
  box-shadow: 0 0 5px rgba(220, 38, 38, 0.8) !important;
}

/* 空间位置与型号标签 */
.clk-location-details {
  display: flex !important;
  align-items: center !important;
  flex-wrap: wrap !important;
  gap: 6px !important;
}

.loc-tag {
  font-size: 12px !important;
  font-weight: 500 !important;
  color: var(--do-text-secondary, #64748b) !important;
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.04) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.14) !important;
  padding: 2px 7px !important;
  border-radius: 4px !important;
}

.loc-tag.tag-model {
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.08) !important;
  color: var(--el-color-primary, #2563eb) !important;
  border-color: rgba(var(--th-accent-rgb, 37, 99, 235), 0.25) !important;
  font-weight: 700 !important;
}

.loc-tag.tag-link {
  background: var(--do-bg-card, #ffffff) !important;
  color: var(--do-text-secondary, #64748b) !important;
  border-color: rgba(var(--th-accent-rgb, 37, 99, 235), 0.15) !important;
}

/* 监视屏：跟随系统主色调，微弱蓝色底与主题色细边框 */
.clk-status-screen {
  position: relative !important;
  min-height: 58px !important;
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.045) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.20) !important;
  border-radius: 6px !important;
  padding: 10px 14px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  box-shadow: inset 0 1px 2px rgba(var(--th-accent-rgb, 37, 99, 235), 0.04) !important;
}

.clk-status-screen.fault {
  background: rgba(var(--th-danger-rgb, 220, 38, 38), 0.045) !important;
  border-color: rgba(var(--th-danger-rgb, 220, 38, 38), 0.25) !important;
}

.clk-status-screen.screen-off {
  background: var(--do-bg-sunken, #f1f5f9) !important;
  border-color: var(--do-border-light, #e2e8f0) !important;
  opacity: 0.8 !important;
}

.screen-content-box {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  min-width: 0 !important;
}

.screen-text-col {
  display: flex !important;
  flex-direction: column !important;
  gap: 2px !important;
}

.sync-title-row {
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.sync-pulse-dot {
  width: 7px !important;
  height: 7px !important;
  border-radius: 50% !important;
  background: var(--el-color-primary, #2563eb) !important;
  box-shadow: 0 0 6px var(--el-color-primary, #2563eb) !important;
  flex-shrink: 0 !important;
}

.screen-main-title {
  font-size: 14px !important;
  font-weight: 700 !important;
  color: var(--do-text-primary, #1e293b) !important;
  letter-spacing: 0.2px !important;
}

.sync-tag-ok {
  font-size: 11px !important;
  font-weight: 600 !important;
  color: var(--do-success-deep, #15803d) !important;
  background: var(--do-success-bg, rgba(22, 163, 74, 0.12)) !important;
  border: 1px solid var(--do-success-border, #4ade80) !important;
  padding: 1px 6px !important;
  border-radius: 3px !important;
}

.screen-sub-desc {
  font-size: 12px !important;
  color: var(--do-text-secondary, #64748b) !important;
  font-weight: 500 !important;
}

/* 右侧偏差胶囊 */
.screen-drift-badge {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-end !important;
  background: var(--do-bg-card, #ffffff) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.24) !important;
  padding: 3px 8px !important;
  border-radius: 5px !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
  flex-shrink: 0 !important;
}

.screen-drift-badge .drift-lbl {
  font-size: 10px !important;
  color: var(--do-text-secondary, #64748b) !important;
  text-transform: uppercase !important;
}

.screen-drift-badge .drift-num {
  font-size: 13px !important;
  font-weight: 800 !important;
  color: var(--el-color-primary, #2563eb) !important;
}

.screen-drift-badge.drift-alert {
  border-color: rgba(var(--th-danger-rgb, 220, 38, 38), 0.3) !important;
  background: rgba(var(--th-danger-rgb, 220, 38, 38), 0.06) !important;
}

.screen-drift-badge.drift-alert .drift-num {
  color: var(--do-danger, #dc2626) !important;
}

/* 参数摘要行 */
.clk-params-row {
  display: flex !important;
  flex-wrap: wrap !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 6px 10px !important;
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.03) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.14) !important;
  padding: 8px 12px !important;
  border-radius: 6px !important;
  font-size: 12.5px !important;
}

.param-pill {
  display: flex !important;
  align-items: center !important;
  gap: 5px !important;
}

.param-pill .p-lbl {
  color: var(--do-text-secondary, #64748b) !important;
  font-size: 12px !important;
}

.param-pill .p-val {
  color: var(--do-text-primary, #1e293b) !important;
  font-size: 13px !important;
}

.param-pill-divider {
  width: 1px !important;
  height: 12px !important;
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.18) !important;
}

/* 操作按钮组 */
.clk-card-actions {
  display: flex !important;
  gap: 8px !important;
  margin-top: 2px !important;
  padding-top: 8px !important;
  border-top: 1px dashed rgba(var(--th-accent-rgb, 37, 99, 235), 0.18) !important;
}

.card-btn {
  flex: 1 !important;
  height: 32px !important;
  border-radius: 5px !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.card-btn.btn-control {
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.08) !important;
  border: 1px solid rgba(var(--th-accent-rgb, 37, 99, 235), 0.25) !important;
  color: var(--el-color-primary, #2563eb) !important;
}

.card-btn.btn-control:hover {
  background: var(--el-color-primary, #2563eb) !important;
  color: #ffffff !important;
  border-color: var(--el-color-primary, #2563eb) !important;
}

.card-btn.btn-power {
  background: var(--do-bg-card, #ffffff) !important;
  border: 1px solid var(--do-border-light, #e2e8f0) !important;
  color: var(--do-text-regular, #334155) !important;
}

.card-btn.btn-power:hover {
  background: rgba(var(--th-accent-rgb, 37, 99, 235), 0.06) !important;
  border-color: rgba(var(--th-accent-rgb, 37, 99, 235), 0.35) !important;
  color: var(--el-color-primary, #2563eb) !important;
}

.card-btn.btn-delete {
  background: var(--do-danger-bg, rgba(220, 38, 38, 0.12)) !important;
  border: 1px solid var(--do-danger-border, #f87171) !important;
  color: var(--do-danger-deep, #b91c1c) !important;
}

.card-btn.btn-delete:hover {
  background: var(--do-danger, #dc2626) !important;
  border-color: var(--do-danger, #dc2626) !important;
  color: #ffffff !important;
}


/* 统一采用系统默认字体，不引入外部等宽字体 */
:deep(.num-mono),
.num-mono {
  font-family: inherit !important;
  font-variant-numeric: tabular-nums;
  letter-spacing: normal !important;
}
</style>
