<template>
  <svg
    class="svg-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :style="{ width: `${size}px`, height: `${size}px`, minWidth: `${size}px`, minHeight: `${size}px` }"
  >
    <!-- 1. 综合态势 -->
    <g v-if="name === 'SvgDashboard'">
      <rect x="3" y="3" width="7" height="9" rx="1"></rect>
      <rect x="14" y="3" width="7" height="5" rx="1"></rect>
      <rect x="14" y="12" width="7" height="9" rx="1"></rect>
      <rect x="3" y="16" width="7" height="5" rx="1"></rect>
    </g>

    <!-- 2. 应用聚合门户 -->
    <g v-else-if="name === 'SvgPortal'">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="2" y1="12" x2="22" y2="12"></line>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
    </g>
    <!-- 应用导航 (罗盘指南针 / 导航大厅) -->
    <g v-else-if="name === 'SvgCompassNav' || name === 'SvgCompass'">
      <circle cx="12" cy="12" r="10"></circle>
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
    </g>
    <g v-else-if="name === 'SvgAppGrid'">
      <rect x="3" y="3" width="7" height="7"></rect>
      <rect x="14" y="3" width="7" height="7"></rect>
      <rect x="14" y="14" width="7" height="7"></rect>
      <rect x="3" y="14" width="7" height="7"></rect>
    </g>
    <g v-else-if="name === 'SvgIframeApp'">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
      <line x1="2" y1="7" x2="22" y2="7"></line>
      <line x1="6" y1="5" x2="6" y2="5"></line>
      <line x1="9" y1="5" x2="9" y2="5"></line>
      <polyline points="10 13 8 11 10 9"></polyline>
      <polyline points="14 13 16 11 14 9"></polyline>
    </g>

    <!-- 3. 物联网控制总线 -->
    <g v-else-if="name === 'SvgIotControl'">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M6.3 6.3a8 8 0 0 0 0 11.4"></path>
      <path d="M17.7 6.3a8 8 0 0 1 0 11.4"></path>
      <path d="M3.5 3.5a12 12 0 0 0 0 17"></path>
      <path d="M20.5 3.5a12 12 0 0 1 0 17"></path>
    </g>
    <g v-else-if="name === 'SvgSoundMatrix'">
      <line x1="4" y1="21" x2="4" y2="14"></line>
      <line x1="4" y1="10" x2="4" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="12"></line>
      <line x1="12" y1="8" x2="12" y2="3"></line>
      <line x1="20" y1="21" x2="20" y2="16"></line>
      <line x1="20" y1="12" x2="20" y2="3"></line>
      <line x1="1" y1="14" x2="7" y2="14"></line>
      <line x1="9" y1="8" x2="15" y2="8"></line>
      <line x1="17" y1="16" x2="23" y2="16"></line>
    </g>
    <g v-else-if="name === 'SvgLighting'">
      <line x1="9" y1="18" x2="15" y2="18"></line>
      <line x1="10" y1="22" x2="14" y2="22"></line>
      <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path>
    </g>
    <g v-else-if="name === 'SvgLedScreen'">
      <rect x="2" y="3" width="20" height="14" rx="2"></rect>
      <line x1="8" y1="21" x2="16" y2="21"></line>
      <line x1="12" y1="17" x2="12" y2="21"></line>
    </g>
    <g v-else-if="name === 'SvgMatchScore'">
      <circle cx="12" cy="12" r="10"></circle>
      <polyline points="12 6 12 12 16 14"></polyline>
      <line x1="12" y1="2" x2="12" y2="4"></line>
    </g>
    <g v-else-if="name === 'SvgFlagSystem'">
      <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
      <line x1="4" y1="22" x2="4" y2="15"></line>
    </g>
    <g v-else-if="name === 'SvgMasterClock'">
      <circle cx="12" cy="12" r="10"></circle>
      <polyline points="12 6 12 12 14 10"></polyline>
      <line x1="2" y1="12" x2="4" y2="12"></line>
      <line x1="20" y1="12" x2="22" y2="12"></line>
    </g>
    <g v-else-if="name === 'SvgCameraMatrix'">
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
      <circle cx="12" cy="13" r="4"></circle>
    </g>
    <g v-else-if="name === 'SvgMediaPlayer'">
      <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </g>
    <g v-else-if="name === 'SvgDynamicDevice'">
      <rect x="3" y="3" width="18" height="18" rx="2"></rect>
      <circle cx="8.5" cy="8.5" r="1.5"></circle>
      <polyline points="21 15 16 10 5 21"></polyline>
    </g>

    <!-- 4. 低代码配置中心 -->
    <g v-else-if="name === 'SvgLowCodeConfig'">
      <polyline points="16 18 22 12 16 6"></polyline>
      <polyline points="8 6 2 12 8 18"></polyline>
      <line x1="14" y1="4" x2="10" y2="20"></line>
    </g>
    <g v-else-if="name === 'SvgDeviceSetting'">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </g>
    <g v-else-if="name === 'SvgButtonAction'">
      <rect x="3" y="8" width="18" height="8" rx="4"></rect>
      <circle cx="8" cy="12" r="2"></circle>
    </g>
    <g v-else-if="name === 'SvgAdapterBook'">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
    </g>
    <g v-else-if="name === 'SvgMediaLibrary'">
      <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
      <line x1="7" y1="2" x2="7" y2="22"></line>
      <line x1="17" y1="2" x2="17" y2="22"></line>
      <line x1="2" y1="12" x2="22" y2="12"></line>
      <line x1="2" y1="7" x2="7" y2="7"></line>
      <line x1="2" y1="17" x2="7" y2="17"></line>
      <line x1="17" y1="17" x2="22" y2="17"></line>
      <line x1="17" y1="7" x2="22" y2="7"></line>
    </g>
    <g v-else-if="name === 'SvgConfigTemplate'">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
      <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
      <line x1="12" y1="22.08" x2="12" y2="12"></line>
    </g>
    <g v-else-if="name === 'SvgMockSandbox'">
      <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
      <polyline points="2 17 12 22 22 17"></polyline>
      <polyline points="2 12 12 17 22 12"></polyline>
    </g>
    <g v-else-if="name === 'SvgMenuList'">
      <circle cx="3.5" cy="6" r="1.5"></circle>
      <circle cx="3.5" cy="12" r="1.5"></circle>
      <circle cx="3.5" cy="18" r="1.5"></circle>
      <line x1="8" y1="6" x2="21" y2="6"></line>
      <line x1="8" y1="12" x2="21" y2="12"></line>
      <line x1="8" y1="18" x2="21" y2="18"></line>
    </g>

    <!-- 5. 运维与安全中心 -->
    <g v-else-if="name === 'SvgSecurityShield'">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    </g>
    <g v-else-if="name === 'SvgAlarmBell'">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
    </g>
    <g v-else-if="name === 'SvgNotifyChannel'">
      <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
      <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
    </g>
    <g v-else-if="name === 'SvgAuditLog'">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </g>
    <g v-else-if="name === 'SvgUserRole'">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
      <circle cx="9" cy="7" r="4"></circle>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
    </g>
    <g v-else-if="name === 'SvgTablet'">
      <rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect>
      <line x1="12" y1="18" x2="12.01" y2="18"></line>
    </g>

    <!-- 6. 新增丰富的体育、物联、声学、视频与子系统精细切片图标 -->
    <!-- 麦克风 / 话筒 -->
    <g v-else-if="name === 'SvgMicrophone'">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" y1="19" x2="12" y2="22"></line>
      <line x1="8" y1="22" x2="16" y2="22"></line>
    </g>

    <!-- 扬声器 / 音响音量 -->
    <g v-else-if="name === 'SvgSpeaker'">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
    </g>

    <!-- 音符 / 背景音乐 -->
    <g v-else-if="name === 'SvgMusicNote'">
      <path d="M9 18V5l12-2v13"></path>
      <circle cx="6" cy="18" r="3"></circle>
      <circle cx="18" cy="16" r="3"></circle>
    </g>

    <!-- 比赛金奖杯 -->
    <g v-else-if="name === 'SvgTrophy'">
      <path d="M6 9H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h2"></path>
      <path d="M18 9h2a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2h-2"></path>
      <path d="M6 3h12v7a6 6 0 0 1-12 0V3z"></path>
      <path d="M12 16v4"></path>
      <path d="M8 20h8"></path>
    </g>

    <!-- 裁判哨子 -->
    <g v-else-if="name === 'SvgWhistle'">
      <circle cx="10" cy="14" r="5"></circle>
      <path d="M15 14h5a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2H9a5 5 0 0 0-4 2"></path>
      <line x1="15" y1="9" x2="15" y2="7"></line>
    </g>

    <!-- 比赛秒表 / 计时 -->
    <g v-else-if="name === 'SvgStopwatch'">
      <circle cx="12" cy="13" r="8"></circle>
      <line x1="12" y1="9" x2="12" y2="13"></line>
      <line x1="12" y1="13" x2="15" y2="15"></line>
      <path d="M10 2h4"></path>
      <line x1="12" y1="2" x2="12" y2="5"></line>
    </g>

    <!-- 泳道 / 水质波纹 -->
    <g v-else-if="name === 'SvgSwimmingPool'">
      <path d="M2 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0"></path>
      <path d="M2 17c2-2 4-2 6 0s4 2 6 0 4-2 6 0"></path>
      <path d="M12 4v4m0 0l-2-2m2 2l2-2"></path>
    </g>

    <!-- HDMI 高清视频接口 -->
    <g v-else-if="name === 'SvgHdHdmi'">
      <rect x="3" y="6" width="18" height="12" rx="2"></rect>
      <line x1="7" y1="11" x2="7" y2="13"></line>
      <line x1="10" y1="11" x2="10" y2="13"></line>
      <line x1="13" y1="11" x2="13" y2="13"></line>
      <line x1="16" y1="11" x2="16" y2="13"></line>
    </g>

    <!-- SDI 专业转播视频 -->
    <g v-else-if="name === 'SvgSdiVideo'">
      <rect x="2" y="4" width="20" height="16" rx="2"></rect>
      <polygon points="10 8 16 12 10 16 10 8"></polygon>
      <line x1="2" y1="8" x2="4" y2="8"></line>
      <line x1="20" y1="8" x2="22" y2="8"></line>
    </g>

    <!-- 水下高速球机 / 云台 PTZ -->
    <g v-else-if="name === 'SvgPtzCamera'">
      <path d="M12 2a8 8 0 0 0-8 8v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3a8 8 0 0 0-8-8z"></path>
      <circle cx="12" cy="10" r="3"></circle>
      <path d="M9 19l3 3 3-3"></path>
    </g>

    <!-- 光纤万兆环网 -->
    <g v-else-if="name === 'SvgFiberNet'">
      <circle cx="6" cy="12" r="3"></circle>
      <circle cx="18" cy="12" r="3"></circle>
      <line x1="9" y1="12" x2="15" y2="12"></line>
      <path d="M6 9a6 6 0 0 1 12 0"></path>
      <path d="M6 15a6 6 0 0 0 12 0"></path>
    </g>

    <!-- 串口通信芯片 RS232/485 -->
    <g v-else-if="name === 'SvgSerialPort'">
      <rect x="4" y="6" width="16" height="12" rx="2"></rect>
      <circle cx="8" cy="10" r="1"></circle>
      <circle cx="12" cy="10" r="1"></circle>
      <circle cx="16" cy="10" r="1"></circle>
      <circle cx="10" cy="14" r="1"></circle>
      <circle cx="14" cy="14" r="1"></circle>
    </g>

    <!-- 票务检票闸机 -->
    <g v-else-if="name === 'SvgTicketGate'">
      <rect x="3" y="4" width="6" height="16" rx="1"></rect>
      <rect x="15" y="4" width="6" height="16" rx="1"></rect>
      <line x1="9" y1="10" x2="15" y2="14"></line>
      <line x1="9" y1="14" x2="15" y2="10"></line>
    </g>

    <!-- 暖通空调系统 HVAC -->
    <g v-else-if="name === 'SvgAirCondition'">
      <path d="M12 2v20M2 12h20"></path>
      <path d="M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14"></path>
      <circle cx="12" cy="12" r="3"></circle>
    </g>

    <!-- 消防报警消火栓 -->
    <g v-else-if="name === 'SvgFireFighting'">
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
    </g>

    <!-- 门禁人脸识别 -->
    <g v-else-if="name === 'SvgAccessDoor'">
      <rect x="4" y="3" width="16" height="18" rx="2"></rect>
      <line x1="4" y1="21" x2="20" y2="21"></line>
      <circle cx="15" cy="12" r="1"></circle>
    </g>

    <!-- 停车场车闸 -->
    <g v-else-if="name === 'SvgParkingCar'">
      <rect x="3" y="10" width="18" height="8" rx="2"></rect>
      <circle cx="7" cy="18" r="2"></circle>
      <circle cx="17" cy="18" r="2"></circle>
      <path d="M6 10l2-5h8l2 5"></path>
    </g>

    <!-- 智能电梯运行 -->
    <g v-else-if="name === 'SvgElevatorCar'">
      <rect x="3" y="3" width="18" height="18" rx="2"></rect>
      <polyline points="7 10 9 7 11 10"></polyline>
      <polyline points="13 14 15 17 17 14"></polyline>
      <line x1="12" y1="3" x2="12" y2="21"></line>
    </g>

    <!-- 能耗分项电表 -->
    <g v-else-if="name === 'SvgEnergyMeter'">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
    </g>

    <!-- 急停物理按钮 -->
    <g v-else-if="name === 'SvgEmergencyHalt'">
      <circle cx="12" cy="12" r="9"></circle>
      <rect x="8.5" y="8.5" width="7" height="7" rx="1"></rect>
    </g>

    <!-- 报文终端 / 终端代码 -->
    <g v-else-if="name === 'SvgTerminalHex'">
      <polyline points="4 17 10 11 4 5"></polyline>
      <line x1="12" y1="19" x2="20" y2="19"></line>
    </g>

    <!-- 信号与无线传输 -->
    <g v-else-if="name === 'SvgSignalWifi'">
      <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
      <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
      <line x1="12" y1="20" x2="12.01" y2="20"></line>
    </g>

    <!-- 心跳与动态波形 -->
    <g v-else-if="name === 'SvgActivity'">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
    </g>

    <!-- 工业级计算核心 / 边缘网关芯片 -->
    <g v-else-if="name === 'SvgCpu'">
      <rect x="4" y="4" width="16" height="16" rx="2"></rect>
      <rect x="9" y="9" width="6" height="6"></rect>
      <line x1="9" y1="1" x2="9" y2="4"></line>
      <line x1="15" y1="1" x2="15" y2="4"></line>
      <line x1="9" y1="20" x2="9" y2="23"></line>
      <line x1="15" y1="20" x2="15" y2="23"></line>
      <line x1="20" y1="9" x2="23" y2="9"></line>
      <line x1="20" y1="15" x2="23" y2="15"></line>
      <line x1="1" y1="9" x2="4" y2="9"></line>
      <line x1="1" y1="15" x2="4" y2="15"></line>
    </g>

    <!-- 存储节点 / 录像服务器 -->
    <g v-else-if="name === 'SvgHardDrive'">
      <line x1="22" y1="12" x2="2" y2="12"></line>
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path>
      <line x1="6" y1="16" x2="6.01" y2="16"></line>
      <line x1="10" y1="16" x2="10.01" y2="16"></line>
    </g>

    <!-- 均衡推子 / 矩阵微调 -->
    <g v-else-if="name === 'SvgSliders'">
      <line x1="4" y1="21" x2="4" y2="14"></line>
      <line x1="4" y1="10" x2="4" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="12"></line>
      <line x1="12" y1="8" x2="12" y2="3"></line>
      <line x1="20" y1="21" x2="20" y2="16"></line>
      <line x1="20" y1="12" x2="20" y2="3"></line>
      <line x1="1" y1="14" x2="7" y2="14"></line>
      <line x1="9" y1="8" x2="15" y2="8"></line>
      <line x1="17" y1="16" x2="23" y2="16"></line>
    </g>

    <!-- 投屏全屏 / 场馆大屏拉伸 -->
    <g v-else-if="name === 'SvgMaximize'">
      <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
    </g>

    <!-- 工业电源启闭 -->
    <g v-else-if="name === 'SvgPower'">
      <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
      <line x1="12" y1="2" x2="12" y2="12"></line>
    </g>

    <!-- 动态刷新 -->
    <g v-else-if="name === 'SvgRefresh'">
      <polyline points="23 4 23 10 17 10"></polyline>
      <polyline points="1 20 1 14 7 14"></polyline>
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
    </g>

    <!-- 快速搜索 -->
    <g v-else-if="name === 'SvgSearch'">
      <circle cx="11" cy="11" r="8"></circle>
      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </g>

    <!-- 系统设置 (精细工控齿轮) -->
    <g v-else-if="name === 'SvgSettingGear' || name === 'SvgSettings'">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </g>

    <!-- 默认通用回退兜底 -->
    <g v-else>
      <rect x="3" y="3" width="7" height="9" rx="1"></rect>
      <rect x="14" y="3" width="7" height="5" rx="1"></rect>
      <rect x="14" y="12" width="7" height="9" rx="1"></rect>
      <rect x="3" y="16" width="7" height="5" rx="1"></rect>
    </g>
  </svg>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    required: true
  },
  size: {
    type: [Number, String],
    default: 18
  },
  strokeWidth: {
    type: [Number, String],
    default: 2
  }
})
</script>

<style scoped>
.svg-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  overflow: hidden;
}
</style>
