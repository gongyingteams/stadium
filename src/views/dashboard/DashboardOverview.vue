<template>
  <div class="dashboard-overview">
    <!-- 顶部核心指标 KPI 栏 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-panel">
        <div class="kpi-icon-wrap primary">
          <SvgIcon name="SvgIotControl" size="24" />
        </div>
        <div class="kpi-meta">
          <span class="kpi-label">全场纳管设备总数</span>
          <span class="kpi-value num-mono">26 <small>台</small></span>
        </div>
        <div class="kpi-trend">
          <span class="trend-tag success">13类基线全接入</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-icon-wrap success">
          <SvgIcon name="SvgSecurityShield" size="24" />
        </div>
        <div class="kpi-meta">
          <span class="kpi-label">综合在线率</span>
          <span class="kpi-value num-mono text-success">96.2%</span>
        </div>
        <div class="kpi-trend">
          <span>正常 25 / 故障 1</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-icon-wrap warning">
          <SvgIcon name="SvgLighting" size="24" />
        </div>
        <div class="kpi-meta">
          <span class="kpi-label">瞬时照明能耗</span>
          <span class="kpi-value num-mono text-warning">142.8 <small>kW</small></span>
        </div>
        <div class="kpi-trend">
          <span>今日累计 864 kWh</span>
        </div>
      </div>

      <div class="kpi-card glass-panel">
        <div class="kpi-icon-wrap info">
          <SvgIcon name="SvgMasterClock" size="24" />
        </div>
        <div class="kpi-meta">
          <span class="kpi-label">北斗卫星授时</span>
          <span class="kpi-value num-mono">12 <small>颗</small></span>
        </div>
        <div class="kpi-trend">
          <span>时钟漂移 2ms</span>
        </div>
      </div>
    </div>

    <!-- 2. 全景数字孪生主视窗：主馆 2D 平面设备拓扑监视视窗 (独占全景展台，彻底消除重叠，高度与留白舒展) -->
    <div class="venue-topology-section glass-panel">
      <div class="panel-header">
        <div class="header-title">
          <SvgIcon name="SvgDashboard" size="24" class="text-primary" />
          <span>主馆 2D 平面设备拓扑监视视窗</span>
          <span class="cad-badge num-mono">CAD-1F · 标高 +0.00m · 比例 1:100</span>
        </div>
        <div class="topology-header-actions">
          <div class="topo-filter-pills">
            <span v-for="flt in topoFilters" :key="'flt-' + flt.key"
              :class="['filter-pill', { active: activeTopoFilter === flt.key }]" @click="activeTopoFilter = flt.key">
              {{ flt.label }}
            </span>
          </div>
          <div class="topology-legend">
            <span class="legend-item"><i class="dot online"></i> 正常在线 (7)</span>
            <span class="legend-item"><i class="dot warning"></i> 告警节点 (1)</span>
            <span class="legend-item"><i class="dot bus-fiber"></i> 骨干光纤双环网</span>
          </div>
        </div>
      </div>

      <!-- 2D SVG 场馆仿真蓝图 (1680 全宽自适应铺满画幅，彻底消除左右空白，零文字压盖，高保真数字孪生) -->
      <div class="venue-svg-wrapper">
        <svg class="venue-plan-svg" viewBox="0 0 1680 440" preserveAspectRatio="none">
          <defs>
            <!-- 建筑工控 CAD 微网格 -->
            <pattern id="cadGrid" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="0.8" fill="rgba(200, 164, 92, 0.22)" />
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(200, 164, 92, 0.06)" stroke-width="0.8" />
            </pattern>
            <!-- 50M 比赛池水质渐变 (通透碧水绿，符合自然高级审美，杜绝刺眼蓝紫) -->
            <linearGradient id="poolWaterGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#CDE8DE" />
              <stop offset="35%" stop-color="#B2DDD0" />
              <stop offset="70%" stop-color="#93CEC0" />
              <stop offset="100%" stop-color="#76BEAD" />
            </linearGradient>
            <!-- 跳水深水池渐变 (深邃清澈翡翠绿) -->
            <linearGradient id="diveWaterGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#BFE2CD" />
              <stop offset="50%" stop-color="#A1D6B3" />
              <stop offset="100%" stop-color="#7FC397" />
            </linearGradient>
            <!-- 场馆地坪底色渐变 -->
            <linearGradient id="floorGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#FAF6EE" />
              <stop offset="100%" stop-color="#F3ECE0" />
            </linearGradient>
            <!-- 发光高亮滤镜 -->
            <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          <!-- 1. 全幅工程网格底板无缝满铺 (覆盖 1680 全宽) -->
          <rect width="1680" height="440" fill="url(#floorGrad)" />
          <rect width="1680" height="440" fill="url(#cadGrid)" />

          <!-- 建筑定位轴网贯穿标记 -->
          <g class="cad-axes" opacity="0.6">
            <line x1="0" y1="50" x2="1680" y2="50" stroke="rgba(200,164,92,0.25)" stroke-dasharray="4,4" />
            <line x1="0" y1="395" x2="1680" y2="395" stroke="rgba(200,164,92,0.25)" stroke-dasharray="4,4" />
            <line x1="18" y1="0" x2="18" y2="440" stroke="rgba(200,164,92,0.22)" stroke-dasharray="4,4" />
            <line x1="1068" y1="0" x2="1068" y2="440" stroke="rgba(200,164,92,0.22)" stroke-dasharray="4,4" />
            <line x1="1662" y1="0" x2="1662" y2="440" stroke="rgba(200,164,92,0.22)" stroke-dasharray="4,4" />
          </g>

          <!-- 北侧看台标牌 (独立顶部中央，居中在 x=840) -->
          <g transform="translate(840, 16)">
            <rect x="-160" y="-11" width="320" height="22" rx="11" fill="rgba(200, 164, 92, 0.12)"
              stroke="rgba(200, 164, 92, 0.35)" />
            <text x="0" y="5" fill="#8C765C" font-size="14" font-weight="600" text-anchor="middle">北侧看台 ·
              VIP贵宾主席席位与国际媒体转播区</text>
          </g>

          <!-- 2. 设备总线拓扑骨干链路 (光纤冗余双环网全宽贯通) -->
          <g class="topo-bus-lines">
            <path
              d="M 220 50 L 620 50 L 1180 50 L 1500 50 L 1650 220 L 1500 395 L 1180 395 L 620 395 L 220 395 L 30 220 Z"
              fill="none" stroke="rgba(200, 164, 92, 0.45)" stroke-width="2" stroke-dasharray="6,4"
              class="flow-bus-dash" />
            <!-- 从节点引出的物理传感测点光纤分支线 -->
            <line v-for="n in topoNodes" :key="'link-' + n.id" :x1="n.x" :y1="n.y > 220 ? n.y - 23 : n.y + 23"
              :x2="n.linkTarget.x" :y2="n.linkTarget.y"
              :stroke="selectedNodeId === n.id ? '#C8963E' : 'rgba(91, 140, 90, 0.45)'"
              :stroke-width="selectedNodeId === n.id ? 2.2 : 1.2" stroke-dasharray="3,3" />
          </g>

          <!-- 3. 【50M 国际竞技泳池】(y=94 ~ 346, 宽度扩展至 1040px，舒展铺满) -->
          <rect x="18" y="94" width="1040" height="252" rx="8" fill="#EAE1D2" stroke="#D3C3A8" stroke-width="1.2" />
          <rect x="26" y="102" width="1024" height="236" rx="6" fill="url(#poolWaterGrad)" stroke="#4A7C49"
            stroke-width="1.8" />

          <!-- 10 条国际比赛泳道 (y: 102 ~ 338, 每道 23.6px) -->
          <g class="swimming-lanes">
            <line v-for="i in 9" :key="'lane-' + i" :x1="26" :y1="102 + i * 23.6" :x2="1046" :y2="102 + i * 23.6"
              stroke="rgba(74, 124, 73, 0.35)" stroke-dasharray="6,3" stroke-width="1.2" />

            <!-- 5m 仰泳标志旗红线 -->
            <line x1="115" y1="102" x2="115" y2="338" stroke="rgba(200, 60, 40, 0.65)" stroke-dasharray="3,3"
              stroke-width="1.4" />
            <!-- 15m 潜水警示线 -->
            <line x1="280" y1="102" x2="280" y2="338" stroke="rgba(200, 150, 40, 0.6)" stroke-dasharray="4,2"
              stroke-width="1.2" />
            <!-- 25m 半程中心线 -->
            <line x1="538" y1="102" x2="538" y2="338" stroke="rgba(74, 124, 73, 0.7)" stroke-width="1.5" />
            <!-- 45m 冲刺准备红线 -->
            <line x1="970" y1="102" x2="970" y2="338" stroke="rgba(200, 60, 40, 0.65)" stroke-dasharray="3,3"
              stroke-width="1.4" />

            <!-- 池底中心 10 条黑色 T 型翻转标志线 -->
            <g v-for="i in 10" :key="'t-line-' + i">
              <line :x1="150" :y1="102 + (i - 0.5) * 23.6" :x2="940" :y2="102 + (i - 0.5) * 23.6"
                stroke="rgba(44, 24, 16, 0.25)" stroke-width="1.8" />
              <line :x1="940" :y1="102 + (i - 0.5) * 23.6 - 5" :x2="940" :y2="102 + (i - 0.5) * 23.6 + 5"
                stroke="rgba(44, 24, 16, 0.35)" stroke-width="2" />
              <!-- 左侧泳道编号徽标 -->
              <rect :x="34" :y="102 + (i - 0.5) * 23.6 - 7" width="16" height="14" rx="2"
                fill="rgba(44, 24, 16, 0.75)" />
              <text :x="42" :y="102 + (i - 0.5) * 23.6 + 4" fill="#FFE599" font-size="14" font-weight="700"
                text-anchor="middle">{{ i }}</text>
            </g>
          </g>

          <!-- 10 个立体出发台 (左侧池壁) -->
          <g class="starting-blocks">
            <g v-for="i in 10" :key="'block-' + i" :transform="`translate(15, ${102 + (i - 1) * 23.6 + 4})`">
              <rect x="0" y="0" width="10" height="15" rx="2" fill="#D4A045" stroke="#7C5E28" stroke-width="0.8" />
              <line x1="0" y1="7" x2="10" y2="7" stroke="#FFF" stroke-width="0.8" />
            </g>
          </g>

          <!-- 右侧 Omega 终点触壁感应板 (TouchPad) 标金线 -->
          <rect x="1044" y="104" width="4" height="232" rx="1" fill="#E5AC44" stroke="#8C6318" stroke-width="1" />

          <!-- 泳池中心标题与水质实时参数盒 -->
          <text x="538" y="180" fill="#1E3324" font-size="17" font-weight="800" text-anchor="middle"
            letter-spacing="1">50M 国际标准竞技游泳池</text>
          <text x="538" y="202" fill="#42664E" font-size="14" font-weight="600" text-anchor="middle">长 50m × 宽 25m · 水深
            2.0m · 10泳道 (国际泳联认证)</text>

          <g transform="translate(380, 220)">
            <rect x="0" y="0" width="316" height="26" rx="13" fill="rgba(255, 255, 255, 0.96)" stroke="#5B8C5A"
              stroke-width="1.2" />
            <circle cx="16" cy="13" r="4.5" fill="#5B8C5A" />
            <text x="30" y="18" fill="#2C1810" font-size="14" font-weight="700">恒温 26.8℃ · pH 7.45 · 余氯 0.55 · 浊度
              0.12NTU</text>
          </g>

          <!-- 4. 【25M 跳水深水池与10米跳台】(y=94 ~ 346, 宽度扩展至 580px) -->
          <rect x="1080" y="94" width="580" height="252" rx="8" fill="#EAE1D2" stroke="#D3C3A8" stroke-width="1.2" />
          <rect x="1088" y="102" width="564" height="236" rx="6" fill="url(#diveWaterGrad)" stroke="#3E6F3D"
            stroke-width="1.8" />

          <!-- 水面安全消波喷水造波涟漪同心圆 (跳水比赛特有防眩光装置) -->
          <g transform="translate(1380, 215)" opacity="0.65">
            <circle cx="0" cy="0" r="32" fill="none" stroke="#FFFFFF" stroke-dasharray="3,3" stroke-width="1.2" />
            <circle cx="0" cy="0" r="64" fill="none" stroke="rgba(255, 255, 255, 0.7)" stroke-dasharray="4,4"
              stroke-width="1" />
            <circle cx="0" cy="0" r="96" fill="none" stroke="rgba(255, 255, 255, 0.4)" stroke-dasharray="5,5"
              stroke-width="0.8" />
          </g>

          <!-- 立体 10M 跳水塔工程模型 -->
          <g class="dive-tower-model" transform="translate(1100, 120)">
            <rect x="0" y="6" width="20" height="116" rx="2" fill="#D3C7B5" stroke="#998369" stroke-width="1" />
            <!-- 10M 平台 -->
            <polygon points="20,6 94,6 88,20 20,20" fill="#FFFDF8" stroke="#7C5E28" stroke-width="1.2" />
            <text x="54" y="17" fill="#7C5E28" font-size="14" font-weight="bold">10M 平台</text>
            <!-- 7.5M 平台 -->
            <polygon points="20,34 80,34 76,44 20,44" fill="#FFFDF8" stroke="#7C5E28" stroke-width="1" />
            <text x="48" y="42" fill="#7C5E28" font-size="14">7.5M</text>
            <!-- 5M 平台 -->
            <polygon points="20,60 70,60 66,70 20,70" fill="#FFFDF8" stroke="#7C5E28" stroke-width="1" />
            <text x="42" y="68" fill="#7C5E28" font-size="14">5M</text>
            <!-- 3M 弹网跳板 -->
            <line x1="20" y1="92" x2="72" y2="92" stroke="#C8963E" stroke-width="3" />
            <text x="44" y="88" fill="#7C5E28" font-size="14">3M板</text>
            <!-- 扶梯网格 -->
            <line x1="10" y1="10" x2="10" y2="120" stroke="#7C5E28" stroke-width="1" stroke-dasharray="2,2" />
          </g>

          <!-- 跳水池标题与参数 -->
          <text x="1380" y="180" fill="#1E3324" font-size="17" font-weight="800" text-anchor="middle"
            letter-spacing="1">跳水深水池与跳台系统</text>
          <text x="1380" y="202" fill="#3D6448" font-size="14" font-weight="600" text-anchor="middle">长25m×宽25m · 水深
            5.5m · 5层跳台</text>

          <g transform="translate(1265, 220)">
            <rect x="0" y="0" width="230" height="26" rx="13" fill="rgba(255, 255, 255, 0.96)" stroke="#3E6F3D"
              stroke-width="1.2" />
            <circle cx="16" cy="13" r="4.5" fill="#5B8C5A" />
            <text x="30" y="18" fill="#2C1810" font-size="14" font-weight="700">恒温 28.2℃ · 消波喷水待命</text>
          </g>

          <!-- 南侧看台标牌 (独立底部中央，居中在 x=840) -->
          <g transform="translate(840, 424)">
            <rect x="-160" y="-11" width="320" height="22" rx="11" fill="rgba(200, 164, 92, 0.12)"
              stroke="rgba(200, 164, 92, 0.35)" />
            <text x="0" y="5" fill="#8C765C" font-size="14" font-weight="600" text-anchor="middle">南侧看台 ·
              主席台与运动员赛前检录区</text>
          </g>

          <!-- 5. 【8大物联设备数字孪生工控卡片】(嵌入真实切片图标，加粗排版，呼吸心跳灯，零压盖) -->
          <g v-for="node in filteredTopoNodes" :key="node.id"
            :class="['svg-node-item', node.status, { active: selectedNodeId === node.id, dimmed: activeTopoFilter !== 'ALL' && activeTopoFilter !== node.type }]"
            :transform="`translate(${node.x}, ${node.y})`" @click="handleNodeClick(node)">
            <!-- 卡片外框与背板 (宽 168, 高 46) -->
            <rect x="-84" y="-23" width="168" height="46" rx="8" class="node-card-bg" />
            <!-- 高亮发光外框 -->
            <rect v-if="selectedNodeId === node.id" x="-86" y="-25" width="172" height="50" rx="10" fill="none"
              stroke="#C8963E" stroke-width="2" class="node-select-glow" />

            <!-- 左侧圆角图标底座 -->
            <rect x="-76" y="-17" width="34" height="34" rx="6" class="node-icon-bg" />
            <!-- 嵌入 Vue SvgIcon 组件 -->
            <foreignObject x="-76" y="-17" width="34" height="34">
              <div class="node-icon-foreign">
                <SvgIcon :name="node.icon" size="18" />
              </div>
            </foreignObject>

            <!-- 中间文本行 (设备名称 + 协议参数) -->
            <text x="-34" y="-2" class="node-title">{{ node.name }}</text>
            <text x="-34" y="14" class="node-sub num-mono">{{ node.sub }}</text>

            <!-- 右上角状态指示徽章与脉冲环 (置于卡片右上角，避免遮挡设备文字与参数) -->
            <circle cx="72" cy="-11" r="3.5" :class="['node-status-dot', node.status]" />
            <circle cx="72" cy="-11" r="6.5" :class="['node-status-ring', node.status]" />
          </g>
        </svg>
      </div>

      <!-- 视窗底部微状态信息条 -->
      <div class="topo-footer-bar">
        <div class="footer-stat-item">
          <span class="stat-dot online"></span>
          <span>骨干光纤环网：<b>双链路热备 · 0 丢包</b></span>
        </div>
        <div class="footer-stat-item">
          <span class="stat-dot online"></span>
          <span>拓扑覆盖：<b>50M比赛池 / 10M跳水池 / 观众看台</b></span>
        </div>
        <div class="footer-stat-item">
          <span class="stat-dot warning"></span>
          <span>异常定位：<b>大厅数码子钟 (偏差 1450ms)</b></span>
        </div>
        <div class="footer-stat-item mode-tag">
          <span>当前聚焦：<b>{{topoNodes.find(n => n.id === selectedNodeId)?.name || '全场巡检'}}</b></span>
        </div>
      </div>
    </div>

    <!-- 3. 中排核心控制台：实时故障告警处置雷达 (左 50%) + LED 主大屏推屏调度视窗 (右 50%) -->
    <div class="dashboard-action-row">
      <!-- 左侧：视频监控画面视窗 (支持 4分屏巡检与单屏特写切换，宽度和高度维持与右侧对称一致) -->
      <div class="video-monitor-panel glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <SvgIcon name="SvgCameraMatrix" size="18" class="text-primary" />
            <span>视频监控画面</span>
            <div class="split-filter-pills">
              <span :class="['split-pill-btn', { active: videoLayoutMode === 4 }]"
                @click="setVideoLayout(4)">
                4分屏巡检
              </span>
              <span :class="['split-pill-btn', { active: videoLayoutMode === 1 }]"
                @click="setVideoLayout(1)">
                单屏特写
              </span>
            </div>
          </div>
          <div class="video-header-actions">
            <span class="video-tag num-mono">4路 H.265 · 0丢包</span>
            <span class="live-dot online"><i class="status-dot online"></i> 实时监视</span>
            <button class="btn-tool-link" @click="router.push('/iot/video')" title="进入视频监控总控中心">
              <SvgIcon name="SvgCompassNav" size="14" style="margin-right: 4px;" />
              矩阵大厅
            </button>
          </div>
        </div>

        <div class="video-monitor-body">
          <!-- 4 分屏多路实时巡检网格 -->
          <div v-if="videoLayoutMode === 4" class="video-quad-grid">
            <div v-for="cam in monitorCameras" :key="cam.id"
              :class="['cam-quad-cell', { active: selectedCamId === cam.id }]"
              @click="selectCamFocus(cam.id)">
              <!-- 视窗 OSD 顶部栏 (半透渐变黑底，去除硬性截断，信息清晰) -->
              <div class="quad-osd-top">
                <div class="osd-left-meta">
                  <span class="status-dot online"></span>
                  <span class="quad-cam-name">{{ cam.name }}</span>
                </div>
                <span class="quad-cam-meta num-mono">{{ cam.res }}@{{ cam.fps }}</span>
              </div>

              <!-- 模拟视频监控动态视窗 (带场景矢量透视图层与微动态) -->
              <div class="quad-screen-visual" :class="cam.themeClass">
                <!-- 场景背景高保真动态矢量图层 -->
                <svg class="cam-scene-svg" viewBox="0 0 320 180" preserveAspectRatio="none">
                  <!-- 1. 比赛池：泳道透视标线与水面反光 -->
                  <g v-if="cam.id === 'cam1'" opacity="0.32">
                    <line x1="160" y1="15" x2="20" y2="180" stroke="#38BDF8" stroke-width="1.2" stroke-dasharray="4 2" />
                    <line x1="160" y1="15" x2="65" y2="180" stroke="#38BDF8" stroke-width="1" />
                    <line x1="160" y1="15" x2="115" y2="180" stroke="#38BDF8" stroke-width="1" />
                    <line x1="160" y1="15" x2="160" y2="180" stroke="#38BDF8" stroke-width="1.5" />
                    <line x1="160" y1="15" x2="205" y2="180" stroke="#38BDF8" stroke-width="1" />
                    <line x1="160" y1="15" x2="255" y2="180" stroke="#38BDF8" stroke-width="1" />
                    <line x1="160" y1="15" x2="300" y2="180" stroke="#38BDF8" stroke-width="1.2" stroke-dasharray="4 2" />
                    <line x1="40" y1="155" x2="280" y2="155" stroke="#EF4444" stroke-width="1.5" opacity="0.6" />
                  </g>
                  <!-- 2. 水下4K：水下蓝绿清澈透视与深度游标 -->
                  <g v-else-if="cam.id === 'cam2'" opacity="0.38">
                    <rect x="12" y="25" width="3" height="130" fill="rgba(52, 211, 153, 0.4)" />
                    <line x1="12" y1="28" x2="20" y2="28" stroke="#34D399" stroke-width="1" />
                    <text x="24" y="32" fill="#34D399" font-size="9" font-family="monospace">0.0m</text>
                    <line x1="12" y1="88" x2="18" y2="88" stroke="#34D399" stroke-width="1" />
                    <text x="22" y="92" fill="#34D399" font-size="9" font-family="monospace">-2.5m</text>
                    <line x1="12" y1="148" x2="20" y2="148" stroke="#34D399" stroke-width="1" />
                    <text x="24" y="152" fill="#34D399" font-size="9" font-family="monospace">-5.5m</text>
                    <circle cx="215" cy="100" r="26" fill="none" stroke="#38BDF8" stroke-width="1" stroke-dasharray="3 3" />
                    <circle cx="215" cy="100" r="12" fill="none" stroke="#38BDF8" stroke-width="1" />
                    <circle cx="215" cy="100" r="2" fill="#38BDF8" />
                  </g>
                  <!-- 3. 看台云台：看台阶梯座椅透视与客流监测区域 -->
                  <g v-else-if="cam.id === 'cam3'" opacity="0.32">
                    <path d="M 20 180 L 120 35 L 200 35 L 300 180 Z" fill="none" stroke="#C8963E" stroke-width="1" stroke-dasharray="4 2" />
                    <line x1="45" y1="145" x2="275" y2="145" stroke="#C8963E" stroke-width="1" />
                    <line x1="70" y1="110" x2="250" y2="110" stroke="#C8963E" stroke-width="1" />
                    <line x1="95" y1="75" x2="225" y2="75" stroke="#C8963E" stroke-width="1" />
                    <polygon points="100,75 220,75 245,110 75,110" fill="rgba(200, 150, 62, 0.15)" stroke="#C8963E" stroke-width="1" />
                  </g>
                  <!-- 4. 检录通道：走廊透视与门禁安全卡位 -->
                  <g v-else opacity="0.32">
                    <rect x="65" y="28" width="190" height="135" fill="none" stroke="#94A3B8" stroke-width="1" />
                    <line x1="0" y1="0" x2="65" y2="28" stroke="#94A3B8" stroke-width="1" />
                    <line x1="320" y1="0" x2="255" y2="28" stroke="#94A3B8" stroke-width="1" />
                    <line x1="0" y1="180" x2="65" y2="163" stroke="#94A3B8" stroke-width="1" />
                    <line x1="320" y1="180" x2="255" y2="163" stroke="#94A3B8" stroke-width="1" />
                    <rect x="115" y="75" width="90" height="88" fill="none" stroke="#10B981" stroke-width="1.2" stroke-dasharray="4 2" />
                  </g>
                </svg>

                <!-- 十字准星 -->
                <div class="cam-crosshair"></div>

                <!-- 科技四角 AI 目标跟踪框 (通透细角标，绝无遮挡大膏药) -->
                <div class="cam-ai-hud" :style="cam.aiBoxStyle">
                  <span class="hud-corner tl"></span>
                  <span class="hud-corner tr"></span>
                  <span class="hud-corner bl"></span>
                  <span class="hud-corner br"></span>
                  <div class="hud-tag num-mono">
                    <span class="hud-dot"></span>
                    <span>{{ cam.aiTag }}</span>
                  </div>
                </div>

                <!-- 视窗底部 OSD 信息 -->
                <div class="quad-osd-bottom num-mono">
                  <span class="quad-ch-tag">{{ cam.code }}</span>
                  <span class="rec-dot">● REC</span>
                  <span class="quad-time">{{ liveVideoTime }}</span>
                </div>

                <!-- 悬浮快速操作层 -->
                <div class="quad-hover-mask">
                  <button class="btn-quad-zoom" @click.stop="zoomCamDetail(cam.id)">
                    <SvgIcon name="SvgCompassNav" size="13" style="margin-right: 3px;" />
                    放大单屏
                  </button>
                  <button class="btn-quad-snap" @click.stop="takeCamSnapshot(cam)">
                    抓拍存盘
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 单屏高保真特写导播视窗 -->
          <div v-else class="video-single-frame">
            <div class="screen-bezel-frame">
              <div class="screen-canvas-preview video-single-canvas" :class="activeCamObj.themeClass">
                <!-- 专业广播监视器 OSD 顶栏 -->
                <div class="osd-top-bar num-mono">
                  <span class="osd-green">TC {{ liveVideoTc }}</span>
                  <span class="osd-ch">[{{ activeCamObj.code }}: {{ activeCamObj.name }}]</span>
                  <span class="rec-dot">● REC UHD</span>
                  <span class="osd-audio">H.265 / {{ activeCamObj.bitrate }} <span class="audio-bar-anim"></span></span>
                </div>

                <!-- 视窗中央十字标与智能追踪框 -->
                <div class="cam-crosshair large"></div>
                <div class="cam-ai-box-single" :style="activeCamObj.aiBoxStyle">
                  <div class="ai-corner tl"></div>
                  <div class="ai-corner tr"></div>
                  <div class="ai-corner bl"></div>
                  <div class="ai-corner br"></div>
                  <span class="ai-label-single num-mono">AI智能分析: {{ activeCamObj.aiTag }} (置信度 98.6%)</span>
                </div>

                <!-- 云台 PTZ 微控悬浮盘 (支持八向微调) -->
                <div class="cam-ptz-floating">
                  <button class="ptz-mini-btn" @click.stop="triggerPtzCmd('UP')">▲</button>
                  <div class="ptz-mid-row">
                    <button class="ptz-mini-btn" @click.stop="triggerPtzCmd('LEFT')">◀</button>
                    <span class="ptz-center-dot">PTZ</span>
                    <button class="ptz-mini-btn" @click.stop="triggerPtzCmd('RIGHT')">▶</button>
                  </div>
                  <button class="ptz-mini-btn" @click.stop="triggerPtzCmd('DOWN')">▼</button>
                </div>

                <!-- 底部 OSD 描述条 -->
                <div class="video-single-desc num-mono">
                  <span>机位预置位: {{ activeCamObj.preset }}</span>
                  <span>光圈: F1.4 · 焦距: 35mm</span>
                  <span>编码延时: 42ms · 丢包率: 0.00%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 监视器底部快捷控制手柄 (高度、按键、质感完全同等对齐右侧控制台) -->
          <div class="video-control-bar">
            <div class="bar-left-group">
              <span class="bar-lbl">机位聚焦:</span>
              <div class="video-btn-group">
                <button v-for="cam in monitorCameras" :key="cam.id"
                  :class="['btn-cam-switch', { active: selectedCamId === cam.id }]"
                  @click="switchCamFocus(cam.id)">
                  {{ cam.shortName }}
                </button>
              </div>
            </div>
            <div class="bar-right-group">
              <button :class="['btn-cam-tool', { active: videoLayoutMode === 4 }]"
                @click="setVideoLayout(4)">
                四分屏全览
              </button>
              <button class="btn-cam-tool btn-snap-action" @click="takeSnapshotCurrent">
                一键抓拍
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：LED 主大屏实时调度与推屏监视视窗 (真实 16:9 画幅，快捷推屏) -->
      <div class="screen-monitor-panel glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <SvgIcon name="SvgLedScreen" size="18" class="text-primary" />
            <span>LED 主大屏实时回传与推屏调度</span>
          </div>
          <div class="screen-header-meta">
            <span class="screen-tag num-mono">SDI-1 输入 · 1080P60</span>
            <span class="live-dot online"><i class="status-dot online"></i> 实时广播</span>
          </div>
        </div>

        <div class="screen-monitor-body">
          <!-- 16:9 仿真监视器画面 (专业广电级工控监视机架) -->
          <div class="screen-bezel-frame">
            <div class="screen-canvas-preview">
              <!-- 监视器 OSD 字符叠加 -->
              <div class="osd-top-bar num-mono">
                <span class="osd-green">TC 00:14:28:19</span>
                <span class="osd-ch">[CH: {{ currentScreenSource }}]</span>
                <span class="rec-dot">● REC 4K UHD</span>
                <span class="osd-audio">AUD CH1/2 <span class="audio-bar-anim"></span></span>
              </div>

              <!-- 画面内容展示：根据信号源动态呈现 -->
              <!-- 1. 赛事比分模式 (ARES-21 破纪录特写) -->
              <div v-if="currentScreenSource === 'SCORE'" class="match-live-content">
                <div class="live-headline">
                  <span class="race-title">2026 全国游泳锦标赛 · 男子100米自由泳决赛</span>
                  <span class="record-badge">新世界纪录 WR 46.80s</span>
                </div>

                <div class="winner-row">
                  <div class="rank-circle gold">1</div>
                  <div class="lane-num num-mono">第4道</div>
                  <div class="athlete-name">潘展乐 (Z.L. PAN)</div>
                  <div class="team-name">中国 (CHN)</div>
                  <div class="score-time num-mono font-bold">46.80s</div>
                  <span class="gold-trophy-tag">
                    <SvgIcon name="SvgTrophy" size="14" style="margin-right: 4px;" />
                    金牌 WR
                  </span>
                </div>

                <!-- 亚军季军紧随其后成绩条 -->
                <div class="runnerup-row num-mono">
                  <div class="r-item">2. 第5道 查尔莫斯 (AUS) 47.48s (+0.68)</div>
                  <div class="r-item">3. 第2道 波波维奇 (ROU) 47.52s (+0.72)</div>
                </div>
              </div>

              <!-- 2. 水下 4K 导播机位模式 -->
              <div v-else-if="currentScreenSource === 'CAM'" class="cam-live-content">
                <div class="cam-hud-cross"></div>
                <div class="cam-meta-tag num-mono">CAM-SUB-02 [4K60P RTSP] 码率 8.6Mbps</div>
                <div class="cam-desc">跳水深水池 5.5m 水下高速慢动作机位实时回传</div>
              </div>

              <!-- 3. 颁奖仪式国旗特写模式 -->
              <div v-else-if="currentScreenSource === 'FLAG'" class="flag-live-content">
                <div class="flag-headline">颁奖仪式升旗机组特写画面</div>
                <div class="flag-tri-display">
                  <div class="flag-card main">1. 中国 (CHN) [冠军国旗上升 100%]</div>
                  <div class="flag-card">2. 澳大利亚 (AUS) [85%]</div>
                  <div class="flag-card">3. 罗马尼亚 (ROU) [70%]</div>
                </div>
              </div>

              <!-- 4. 紧急安全黑屏防呆模式 -->
              <div v-else class="blackout-live-content">
                <div class="blackout-warn">EMERGENCY BLACKOUT ACTIVE</div>
                <div class="blackout-desc num-mono">广播通道已安全静默 · 正在等待主裁判仲裁信号复位</div>
              </div>
            </div>
          </div>

          <!-- 监视器底部快捷推屏控制手柄 (沙金广播切换台风格按键) -->
          <div class="screen-control-bar">
            <span class="bar-lbl">广播主路通道切换:</span>
            <div class="screen-btn-group">
              <button :class="['btn-src-switch', { active: currentScreenSource === 'SCORE' }]"
                @click="switchScreenSource('SCORE')">
                <SvgIcon name="SvgMatchScore" size="14" style="margin-right: 4px;" />
                ARES-21 赛事比分
              </button>
              <button :class="['btn-src-switch', { active: currentScreenSource === 'CAM' }]"
                @click="switchScreenSource('CAM')">
                <SvgIcon name="SvgCameraMatrix" size="14" style="margin-right: 4px;" />
                4K 水下机位
              </button>
              <button :class="['btn-src-switch', { active: currentScreenSource === 'FLAG' }]"
                @click="switchScreenSource('FLAG')">
                <SvgIcon name="SvgFlagSystem" size="14" style="margin-right: 4px;" />
                颁奖国旗特写
              </button>
              <button :class="['btn-src-switch btn-blackout', { active: currentScreenSource === 'BLACK' }]"
                @click="switchScreenSource('BLACK')">
                紧急安全黑屏
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. 下排保障控制台：24h 场地照明功率走势 (左 50%) + 主馆赛场环境舒适度遥测 (右 50%) -->
    <div class="dashboard-telemetry-row">
      <!-- 左侧：24h 场地照明功率走势 -->
      <div class="energy-trend-box glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <SvgIcon name="SvgLighting" size="18" class="text-primary" />
            <span>24h 场地照明功率走势与能耗监测 (kW)</span>
          </div>
          <div class="trend-header-right">
            <span class="lighting-mode-badge"><i class="status-dot online"></i> 赛事高照度 (Class I)</span>
            <span class="num-mono current-power-val">142.8 <small>kW</small></span>
          </div>
        </div>

        <!-- 照明快捷时段工况胶囊导航 -->
        <div class="lighting-mode-strip">
          <div class="strip-item">
            <span class="strip-label">00:00~06:00</span>
            <span class="strip-name">夜间值守</span>
            <span class="strip-val num-mono">18.2 kW</span>
          </div>
          <div class="strip-item">
            <span class="strip-label">08:00~12:00</span>
            <span class="strip-name">日常训练</span>
            <span class="strip-val num-mono">58.4 kW</span>
          </div>
          <div class="strip-item">
            <span class="strip-label">14:00~17:30</span>
            <span class="strip-name">赛前热身</span>
            <span class="strip-val num-mono">86.0 kW</span>
          </div>
          <div class="strip-item active">
            <span class="strip-label">19:30~22:00</span>
            <span class="strip-name">赛事转播 (当前)</span>
            <span class="strip-val num-mono">142.8 kW</span>
          </div>
        </div>

        <!-- SVG 工业能耗走势图 (平滑贝塞尔曲线、黄金发光渐变与标尺参考线) -->
        <div class="chart-mini-svg">
          <svg viewBox="0 0 540 168" class="line-svg">
            <defs>
              <linearGradient id="goldLineGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="#C8963E" />
                <stop offset="45%" stop-color="#E2B155" />
                <stop offset="85%" stop-color="#D99B26" />
                <stop offset="100%" stop-color="#C8963E" />
              </linearGradient>
              <linearGradient id="goldAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="rgba(200, 150, 62, 0.30)" />
                <stop offset="60%" stop-color="rgba(200, 150, 62, 0.08)" />
                <stop offset="100%" stop-color="rgba(200, 150, 62, 0.01)" />
              </linearGradient>
              <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            <!-- 横向功率刻度虚线 (0kW ~ 200kW) -->
            <g class="power-grid-lines">
              <line x1="36" y1="20" x2="525" y2="20" stroke="rgba(200, 164, 92, 0.16)" stroke-dasharray="3,3" />
              <text x="30" y="24" fill="#8B7355" font-size="14" text-anchor="end" class="num-mono">200</text>
              <line x1="36" y1="48" x2="525" y2="48" stroke="rgba(200, 164, 92, 0.16)" stroke-dasharray="3,3" />
              <text x="30" y="52" fill="#8B7355" font-size="14" text-anchor="end" class="num-mono">150</text>
              <line x1="36" y1="76" x2="525" y2="76" stroke="rgba(200, 164, 92, 0.16)" stroke-dasharray="3,3" />
              <text x="30" y="80" fill="#8B7355" font-size="14" text-anchor="end" class="num-mono">100</text>
              <line x1="36" y1="104" x2="525" y2="104" stroke="rgba(200, 164, 92, 0.16)" stroke-dasharray="3,3" />
              <text x="30" y="108" fill="#8B7355" font-size="14" text-anchor="end" class="num-mono">50</text>
              <line x1="36" y1="130" x2="525" y2="130" stroke="rgba(200, 164, 92, 0.35)" stroke-width="1.2" />
              <text x="30" y="134" fill="#8B7355" font-size="14" text-anchor="end" class="num-mono">0</text>
            </g>

            <!-- 赛事高照度时段高光背景条 -->
            <rect x="385" y="12" width="135" height="118" rx="4" fill="rgba(200, 150, 62, 0.08)" />
            <text x="452" y="25" fill="#A8823E" font-size="14" font-weight="600" text-anchor="middle">晚间高照度赛段</text>

            <!-- 面积填充渐变 -->
            <path
              d="M 40,121 C 70,122 100,121 125,115 C 145,102 165,84 195,82 C 220,81 240,86 260,88 C 280,90 295,68 320,65 C 345,62 370,74 395,71 C 415,68 435,46 460,45 C 480,45 495,48 505,46 L 505,130 L 40,130 Z"
              fill="url(#goldAreaGrad)" />

            <!-- 平滑贝塞尔功率曲线 -->
            <path
              d="M 40,121 C 70,122 100,121 125,115 C 145,102 165,84 195,82 C 220,81 240,86 260,88 C 280,90 295,68 320,65 C 345,62 370,74 395,71 C 415,68 435,46 460,45 C 480,45 495,48 505,46"
              fill="none" stroke="url(#goldLineGrad)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"
              filter="url(#goldGlow)" />

            <circle cx="195" cy="82" r="3" fill="#FFFDF9" stroke="#C8963E" stroke-width="1.8" />
            <circle cx="320" cy="65" r="3" fill="#FFFDF9" stroke="#C8963E" stroke-width="1.8" />

            <line x1="460" y1="26" x2="460" y2="130" stroke="#C8963E" stroke-dasharray="2,2" stroke-width="1.2" />
            <circle cx="460" cy="45" r="7.5" fill="none" stroke="#E5AC44" stroke-width="1.5" class="peak-pulse-ring" />
            <circle cx="460" cy="45" r="4" fill="#C8963E" stroke="#FFFDF9" stroke-width="1.5" />

            <!-- 当前峰值悬浮标签 -->
            <g transform="translate(325, 34)">
              <rect x="0" y="0" width="125" height="24" rx="4" fill="#2C1810" />
              <text x="62" y="17" fill="#E5AC44" font-size="14" font-weight="bold" text-anchor="middle"
                class="num-mono">142.8 kW (峰值)</text>
            </g>

            <!-- X 轴时间刻度 -->
            <text x="40" y="152" fill="#8B7355" font-size="14" text-anchor="middle">00:00</text>
            <text x="125" y="152" fill="#8B7355" font-size="14" text-anchor="middle">06:00</text>
            <text x="195" y="152" fill="#8B7355" font-size="14" text-anchor="middle">08:30 (训练)</text>
            <text x="260" y="152" fill="#8B7355" font-size="14" text-anchor="middle">12:00</text>
            <text x="320" y="152" fill="#8B7355" font-size="14" text-anchor="middle">14:30 (热身)</text>
            <text x="395" y="152" fill="#8B7355" font-size="14" text-anchor="middle">18:00</text>
            <text x="475" y="152" fill="#C8963E" font-size="14" font-weight="bold" text-anchor="middle">19:30
              (当前)</text>
          </svg>
        </div>

        <!-- 底部微能耗工况统计指标条 (名称与数值在同一行并列显示) -->
        <div class="lighting-metrics-footer">
          <div class="metric-col">
            <span class="m-label">全天最高负荷:</span>
            <span class="m-val num-mono">142.8 <small>kW</small></span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-col">
            <span class="m-label">谷值清场负荷:</span>
            <span class="m-val num-mono">16.5 <small>kW</small></span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-col">
            <span class="m-label">变压器负荷率:</span>
            <span class="m-val num-mono">71.4% <small>(正常)</small></span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-col">
            <span class="m-label">智能恒照度节电:</span>
            <span class="m-val num-mono text-success">18.6%</span>
          </div>
        </div>
      </div>

      <!-- 右侧：主馆赛场环境舒适度与竞技水质动态遥测 -->
      <div class="environment-telemetry-box glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <SvgIcon name="SvgSwimmingPool" size="18" class="text-primary" />
            <span>主馆赛场环境舒适度与竞技水质动态遥测</span>
          </div>
          <div class="env-header-right">
            <span class="env-tag-live"><i class="status-dot online"></i> 实时传感器巡检中</span>
            <span class="panel-subtitle">World Aquatics 认证标准</span>
          </div>
        </div>
        <div class="env-telemetry-grid">
          <div v-for="env in envTelemetry" :key="env.label" class="env-metric-item">
            <div class="env-item-label">{{ env.label }}</div>
            <div class="env-item-val-row">
              <span class="env-val num-mono">{{ env.value }}</span>
              <span class="env-unit">{{ env.unit }}</span>
            </div>
            <div class="env-bar-wrap">
              <div class="env-bar-fill" :style="{ width: env.progress + '%' }"></div>
            </div>
            <div class="env-standard-text">{{ env.standard }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 5. 底层基础设施：全场异构通信总线物理链路健康矩阵 -->
    <div class="bus-matrix-section glass-panel">
      <div class="panel-header">
        <div class="header-title">
          <SvgIcon name="SvgAdapterBook" size="18" class="text-primary" />
          <span>全场异构物理通信总线与链路健康矩阵</span>
        </div>
        <div class="bus-header-right">
          <span class="bus-pill online"><i class="status-dot online"></i> 4大总线池全活</span>
          <span class="panel-subtitle">平均往返时延: 14.8ms · 实时重试: 0</span>
        </div>
      </div>
      <div class="bus-cards-grid">
        <div v-for="bus in busLinks" :key="bus.name" class="bus-item-card">
          <div class="bus-item-head">
            <div class="bus-icon-wrap">
              <SvgIcon :name="bus.icon" size="18" />
            </div>
            <div class="bus-head-info">
              <span class="bus-name">{{ bus.name }}</span>
              <span class="bus-proto num-mono">{{ bus.proto }}</span>
            </div>
            <span class="bus-rate-badge num-mono">{{ bus.rate }}</span>
          </div>
          <div class="bus-item-body">
            <div class="bus-channel-tag num-mono">{{ bus.tag }}</div>
            <div class="bus-instances">挂载设备: {{ bus.instances }}</div>
            <div class="bus-metrics-text num-mono">{{ bus.metrics }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

const router = useRouter()
const appStore = useAppStore()

// 2D 拓扑图图层筛选与设备节点数据
const activeTopoFilter = ref('ALL')
const selectedNodeId = ref('clock') // 默认聚焦有告警的大厅子钟
const topoFilters = [
  { key: 'ALL', label: '全部设备 (8)' },
  { key: 'TIMING_CLOCK', label: '计时与时钟' },
  { key: 'AUDIO_VIDEO', label: '音视与大屏' },
  { key: 'POWER_LIGHT', label: '配电与电控' }
]

const topoNodes = [
  {
    id: 'lighting',
    type: 'POWER_LIGHT',
    name: '配电柜回路B3',
    sub: 'Modbus · 142.8kW',
    icon: 'SvgLighting',
    x: 220,
    y: 50,
    status: 'online',
    linkTarget: { x: 220, y: 100 }
  },
  {
    id: 'led',
    type: 'AUDIO_VIDEO',
    name: '主LED大屏4K',
    sub: 'Novastar 4K 直通',
    icon: 'SvgLedScreen',
    x: 620,
    y: 50,
    status: 'online',
    linkTarget: { x: 620, y: 100 }
  },
  {
    id: 'valve',
    type: 'POWER_LIGHT',
    name: '跳水消波气垫阀',
    sub: '0.6MPa 气阀就绪',
    icon: 'SvgAirCondition',
    x: 1180,
    y: 50,
    status: 'online',
    linkTarget: { x: 1220, y: 100 }
  },
  {
    id: 'clock',
    type: 'TIMING_CLOCK',
    name: '观众大厅数码子钟',
    sub: 'NTP漂移 1450ms',
    icon: 'SvgMasterClock',
    x: 1500,
    y: 50,
    status: 'warning',
    linkTarget: { x: 1500, y: 100 }
  },
  {
    id: 'flag',
    type: 'POWER_LIGHT',
    name: '自动升旗PLC系统',
    sub: 'S7-1200 · 待命',
    icon: 'SvgFlagSystem',
    x: 220,
    y: 395,
    status: 'online',
    linkTarget: { x: 220, y: 345 }
  },
  {
    id: 'timing',
    type: 'TIMING_CLOCK',
    name: 'ARES-21计时计分',
    sub: '欧米茄仲裁终端',
    icon: 'SvgMatchScore',
    x: 620,
    y: 395,
    status: 'online',
    linkTarget: { x: 620, y: 345 }
  },
  {
    id: 'audio',
    type: 'AUDIO_VIDEO',
    name: 'Soundcraft调音台',
    sub: 'Vi3000 · 16通道',
    icon: 'SvgSoundMatrix',
    x: 1180,
    y: 395,
    status: 'online',
    linkTarget: { x: 1220, y: 345 }
  },
  {
    id: 'cam',
    type: 'AUDIO_VIDEO',
    name: '跳水池水下摄像机',
    sub: '4K60 RTSP流',
    icon: 'SvgCameraMatrix',
    x: 1500,
    y: 395,
    status: 'online',
    linkTarget: { x: 1500, y: 345 }
  }
]

const filteredTopoNodes = computed(() => {
  if (activeTopoFilter.value === 'ALL') return topoNodes
  return topoNodes.filter(n => n.type === activeTopoFilter.value)
})

const handleNodeClick = (node) => {
  selectedNodeId.value = node.id
  ElMessage.info(`聚焦查看拓扑设备: ${node.name} (${node.sub})`)
}

// 视频监控视窗：四路高清 RTSP 汇聚与机位调度
const videoLayoutMode = ref(4) // 4: 四分屏巡检, 1: 单屏特写
const selectedCamId = ref('cam1')
const liveVideoTime = ref('')
const liveVideoTc = ref('00:14:28:19')

const monitorCameras = [
  {
    id: 'cam1',
    code: 'CAM-01',
    name: 'CAM-01 比赛池主路全景',
    shortName: 'CAM-01 比赛池',
    res: '1080P',
    fps: 60,
    bitrate: '4.2Mbps',
    preset: 'PRESET-01 (终点全景)',
    themeClass: 'cam-theme-pool',
    aiTag: '泳道跟踪 · 8道全覆盖',
    aiBoxStyle: { top: '32%', left: '25%', width: '45%', height: '36%' }
  },
  {
    id: 'cam2',
    code: 'CAM-02',
    name: 'CAM-02 跳水水下4K慢动作',
    shortName: 'CAM-02 水下4K',
    res: '4K UHD',
    fps: 60,
    bitrate: '8.6Mbps',
    preset: 'PRESET-04 (触壁特写)',
    themeClass: 'cam-theme-underwater',
    aiTag: '水下姿态 · 触板识别',
    aiBoxStyle: { top: '36%', left: '38%', width: '30%', height: '38%' }
  },
  {
    id: 'cam3',
    code: 'CAM-03',
    name: 'CAM-03 VIP看台高速云台',
    shortName: 'CAM-03 看台云台',
    res: '1080P',
    fps: 30,
    bitrate: '3.8Mbps',
    preset: 'PRESET-02 (主席台全貌)',
    themeClass: 'cam-theme-stand',
    aiTag: '客流密度 · 状态优良',
    aiBoxStyle: { top: '28%', left: '22%', width: '52%', height: '42%' }
  },
  {
    id: 'cam4',
    code: 'CAM-04',
    name: 'CAM-04 赛前检录进场通道',
    shortName: 'CAM-04 检录通道',
    res: '1080P',
    fps: 30,
    bitrate: '3.2Mbps',
    preset: 'PRESET-01 (通道闸机)',
    themeClass: 'cam-theme-gate',
    aiTag: '人脸比对 · 100%放行',
    aiBoxStyle: { top: '30%', left: '35%', width: '30%', height: '44%' }
  }
]

const activeCamObj = computed(() => {
  return monitorCameras.find(c => c.id === selectedCamId.value) || monitorCameras[0]
})

const setVideoLayout = (mode) => {
  videoLayoutMode.value = mode
  ElMessage.info(mode === 4 ? '已切换至 4分屏多路巡检模式' : `已切换至单屏特写：【${activeCamObj.value.name}】`)
}

const selectCamFocus = (id) => {
  selectedCamId.value = id
}

const zoomCamDetail = (id) => {
  selectedCamId.value = id
  videoLayoutMode.value = 1
  ElMessage.success(`已放大机位特写：【${activeCamObj.value.name}】`)
}

const switchCamFocus = (id) => {
  selectedCamId.value = id
  const cam = monitorCameras.find(c => c.id === id)
  ElMessage.info(`已聚焦机位：【${cam ? cam.name : id}】`)
}

const takeCamSnapshot = (cam) => {
  ElMessage.success(`【${cam.name}】实时画面抓拍成功，已归档至媒体资源库`)
}

const takeSnapshotCurrent = () => {
  ElMessage.success(`已抓拍当前【${activeCamObj.value.name}】实时画面`)
}

const triggerPtzCmd = (dir) => {
  const map = { UP: '向上俯仰', DOWN: '向下俯仰', LEFT: '向左水平旋转', RIGHT: '向右水平旋转' }
  ElMessage.info(`【${activeCamObj.value.code}】PTZ云台指令已发送：${map[dir]}`)
}

const updateVideoClock = () => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  const y = now.getFullYear()
  const m = pad(now.getMonth() + 1)
  const d = pad(now.getDate())
  const hh = pad(now.getHours())
  const mm = pad(now.getMinutes())
  const ss = pad(now.getSeconds())
  liveVideoTime.value = `${y}-${m}-${d} ${hh}:${mm}:${ss}`
  const ff = pad(Math.floor(now.getMilliseconds() / 40))
  liveVideoTc.value = `${hh}:${mm}:${ss}:${ff}`
}

let videoTimer = null
onMounted(() => {
  updateVideoClock()
  videoTimer = setInterval(updateVideoClock, 1000)
})

onUnmounted(() => {
  if (videoTimer) clearInterval(videoTimer)
})

// 告警流高级联动与交互状态
const activeAlarmFilter = ref('ALL')
const isMuted = ref(false)

const locateTopoNode = (deviceName) => {
  const match = topoNodes.find(n => deviceName.includes(n.name.substring(0, 3)) || n.name.includes(deviceName.substring(0, 3)))
  if (match) {
    selectedNodeId.value = match.id
    ElMessage.success(`已在 2D 拓扑图中高亮锁定：【${match.name}】`)
  } else {
    ElMessage.info(`定位关联设备：${deviceName}`)
  }
}

const toggleSilenceAlarms = () => {
  isMuted.value = !isMuted.value
  ElMessage.warning(isMuted.value ? '已临时静音主控声光告警蜂鸣器' : '已恢复主控声光告警蜂鸣器')
}

// 告警分类指标统计
const emergencyCount = computed(() => displayAlarms.value.filter(a => a.level === 'EMERGENCY').length)
const warningCount = computed(() => displayAlarms.value.filter(a => a.level === 'WARNING').length)
const infoCount = computed(() => displayAlarms.value.filter(a => a.level === 'INFO').length)

const filteredAlarms = computed(() => {
  if (activeAlarmFilter.value === 'ALL') return displayAlarms.value
  return displayAlarms.value.filter(a => a.level === activeAlarmFilter.value)
})

const batchConfirmAlarms = () => {
  const unconfirmed = displayAlarms.value.filter(a => a.status === 'NEW')
  unconfirmed.forEach(a => appStore.confirmAlarm(a.id))
  ElMessage.success(`已批量确认 ${unconfirmed.length} 项实时故障告警`)
}

// 大屏信号源调度
const currentScreenSource = ref('SCORE') // 'SCORE', 'CAM', 'FLAG', 'BLACK'
const switchScreenSource = (src) => {
  currentScreenSource.value = src
  const names = {
    SCORE: 'Omega ARES-21 赛事比分',
    CAM: '现场 4K 水下机位实时追踪',
    FLAG: '颁奖仪式三面国旗特写',
    BLACK: '紧急安全黑屏 (防呆)'
  }
  ElMessage.success(`LED 主大屏信号已即时切换为：【${names[src]}】`)
}

// 工业级高拟真告警流数据 (双重保底，确保界面始终呈现生动的实时流水)
const displayAlarms = computed(() => {
  if (appStore.alarms && appStore.alarms.length > 0) {
    return appStore.alarms
  }
  return [
    {
      id: 'ALM-101',
      level: 'EMERGENCY',
      subsystem: 'STANDARD_CLOCK',
      device: '标准时钟子钟 CLK-HALL-06',
      title: '观众大厅数码子钟时间漂移过大',
      desc: '与北斗主母钟时钟偏差达到 1450ms (阈值 500ms)，可能引发检录时间不同步',
      time: '10:22:15',
      status: 'NEW'
    },
    {
      id: 'ALM-102',
      level: 'WARNING',
      subsystem: 'LIGHTING',
      device: '比赛池场地照明配电柜 B3',
      title: '配电箱回路B3瞬时过流波动',
      desc: '训练模式向赛事模式过渡时出现 14.2A 阶跃波动，现已进入自适应稳压',
      time: '10:15:32',
      status: 'CONFIRMED'
    },
    {
      id: 'ALM-103',
      level: 'EMERGENCY',
      subsystem: 'FIELD_VIDEO',
      device: '跳水池水下摄像机 CAM-SUB-02',
      title: '水下高清视频流丢包率超过 15%',
      desc: 'RTSP 码流检测到关键帧延迟达 850ms，触发网络交换机光电转换器排查预警',
      time: '09:58:40',
      status: 'NEW'
    },
    {
      id: 'ALM-104',
      level: 'WARNING',
      subsystem: 'AUDIO_MATRIX',
      device: 'Soundcraft Vi3000 数字调音台',
      title: '串口通讯心跳超时重试 (COM3/RS232)',
      desc: '主控制台下发场景音效切流指令时收到应答延迟 320ms，已自动启用备用总线重发成功',
      time: '09:40:18',
      status: 'PROCESSING'
    },
    {
      id: 'ALM-105',
      level: 'INFO',
      subsystem: 'FIELD_VIDEO',
      device: '看台主摄像机 CAM-FIELD-01',
      title: 'RTSP流自愈重连完成',
      desc: '交换机瞬时抖动触发指数退避重连状态机，耗时 1.2s 自动恢复',
      time: '09:12:05',
      status: 'RECOVERED'
    },
    {
      id: 'ALM-106',
      level: 'INFO',
      subsystem: 'LED_SCREEN',
      device: 'Novastar UHD-v3.0 视频推屏处理器',
      title: '大屏输入信号源成功切换为计时计分',
      desc: '已完成 SDI-1 (转播流) 向 TCP 接收卡 (ARES-21) 的画面无缝淡入淡出切换',
      time: '08:30:00',
      status: 'CLOSED'
    }
  ]
})

// 全场通信总线物理链路健康矩阵
const busLinks = [
  {
    name: '工业串口总线池',
    proto: 'RS232 / RS485',
    tag: 'COM1 / COM3 / COM4',
    instances: '调音台、照明Modbus、升旗PLC',
    metrics: '波特率 115200 · 轮询 500ms · 往返 14ms',
    rate: '99.8%',
    icon: 'SvgAdapterBook'
  },
  {
    name: 'TCP/UDP 网络长连接池',
    proto: 'Socket / NTP / HTTP',
    tag: 'Port: 5000 / 123 / 8088',
    instances: '计时计分、北斗卫星授时、LED推屏',
    metrics: '长连接 3路 · 丢包 0.00% · 时钟漂移 2ms',
    rate: '100%',
    icon: 'SvgMasterClock'
  },
  {
    name: '流媒体分发转播矩阵',
    proto: 'RTSP / WebRTC',
    tag: '1080P60 · H.264 / H.265',
    instances: '水下抓拍机位、看台云台、转播监视',
    metrics: '实时码率 8.6 Mbps · 缓冲 120ms · 0重连',
    rate: '60 fps',
    icon: 'SvgCameraMatrix'
  },
  {
    name: 'API 与代理隔离网关',
    proto: 'RESTful / iframe',
    tag: 'Ticket 单次令牌鉴权',
    instances: '售验票闸机、信息发布、Redis会话',
    metrics: '短时效鉴权 · 响应 28ms · 跨域代理正常',
    rate: '100%',
    icon: 'SvgSecurityShield'
  }
]

// 主馆赛场环境舒适度与竞技水质遥测
const envTelemetry = [
  { label: '50M比赛池水温', value: '26.8', unit: '℃', standard: '标准: 25~28℃ (国际泳联)', progress: 75 },
  { label: '跳水深水池水温', value: '28.2', unit: '℃', standard: '标准: 26~30℃ (恒温保温)', progress: 80 },
  { label: '池水 pH 动态值', value: '7.45', unit: 'pH', standard: '标准: 7.2~7.8 (弱碱舒适)', progress: 68 },
  { label: '游离余氯电极浓度', value: '0.55', unit: 'mg/L', standard: '标准: 0.3~1.0 mg/L', progress: 55 },
  { label: '场馆室内环境温度', value: '24.6', unit: '℃', standard: '新风自适应恒温自控', progress: 60 },
  { label: '比赛看台相对湿度', value: '58.5', unit: '%', standard: '标准: 45~65% (除湿平衡)', progress: 65 },
  { label: '场地平均垂直照度', value: '2040', unit: 'Lux', standard: 'HDTV转播级赛事照明', progress: 85 },
  { label: '看台主扩声声压级', value: '82.4', unit: 'dB', standard: '语言清晰度 STI 0.62', progress: 72 }
]

const handleAlarmQuick = (alm) => {
  if (alm.status === 'NEW') {
    appStore.confirmAlarm(alm.id)
    ElMessage.success(`已确认告警: ${alm.title}`)
  } else {
    router.push('/ops/alarms')
  }
}
</script>

<style scoped>
.dashboard-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 顶部 KPI (大马士革白 + 沙金微投影) */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-card {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  background: linear-gradient(145deg, var(--do-bg-card) 0%, rgba(var(--th-accent-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--th-accent-rgb), 0.22);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.22s ease, box-shadow 0.22s ease, transform 0.22s ease;
}

.kpi-card:hover {
  border-color: var(--do-gold);
  box-shadow: 0 4px 16px rgba(var(--th-accent-rgb), 0.16);
}

.kpi-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  margin-bottom: 2px;
}

.kpi-icon-wrap.primary {
  background: rgba(var(--th-accent-rgb), 0.15);
  color: var(--do-gold);
}

.kpi-icon-wrap.success {
  background: var(--do-success-bg);
  color: var(--do-success);
}

.kpi-icon-wrap.warning {
  background: var(--do-warning-bg);
  color: var(--do-warning);
}

.kpi-icon-wrap.info {
  background: var(--do-info-bg);
  color: var(--do-info);
}

.kpi-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
  gap: 4px;
}

.kpi-label {
  font-size: 14px;
  color: var(--do-text-secondary);
  text-align: center;
  width: 100%;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--do-text-primary);
  display: flex;
  align-items: baseline;
  justify-content: center;
  text-align: center;
  width: 100%;
  margin: 2px 0;
  gap: 4px;
}

.kpi-value small {
  font-size: 14px;
  font-weight: normal;
  color: var(--do-text-secondary);
}

.kpi-trend {
  font-size: 14px;
  color: var(--do-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
}

.trend-tag.success {
  background: var(--do-success-bg);
  color: var(--do-success);
  border: none;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dashboard-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 24px;
}

/* 2. 【核心主馆 2D 平面设备拓扑视窗】(独占全宽大屏架构，高通透、零压盖) */
.venue-topology-section {
  display: flex;
  flex-direction: column;
  width: 100%;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--do-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(var(--th-accent-rgb), 0.04);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.cad-badge {
  font-size: 14px;
  color: var(--do-gold-deep);
  /* background: rgba(var(--th-accent-rgb), 0.12); */
  /* border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  padding: 3px 10px; */
  /* border-radius: 4px; */
  /* font-weight: 600; */
}

.topology-header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.topo-filter-pills {
  display: flex;
  gap: 8px;
}

.filter-pill {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  padding: 4px 12px;
  border-radius: 14px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.filter-pill:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.filter-pill.active {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.3);
}

.topology-legend {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: var(--do-text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item .dot.online {
  background: var(--do-success);
}

.legend-item .dot.warning {
  background: var(--do-warning);
}

.legend-item .dot.bus-fiber {
  width: 16px;
  height: 2px;
  border-radius: 1px;
  background: repeating-linear-gradient(90deg, var(--do-gold), var(--do-gold) 4px, transparent 4px, transparent 8px);
}

.venue-svg-wrapper {
  width: 100%;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  padding: 0;
  margin: 0;
  background: var(--do-bg-input);
  overflow: hidden;
  position: relative;
}

.venue-plan-svg {
  width: 100%;
  height: auto;
  min-height: 440px;
  display: block;
}

/* 拓扑网络虚线流动动画 */
@keyframes flowDash {
  to {
    stroke-dashoffset: -20;
  }
}

.flow-bus-dash {
  animation: flowDash 15s linear infinite;
}

/* 设备节点卡片样式与交互微动效 */
.svg-node-item {
  cursor: pointer;
  opacity: 1;
  transition: opacity 0.2s ease;
}

/* 统一感应区：内部文字、图标和呼吸光环全部禁用事件捕获，仅底层背景卡片响应鼠标，消除层级边界抖动 */
.svg-node-item * {
  pointer-events: none;
}

.svg-node-item.dimmed {
  opacity: 0.22;
}

.node-card-bg {
  pointer-events: all;
  fill: var(--do-bg-card-hover);
  stroke: var(--do-gold);
  stroke-width: 1.2;
  filter: drop-shadow(0 2px 6px rgba(var(--th-shadow-rgb), 0.08));
  transition: stroke 0.22s ease, stroke-width 0.22s ease, fill 0.22s ease, filter 0.22s ease;
}

.node-icon-bg {
  fill: rgba(var(--th-accent-rgb), 0.14);
  stroke: rgba(var(--th-accent-rgb), 0.4);
  stroke-width: 1;
  transition: stroke 0.22s ease, fill 0.22s ease;
}

.node-icon-foreign {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--do-gold-deep);
}

.node-select-glow {
  animation: selectPulse 1.8s infinite ease-in-out;
}

@keyframes selectPulse {
  0% {
    stroke: var(--do-warning);
    stroke-width: 2;
    opacity: 1;
  }

  50% {
    stroke: var(--do-gold-hover);
    stroke-width: 3.5;
    opacity: 0.6;
  }

  100% {
    stroke: var(--do-warning);
    stroke-width: 2;
    opacity: 1;
  }
}

/* 鼠标悬停或选中：零坐标位移，采用高保真微边框加粗与四周柔和发光，彻底杜绝抖动与漂移 */
.svg-node-item:hover .node-card-bg,
.svg-node-item.active .node-card-bg {
  stroke: var(--do-gold-deep);
  stroke-width: 2;
  fill: #FFFFFF;
  filter: drop-shadow(0 4px 14px rgba(var(--th-warning-rgb), 0.35));
}

.svg-node-item:hover .node-icon-bg,
.svg-node-item.active .node-icon-bg {
  fill: rgba(var(--th-accent-rgb), 0.24);
  stroke: var(--do-gold-deep);
  stroke-width: 1.5;
}

.svg-node-item.warning .node-card-bg {
  stroke: var(--do-warning);
  fill: var(--do-bg-card-hover);
}

.node-title {
  font-size: 14px;
  /* font-weight: 700; */
  fill: var(--do-text-primary);
  pointer-events: none;
}

.node-sub {
  font-size: 13px;
  fill: var(--do-text-secondary);
}

.node-status-dot.online {
  fill: var(--do-success);
}

.node-status-dot.warning {
  fill: var(--do-warning);
}

.node-status-dot.offline {
  fill: var(--do-text-muted);
}

@keyframes nodePulse {
  0% {
    r: 3.5px;
    opacity: 0.8;
  }

  50% {
    r: 7.2px;
    opacity: 0;
  }

  100% {
    r: 3.5px;
    opacity: 0;
  }
}

@keyframes nodePulseWarn {
  0% {
    r: 3.5px;
    opacity: 0.9;
  }

  50% {
    r: 7.5px;
    opacity: 0;
  }

  100% {
    r: 3.5px;
    opacity: 0;
  }
}

.node-status-ring.online {
  stroke: var(--do-success);
  fill: none;
  stroke-width: 1;
  animation: nodePulse 2.2s infinite ease-out;
}

.node-status-ring.warning {
  stroke: var(--do-warning);
  fill: none;
  stroke-width: 1.2;
  animation: nodePulseWarn 1.5s infinite ease-out;
}

.node-status-ring.offline {
  stroke: var(--do-text-muted);
  fill: none;
  stroke-width: 1;
  opacity: 0.3;
}

/* 拓扑视窗底部信息条 */
.topo-footer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  background: rgba(var(--th-accent-rgb), 0.06);
  border-top: 1px solid var(--do-border-light);
  font-size: 14px;
  color: var(--do-text-secondary);
}

.footer-stat-item {
  display: flex;
  align-items: center;
  gap: 7px;
}

.footer-stat-item b {
  color: var(--do-text-primary);
  font-weight: 600;
}

.footer-stat-item .stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.footer-stat-item .stat-dot.online {
  background: var(--do-success);
}

.footer-stat-item .stat-dot.warning {
  background: var(--do-warning);
}

.footer-stat-item.mode-tag {
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.12);
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.25);
}

/* 3. 【中排双翼核心控制台】：故障告警雷达 (左 50%) + LED 视窗与推屏调度 (右 50%) */
.dashboard-action-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 400px;
}

/* 左侧：视频监控画面视窗 (维持与右侧 LED 大屏同等的 420px 高度与 50% 宽度对称排布) */
.video-monitor-panel {
  display: flex;
  flex-direction: column;
  height: 420px;
}

/* 顶栏分屏分段控制器 (Segmented Control) */
.split-filter-pills {
  display: inline-flex;
  align-items: center;
  background: var(--do-bg-input);
  padding: 2px;
  border-radius: 14px;
  border: 1px solid var(--do-border-light);
  margin-left: 10px;
  gap: 2px;
}

.split-pill-btn {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: var(--do-text-secondary);
  cursor: pointer;
  transition: var(--transition-fast);
}

.split-pill-btn:hover {
  color: var(--do-text-primary);
}

.split-pill-btn.active {
  background: var(--do-gold);
  color: #FFFFFF;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

.video-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.video-tag {
  font-size: 13px;
  color: var(--do-text-secondary);
  background: var(--do-bg-input);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--do-border-light);
}

.btn-tool-link {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 4px;
  background: rgba(var(--th-accent-rgb), 0.12);
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
  color: var(--do-gold-deep);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  font-weight: 600;
  transition: var(--transition-fast);
}

.btn-tool-link:hover {
  background: var(--do-gold);
  color: #FFFFFF;
}

.video-monitor-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 10px 14px;
  gap: 8px;
  overflow: hidden;
}

/* 4 分屏多路实时巡检网格 (2x2 舒展布局) */
.video-quad-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 8px;
}

.cam-quad-cell {
  position: relative;
  background: #060B11;
  border: 1px solid rgba(var(--th-accent-rgb), 0.24);
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease;
  box-shadow: inset 0 0 14px rgba(0, 0, 0, 0.6);
}

.cam-quad-cell:hover {
  border-color: rgba(var(--th-accent-rgb), 0.65);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35), inset 0 0 16px rgba(var(--th-accent-rgb), 0.12);
}

.cam-quad-cell.active {
  border-color: var(--do-gold);
  box-shadow: 0 0 0 1px var(--do-gold), 0 4px 16px rgba(var(--th-accent-rgb), 0.25);
}

/* 视窗 OSD 顶栏 (黑透渐变，文字全展示不截断) */
.quad-osd-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 8px;
  background: linear-gradient(180deg, rgba(5, 9, 15, 0.88) 0%, rgba(5, 9, 15, 0.45) 70%, transparent 100%);
  font-size: 13px;
  pointer-events: none;
}

.osd-left-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.quad-cam-name {
  font-weight: 600;
  color: #F1F5F9;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.quad-cam-meta {
  color: #94A3B8;
  font-size: 13px;
  opacity: 0.9;
  white-space: nowrap;
}

.quad-screen-visual {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 场景矢量动态图层 SVG */
.cam-scene-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* 机位场景仿真微光影纹理 (深邃科技质感，严禁蓝紫渐变) */
.cam-theme-pool {
  background: radial-gradient(ellipse at 50% 60%, #0a2638 0%, #051622 60%, #030c14 100%);
}

.cam-theme-underwater {
  background: radial-gradient(ellipse at 45% 50%, #072e38 0%, #041a22 65%, #020e14 100%);
}

.cam-theme-stand {
  background: radial-gradient(ellipse at 50% 50%, #1c1810 0%, #120f09 65%, #080603 100%);
}

.cam-theme-gate {
  background: radial-gradient(ellipse at 50% 50%, #141c26 0%, #0c1219 65%, #05080c 100%);
}

/* 准星十字 */
.cam-crosshair {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 22px;
  height: 22px;
  transform: translate(-50%, -50%);
  pointer-events: none;
  opacity: 0.45;
}

.cam-crosshair::before,
.cam-crosshair::after {
  content: '';
  position: absolute;
  background: rgba(255, 255, 255, 0.6);
}

.cam-crosshair::before {
  top: 10px;
  left: 0;
  width: 22px;
  height: 1px;
}

.cam-crosshair::after {
  top: 0;
  left: 10px;
  width: 1px;
  height: 22px;
}

.cam-crosshair.large {
  width: 36px;
  height: 36px;
  opacity: 0.65;
}

.cam-crosshair.large::before {
  top: 17px;
  left: 0;
  width: 36px;
  height: 1px;
}

.cam-crosshair.large::after {
  top: 0;
  left: 17px;
  width: 1px;
  height: 36px;
}

/* 科技四角 AI HUD 角标与标签 (通透细角标，绝无生硬大膏药) */
.cam-ai-hud {
  position: absolute;
  pointer-events: none;
  transition: all 0.3s ease;
}

.hud-corner {
  position: absolute;
  width: 8px;
  height: 8px;
}

.hud-corner.tl { top: 0; left: 0; border-top: 1.5px solid #34D399; border-left: 1.5px solid #34D399; }
.hud-corner.tr { top: 0; right: 0; border-top: 1.5px solid #34D399; border-right: 1.5px solid #34D399; }
.hud-corner.bl { bottom: 0; left: 0; border-bottom: 1.5px solid #34D399; border-left: 1.5px solid #34D399; }
.hud-corner.br { bottom: 0; right: 0; border-bottom: 1.5px solid #34D399; border-right: 1.5px solid #34D399; }

.hud-tag {
  position: absolute;
  top: 4px;
  left: 6px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(8, 14, 22, 0.78);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(52, 211, 153, 0.45);
  color: #6EE7B7;
  font-size: 13px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
}

.hud-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 6px #10B981;
  animation: pulseDot 1.8s infinite;
}

.quad-osd-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: linear-gradient(0deg, rgba(5, 9, 15, 0.88) 0%, rgba(5, 9, 15, 0.45) 70%, transparent 100%);
  font-size: 13px;
  color: #CBD5E1;
  pointer-events: none;
}

.quad-ch-tag {
  color: var(--do-gold);
  font-weight: 700;
  background: rgba(var(--th-accent-rgb), 0.16);
  padding: 1px 5px;
  border-radius: 3px;
}

.quad-time {
  color: #94A3B8;
}

/* 悬停快捷蒙层 */
.quad-hover-mask {
  position: absolute;
  inset: 0;
  background: rgba(5, 9, 15, 0.5);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 6;
}

.cam-quad-cell:hover .quad-hover-mask {
  opacity: 1;
  pointer-events: all;
}

.btn-quad-zoom {
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  background: var(--do-gold);
  border: 1px solid var(--do-gold);
  color: #FFFFFF;
  display: inline-flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  transition: var(--transition-fast);
}

.btn-quad-snap {
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  transition: var(--transition-fast);
}

.btn-quad-zoom:hover,
.btn-quad-snap:hover {
  transform: translateY(-1px);
}

/* 单屏高保真特写视窗 */
.video-single-frame {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.video-single-frame .screen-bezel-frame {
  flex: 1;
  min-height: 0;
  background: #060B10;
  border: 1px solid var(--do-border-light);
  border-radius: var(--radius-sm);
  padding: 6px;
  display: flex;
  flex-direction: column;
}

.video-single-canvas {
  position: relative;
  flex: 1;
  min-height: 0;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.cam-ai-box-single {
  position: absolute;
  border: 1.5px solid rgba(var(--th-accent-rgb), 0.9);
  background: rgba(var(--th-accent-rgb), 0.08);
  box-shadow: 0 0 16px rgba(var(--th-accent-rgb), 0.35);
  pointer-events: none;
}

.cam-ai-box-single .ai-corner {
  position: absolute;
  width: 8px;
  height: 8px;
  border-color: #FFFFFF;
}

.cam-ai-box-single .ai-corner.tl { top: -2px; left: -2px; border-top: 2px solid #FFFFFF; border-left: 2px solid #FFFFFF; }
.cam-ai-box-single .ai-corner.tr { top: -2px; right: -2px; border-top: 2px solid #FFFFFF; border-right: 2px solid #FFFFFF; }
.cam-ai-box-single .ai-corner.bl { bottom: -2px; left: -2px; border-bottom: 2px solid #FFFFFF; border-left: 2px solid #FFFFFF; }
.cam-ai-box-single .ai-corner.br { bottom: -2px; right: -2px; border-bottom: 2px solid #FFFFFF; border-right: 2px solid #FFFFFF; }

.ai-label-single {
  position: absolute;
  top: -24px;
  left: 0;
  background: var(--do-gold);
  color: #FFFFFF;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 700;
  white-space: nowrap;
}

/* 云台 PTZ 浮动微控盘 */
.cam-ptz-floating {
  position: absolute;
  right: 12px;
  top: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  background: rgba(10, 16, 24, 0.78);
  padding: 6px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(4px);
  z-index: 4;
}

.ptz-mid-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ptz-mini-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #FFFFFF;
  border-radius: 3px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.ptz-mini-btn:hover {
  background: var(--do-gold);
  border-color: var(--do-gold);
}

.ptz-center-dot {
  font-size: 13px;
  font-weight: 700;
  color: var(--do-gold);
  padding: 0 2px;
}

.video-single-desc {
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 10px;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.85) 0%, transparent 100%);
  font-size: 13px;
  color: #CBD5E1;
}

/* 监视器底部快捷控制手柄 (左侧机位聚焦，右侧模式工具，质感高级) */
.video-control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: rgba(var(--th-accent-rgb), 0.04);
  border: 1px solid var(--do-border-light);
  border-radius: var(--radius-sm);
  min-height: 38px;
}

.bar-left-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-lbl {
  font-size: 13px;
  color: var(--do-text-secondary);
  font-weight: 600;
  white-space: nowrap;
}

.video-btn-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-cam-switch {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-light);
  color: var(--do-text-regular);
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-cam-switch:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.btn-cam-switch.active {
  background: rgba(var(--th-accent-rgb), 0.16);
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
  box-shadow: 0 0 8px rgba(var(--th-accent-rgb), 0.2);
}

.bar-right-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-cam-tool {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  color: var(--do-text-secondary);
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-cam-tool:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.btn-cam-tool.active {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
}

.btn-cam-tool.btn-snap-action {
  background: rgba(var(--th-accent-rgb), 0.1);
  border-color: rgba(var(--th-accent-rgb), 0.35);
  color: var(--do-gold-deep);
}

.btn-cam-tool.btn-snap-action:hover {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
}

/* 右侧：LED 主大屏实时调度与推屏监视视窗 */
.screen-monitor-panel {
  display: flex;
  flex-direction: column;
  height: 420px;
}

.screen-header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.screen-tag {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: rgba(var(--th-shadow-rgb), 0.04);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--do-border-light);
}

.live-dot.online {
  font-size: 14px;
  color: var(--do-success);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.screen-monitor-body {
  flex: 1;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--do-bg-input);
}

/* 16:9 专业工控大屏监视边框 */
.screen-bezel-frame {
  flex: 1;
  background: var(--do-bg-dark);
  border: 2px solid var(--do-text-primary);
  border-radius: 8px;
  padding: 6px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.7), 0 4px 12px rgba(var(--th-shadow-rgb), 0.15);
  display: flex;
  flex-direction: column;
}

.screen-canvas-preview {
  flex: 1;
  background: radial-gradient(circle at 50% 40%, var(--do-bg-dark) 0%, var(--do-bg-dark) 100%);
  border-radius: 4px;
  border: 1px solid var(--do-text-regular);
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  overflow: hidden;
}

.osd-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--do-border);
  border-bottom: 1px solid rgba(var(--th-accent-rgb), 0.2);
  padding-bottom: 5px;
}

.osd-green {
  color: var(--do-success);
  font-weight: 700;
}

.osd-ch {
  color: var(--do-gold-hover);
  font-weight: 700;
}

.rec-dot {
  color: var(--do-danger);
  font-weight: bold;
}

.osd-audio {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--do-border);
}

.audio-bar-anim {
  width: 14px;
  height: 8px;
  background: linear-gradient(90deg, var(--do-success) 70%, var(--do-danger) 100%);
  display: inline-block;
  border-radius: 1px;
}

.match-live-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.live-headline {
  display: flex;
  align-items: center;
  gap: 12px;
}

.race-title {
  color: var(--do-gold-light);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.record-badge {
  background: var(--do-warning);
  color: var(--do-bg-dark);
  font-size: 14px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 3px;
  box-shadow: 0 0 10px rgba(var(--th-warning-rgb), 0.5);
}

.winner-row {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(var(--th-accent-rgb), 0.12);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  padding: 6px 16px;
  border-radius: 6px;
}

.rank-circle.gold {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, var(--do-warning) 0%, var(--do-warning) 100%);
  color: var(--do-text-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 14px;
  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.4);
}

.lane-num {
  color: var(--do-border);
  font-size: 14px;
}

.athlete-name {
  color: #FFFFFF;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.team-name {
  color: var(--do-gold);
  font-size: 14px;
  font-weight: 600;
}

.score-time {
  color: var(--do-warning);
  font-size: 18px;
  font-weight: 900;
}

.gold-trophy-tag {
  background: rgba(var(--th-accent-rgb), 0.25);
  color: var(--do-warning);
  border: 1px solid var(--do-warning);
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  font-weight: 700;
}

.runnerup-row {
  display: flex;
  gap: 16px;
  color: var(--do-text-secondary);
  font-size: 14px;
}

/* 4K 水下机位实时画面 */
.cam-live-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  position: relative;
}

.cam-hud-cross {
  width: 60px;
  height: 60px;
  border: 1px dashed rgba(var(--th-accent-rgb), 0.4);
  border-radius: 50%;
  position: relative;
}

.cam-hud-cross::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: rgba(var(--th-accent-rgb), 0.5);
}

.cam-hud-cross::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(var(--th-accent-rgb), 0.5);
}

.cam-meta-tag {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  color: var(--do-success);
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.cam-desc {
  color: var(--do-border);
  font-size: 14px;
}

/* 颁奖国旗特写 */
.flag-live-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.flag-headline {
  color: var(--do-gold-hover);
  font-size: 14px;
  font-weight: 700;
}

.flag-tri-display {
  display: flex;
  gap: 12px;
}

.flag-card {
  background: rgba(var(--th-accent-rgb), 0.12);
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
  color: var(--do-gold-light);
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.flag-card.main {
  background: rgba(var(--th-accent-rgb), 0.25);
  border-color: var(--do-warning);
  color: var(--do-warning);
  font-weight: 700;
}

/* 紧急安全黑屏 */
.blackout-live-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  background: #000000;
  border-radius: 4px;
}

.blackout-warn {
  color: var(--do-danger);
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 2px;
}

.blackout-desc {
  color: var(--do-text-secondary);
  font-size: 14px;
}

/* 监视器控制栏 */
.screen-control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
}

.bar-lbl {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-secondary);
}

.screen-btn-group {
  display: flex;
  gap: 8px;
}

.btn-src-switch {
  font-size: 14px;
  padding: 4px 10px;
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  color: var(--do-text-primary);
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: var(--transition-fast);
}

.btn-src-switch:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.btn-src-switch.active {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.3);
}

.btn-src-switch.btn-blackout {
  color: var(--do-danger-deep);
}

.btn-src-switch.btn-blackout.active {
  background: var(--do-danger-deep);
  border-color: var(--do-danger-deep);
  color: #FFFFFF;
}

/* 4. 【下排保障控制台】：24h 场地照明功率走势 (左 50%) + 主馆赛场环境与水质遥测 (右 50%) */
.dashboard-telemetry-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* 24h 照明功率走势图美化 */
.energy-trend-box {
  display: flex;
  flex-direction: column;
  height: 380px;
}

.trend-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lighting-mode-badge {
  background: var(--do-success-bg);
  color: var(--do-success);
  border: 1px solid var(--do-success-border);
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.current-power-val {
  font-size: 18px;
  font-weight: 800;
  color: var(--do-warning);
}

.current-power-val small {
  font-size: 14px;
  font-weight: 500;
  color: var(--do-text-secondary);
}

/* 照明工况时段微导航胶囊条 */
.lighting-mode-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 10px 14px;
  background: rgba(var(--th-accent-rgb), 0.03);
  border-bottom: 1px solid var(--do-border-light);
}

.strip-item {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  transition: var(--transition-fast);
}

.strip-item.active {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  box-shadow: 0 1px 4px rgba(var(--th-accent-rgb), 0.15);
}

.strip-label {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.strip-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.strip-item.active .strip-name {
  color: var(--do-gold-deep);
}

.strip-val {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 500;
}

.strip-item.active .strip-val {
  color: var(--do-warning);
  font-weight: 700;
}

.chart-mini-svg {
  flex: 1;
  padding: 8px 14px;
}

.line-svg {
  width: 100%;
  height: 100%;
  max-height: 170px;
}

/* 峰值呼吸环扩散动画 */
@keyframes peakPulse {
  0% {
    r: 4px;
    opacity: 0.9;
  }

  60% {
    r: 12px;
    opacity: 0;
  }

  100% {
    r: 4px;
    opacity: 0;
  }
}

.peak-pulse-ring {
  animation: peakPulse 2.2s infinite ease-out;
}

/* 照明底部统计指标栏 (名称与数值严格同一行并列) */
.lighting-metrics-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgba(var(--th-accent-rgb), 0.05);
  border-top: 1px solid var(--do-border-light);
}

.metric-col {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  white-space: nowrap;
}

.metric-divider {
  width: 1px;
  height: 18px;
  background: var(--do-border-light);
}

.m-label {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 500;
}

.m-val {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.m-val small {
  font-size: 14px;
  font-weight: normal;
  color: var(--do-text-secondary);
  margin-left: 2px;
}

/* 右侧：赛场环境舒适度与竞技水质动态遥测 */
.environment-telemetry-box {
  display: flex;
  flex-direction: column;
  height: 380px;
}

.env-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.env-tag-live {
  font-size: 14px;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.15);
  border: 1px solid var(--do-gold);
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.env-telemetry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 14px 16px;
  flex: 1;
}

.env-metric-item {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  transition: var(--transition-fast);
}

.env-metric-item:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  box-shadow: 0 2px 8px rgba(var(--th-shadow-rgb), 0.05);
}

.env-item-label {
  font-size: 14px;
  color: var(--do-text-secondary);
  font-weight: 600;
}

.env-item-val-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.env-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.env-unit {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.env-bar-wrap {
  width: 100%;
  height: 5px;
  background: var(--do-gold-light);
  border-radius: 3px;
  overflow: hidden;
  margin: 2px 0;
}

.env-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--do-success-border), var(--do-success));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.env-standard-text {
  font-size: 14px;
  color: var(--do-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 5. 底层基础设施：通信总线健康矩阵 */
.bus-matrix-section {
  display: flex;
  flex-direction: column;
}

.bus-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bus-pill.online {
  background: var(--do-success-bg);
  color: var(--do-success);
  border: 1px solid var(--do-success-border);
  font-size: 14px;
  padding: 2px 10px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.bus-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 16px;
}

.bus-item-card {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: var(--transition-fast);
}

.bus-item-card:hover {
  background: var(--do-bg-card-hover);
  border-color: var(--do-gold);
  box-shadow: var(--shadow-card);
}

.bus-item-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bus-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 6px;
  background: rgba(var(--th-accent-rgb), 0.12);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(var(--th-accent-rgb), 0.3);
}

.bus-head-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.bus-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.bus-proto {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.bus-rate-badge {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-success);
  background: var(--do-success-bg);
  border: 1px solid var(--do-success-border);
  padding: 2px 8px;
  border-radius: 4px;
}

.bus-item-body {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 14px;
}

.bus-channel-tag {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: rgba(139, 115, 85, 0.08);
  padding: 2px 8px;
  border-radius: 3px;
  align-self: flex-start;
  font-weight: 600;
}

.bus-instances {
  color: var(--do-text-secondary);
  font-size: 14px;
}

.bus-metrics-text {
  color: var(--do-text-regular);
  font-size: 14px;
  font-weight: 500;
  background: rgba(var(--th-shadow-rgb), 0.03);
  padding: 4px 8px;
  border-radius: 4px;
  margin-top: 2px;
}

.text-success {
  color: var(--do-success);
}

.text-warning {
  color: var(--do-warning);
}

.text-primary {
  color: var(--do-gold);
}

.font-bold {
  font-weight: bold;
}

@media (max-width: 1400px) {

  .dashboard-action-row,
  .dashboard-telemetry-row {
    grid-template-columns: 1fr;
  }

  .bus-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .env-telemetry-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
