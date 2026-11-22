<template>
  <div class="adapter-book-workspace">
    <!-- 顶部状态栏 -->
    <div class="adapter-top-bar glass-panel">
      <div class="top-left">
        <SvgIcon name="SvgAdapterBook" size="20" class="text-primary" />
        <div class="title-meta">
          <span class="view-title">外置硬件适配器与接线引脚登记台账</span>
          <p>登记协议转换器、物理接线和引脚定义，形成可追溯的硬件资产拓扑。</p>
        </div>
      </div>

      <div class="top-right">
        <button class="btn-header-action btn-header-primary" @click="addAdapter" title="登记并录入新的外置协议转换器或引脚连线台账">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>+ 登记外置硬件适配器</span>
        </button>
      </div>
    </div>

    <!-- 左右两栏布局：台账明细大表 + 右侧物理接线拓扑示意图 -->
    <div class="adapter-main-layout">
      <!-- 左栏：适配硬件台账明细表 -->
      <div class="col-table glass-panel">
        <div class="panel-header">
          <div class="header-title">
            <span>外置通信适配硬件资产名录 (Adapters & Converters)</span>
            <span class="panel-subtitle">登记物理转换器型号、接线方式、DB9/RJ45 引脚定义与责任人</span>
          </div>
          <span class="num-mono text-muted">共 {{ adapterList.length }} 项适配硬件</span>
        </div>

        <el-table :data="adapterList" style="width: 100%" size="small">
          <el-table-column prop="name" label="硬件适配设备名称" min-width="160">
            <template #default="{ row }">
              <span class="font-bold text-highlight">{{ row.name }}</span>
              <span class="model-tag num-mono">{{ row.model }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="convType" label="通信转换方式" width="140">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.convType }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="pinDef" label="接线与引脚定义 (Pinout)" min-width="180">
            <template #default="{ row }">
              <span class="num-mono text-sub">{{ row.pinDef }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="location" label="物理安装机柜" width="130" />

          <el-table-column prop="duty" label="责任运维人" width="110">
            <template #default="{ row }">
              <span class="duty-badge">{{ row.duty }}</span>
            </template>
          </el-table-column>

          <el-table-column label="动作" width="100" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="viewDetail(row)">
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 右栏：物理接线拓扑示意图 -->
      <div class="col-topology glass-panel">
        <div class="panel-header">
          <span class="header-title">工业物理接口接线引脚走向拓扑</span>
          <span class="num-mono text-primary">DB9 / RJ45 / RS485</span>
        </div>

        <div class="topology-diagram-box">
          <svg viewBox="0 0 380 400" class="topo-svg">
            <!-- 顶部服务器 -->
            <rect x="90" y="20" width="200" height="46" rx="6" fill="#2C1810" stroke="#C8A45C" stroke-width="2" />
            <text x="190" y="48" fill="#FDF8F0" font-size="14" font-weight="bold" text-anchor="middle">管控主机 / 前置网关</text>

            <!-- 主机下行网线 -->
            <line x1="190" y1="66" x2="190" y2="118" stroke="#8B6914" stroke-width="2" stroke-dasharray="4" />
            <text x="202" y="96" fill="#8C765C" font-size="14" class="num-mono">TCP/IP (RJ45)</text>

            <!-- 中间核心适配器：研华网络串口服务器 -->
            <rect x="60" y="118" width="260" height="66" rx="8" fill="#FDF8F0" stroke="#C8A45C" stroke-width="2" />
            <text x="190" y="144" fill="#2C1810" font-size="14" font-weight="bold" text-anchor="middle">研华 EKI-1524 串口服务器</text>
            <text x="190" y="168" fill="#8C765C" font-size="14" text-anchor="middle">4口 RS232/485 光电隔离</text>

            <!-- 3条下行总线 -->
            <!-- Port 1: 调音台 RS232 -->
            <path d="M 110 184 L 110 240 L 68 276" fill="none" stroke="#C8963E" stroke-width="1.8" />
            <rect x="15" y="276" width="106" height="52" rx="6" fill="#FFFFFF" stroke="#C8963E" stroke-width="1.8" />
            <text x="68" y="298" fill="#2C1810" font-size="14" font-weight="bold" text-anchor="middle">Soundcraft</text>
            <text x="68" y="318" fill="#8B6914" font-size="14" text-anchor="middle" class="num-mono">Pin 2/3/5</text>

            <!-- Port 2: 照明 Modbus -->
            <path d="M 190 184 L 190 276" fill="none" stroke="#C8A45C" stroke-width="1.8" />
            <rect x="137" y="276" width="106" height="52" rx="6" fill="#FFFFFF" stroke="#C8A45C" stroke-width="1.8" />
            <text x="190" y="298" fill="#2C1810" font-size="14" font-weight="bold" text-anchor="middle">照明 Lutron</text>
            <text x="190" y="318" fill="#8B6914" font-size="14" text-anchor="middle" class="num-mono">RS485 A+/B-</text>

            <!-- Port 3: 升旗 PLC -->
            <path d="M 270 184 L 270 240 L 312 276" fill="none" stroke="#5B8C5A" stroke-width="1.8" />
            <rect x="259" y="276" width="106" height="52" rx="6" fill="#FFFFFF" stroke="#5B8C5A" stroke-width="1.8" />
            <text x="312" y="298" fill="#2C1810" font-size="14" font-weight="bold" text-anchor="middle">升旗 S7 PLC</text>
            <text x="312" y="318" fill="#5B8C5A" font-size="14" text-anchor="middle" class="num-mono">Profibus屏蔽</text>

            <!-- 底部引脚规范提示 -->
            <text x="190" y="375" fill="#8C765C" font-size="14" text-anchor="middle">接地端统一采用 2.5mm² 多股铜芯等电位连接</text>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const adapterList = ref([
  {
    id: 1,
    name: '研华4口工业网络串口服务器',
    model: 'Advantech EKI-1524',
    convType: 'RJ45以太网转4路RS232/485',
    pinDef: 'P1: DB9-M (Pin2:RxD, Pin3:TxD, Pin5:GND); P2: Terminal (A+, B-, GND)',
    location: '弱电核心机房 02号网络机柜 12U',
    duty: '陈工 (机电)'
  },
  {
    id: 2,
    name: 'FTDI 工业级 USB 转 RS485 隔离转换器',
    model: 'Waveshare USB-TO-RS485 (B)',
    convType: 'USB 转 RS485 双向半双工',
    pinDef: 'A+ (485+), B- (485-), PE (屏蔽地线, 内置 600W 防雷防浪涌)',
    location: '主席台升旗基座下侧检修口',
    duty: '李工 (弱电)'
  },
  {
    id: 3,
    name: '双通道光电高速信号隔离中继器',
    model: 'Moxa TCC-120',
    convType: 'RS422/485 信号中继与光电隔离',
    pinDef: '2500V 光电隔离, 拨码开关设定终端匹配电阻 120Ω',
    location: '东看台声控室 调音台侧跳线架',
    duty: '刘主管 (音控)'
  },
  {
    id: 4,
    name: 'Blackmagic SDI 转 HDMI 视频转换盒',
    model: 'Micro Converter SDI to HDMI 3G',
    convType: 'SDI 广播信号转 HDMI 预览',
    pinDef: 'BNC 75Ω 接口输入, Type-A HDMI 输出',
    location: '大屏拼接控制器输入机柜',
    duty: '张工 (总控)'
  }
])

const viewDetail = (row) => {
  ElMessage.info(`查看硬件详情：${row.name} (${row.model})`)
}

const addAdapter = () => {
  ElMessage.info('打开外置适配器台账新增表单')
}
</script>

<style scoped>
.adapter-book-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.3s ease-out;
}

.adapter-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--do-coffee);
  letter-spacing: 0.5px;
}

.top-right {
  display: flex;
  gap: 12px;
}

.adapter-main-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 16px;
}

.col-table,
.col-topology {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border-card);
  border-radius: var(--do-radius-card);
  box-shadow: var(--do-shadow-card);
  overflow: hidden;
}

.panel-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--do-border-card);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(240, 235, 227, 0.4);
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-coffee);
}

.panel-subtitle {
  font-size: 14px;
  color: var(--do-coffee-light);
  font-weight: 400;
}

.model-tag {
  font-size: 14px;
  color: var(--do-gold-dark);
  display: block;
}

.duty-badge {
  background: rgba(var(--th-shadow-rgb), 0.05);
  border: 1px solid var(--do-border-card);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 14px;
  color: var(--do-coffee);
  font-weight: 600;
}

.topology-diagram-box {
  padding: 16px;
  background: var(--do-sand-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.topo-svg {
  width: 100%;
  max-height: 420px;
}
</style>
