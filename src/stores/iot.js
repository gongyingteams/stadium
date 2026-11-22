import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'

export const useIotStore = defineStore('iot', () => {
  // 13大基线子系统总览数据
  const subsystems = ref([
    {
      code: 'AUDIO_MATRIX',
      name: '扩声系统',
      status: 'ONLINE',
      deviceCount: 4,
      onlineCount: 4,
      protocol: '串口 RS232 (115200bps)',
      route: '/iot/audio',
      icon: 'SvgSoundMatrix',
      summary: '8~16通道矩阵推子控制、场景音效一键调用',
      integrationMode: 'API'
    },
    {
      code: 'LIGHTING',
      name: '场地照明及控制系统',
      status: 'ONLINE',
      deviceCount: 6,
      onlineCount: 6,
      protocol: '串口 / Modbus RTU',
      route: '/iot/lighting',
      icon: 'SvgLighting',
      summary: '赛事/训练/演播一键场景，24h电表能耗趋势',
      integrationMode: 'API'
    },
    {
      code: 'LED_SCREEN',
      name: 'LED大屏系统',
      status: 'ONLINE',
      deviceCount: 2,
      onlineCount: 2,
      protocol: 'Web API / 串口',
      route: '/iot/screen',
      icon: 'SvgLedScreen',
      summary: '摄像机/播控/成绩多输入源无缝切换，实时推流监视',
      integrationMode: 'API'
    },
    {
      code: 'MATCH_SCORE',
      name: '计时计分及现场成绩处理系统',
      status: 'ONLINE',
      deviceCount: 1,
      onlineCount: 1,
      protocol: 'TCP Socket (Port: 5000)',
      route: '/iot/score',
      icon: 'SvgMatchScore',
      summary: '比赛成绩毫秒捕获，支持自动/手动大屏一键推送',
      integrationMode: 'API'
    },
    {
      code: 'TICKETING',
      name: '售验票系统',
      status: 'ONLINE',
      deviceCount: 8,
      onlineCount: 8,
      protocol: 'HTTP RESTful / iframe降级',
      route: '/portal/nav',
      icon: 'SvgPortal',
      summary: '门禁闸机验票核验，支持双模式安全代理无缝嵌入',
      integrationMode: 'IFRAME_FALLBACK'
    },
    {
      code: 'STANDARD_CLOCK',
      name: '标准时钟系统',
      status: 'WARNING',
      deviceCount: 7,
      onlineCount: 6,
      protocol: 'TCP / UDP (北斗/GPS双模)',
      route: '/iot/clock',
      icon: 'SvgMasterClock',
      summary: '卫星12颗，毫秒漂移校验，全场6台子钟分类拓扑',
      integrationMode: 'API'
    },
    {
      code: 'FLAG_SYSTEM',
      name: '自动升旗控制系统',
      status: 'ONLINE',
      deviceCount: 1,
      onlineCount: 1,
      protocol: '串口 RS485 (Siemens S7 PLC)',
      route: '/iot/flag',
      icon: 'SvgFlagSystem',
      summary: '音画同步智能测速，Canvas高拟真仿真，最高优先级急停',
      integrationMode: 'API'
    },
    {
      code: 'FIELD_VIDEO',
      name: '现场影像采集回放系统',
      status: 'ONLINE',
      deviceCount: 4,
      onlineCount: 4,
      protocol: 'RTSP / WebRTC',
      route: '/iot/video',
      icon: 'SvgCameraMatrix',
      summary: '全场看台全景视窗，录像检索回放，画面高清抓拍',
      integrationMode: 'API'
    },
    {
      code: 'UNDERWATER_VISION',
      name: '水下影像采集识别系统',
      status: 'ONLINE',
      deviceCount: 2,
      onlineCount: 2,
      protocol: 'RTSP / 专用采集卡',
      route: '/iot/video',
      icon: 'SvgCameraMatrix',
      summary: '游泳跳水深水池特种视窗，裁判触壁回放与拍摄',
      integrationMode: 'API'
    },
    {
      code: 'TV_BROADCAST',
      name: '电视转播系统',
      status: 'ONLINE',
      deviceCount: 1,
      onlineCount: 1,
      protocol: 'HDMI/SDI 采集适配',
      route: '/iot/video',
      icon: 'SvgCameraMatrix',
      summary: '广播级视频源画面监视，输入格式/分辨率/帧率监测',
      integrationMode: 'API'
    },
    {
      code: 'INFO_PUBLISH',
      name: '信息发布系统',
      status: 'ONLINE',
      deviceCount: 12,
      onlineCount: 12,
      protocol: 'HTTP API / iframe降级',
      route: '/portal/nav',
      icon: 'SvgPortal',
      summary: '导视屏节目单排期，赛程滚动播出，多模式免密内嵌',
      integrationMode: 'API'
    },
    {
      code: 'AUDIO_PLAYBACK',
      name: '音频播放服务',
      status: 'ONLINE',
      deviceCount: 1,
      onlineCount: 1,
      protocol: '配置化播放输出',
      route: '/iot/media',
      icon: 'SvgMediaPlayer',
      summary: '直接拉取媒体素材库，国歌、颁奖进行曲与环境BGM',
      integrationMode: 'API'
    },
    {
      code: 'VIDEO_PLAYBACK',
      name: '视频播放服务',
      status: 'ONLINE',
      deviceCount: 1,
      onlineCount: 1,
      protocol: '配置化投屏输出',
      route: '/iot/media',
      icon: 'SvgMediaPlayer',
      summary: '赛事宣传片、回放视频多路大屏定向投屏',
      integrationMode: 'API'
    }
  ])

  // 快捷执行动作记录
  const lastCommandReceipt = ref({
    command: '',
    time: '',
    receipt: '',
    status: 'IDLE'
  })

  const sendDeviceCommand = async (cmdText, targetDevice = '下位机', payload = {}) => {
    try {
      const result = await api.deviceCommand(targetDevice, cmdText, payload)
      lastCommandReceipt.value = {
        command: cmdText,
        time: new Date().toLocaleTimeString(),
        receipt: result.receipt || result.message || '已处理',
        status: result.simulated ? 'MOCK_SUCCESS' : 'SUCCESS'
      }
      return result
    } catch (error) {
      lastCommandReceipt.value = {
        command: cmdText,
        time: new Date().toLocaleTimeString(),
        receipt: error.message || '设备驱动未配置，已拒绝下发',
        status: 'REJECTED'
      }
      throw error
    }
  }

  return {
    subsystems,
    lastCommandReceipt,
    sendDeviceCommand
  }
})
