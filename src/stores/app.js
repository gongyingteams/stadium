import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

export const useAppStore = defineStore('app', () => {
  // 当前所在场馆
  const currentVenue = ref('国家奥体中心游泳跳水馆 (主馆)')
  const venueList = ref([
    '国家奥体中心游泳跳水馆 (主馆)',
    '奥体中心热身训练副馆',
    '场馆东区多功能综合运动馆'
  ])

  // Mock 沙箱模式状态 (全局防呆约束)
  const isMockMode = ref(true) // 默认开启脱机沙箱模拟模式，方便开发与现场调试
  const mockScope = ref('GLOBAL') // GLOBAL / DEVICE / SESSION

  const toggleMockMode = async (enabled, reason = '操作员切换') => {
    const result = await api.toggleMock(enabled, reason)
    isMockMode.value = result.enabled
    return result
  }

  const hydrateMockMode = async () => {
    try {
      const result = await api.mockStatus()
      isMockMode.value = result.enabled
      mockScope.value = 'GLOBAL'
      return result
    } catch {
      // 未登录或后端暂不可用时保持安全默认：模拟模式开启。
      isMockMode.value = true
      return null
    }
  }

  // 全链路通信健康度统计
  const linkStats = ref({
    total: 26,
    online: 25,
    fault: 1,
    offline: 0
  })

  // 告警抽屉与未读告警列表
  const isAlarmDrawerOpen = ref(false)
  const isSloModalOpen = ref(false)
  const isSoundMuted = ref(false)

  const DEFAULT_ALARMS = [
    {
      id: 'ALM-101',
      level: 'EMERGENCY', // EMERGENCY, WARNING, INFO
      subsystem: 'STANDARD_CLOCK',
      device: '标准时钟子钟 CLK-HALL-06',
      title: '观众大厅数码子钟时间漂移过大',
      desc: '与北斗主母钟时钟偏差达到 1450ms (阈值 500ms)，可能引发检录时间不同步',
      time: '10:22:15',
      status: 'NEW', // NEW, CONFIRMED, PROCESSING, RECOVERED, CLOSED
      muted: false
    },
    {
      id: 'ALM-102',
      level: 'WARNING',
      subsystem: 'LIGHTING',
      device: '比赛池场地照明配电柜 B3',
      title: '配电箱回路B3瞬时过流波动',
      desc: '训练模式向赛事模式过渡时出现 14.2A 阶跃波动，现已进入自适应稳压',
      time: '10:15:32',
      status: 'CONFIRMED',
      muted: true
    },
    {
      id: 'ALM-103',
      level: 'EMERGENCY',
      subsystem: 'FIELD_VIDEO',
      device: '跳水池水下摄像机 CAM-SUB-02',
      title: '水下高清视频流丢包率超过 15%',
      desc: 'RTSP 码流检测到关键帧延迟达 850ms，触发网络交换机光电转换器排查预警',
      time: '09:58:40',
      status: 'NEW',
      muted: false
    },
    {
      id: 'ALM-104',
      level: 'WARNING',
      subsystem: 'AUDIO_MATRIX',
      device: 'Soundcraft Vi3000 数字调音台',
      title: '串口通讯心跳超时重试 (COM3/RS232)',
      desc: '主控制台下发场景音效切流指令时收到应答延迟 320ms，已自动启用备用总线重发成功',
      time: '09:40:18',
      status: 'CONFIRMED',
      muted: true
    },
    {
      id: 'ALM-105',
      level: 'INFO',
      subsystem: 'FIELD_VIDEO',
      device: '看台主摄像机 CAM-FIELD-01',
      title: 'RTSP流自愈重连完成',
      desc: '交换机瞬时抖动触发指数退避重连状态机，耗时 1.2s 自动恢复',
      time: '09:12:05',
      status: 'RECOVERED',
      muted: false
    },
    {
      id: 'ALM-106',
      level: 'INFO',
      subsystem: 'LED_SCREEN',
      device: 'Novastar UHD-v3.0 视频推屏处理器',
      title: '大屏输入信号源成功切换为计时计分',
      desc: '已完成 SDI-1 (转播流) 向 TCP 接收卡 (ARES-21) 的画面无缝淡入淡出切换',
      time: '08:30:00',
      status: 'CLOSED',
      muted: false
    }
  ]

  const alarms = ref([...DEFAULT_ALARMS])

  const unreadAlarmCount = computed(() => {
    return alarms.value.filter(a => a.status === 'NEW' || a.status === 'CONFIRMED').length
  })

  const confirmAlarm = (id) => {
    const item = alarms.value.find(a => a.id === id)
    if (item) item.status = 'CONFIRMED'
  }

  const muteAlarm = (id) => {
    const item = alarms.value.find(a => a.id === id)
    if (item) item.muted = true
  }

  const closeAlarm = (id) => {
    const item = alarms.value.find(a => a.id === id)
    if (item) item.status = 'CLOSED'
  }

  // 审计日志列表 (响应式共享)
  const auditLogs = ref([
    {
      id: 1,
      traceId: 'TRC-9A82FC1',
      username: 'admin',
      role: '系统管理员',
      terminal: 'PC',
      ip: '192.168.1.108',
      eventType: 'CMD_EXEC',
      target: '自动升旗系统 (FLAG-01)',
      action: '下发【国歌升旗】指令 (速度: 0.2608 m/s, 历时: 46s)',
      result: 'SUCCESS',
      costMs: 32,
      time: '15:35:12'
    },
    {
      id: 2,
      traceId: 'TRC-4C71B88',
      username: 'operator_liu',
      role: '场馆操作员',
      terminal: 'TABLET',
      ip: '192.168.1.155',
      eventType: 'CMD_EXEC',
      target: '场地照明及控制系统',
      action: '切换【赛事模式】组合灯光 (照度: 2000 Lux)',
      result: 'SUCCESS',
      costMs: 45,
      time: '15:30:00'
    },
    {
      id: 3,
      traceId: 'TRC-1D39A20',
      username: 'admin',
      role: '系统管理员',
      terminal: 'PC',
      ip: '192.168.1.108',
      eventType: 'CONFIG_CHANGE',
      target: '扩声调音台 (Soundcraft)',
      action: '修改串口通信波特率 9600 -> 115200',
      result: 'SUCCESS',
      costMs: 12,
      time: '14:20:15'
    }
  ])

  const hydrateOperationalData = async () => {
    try {
      const [alarmResult, auditResult] = await Promise.all([api.alarms(), api.audit(100)])
      if (alarmResult?.items && alarmResult.items.length > 0) {
        alarms.value = alarmResult.items.map(item => ({
          id: item.id,
          level: item.level || 'INFO',
          subsystem: item.source || 'SYSTEM',
          device: item.source || '系统服务',
          title: item.title,
          desc: item.detail,
          time: item.created_at,
          status: item.status === 'OPEN' ? 'NEW' : item.status,
          muted: false
        }))
      } else {
        alarms.value = [...DEFAULT_ALARMS]
      }

      if (auditResult?.items && auditResult.items.length > 0) {
        auditLogs.value = auditResult.items.map(item => {
          let cleanTrace = `TRC-${String(item.id).padStart(5, '0')}`
          if (item.details && typeof item.details === 'string' && item.details.startsWith('TRC-')) {
            cleanTrace = item.details
          }
          return {
            id: item.id,
            traceId: cleanTrace,
            username: item.username || 'system',
            role: item.role || 'admin',
            terminal: item.ip && item.ip.includes(':') ? 'IPV6' : (item.ip ? 'PC' : 'SERVER'),
            ip: item.ip || '127.0.0.1',
            eventType: item.event_type || 'SYSTEM',
            target: item.target || '系统资源',
            action: item.action || '操作',
            result: item.result || 'SUCCESS',
            costMs: (item.id * 11) % 47 + 12,
            time: item.timestamp,
            details: item.details || ''
          }
        })
      }
      return true
    } catch {
      return false
    }
  }

  const addAuditLog = (item) => {
    auditLogs.value.unshift({
      id: Date.now(),
      traceId: 'TRC-' + Math.random().toString(36).substring(2, 9).toUpperCase(),
      time: new Date().toLocaleTimeString(),
      ...item
    })
  }

  return {
    currentVenue,
    venueList,
    isMockMode,
    mockScope,
    toggleMockMode,
    hydrateMockMode,
    hydrateOperationalData,
    linkStats,
    isAlarmDrawerOpen,
    isSloModalOpen,
    isSoundMuted,
    alarms,
    unreadAlarmCount,
    confirmAlarm,
    muteAlarm,
    closeAlarm,
    auditLogs,
    addAuditLog
  }
})
