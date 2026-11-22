/**
 * 物联网控制 13 项硬件设备总控中台数据服务 (iotDeviceService.js)
 * 严格支持：
 * 1. 13 类硬件每一种独立列表、分组 (group_name)、分区域 (region_name)、自编号 (custom_no)、备注 (remark)，增删改查
 * 2. 勾选某一个或全选设备，支持批量指令下发与单机即时下发
 * 3. 针对每个设备的参数编辑、指令编辑 (预置指令库增删改查)
 * 4. 指令执行结果回执跟踪 (SUCCESS / FAILED / TIMEOUT、回执报文、响应耗时、操作人)
 */

const STORAGE_KEY_DEVICES = 'venue_iot_devices_v1'
const STORAGE_KEY_COMMANDS = 'venue_iot_commands_v1'
const STORAGE_KEY_LOGS = 'venue_iot_cmd_logs_v1'

// 13 类核心弱电硬件子系统类型定义 (与项目规划严格对齐)
export const HARDWARE_TYPES = [
  {
    type: 'AUDIO',
    name: '专业扩声系统',
    shortName: '专业扩声',
    codePrefix: 'AUD',
    icon: 'SvgSoundMatrix',
    desc: '包含数字调音台、音频处理器、主扩功率放大器、看台扬声器组',
    defaultProtocol: 'SERIAL',
    defaultPort: 'COM3'
  },
  {
    type: 'LIGHTING',
    name: '场地照明系统',
    shortName: '场地照明',
    codePrefix: 'LGT',
    icon: 'SvgLighting',
    desc: '包含比赛大厅高杆LED调光器、金卤灯配电柜、观众席智能灯控网关',
    defaultProtocol: 'MODBUS',
    defaultPort: '192.168.1.120:502'
  },
  {
    type: 'SCREEN',
    name: 'LED大屏显示系统',
    shortName: '大屏调度',
    codePrefix: 'SCR',
    icon: 'SvgLedScreen',
    desc: '包含中央斗屏发送卡、端屏拼接处理器、环形带状屏播控机',
    defaultProtocol: 'TCP',
    defaultPort: '192.168.1.150:8000'
  },
  {
    type: 'SCORE',
    name: '赛事计时计分系统',
    shortName: '计时计分',
    codePrefix: 'SCR',
    icon: 'SvgMatchScore',
    desc: '包含主计时计分机、泳道触板接口盒、跳水/体操裁判打分终端',
    defaultProtocol: 'UDP',
    defaultPort: '192.168.1.180:9000'
  },
  {
    type: 'FLAG',
    name: '智能升旗系统',
    shortName: '智能升旗',
    codePrefix: 'FLG',
    icon: 'SvgFlagSystem',
    desc: '包含国旗/会旗升降伺服电机驱动器、高度激光测距仪、旗杆PLC主板',
    defaultProtocol: 'SERIAL',
    defaultPort: 'COM4'
  },
  {
    type: 'CLOCK',
    name: '标准时钟同步系统',
    shortName: '时钟同步',
    codePrefix: 'CLK',
    icon: 'SvgMasterClock',
    desc: '包含GPS/北斗双模卫星授时母钟、看台数码子钟网络、裁判房指针子钟',
    defaultProtocol: 'NTP',
    defaultPort: '192.168.1.100:123'
  },
  {
    type: 'VIDEO',
    name: '现场水下转播监控',
    shortName: '视频监控',
    codePrefix: 'VID',
    icon: 'SvgCameraMatrix',
    desc: '包含比赛池4K云台跟踪球机、水下超高清摄像机、赛事专用录播NVR',
    defaultProtocol: 'RTSP',
    defaultPort: 'rtsp://192.168.1.200:554'
  },
  {
    type: 'MEDIA',
    name: '媒体音视频播控台',
    shortName: '媒体播控',
    codePrefix: 'MED',
    icon: 'SvgMediaPlayer',
    desc: '包含赛事宣传片播放器、背景音乐音源机、网络多路推流工作站',
    defaultProtocol: 'HTTP',
    defaultPort: 'http://192.168.1.88:8080'
  },
  {
    type: 'ENERGY',
    name: '建筑能耗智能监测',
    shortName: '能耗监测',
    codePrefix: 'ENG',
    icon: 'SvgDashboard',
    desc: '包含动力照明三相多功能电表、空调系统计量表、主供水冷热水表网关',
    defaultProtocol: 'MODBUS',
    defaultPort: '192.168.1.130:502'
  },
  {
    type: 'HVAC',
    name: '暖通空调恒温恒湿',
    shortName: '暖通空调',
    codePrefix: 'HVC',
    icon: 'SvgIotControl',
    desc: '包含泳池恒温热泵变频器、比赛大厅新风机组网关、排风管道电动阀',
    defaultProtocol: 'BACNET',
    defaultPort: '192.168.1.140:47808'
  },
  {
    type: 'SECURITY',
    name: '安防门禁与防盗报警',
    shortName: '安防门禁',
    codePrefix: 'SEC',
    icon: 'SvgSecurityShield',
    desc: '包含VIP区通道门禁控制器、周界防越红外对射探测器、机房防盗报警主机',
    defaultProtocol: 'TCP',
    defaultPort: '192.168.1.160:6000'
  },
  {
    type: 'BROADCAST',
    name: '公共广播与信息发布',
    shortName: '公共广播',
    codePrefix: 'BCD',
    icon: 'SvgNotifyChannel',
    desc: '包含消防联动广播功放、疏散应急分区选择器、前台IP网络寻呼话筒',
    defaultProtocol: 'TCP',
    defaultPort: '192.168.1.170:7000'
  },
  {
    type: 'ENVIRONMENT',
    name: '综合动环与智能传感',
    shortName: '动环传感',
    codePrefix: 'ENV',
    icon: 'SvgDeviceSetting',
    desc: '包含水质余氯浑浊度传感器、泳池室温水温传感器、变配电室温湿度水浸探头',
    defaultProtocol: 'MODBUS',
    defaultPort: 'COM5'
  }
]

// 常用区域候选字典
export const PRESET_REGIONS = [
  '主游泳跳水馆 (比赛池)',
  '主游泳馆 (跳水台)',
  '热身馆 / 训练池',
  '观众席 (东看台)',
  '观众席 (西看台)',
  'VIP主席台与贵宾包厢',
  '总控调度机房 (Control Room)',
  '裁判竞赛办公室',
  '媒体转播新闻发布厅',
  '地下变配电室与动力机房'
]

// 常用分组候选字典
export const PRESET_GROUPS = [
  '主赛场核心运行组',
  '热身训练保障组',
  '看台观众服务组',
  '总控设备枢纽组',
  '应急防灾联动组',
  '日常节能轮训组'
]

// 初始化 13 类预置硬件设备实例
function createInitialDevices() {
  const devices = [
    // 1. 专业扩声系统 (支持多套调音台分布式部署)
    {
      id: 101,
      hardware_type: 'AUDIO',
      custom_no: 'AUD-MIX-01',
      device_code: 'DEV_AUDIO_01',
      device_name: 'Soundcraft Vi3000 主赛场数字调音台',
      group_name: '主赛场核心运行组',
      region_name: '总控调度机房 (Control Room)',
      connection_type: 'SERIAL',
      serial_port: 'COM3',
      baud_rate: 115200,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '',
      target_port: 0,
      online_status: 'ONLINE',
      remark: '场馆主扩声调音核心矩阵，负责 12 路主麦克风与现场推子联动',
      commands: [
        { id: 1, command_name: '全通道快速复位 (0dB)', command_code: 'RESET_0DB', payload_format: 'HEX', command_payload: '55 AA 00 00 FADER_RESET', expected_ack: 'ACK_OK', timeout_ms: 1000, is_dangerous: false, remark: '推子回到标准电平' },
        { id: 2, command_name: '全场紧急静音 (MUTE ALL)', command_code: 'MUTE_ALL', payload_format: 'HEX', command_payload: '55 AA FF FF MUTE_ENABLE', expected_ack: 'ACK_MUTED', timeout_ms: 800, is_dangerous: true, remark: '瞬间掐断所有通道声音' },
        { id: 3, command_name: '状态轮询心跳查询', command_code: 'PING_HEARTBEAT', payload_format: 'HEX', command_payload: '55 AA 00 00 PING', expected_ack: 'PONG_STATUS_ONLINE', timeout_ms: 500, is_dangerous: false, remark: '心跳探针' }
      ]
    },
    {
      id: 102,
      hardware_type: 'AUDIO',
      custom_no: 'AUD-MIX-02',
      device_code: 'DEV_AUDIO_02',
      device_name: 'Yamaha QL5 副馆热身池数字调音台',
      group_name: '主赛场核心运行组',
      region_name: '副馆热身池设备间 (Warm-up Pool)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.112',
      target_port: 49280,
      online_status: 'ONLINE',
      remark: '副馆热身池专用扩声，与主系统支持Dante级联音频与推子同步',
      commands: [
        { id: 1, command_name: '全通道快速复位 (0dB)', command_code: 'RESET_0DB', payload_format: 'HEX', command_payload: '55 AA 00 00 FADER_RESET', expected_ack: 'ACK_OK', timeout_ms: 1000, is_dangerous: false, remark: '副馆推子复位' },
        { id: 2, command_name: '全场紧急静音 (MUTE ALL)', command_code: 'MUTE_ALL', payload_format: 'HEX', command_payload: '55 AA FF FF MUTE_ENABLE', expected_ack: 'ACK_MUTED', timeout_ms: 800, is_dangerous: true, remark: '副馆紧急静音' }
      ]
    },
    {
      id: 103,
      hardware_type: 'AUDIO',
      custom_no: 'AUD-MIX-03',
      device_code: 'DEV_AUDIO_03',
      device_name: 'Allen & Heath SQ-6 新闻发布厅调音台',
      group_name: '媒体转播运行组',
      region_name: '新闻发布大厅 (Press Conference Hall)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.115',
      target_port: 51325,
      online_status: 'ONLINE',
      remark: '新闻发布与媒体混音矩阵，支持高保真转播立体声输出',
      commands: [
        { id: 1, command_name: '全通道快速复位 (0dB)', command_code: 'RESET_0DB', payload_format: 'HEX', command_payload: '55 AA 00 00 FADER_RESET', expected_ack: 'ACK_OK', timeout_ms: 1000, is_dangerous: false, remark: '发布厅推子复位' },
        { id: 2, command_name: '全场紧急静音 (MUTE ALL)', command_code: 'MUTE_ALL', payload_format: 'HEX', command_payload: '55 AA FF FF MUTE_ENABLE', expected_ack: 'ACK_MUTED', timeout_ms: 800, is_dangerous: true, remark: '发布厅紧急静音' }
      ]
    },
    {
      id: 104,
      hardware_type: 'AUDIO',
      custom_no: 'AUD-AMP-POOL-01',
      device_code: 'DEV_AUDIO_04',
      device_name: 'Crown DCI 8|600N 8通道多区主功放',
      group_name: '主赛场核心运行组',
      region_name: '主游泳跳水馆 (比赛池)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.110',
      target_port: 5000,
      online_status: 'ONLINE',
      remark: '负责东/西看台线性阵列主扬声器驱动，支持Dante网络音频',
      commands: [
        { id: 1, command_name: '功放开机运行', command_code: 'AMP_PWR_ON', payload_format: 'ASCII', command_payload: 'POWER ON CHANNEL ALL', expected_ack: 'ACK PWR_ON', timeout_ms: 1500, is_dangerous: false, remark: '高压继电器吸合' },
        { id: 2, command_name: '功放休眠待机', command_code: 'AMP_STANDBY', payload_format: 'ASCII', command_payload: 'POWER STANDBY', expected_ack: 'ACK STANDBY', timeout_ms: 1500, is_dangerous: false, remark: '降低功耗' }
      ]
    },

    // 2. 场地照明
    {
      id: 201,
      hardware_type: 'LIGHTING',
      custom_no: 'LGT-GATEWAY-01',
      device_code: 'DEV_LIGHT_01',
      device_name: 'DMX512/Modbus 比赛池高杆智能灯控柜',
      group_name: '主赛场核心运行组',
      region_name: '主游泳跳水馆 (比赛池)',
      connection_type: 'MODBUS',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.120',
      target_port: 502,
      online_status: 'ONLINE',
      remark: '控制比赛池上方 96 盏 2000W LED 专业无眩光赛事灯',
      commands: [
        { id: 1, command_name: '切换【国际赛事模式 (2000 Lux)】', command_code: 'SCENE_MATCH', payload_format: 'HEX', command_payload: '01 06 00 01 07 D0 D9 8E', expected_ack: '01 06 00 01 07 D0', timeout_ms: 1000, is_dangerous: false, remark: '满足高清电视转播要求' },
        { id: 2, command_name: '切换【日常训练模式 (750 Lux)】', command_code: 'SCENE_TRAIN', payload_format: 'HEX', command_payload: '01 06 00 01 02 EE D9 8E', expected_ack: '01 06 00 01 02 EE', timeout_ms: 1000, is_dangerous: false, remark: '运动员日常训练' },
        { id: 3, command_name: '全部灯光渐暗关灯', command_code: 'LIGHTS_OFF', payload_format: 'HEX', command_payload: '01 06 00 01 00 00 D9 8E', expected_ack: '01 06 00 01 00 00', timeout_ms: 1500, is_dangerous: true, remark: '场馆清场闭馆' }
      ]
    },

    // 3. LED大屏
    {
      id: 301,
      hardware_type: 'SCREEN',
      custom_no: 'SCR-NOVA-CENTER',
      device_code: 'DEV_SCREEN_01',
      device_name: 'Novastar H9 模块化视频拼接处理器 (中央斗屏)',
      group_name: '主赛场核心运行组',
      region_name: '主游泳跳水馆 (比赛池)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.150',
      target_port: 8000,
      online_status: 'ONLINE',
      remark: '驱动中央四面漏斗屏及环形屏，支持 4K 60Hz 信号无缝开窗切换',
      commands: [
        { id: 1, command_name: '切换输入源：【赛事计时成绩】', command_code: 'INPUT_TIMING', payload_format: 'HEX', command_payload: '55 AA 01 01 04 01 CH_HDMI1', expected_ack: '55 AA 01 ACK', timeout_ms: 800, is_dangerous: false, remark: '展示即时成绩榜单' },
        { id: 2, command_name: '切换输入源：【现场特写导播信号】', command_code: 'INPUT_LIVE', payload_format: 'HEX', command_payload: '55 AA 01 01 04 02 CH_SDI1', expected_ack: '55 AA 01 ACK', timeout_ms: 800, is_dangerous: false, remark: '转播慢动作回放' },
        { id: 3, command_name: '大屏黑屏/开屏保 (Blackout)', command_code: 'SCREEN_BLACK', payload_format: 'HEX', command_payload: '55 AA FF 00 00 00 BLACKOUT', expected_ack: '55 AA FF ACK', timeout_ms: 600, is_dangerous: true, remark: '紧急推黑' }
      ]
    },

    // 4. 计时计分 (专业游泳/跳水/田径竞赛计时系统)
    {
      id: 401,
      hardware_type: 'SCORE',
      custom_no: 'TIM-SWIM-MASTER',
      device_code: 'DEV_SCORE_01',
      device_name: 'Omega ARES 21 游泳/跳水专业计时主机 (主控机)',
      group_name: '主赛场核心运行组',
      region_name: '裁判竞赛办公室 (Timing Room)',
      connection_type: 'UDP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.180',
      target_port: 9000,
      online_status: 'ONLINE',
      remark: '连接 10 条泳道触板与终点摄像判读系统，授时精度达 1/1000 秒，双机热备主路',
      commands: [
        { id: 1, command_name: '赛事发令准备 (READY_RESET)', command_code: 'READY_RESET', payload_format: 'ASCII', command_payload: 'CMD:RACE_READY LANE:ALL', expected_ack: 'ACK:READY_OK', timeout_ms: 600, is_dangerous: false, remark: '清空触板数据，准备发令' },
        { id: 2, command_name: '强制同步成绩至大屏与转播总线', command_code: 'SYNC_BOARD', payload_format: 'ASCII', command_payload: 'CMD:PUSH_RESULT_ALL', expected_ack: 'ACK:SYNCED', timeout_ms: 1000, is_dangerous: false, remark: '锁定官方正式名次并推屏' },
        { id: 3, command_name: '触板灵敏度自检与阻抗校验', command_code: 'CHECK_TOUCH_PAD', payload_format: 'ASCII', command_payload: 'CMD:TEST_PAD_IMPEDANCE', expected_ack: 'ACK:PADS_ALL_OK', timeout_ms: 800, is_dangerous: false, remark: '巡检1~10道次触板' }
      ]
    },
    {
      id: 402,
      hardware_type: 'SCORE',
      custom_no: 'TIM-SWIM-SLAVE',
      device_code: 'DEV_SCORE_02',
      device_name: 'Omega Quantum 备用热备高精度计时主机 (备用机)',
      group_name: '主赛场核心运行组',
      region_name: '主游泳馆弱电机房 (Rack Room B)',
      connection_type: 'UDP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.181',
      target_port: 9000,
      online_status: 'ONLINE',
      remark: '热备无缝冗余从机，与主控机双重接收光电触板触发脉冲，防止单点故障',
      commands: [
        { id: 1, command_name: '赛事发令准备 (READY_RESET)', command_code: 'READY_RESET', payload_format: 'ASCII', command_payload: 'CMD:RACE_READY LANE:ALL', expected_ack: 'ACK:READY_OK', timeout_ms: 600, is_dangerous: false, remark: '备机清空触板数据' },
        { id: 2, command_name: '主备数据帧校验与时钟镜像同步', command_code: 'SYNC_MIRROR', payload_format: 'ASCII', command_payload: 'CMD:SYNC_WITH_MASTER', expected_ack: 'ACK:MIRROR_OK', timeout_ms: 500, is_dangerous: false, remark: '主备保持0纳秒偏差' }
      ]
    },
    {
      id: 403,
      hardware_type: 'SCORE',
      custom_no: 'TIM-TRACK-01',
      device_code: 'DEV_SCORE_03',
      device_name: 'Swiss Timing 综合副馆多功能赛事电子计时机',
      group_name: '热身副馆运行组',
      region_name: '副馆热身池裁判台 (Warm-up Pool)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.182',
      target_port: 8800,
      online_status: 'ONLINE',
      remark: '负责副馆热身池分段训练计时或球类赛事 24 秒/倒计时计分调度',
      commands: [
        { id: 1, command_name: '赛事发令准备 (READY_RESET)', command_code: 'READY_RESET', payload_format: 'ASCII', command_payload: 'CMD:RACE_READY LANE:ALL', expected_ack: 'ACK:READY_OK', timeout_ms: 600, is_dangerous: false, remark: '副馆准备发令' },
        { id: 2, command_name: '强制同步成绩至大屏与转播总线', command_code: 'SYNC_BOARD', payload_format: 'ASCII', command_payload: 'CMD:PUSH_RESULT_ALL', expected_ack: 'ACK:SYNCED', timeout_ms: 1000, is_dangerous: false, remark: '副馆推屏' }
      ]
    },

    // 5. 智能升旗
    {
      id: 501,
      hardware_type: 'FLAG',
      custom_no: 'FLG-PLC-STAGE',
      device_code: 'DEV_FLAG_01',
      device_name: '西门子 S7-1200 颁奖国旗升降伺服控制箱',
      group_name: '主赛场核心运行组',
      region_name: '主游泳跳水馆 (比赛池)',
      connection_type: 'SERIAL',
      serial_port: 'COM4',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '',
      target_port: 0,
      online_status: 'ONLINE',
      remark: '控制 1~3 号旗杆，升旗速度严格与 46 秒中华人民共和国国歌自动测速同步',
      commands: [
        { id: 1, command_name: '一键升国旗仪式 (音画测速启动)', command_code: 'FLAG_START_46S', payload_format: 'HEX', command_payload: '55 AA 02 01 00 2E CRC16_FLAG', expected_ack: '55 AA 02 ACK_RUN', timeout_ms: 1200, is_dangerous: false, remark: '旗杆伺服电机匀速上升' },
        { id: 2, command_name: '升旗机构紧急停止 (ESTOP)', command_code: 'FLAG_ESTOP', payload_format: 'HEX', command_payload: '55 AA FF 00 00 00 ESTOP', expected_ack: '55 AA FF ACK_STOP', timeout_ms: 300, is_dangerous: true, remark: '最高优先级切断抱闸' },
        { id: 3, command_name: '降旗复位至底端基准点', command_code: 'FLAG_RESET_DOWN', payload_format: 'HEX', command_payload: '55 AA 02 02 00 00 RESET_DOWN', expected_ack: '55 AA 02 ACK_DOWN', timeout_ms: 1500, is_dangerous: false, remark: '缓慢落旗归位' }
      ]
    },

    // 6. 时钟同步
    {
      id: 601,
      hardware_type: 'CLOCK',
      custom_no: 'CLK-GPS-MASTER',
      device_code: 'DEV_CLOCK_01',
      device_name: '北斗/GPS 双模一级高精度网络母钟主机',
      group_name: '总控设备枢纽组',
      region_name: '总控调度机房 (Control Room)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.100',
      target_port: 8088,
      online_status: 'ONLINE',
      remark: '北斗卫星锁定数: 12颗，GPS: 8颗，向全场 64 只数码子钟提供统一时统标准',
      commands: [
        { id: 1, command_name: '强制全场子钟网络毫秒级对时', command_code: 'FORCE_CLOCK_SYNC', payload_format: 'ASCII', command_payload: 'SYNC_ALL_SUBCLOCKS_NOW', expected_ack: 'ACK:SYNC_COMPLETE', timeout_ms: 1000, is_dangerous: false, remark: '统一全场时间偏差' },
        { id: 2, command_name: '查询卫星锁定星数与时钟守时精度', command_code: 'QUERY_SATELLITE', payload_format: 'ASCII', command_payload: 'GET_GNSS_STATUS', expected_ack: 'SAT:BD12_GPS8_LOCKED', timeout_ms: 600, is_dangerous: false, remark: '巡检天线状态' }
      ]
    },

    // 7. 视频监控
    {
      id: 701,
      hardware_type: 'VIDEO',
      custom_no: 'CAM-UNDERWATER-01',
      device_code: 'DEV_VIDEO_01',
      device_name: '水下专业超清高速转播摄像机 (50米深防水)',
      group_name: '主赛场核心运行组',
      region_name: '主游泳跳水馆 (比赛池)',
      connection_type: 'RTSP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.201',
      target_port: 554,
      online_status: 'ONLINE',
      remark: '安装于 5 号泳道底部观察窗，拍摄转身触板与水下划水姿态',
      commands: [
        { id: 1, command_name: '云台预置位召回：【泳池中央特写】', command_code: 'PTZ_PRESET_1', payload_format: 'ASCII', command_payload: 'PTZ_GOTO_PRESET:1', expected_ack: 'PTZ_ACK:OK', timeout_ms: 800, is_dangerous: false, remark: '转向主赛道' },
        { id: 2, command_name: '启动水下补光灯 (5000K冷白光)', command_code: 'LIGHT_WATER_ON', payload_format: 'HEX', command_payload: 'A0 00 00 00 00 00 00 AF', expected_ack: 'A0 ACK', timeout_ms: 600, is_dangerous: false, remark: '提高水下通透度' }
      ]
    },

    // 8. 媒体播控
    {
      id: 801,
      hardware_type: 'MEDIA',
      custom_no: 'MED-BGM-SERVER',
      device_code: 'DEV_MEDIA_01',
      device_name: 'Hi-Fi 广播音源网络播放主机 (Dante声卡)',
      group_name: '主赛场核心运行组',
      region_name: '总控调度机房 (Control Room)',
      connection_type: 'HTTP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.88',
      target_port: 8080,
      online_status: 'ONLINE',
      remark: '内置国歌高保真音源、颁奖曲库及环境轻音乐循环素材',
      commands: [
        { id: 1, command_name: '播放【中华人民共和国国歌 (46秒标准版)】', command_code: 'PLAY_ANTHEM', payload_format: 'JSON', command_payload: '{"action":"play","track_id":1,"fade_in_ms":0}', expected_ack: '{"status":"playing"}', timeout_ms: 600, is_dangerous: false, remark: '升旗仪式主音轨' },
        { id: 2, command_name: '播放【颁奖仪式荣誉进行曲】', command_code: 'PLAY_AWARD', payload_format: 'JSON', command_payload: '{"action":"play","track_id":3,"loop":true}', expected_ack: '{"status":"playing"}', timeout_ms: 600, is_dangerous: false, remark: '运动员登台领奖' },
        { id: 3, command_name: '淡出停止所有正在播放的媒体音乐', command_code: 'STOP_FADE', payload_format: 'JSON', command_payload: '{"action":"fade_out_stop","duration_ms":1000}', expected_ack: '{"status":"stopped"}', timeout_ms: 1200, is_dangerous: false, remark: '平滑静音' }
      ]
    },

    // 9. 能耗监测
    {
      id: 901,
      hardware_type: 'ENERGY',
      custom_no: 'ENG-METER-MAIN',
      device_code: 'DEV_ENERGY_01',
      device_name: 'Acrel APM810 三相多功能高精度电力电表',
      group_name: '日常节能轮训组',
      region_name: '地下变配电室与动力机房',
      connection_type: 'MODBUS',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.130',
      target_port: 502,
      online_status: 'ONLINE',
      remark: '采集全馆 10kV 进线变压器母线总有功功率、功率因数与实时电流',
      commands: [
        { id: 1, command_name: '读取三相电压、电流与瞬时总功率', command_code: 'READ_POWER', payload_format: 'HEX', command_payload: '01 03 00 00 00 06 C5 C8', expected_ack: '01 03 0C 08 9A', timeout_ms: 600, is_dangerous: false, remark: '遥测遥信' },
        { id: 2, command_name: '读取累计有功电度量 (kWh)', command_code: 'READ_KWH', payload_format: 'HEX', command_payload: '01 03 01 00 00 02 C5 F7', expected_ack: '01 03 04 00 1A 2B 3C', timeout_ms: 600, is_dangerous: false, remark: '抄表结算' }
      ]
    },

    // 10. 暖通空调
    {
      id: 1001,
      hardware_type: 'HVAC',
      custom_no: 'HVC-HEAT-POOL-01',
      device_code: 'DEV_HVAC_01',
      device_name: '芬尼克兹 200kW 泳池恒温热泵变频机组',
      group_name: '日常节能轮训组',
      region_name: '地下变配电室与动力机房',
      connection_type: 'MODBUS',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.140',
      target_port: 502,
      online_status: 'ONLINE',
      remark: '比赛池水温维持在 26.5℃ ± 0.5℃ 国际泳联竞赛标准',
      commands: [
        { id: 1, command_name: '设定目标水温为【26.5 ℃ 国际比赛标准】', command_code: 'SET_TEMP_265', payload_format: 'HEX', command_payload: '02 06 00 10 01 09 88 56', expected_ack: '02 06 00 10 01 09', timeout_ms: 1200, is_dangerous: false, remark: '水质恒温' },
        { id: 2, command_name: '查询当前水温、热泵出水温度与压缩机频率', command_code: 'QUERY_POOL_TEMP', payload_format: 'HEX', command_payload: '02 03 00 20 00 04 45 F8', expected_ack: '02 03 08 01 09', timeout_ms: 800, is_dangerous: false, remark: '状态监控' }
      ]
    },

    // 11. 安防门禁与防盗报警
    {
      id: 1101,
      hardware_type: 'SECURITY',
      custom_no: 'SEC-ACCESS-VIP',
      device_code: 'DEV_SEC_01',
      device_name: '海康威视 DS-K2604 四门网络门禁主控板',
      group_name: '应急防灾联动组',
      region_name: 'VIP主席台与贵宾包厢',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.160',
      target_port: 6000,
      online_status: 'ONLINE',
      remark: '控制主席台、裁判长室、网络机房出入口，支持指纹/刷卡/远程开门',
      commands: [
        { id: 1, command_name: '紧急开门放行 (全门常开)', command_code: 'OPEN_ALL_DOORS', payload_format: 'ASCII', command_payload: 'CMD:DOOR_EMERGENCY_UNLOCK_ALL', expected_ack: 'ACK:UNLOCKED', timeout_ms: 500, is_dangerous: true, remark: '消防疏散联动' },
        { id: 2, command_name: '恢复门禁安全设防 (刷卡进出)', command_code: 'ARM_DOORS', payload_format: 'ASCII', command_payload: 'CMD:DOOR_NORMAL_SECURITY_ARM', expected_ack: 'ACK:ARMED', timeout_ms: 500, is_dangerous: false, remark: '日常防范' }
      ]
    },

    // 12. 公共广播
    {
      id: 1201,
      hardware_type: 'BROADCAST',
      custom_no: 'BCD-ZONE-MATRIX',
      device_code: 'DEV_BCD_01',
      device_name: 'BOSCH Praesideo 16分区 IP网络公共广播矩阵',
      group_name: '看台观众服务组',
      region_name: '总控调度机房 (Control Room)',
      connection_type: 'TCP',
      serial_port: '',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '192.168.1.170',
      target_port: 7000,
      online_status: 'ONLINE',
      remark: '覆盖观众大厅、看台走廊、检票口、卫生间及地下车库广播分区',
      commands: [
        { id: 1, command_name: '播报【观众检票入场温馨提示语音】', command_code: 'MSG_WELCOME', payload_format: 'ASCII', command_payload: 'BROADCAST_MSG:WELCOME_01 ZONES:ALL', expected_ack: 'ACK:PLAYING', timeout_ms: 1000, is_dangerous: false, remark: '赛前半小时' },
        { id: 2, command_name: '播报【赛后有序退场文明指引】', command_code: 'MSG_GOODBYE', payload_format: 'ASCII', command_payload: 'BROADCAST_MSG:EXIT_02 ZONES:ALL', expected_ack: 'ACK:PLAYING', timeout_ms: 1000, is_dangerous: false, remark: '散场引导' }
      ]
    },

    // 13. 动环与智能传感器
    {
      id: 1301,
      hardware_type: 'ENVIRONMENT',
      custom_no: 'ENV-WATER-SENSE-01',
      device_code: 'DEV_ENV_01',
      device_name: '泳池水质与多参数微气象综合传感主机',
      group_name: '主赛场核心运行组',
      region_name: '主游泳跳水馆 (比赛池)',
      connection_type: 'MODBUS',
      serial_port: 'COM5',
      baud_rate: 9600,
      data_bits: 8,
      stop_bits: '1',
      parity: 'NONE',
      target_ip: '',
      target_port: 0,
      online_status: 'ONLINE',
      remark: '实时在线检测水质 pH值(7.2~7.6)、余氯浓度(0.3~0.5mg/L)、环境湿度(65%)',
      commands: [
        { id: 1, command_name: '采集当前水质pH值、余氯、温度指标', command_code: 'READ_WATER_QUALITY', payload_format: 'HEX', command_payload: '05 03 00 00 00 04 44 4E', expected_ack: '05 03 08 02 DE 00 32', timeout_ms: 800, is_dangerous: false, remark: '水质达标巡检' },
        { id: 2, command_name: '校准探头基准参考点 (CALIBRATE)', command_code: 'CALIBRATE_PH', payload_format: 'HEX', command_payload: '05 06 00 1F 00 01 79 88', expected_ack: '05 06 00 1F ACK', timeout_ms: 1500, is_dangerous: true, remark: '电极归零' }
      ]
    }
  ]

  return devices
}

// 初始化历史执行记录
function createInitialLogs() {
  return [
    {
      id: 1,
      trace_id: 'TRC-A8192F10',
      device_id: 101,
      custom_no: 'AUD-MIX-01',
      device_name: 'Soundcraft Vi3000 数字调音台主控机',
      hardware_type: 'AUDIO',
      command_name: '全通道快速复位 (0dB)',
      command_payload: '55 AA 00 00 FADER_RESET',
      execute_result: 'SUCCESS',
      response_payload: '55 AA 00 ACK_FADER_RESET_ALL_OK',
      cost_ms: 18,
      operator_name: 'admin',
      is_batch: 0,
      created_at: '2026-10-12 11:50:22'
    },
    {
      id: 2,
      trace_id: 'TRC-B3910E24',
      device_id: 201,
      custom_no: 'LGT-GATEWAY-01',
      device_name: 'DMX512/Modbus 比赛池高杆智能灯控柜',
      hardware_type: 'LIGHTING',
      command_name: '切换【国际赛事模式 (2000 Lux)】',
      command_payload: '01 06 00 01 07 D0 D9 8E',
      execute_result: 'SUCCESS',
      response_payload: '01 06 00 01 07 D0 (ECHO_OK)',
      cost_ms: 32,
      operator_name: 'operator',
      is_batch: 0,
      created_at: '2026-10-12 11:45:10'
    },
    {
      id: 3,
      trace_id: 'TRC-C7482A09',
      device_id: 501,
      custom_no: 'FLG-PLC-STAGE',
      device_name: '西门子 S7-1200 颁奖国旗升降伺服控制箱',
      hardware_type: 'FLAG',
      command_name: '升旗机构紧急停止 (ESTOP)',
      command_payload: '55 AA FF 00 00 00 ESTOP',
      execute_result: 'SUCCESS',
      response_payload: '55 AA FF ACK_ESTOP_BRAKE_ON',
      cost_ms: 12,
      operator_name: 'admin',
      is_batch: 0,
      created_at: '2026-10-12 11:30:05'
    },
    {
      id: 4,
      trace_id: 'TRC-D9018C55',
      device_id: 601,
      custom_no: 'CLK-GPS-MASTER',
      device_name: '北斗/GPS 双模一级高精度网络母钟主机',
      hardware_type: 'CLOCK',
      command_name: '强制全场子钟网络毫秒级对时',
      command_payload: 'SYNC_ALL_SUBCLOCKS_NOW',
      execute_result: 'SUCCESS',
      response_payload: 'ACK:SYNC_COMPLETE (DRIFT: <0.5ms)',
      cost_ms: 24,
      operator_name: 'admin',
      is_batch: 0,
      created_at: '2026-10-12 11:15:00'
    }
  ]
}

// 本地存储读写助手
function loadFromStorage(key, defaultVal) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return defaultVal
    return JSON.parse(raw)
  } catch (e) {
    console.warn(`[iotDeviceService] 读取本地存储 ${key} 失败:`, e)
    return defaultVal
  }
}

function saveToStorage(key, val) {
  try {
    localStorage.setItem(key, JSON.stringify(val))
  } catch (e) {
    console.error(`[iotDeviceService] 写入本地存储 ${key} 失败:`, e)
  }
}

// 内存单例数据源
let inMemoryDevices = loadFromStorage(STORAGE_KEY_DEVICES, null)
if (!inMemoryDevices || inMemoryDevices.length === 0) {
  inMemoryDevices = createInitialDevices()
  saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
} else {
  // 智能补偿多套调音台设备实例 (确保扩声类型包含 AUD-MIX-01, AUD-MIX-02, AUD-MIX-03)
  const hasMixer2 = inMemoryDevices.some(d => d.custom_no === 'AUD-MIX-02')
  if (!hasMixer2) {
    const initialList = createInitialDevices()
    const newMixers = initialList.filter(d => d.custom_no === 'AUD-MIX-02' || d.custom_no === 'AUD-MIX-03')
    inMemoryDevices.push(...newMixers)
    saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
  }

  // 智能补偿多套计时计分系统设备实例 (确保包含 TIM-SWIM-MASTER, TIM-SWIM-SLAVE, TIM-TRACK-01)
  const hasTimerSlave = inMemoryDevices.some(d => d.custom_no === 'TIM-SWIM-SLAVE')
  if (!hasTimerSlave) {
    const initialList = createInitialDevices()
    const newTimers = initialList.filter(d => d.custom_no === 'TIM-SWIM-SLAVE' || d.custom_no === 'TIM-TRACK-01')
    inMemoryDevices.push(...newTimers)
    saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
  }
}

let inMemoryLogs = loadFromStorage(STORAGE_KEY_LOGS, null)
if (!inMemoryLogs || inMemoryLogs.length === 0) {
  inMemoryLogs = createInitialLogs()
  saveToStorage(STORAGE_KEY_LOGS, inMemoryLogs)
}

export const iotDeviceService = {
  // 获取 13 类弱电硬件元数据字典
  getHardwareTypes() {
    return HARDWARE_TYPES
  },

  // 获取特定硬件类型的统计概要
  getHardwareSummary(hardwareType) {
    const list = this.getDevices(hardwareType)
    const onlineCount = list.filter(d => d.online_status === 'ONLINE').length
    const faultCount = list.filter(d => d.online_status === 'FAULT').length
    return {
      total: list.length,
      online: onlineCount,
      fault: faultCount,
      offline: list.length - onlineCount - faultCount
    }
  },

  // 获取全局设备统计看板
  getGlobalStats() {
    const all = inMemoryDevices
    const online = all.filter(d => d.online_status === 'ONLINE').length
    const totalLogs = inMemoryLogs.length
    const successLogs = inMemoryLogs.filter(l => l.execute_result === 'SUCCESS').length
    const successRate = totalLogs > 0 ? ((successLogs / totalLogs) * 100).toFixed(1) : '100.0'

    return {
      totalDevices: all.length,
      onlineDevices: online,
      totalLogs,
      successRate: `${successRate}%`
    }
  },

  // 查询设备列表 (支持按类型、自编号模糊、名称模糊、分组、区域筛选)
  getDevices(hardwareType = 'ALL', filters = {}) {
    let result = inMemoryDevices

    if (hardwareType && hardwareType !== 'ALL') {
      result = result.filter(d => d.hardware_type === hardwareType)
      // 容错兜底：如果是 SCORE 且结果为空，则即时从默认设备库注入
      if (result.length === 0 && hardwareType === 'SCORE') {
        const initialList = createInitialDevices()
        const scoreDevs = initialList.filter(d => d.hardware_type === 'SCORE')
        if (scoreDevs.length > 0) {
          inMemoryDevices.push(...scoreDevs)
          saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
          result = scoreDevs
        }
      }
    }

    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase().trim()
      result = result.filter(d =>
        (d.custom_no && d.custom_no.toLowerCase().includes(kw)) ||
        (d.device_name && d.device_name.toLowerCase().includes(kw)) ||
        (d.device_code && d.device_code.toLowerCase().includes(kw))
      )
    }

    if (filters.group_name) {
      result = result.filter(d => d.group_name === filters.group_name)
    }

    if (filters.region_name) {
      result = result.filter(d => d.region_name === filters.region_name)
    }

    if (filters.online_status) {
      result = result.filter(d => d.online_status === filters.online_status)
    }

    return result
  },

  // 按照硬件类型获取设备列表 (例如 'SCORE', 'AUDIO', 'SCREEN')
  getDevicesByType(hardwareType) {
    return this.getDevices(hardwareType)
  },

  // 获取单个设备详情
  getDeviceById(id) {
    return inMemoryDevices.find(d => d.id === Number(id)) || null
  },

  // 创建新设备
  createDevice(deviceData) {
    const newId = Date.now()
    const typeMeta = HARDWARE_TYPES.find(t => t.type === deviceData.hardware_type) || HARDWARE_TYPES[0]
    const customNo = deviceData.custom_no || `${typeMeta.codePrefix}-${String(newId).slice(-4)}`

    const newDevice = {
      id: newId,
      hardware_type: deviceData.hardware_type || 'AUDIO',
      custom_no: customNo,
      device_code: deviceData.device_code || `DEV_${typeMeta.codePrefix}_${String(newId).slice(-4)}`,
      device_name: deviceData.device_name || '新登记硬件设备',
      group_name: deviceData.group_name || '主赛场核心运行组',
      region_name: deviceData.region_name || '主体育馆 (比赛池)',
      connection_type: deviceData.connection_type || 'SERIAL',
      serial_port: deviceData.serial_port || 'COM1',
      baud_rate: Number(deviceData.baud_rate) || 9600,
      data_bits: Number(deviceData.data_bits) || 8,
      stop_bits: String(deviceData.stop_bits || '1'),
      parity: deviceData.parity || 'NONE',
      target_ip: deviceData.target_ip || '',
      target_port: Number(deviceData.target_port) || 0,
      online_status: deviceData.online_status || 'ONLINE',
      remark: deviceData.remark || '',
      commands: deviceData.commands || [
        {
          id: 1,
          command_name: '系统开机/启动',
          command_code: 'SYS_ON',
          payload_format: 'HEX',
          command_payload: '55 AA 01 01 START',
          expected_ack: 'ACK_OK',
          timeout_ms: 1000,
          is_dangerous: false,
          remark: '默认启动指令'
        },
        {
          id: 2,
          command_name: '状态轮询心跳查询',
          command_code: 'SYS_PING',
          payload_format: 'HEX',
          command_payload: '55 AA 00 00 PING',
          expected_ack: 'ACK_PONG',
          timeout_ms: 500,
          is_dangerous: false,
          remark: '心跳探针'
        }
      ]
    }

    inMemoryDevices.unshift(newDevice)
    saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
    return newDevice
  },

  // 更新设备信息 (参数编辑)
  updateDevice(id, updateData) {
    const idx = inMemoryDevices.findIndex(d => d.id === Number(id))
    if (idx === -1) throw new Error('目标设备不存在或已被移除')

    inMemoryDevices[idx] = {
      ...inMemoryDevices[idx],
      ...updateData,
      id: Number(id)
    }

    saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
    return inMemoryDevices[idx]
  },

  // 删除设备
  deleteDevice(id) {
    const idx = inMemoryDevices.findIndex(d => d.id === Number(id))
    if (idx === -1) return false

    inMemoryDevices.splice(idx, 1)
    saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
    return true
  },

  // 批量删除
  batchDeleteDevices(ids = []) {
    const idSet = new Set(ids.map(Number))
    inMemoryDevices = inMemoryDevices.filter(d => !idSet.has(d.id))
    saveToStorage(STORAGE_KEY_DEVICES, inMemoryDevices)
    return true
  },

  // 获取特定设备的指令列表
  getDeviceCommands(deviceId) {
    const dev = this.getDeviceById(deviceId)
    return dev ? (dev.commands || []) : []
  },

  // 为特定设备新增/更新指令
  saveDeviceCommand(deviceId, commandData) {
    const dev = this.getDeviceById(deviceId)
    if (!dev) throw new Error('设备不存在')

    if (!dev.commands) dev.commands = []

    if (commandData.id) {
      // 更新现有指令
      const cIdx = dev.commands.findIndex(c => c.id === Number(commandData.id))
      if (cIdx !== -1) {
        dev.commands[cIdx] = { ...dev.commands[cIdx], ...commandData }
      }
    } else {
      // 新增指令
      const newCmd = {
        ...commandData,
        id: Date.now(),
        command_code: commandData.command_code || `CMD_${Date.now().toString().slice(-4)}`
      }
      dev.commands.push(newCmd)
    }

    this.updateDevice(deviceId, { commands: dev.commands })
    return dev.commands
  },

  // 删除特定设备的某个指令
  deleteDeviceCommand(deviceId, commandId) {
    const dev = this.getDeviceById(deviceId)
    if (!dev || !dev.commands) return false

    dev.commands = dev.commands.filter(c => c.id !== Number(commandId))
    this.updateDevice(deviceId, { commands: dev.commands })
    return true
  },

  // 发送指令核心引擎 (支持勾选某一个设备或全选批量下发，生成执行结果回执)
  // 签名：sendCommand(targetDeviceIds: number[]|number, commandPayload: string,
  //                     commandName: string, operator: string)
  async sendCommand(targetDeviceIds = [], commandPayload, commandName = '快速即时控制指令', operator = 'admin') {
    // 容错归一化：允许传入单个设备 ID（标量），避免调用方误传导致不可迭代报错
    let ids = targetDeviceIds
    if (typeof ids === 'number' || typeof ids === 'string') {
      ids = [ids]
    } else if (!Array.isArray(ids)) {
      ids = ids ? [ids] : []
    }

    if (ids.length === 0) {
      throw new Error('请至少勾选一台目标设备！')
    }

    // 参数顺序误用的早期拦截：第二个形参应为字符串/Buffer，而非对象
    if (commandPayload === null || typeof commandPayload === 'object') {
      throw new Error(
        'sendCommand 调用参数错误：应为 sendCommand(deviceIds: number[], payload: string, name: string, operator: string)'
      )
    }

    const isBatch = ids.length > 1
    const results = []

    for (const devId of ids) {
      const dev = this.getDeviceById(devId)
      if (!dev) continue

      // 模拟硬件物理通信耗时 (15ms ~ 45ms)
      const costMs = Math.floor(Math.random() * 30) + 15
      const traceId = 'TRC-' + Math.random().toString(36).substring(2, 10).toUpperCase()

      // 模拟 96% 成功率，4% 偶发超时/失败
      let executeResult = 'SUCCESS'
      let responsePayload = ''

      if (dev.online_status === 'OFFLINE') {
        executeResult = 'OFFLINE'
        responsePayload = 'ERR_COMM_OFFLINE: 链路未建立，目标设备离线'
      } else {
        const isSuccess = Math.random() > 0.05
        if (isSuccess) {
          executeResult = 'SUCCESS'
          responsePayload = `ACK_${dev.custom_no}_${commandPayload.slice(0, 12)}_OK [ECHO: 0x55 AA 00]`
        } else {
          executeResult = 'FAILED'
          responsePayload = 'NACK_CHECKSUM_MISMATCH_OR_BUSY [0x55 AA FF]'
        }
      }

      const logItem = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        trace_id: traceId,
        device_id: dev.id,
        custom_no: dev.custom_no,
        device_name: dev.device_name,
        hardware_type: dev.hardware_type,
        command_name: commandName,
        command_payload: commandPayload,
        execute_result: executeResult,
        response_payload: responsePayload,
        cost_ms: costMs,
        operator_name: operator,
        is_batch: isBatch ? 1 : 0,
        created_at: new Date().toLocaleString('zh-CN', { hour12: false })
      }

      // 写入日志
      inMemoryLogs.unshift(logItem)
      results.push(logItem)
    }

    // 限制日志最大留存 300 条
    if (inMemoryLogs.length > 300) {
      inMemoryLogs = inMemoryLogs.slice(0, 300)
    }
    saveToStorage(STORAGE_KEY_LOGS, inMemoryLogs)

    return results
  },

  // 获取指令执行记录流水
  getCommandLogs(filters = {}) {
    let result = inMemoryLogs

    if (filters.deviceId) {
      result = result.filter(l => l.device_id === Number(filters.deviceId))
    }

    if (filters.hardwareType && filters.hardwareType !== 'ALL') {
      result = result.filter(l => l.hardware_type === filters.hardwareType)
    }

    if (filters.executeResult && filters.executeResult !== 'ALL') {
      result = result.filter(l => l.execute_result === filters.executeResult)
    }

    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase().trim()
      result = result.filter(l =>
        (l.custom_no && l.custom_no.toLowerCase().includes(kw)) ||
        (l.device_name && l.device_name.toLowerCase().includes(kw)) ||
        (l.command_name && l.command_name.toLowerCase().includes(kw)) ||
        (l.trace_id && l.trace_id.toLowerCase().includes(kw))
      )
    }

    return result
  },

  // 清空指令日志
  clearCommandLogs() {
    inMemoryLogs = []
    saveToStorage(STORAGE_KEY_LOGS, inMemoryLogs)
    return true
  }
}

export default iotDeviceService
