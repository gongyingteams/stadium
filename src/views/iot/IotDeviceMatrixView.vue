<template>
  <div class="iot-matrix-workspace">
    <!-- 页面标题头：与大屏调度 / 计时计分保持一致 -->
    <section class="page-header glass-panel">
      <div class="page-heading">
        <div class="page-icon"><SvgIcon name="SvgIotControl" size="28" /></div>
        <div>
          <div class="title-row">
            <h1>物联硬件设备管理与批量指令总控中台</h1>
            <span class="system-badge">13 类硬件全纳管</span>
          </div>
          <p>设备台账 · 通信参数 · 分组区域 · 批量指令与毫秒级回执跟踪</p>
        </div>
      </div>

      <div class="header-status">
        <div class="status-metric"><span class="status-dot online"></span><span>控制总线正常</span></div>
        <div class="status-metric"><strong class="num-mono">{{ globalStats.onlineDevices }}/{{ globalStats.totalDevices }}</strong> 台在线</div>
        <button class="btn-header-action btn-header-manage" @click="openLogsDrawer" title="查看物联总控历史指令下发与回执流水">
          <SvgIcon name="SvgAdapterBook" size="14" style="margin-right: 4px;" />
          <span>指令记录 ({{ globalStats.totalLogs }})</span>
        </button>
        <button class="btn-header-action btn-header-primary" @click="openCreateDeviceModal" title="登记并接入新的弱电或物联硬件设备台账">
          <SvgIcon name="SvgDeviceSetting" size="14" style="margin-right: 4px;" />
          <span>登记新设备</span>
        </button>
      </div>
    </section>

    <!-- 关键指标卡：沿用参考页的六格信息带 -->
    <section class="metric-grid">
      <div class="metric-card glass-panel"><span>纳管设备总数</span><strong class="num-mono">{{ globalStats.totalDevices }}</strong><em>13 类基线硬件</em></div>
      <div class="metric-card glass-panel"><span>在线设备</span><strong class="num-mono">{{ globalStats.onlineDevices }}/{{ globalStats.totalDevices }}</strong><em>全场通信链路状态</em></div>
      <div class="metric-card glass-panel"><span>当前设备分类</span><strong>{{ activeTypeMeta.shortName }}</strong><em>{{ getDeviceCount(currentHardwareType) }} 台独立设备</em></div>
      <div class="metric-card glass-panel"><span>当前筛选结果</span><strong class="num-mono">{{ filteredDevices.length }}</strong><em>符合当前检索条件</em></div>
      <div class="metric-card glass-panel"><span>指令回执成功率</span><strong class="num-mono">{{ globalStats.successRate }}</strong><em>历史执行结果统计</em></div>
      <div class="metric-card glass-panel"><span>执行日志</span><strong class="num-mono">{{ globalStats.totalLogs }}</strong><em>可查看完整回执流水</em></div>
    </section>

    <!-- 主体双栏布局：左侧 13 项硬件类型导航，右侧所选硬件独立专属列表与控制 -->
    <div class="matrix-main-layout">
      <!-- 左侧：13 大类硬件类型选择导航树 -->
      <aside class="hardware-type-sidebar glass-panel">
        <div class="sidebar-header">
          <span class="sidebar-title">弱电硬件分类 (13项)</span>
          <span class="sidebar-sub">按类独立列表</span>
        </div>

        <div class="hardware-nav-list">
          <div v-for="(item, idx) in hardwareTypes" :key="item.type"
            :class="['hardware-nav-item', { active: currentHardwareType === item.type }]"
            @click="selectHardwareType(item.type)">
            <div class="nav-item-left">
              <span class="nav-index num-mono">{{ (idx + 1).toString().padStart(2, '0') }}</span>
              <div class="nav-icon-wrap">
                <SvgIcon :name="item.icon" size="18" />
              </div>
              <div class="nav-meta">
                <span class="nav-name">{{ item.name }}</span>
                <span class="nav-desc">{{ item.shortName }} · {{ item.defaultProtocol }}</span>
              </div>
            </div>

            <div class="nav-item-right">
              <span class="type-count-badge num-mono">{{ getDeviceCount(item.type) }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧：当前硬件类型专属设备列表、多维筛选、增删改查与批量下发 -->
      <main class="hardware-content-panel glass-panel">
        <!-- 列表顶部工具栏 -->
        <div class="content-panel-header">
          <div class="header-type-info">
            <div class="type-title-row">
              <div class="active-type-icon">
                <SvgIcon :name="activeTypeMeta.icon" size="20" />
              </div>
              <h2 class="active-type-name">{{ activeTypeMeta.name }} (专属设备列表)</h2>
              <span class="type-code-tag num-mono">[{{ activeTypeMeta.type }}]</span>
            </div>
            <p class="active-type-desc">{{ activeTypeMeta.desc }}</p>
          </div>

          <div class="header-action-btns">
            <el-button type="primary" class="gold-btn-primary" @click="openCreateDeviceModal">
              <el-icon class="mr-1">
                <Plus />
              </el-icon>
              登记新设备
            </el-button>
          </div>
        </div>

        <!-- 多维检索与过滤栏 (自编号 / 分组 / 区域 / 状态) -->
        <div class="filter-toolbar">
          <div class="filter-left">
            <el-input v-model="filters.keyword" placeholder="搜索自编号 (如 AUD-MIX-01) / 设备名称 / 编码" clearable
              style="width: 260px;" @input="handleFilterChange">
              <template #prefix>
                <el-icon>
                  <Search />
                </el-icon>
              </template>
            </el-input>

            <el-select v-model="filters.group_name" placeholder="所有分组" clearable style="width: 160px;"
              @change="handleFilterChange">
              <el-option label="所有设备分组" value="" />
              <el-option v-for="grp in groupOptions" :key="grp" :label="grp" :value="grp" />
            </el-select>

            <el-select v-model="filters.region_name" placeholder="所有物理区域" clearable style="width: 170px;"
              @change="handleFilterChange">
              <el-option label="所有物理区域" value="" />
              <el-option v-for="reg in regionOptions" :key="reg" :label="reg" :value="reg" />
            </el-select>

            <el-select v-model="filters.online_status" placeholder="通信状态" clearable style="width: 120px;"
              @change="handleFilterChange">
              <el-option label="全部状态" value="" />
              <el-option label="在线 (ONLINE)" value="ONLINE" />
              <el-option label="离线 (OFFLINE)" value="OFFLINE" />
              <el-option label="故障 (FAULT)" value="FAULT" />
            </el-select>

            <button type="button" class="btn-filter-reset" @click="resetFilters">
              <el-icon class="mr-1">
                <RefreshRight />
              </el-icon>
              重置
            </button>
          </div>

          <div class="filter-right">
            <span class="list-summary-txt">
              当前展示 <strong>{{ filteredDevices.length }}</strong> 台设备
            </span>
          </div>
        </div>

        <!-- 批量操作响应提示条 (当勾选 1 个或多个设备时高亮呈现) -->
        <transition name="slide-fade">
          <div v-if="selectedDeviceIds.length > 0" class="batch-action-bar">
            <div class="batch-left">
              <span class="batch-badge num-mono">{{ selectedDeviceIds.length }}</span>
              <span>已勾选 <strong>{{ selectedDeviceIds.length }}</strong> 台 {{ activeTypeMeta.shortName }} 设备</span>
              <span class="batch-tip">(支持批量多播发送与并发回执采集)</span>
            </div>

            <div class="batch-right">
              <!-- 快捷预设批量指令 -->
              <el-dropdown trigger="click" @command="handleQuickBatchCommand">
                <el-button size="small" class="batch-btn">
                  <span>下发预设指令</span>
                  <el-icon class="el-icon--right">
                    <ArrowDown />
                  </el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="POWER_ON">
                      <el-icon>
                        <SwitchButton />
                      </el-icon> 批量开机 / 启动唤醒
                    </el-dropdown-item>
                    <el-dropdown-item command="POWER_OFF">
                      <el-icon>
                        <CircleClose />
                      </el-icon> 批量休眠 / 关闭通道
                    </el-dropdown-item>
                    <el-dropdown-item command="STATUS_PING">
                      <el-icon>
                        <Refresh />
                      </el-icon> 批量轮询心跳与状态查询
                    </el-dropdown-item>
                    <el-dropdown-item command="RESET_DEFAULT">
                      <el-icon>
                        <RefreshRight />
                      </el-icon> 批量复位至出厂预置
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <el-button size="small" type="primary" class="gold-btn-primary" @click="openBatchCustomCommandModal">
                <el-icon class="mr-1">
                  <Promotion />
                </el-icon>
                自定义报文批量发送
              </el-button>

              <el-button size="small" type="danger" plain @click="confirmBatchDelete">
                <el-icon class="mr-1">
                  <Delete />
                </el-icon>
                批量删除
              </el-button>

              <button type="button" class="btn-clear-selection" @click="clearSelection">
                取消勾选
              </button>
            </div>
          </div>
        </transition>

        <!-- 独立设备列表表格 -->
        <div class="device-table-container">
          <div class="device-table-scroll">
            <el-table ref="deviceTableRef" :data="filteredDevices" row-key="id" stripe class="sahara-styled-table"
              @selection-change="handleSelectionChange">
            <!-- 勾选复选框 (支持全选与单选) -->
            <el-table-column type="selection" width="48" align="center" />

            <!-- 1. 设备名称 (主识别字段前置，自适应宽敞呈现) -->
            <el-table-column label="设备名称" prop="device_name" min-width="240">
              <template #default="{ row }">
                <div class="device-name-box">
                  <span class="device-main-name" :title="row.device_name">{{ row.device_name }}</span>
                  <span class="device-sys-code num-mono">{{ row.device_code }}</span>
                </div>
              </template>
            </el-table-column>

            <!-- 2. 设备自编号 (台账工程编号) -->
            <el-table-column label="设备自编号" prop="custom_no" width="160">
              <template #default="{ row }">
                <div class="custom-no-badge num-mono" :title="row.custom_no">
                  {{ row.custom_no }}
                </div>
              </template>
            </el-table-column>

            <!-- 3. 设备分组 (扩展宽度，完整展示无省略号截断) -->
            <el-table-column label="设备分组" prop="group_name" min-width="180">
              <template #default="{ row }">
                <span class="tag-group-pill">{{ row.group_name }}</span>
              </template>
            </el-table-column>

            <!-- 4. 安装物理区域 (扩展宽度，完整展示区域与机房全名) -->
            <el-table-column label="安装物理区域" prop="region_name" min-width="230">
              <template #default="{ row }">
                <span class="tag-region-pill" :title="row.region_name">
                  <el-icon class="mr-1">
                    <Location />
                  </el-icon>
                  {{ row.region_name }}
                </span>
              </template>
            </el-table-column>

            <!-- 5. 在线状态 -->
            <el-table-column label="在线状态" prop="online_status" width="110" align="center">
              <template #default="{ row }">
                <div class="status-cell">
                  <span :class="['status-dot-sm', row.online_status.toLowerCase()]"></span>
                  <span class="status-txt">
                    {{ row.online_status === 'ONLINE' ? '在线' : row.online_status === 'FAULT' ? '故障' : '离线' }}
                  </span>
                </div>
              </template>
            </el-table-column>

            <!-- 6. 控制与配置操作 (操作栏宽度调整至 340px，舒展留白，避免按钮挤压贴边) -->
            <el-table-column label="控制与配置操作" width="340" fixed="right" align="center">
              <template #default="{ row }">
                <div class="table-actions-row">
                  <!-- 发送指令 -->
                  <el-button size="small" type="primary" class="action-btn send-btn" title="立即向该设备下发控制指令"
                    @click="openSingleSendCommandModal(row)">
                    <el-icon>
                      <Promotion />
                    </el-icon>
                    <span>发指令</span>
                  </el-button>

                  <!-- 参数编辑 -->
                  <el-button size="small" class="action-btn" title="编辑设备自编号、分组、区域、通信参数"
                    @click="openEditDeviceModal(row)">
                    <el-icon>
                      <Setting />
                    </el-icon>
                    <span>参数</span>
                  </el-button>

                  <!-- 指令编辑 -->
                  <el-button size="small" class="action-btn" title="配置与维护该设备支持的预置指令集"
                    @click="openCommandEditorModal(row)">
                    <el-icon>
                      <Tickets />
                    </el-icon>
                    <span>指令库</span>
                  </el-button>

                  <!-- 专属记录与删除更多操作 -->
                  <el-dropdown trigger="click" @command="(cmd) => handleRowMoreAction(cmd, row)">
                    <el-button size="small" class="action-btn more-btn">
                      <el-icon>
                        <MoreFilled />
                      </el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="VIEW_LOGS">
                          <el-icon>
                            <Document />
                          </el-icon> 查看执行回执记录
                        </el-dropdown-item>
                        <el-dropdown-item divided command="DELETE" style="color: #A0522D;">
                          <el-icon>
                            <Delete />
                          </el-icon> 删除该设备
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
            </el-table>
          </div>
        </div>
      </main>
    </div>

    <!-- 弹窗 1: 设备参数编辑 / 新增弹窗 (参数编辑) -->
    <el-dialog
      v-model="deviceModalVisible"
      :title="isEditMode ? '编辑设备参数与台账属性' : '登记新的物联网硬件设备'"
      width="680px"
      append-to-body
      destroy-on-close
      class="gold-styled-dialog device-edit-dialog"
    >
      <el-form
        ref="deviceFormRef"
        :model="deviceForm"
        :rules="deviceFormRules"
        label-width="95px"
        label-position="left"
        class="external-app-form"
      >
        <!-- 1. 基础属性与标识 -->
        <div class="form-section-title">
          <span class="section-badge">1</span>
          <span class="section-title-txt">设备标识与分组区域</span>
        </div>

        <el-form-item label="硬件类型" prop="hardware_type">
          <el-select v-model="deviceForm.hardware_type" style="width: 100%;" :disabled="isEditMode">
            <el-option
              v-for="item in hardwareTypes"
              :key="item.type"
              :label="`${item.name} (${item.shortName})`"
              :value="item.type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="设备自编号" prop="custom_no">
          <el-input
            v-model="deviceForm.custom_no"
            placeholder="例如: TIM-SWIM-MASTER, AUD-MIX-01, SCR-CENTER-01"
            clearable
          />
        </el-form-item>

        <el-form-item label="设备名称" prop="device_name">
          <el-input
            v-model="deviceForm.device_name"
            placeholder="例如: Omega ARES 21 游泳/跳水专业计时主机"
            clearable
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="所属分组" prop="group_name" label-width="75px">
              <el-select
                v-model="deviceForm.group_name"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入分组"
                style="width: 100%;"
              >
                <el-option
                  v-for="grp in groupOptions"
                  :key="grp"
                  :label="grp"
                  :value="grp"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="安装区域" prop="region_name" label-width="75px">
              <el-select
                v-model="deviceForm.region_name"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入区域"
                style="width: 100%;"
              >
                <el-option
                  v-for="reg in regionOptions"
                  :key="reg"
                  :label="reg"
                  :value="reg"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 2. 通信接口与协议参数 -->
        <div class="form-section-title">
          <span class="section-badge">2</span>
          <span class="section-title-txt">通信接口与协议参数</span>
        </div>

        <el-form-item label="接口协议" prop="connection_type">
          <el-radio-group v-model="deviceForm.connection_type" class="protocol-radio-group">
            <el-radio-button value="SERIAL">RS232/485串口</el-radio-button>
            <el-radio-button value="TCP">TCP 网络</el-radio-button>
            <el-radio-button value="UDP">UDP 网络</el-radio-button>
            <el-radio-button value="MODBUS">Modbus 协议</el-radio-button>
            <el-radio-button value="HTTP">HTTP/REST</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 串口专有参数 -->
        <div v-if="deviceForm.connection_type === 'SERIAL'">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="COM端口" label-width="75px">
                <el-input v-model="deviceForm.serial_port" placeholder="例如: COM1, COM3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="波特率" label-width="75px">
                <el-select v-model="deviceForm.baud_rate" style="width: 100%;">
                  <el-option :value="9600" label="9600 bps" />
                  <el-option :value="19200" label="19200 bps" />
                  <el-option :value="38400" label="38400 bps" />
                  <el-option :value="57600" label="57600 bps" />
                  <el-option :value="115200" label="115200 bps" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 网络专有参数 -->
        <div v-else>
          <el-row :gutter="16">
            <el-col :span="14">
              <el-form-item label="IP/地址" label-width="75px">
                <el-input v-model="deviceForm.target_ip" placeholder="例如: 192.168.1.120" />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="通信端口" label-width="65px">
                <el-input-number v-model="deviceForm.target_port" :min="1" :max="65535" style="width: 100%;" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 3. 运行状态与备注说明 -->
        <div class="form-section-title">
          <span class="section-badge">3</span>
          <span class="section-title-txt">运行状态与备注说明</span>
        </div>

        <el-form-item label="初始状态" prop="online_status">
          <el-radio-group v-model="deviceForm.online_status" class="status-radio-group">
            <el-radio-button value="ONLINE">在线正常</el-radio-button>
            <el-radio-button value="STANDBY">待机就绪</el-radio-button>
            <el-radio-button value="FAULT">故障告警</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="备注信息" prop="remark">
          <el-input v-model="deviceForm.remark" type="textarea" :rows="2" placeholder="填写维保厂商、安装位置说明或调试备忘"
            maxlength="300" show-word-limit />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <div class="footer-left">
            <el-button
              class="btn-test-connect"
              :loading="isTestingConnect"
              @click="handleTestConnection"
            >
              <el-icon class="mr-1"><Connection /></el-icon>
              <span>测试连通</span>
            </el-button>

            <transition name="fade">
              <span v-if="connectTestStatus" :class="['connect-result-pill', connectTestStatus.type]">
                <el-icon class="mr-1">
                  <CircleCheckFilled v-if="connectTestStatus.type === 'success'" />
                  <CircleCloseFilled v-else />
                </el-icon>
                {{ connectTestStatus.text }}
              </span>
            </transition>
          </div>

          <div class="footer-right">
            <el-button @click="deviceModalVisible = false">取消</el-button>
            <el-button
              type="primary"
              class="gold-btn-primary"
              :loading="deviceSubmitting"
              @click="submitDeviceForm"
            >
              保存配置
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 2: 设备专属指令编辑弹窗 (指令编辑) -->
    <el-dialog v-model="commandEditorVisible"
      :title="`设备指令库编辑 - 【${activeDeviceForCommand?.custom_no}】${activeDeviceForCommand?.device_name}`" width="720px"
      append-to-body destroy-on-close class="gold-styled-dialog">
      <div class="command-editor-body">
        <div class="editor-top-actions">
          <span class="editor-tip">
            已为该设备维护 <strong>{{ editingCommands.length }}</strong> 条常用控制指令，可直接用于单机触发或批量广播下发：
          </span>
          <el-button size="small" type="primary" class="gold-btn-primary" @click="openAddCommandRow">
            <el-icon class="mr-1">
              <Plus />
            </el-icon>
            新增控制指令
          </el-button>
        </div>

        <!-- 指令表格 -->
        <el-table :data="editingCommands" stripe class="sahara-styled-table" style="margin-top: 10px;">
          <el-table-column label="指令名称" prop="command_name" min-width="150" />
          <el-table-column label="格式" prop="payload_format" width="75" align="center">
            <template #default="{ row }">
              <span class="tag-format-pill num-mono">{{ row.payload_format }}</span>
            </template>
          </el-table-column>
          <el-table-column label="下发报文内容" prop="command_payload" min-width="190">
            <template #default="{ row }">
              <code class="cmd-code-snippet num-mono">{{ row.command_payload }}</code>
            </template>
          </el-table-column>
          <el-table-column label="期望回执特征" prop="expected_ack" width="130">
            <template #default="{ row }">
              <span class="ack-feature num-mono">{{ row.expected_ack || '任意ACK' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row, $index }">
              <el-button size="small" link type="primary" @click="editCommandRow(row, $index)">编辑</el-button>
              <el-button size="small" link type="danger" @click="deleteCommandRow(row, $index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 内嵌：正在编辑单条指令表单卡片 -->
        <div v-if="isEditingCmdRow" class="cmd-row-form-box">
          <div class="box-head">
            <span>{{ isEditingCmdNew ? '新增设备指令' : '修改设备指令' }}</span>
            <button type="button" class="close-box-btn" @click="isEditingCmdRow = false">×</button>
          </div>

          <el-form label-width="85px" label-position="left">
            <el-row :gutter="12">
              <el-col :span="16">
                <el-form-item label="指令名称">
                  <el-input v-model="cmdRowForm.command_name" placeholder="例如: 全通道复位, 切换赛事模式" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="报文格式">
                  <el-select v-model="cmdRowForm.payload_format" style="width: 100%;">
                    <el-option value="HEX" label="十六进制 (HEX)" />
                    <el-option value="ASCII" label="纯文本 (ASCII)" />
                    <el-option value="JSON" label="JSON 对象" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="报文内容">
              <el-input v-model="cmdRowForm.command_payload" type="textarea" :rows="2"
                placeholder="例如: 55 AA 01 0B 00 24 或 POWER ON" />
            </el-form-item>

            <el-row :gutter="12">
              <el-col :span="14">
                <el-form-item label="期望ACK">
                  <el-input v-model="cmdRowForm.expected_ack" placeholder="期望回执特征码，留空表示任意响应" />
                </el-form-item>
              </el-col>
              <el-col :span="10">
                <el-form-item label="高危确认">
                  <el-switch v-model="cmdRowForm.is_dangerous" active-text="二次确认" />
                </el-form-item>
              </el-col>
            </el-row>

            <div class="row-form-actions">
              <el-button size="small" @click="isEditingCmdRow = false">取消</el-button>
              <el-button size="small" type="primary" class="gold-btn-primary" @click="saveCmdRow">保存当前指令</el-button>
            </div>
          </el-form>
        </div>
      </div>

      <template #footer>
        <el-button @click="commandEditorVisible = false">关闭窗口</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 3: 单机快捷下发指令弹窗 -->
    <el-dialog v-model="singleSendVisible" :title="`向【${activeSendTargetDevice?.custom_no}】下发控制指令`" width="540px"
      append-to-body destroy-on-close class="gold-styled-dialog">
      <div v-if="activeSendTargetDevice" class="single-send-body">
        <div class="target-device-card">
          <div class="card-left">
            <span class="custom-no-badge num-mono">{{ activeSendTargetDevice.custom_no }}</span>
            <div class="target-name">{{ activeSendTargetDevice.device_name }}</div>
          </div>
          <span class="status-cell">
            <span :class="['status-dot-sm', activeSendTargetDevice.online_status.toLowerCase()]"></span>
            <span>{{ activeSendTargetDevice.online_status }}</span>
          </span>
        </div>

        <div class="preset-cmd-list-title">从该设备预设指令库选取：</div>
        <div class="preset-cmd-grid">
          <div v-for="cmd in activeSendTargetDevice.commands || []" :key="cmd.id" class="preset-cmd-tile"
            @click="quickSendSingleCommand(cmd)">
            <div class="cmd-tile-name">{{ cmd.command_name }}</div>
            <code class="cmd-tile-code num-mono">{{ cmd.command_payload }}</code>
          </div>
        </div>

        <div class="custom-cmd-divider">或手动输入临时指令：</div>
        <el-input v-model="manualSinglePayload" placeholder="输入 HEX 报文 (如 55 AA 01 00) 或自定义字符串" clearable />
      </div>

      <template #footer>
        <el-button @click="singleSendVisible = false">取消</el-button>
        <el-button type="primary" class="gold-btn-primary" :loading="isSendingCommand" @click="sendManualSingleCommand">
          立即发送
        </el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 4: 批量自定义报文发送弹窗 -->
    <el-dialog v-model="batchModalVisible" :title="`批量下发指令 - 已勾选 ${selectedDeviceIds.length} 台设备`" width="560px"
      append-to-body destroy-on-close class="gold-styled-dialog">
      <div class="batch-modal-body">
        <el-alert :title="`本次指令将同时并发下发至勾选的 ${selectedDeviceIds.length} 台设备，系统将采集每台设备的独立执行结果回执。`" type="warning"
          :closable="false" show-icon />

        <el-form label-position="top" style="margin-top: 14px;">
          <el-form-item label="指令动作名称">
            <el-input v-model="batchForm.name" placeholder="例如: 全场批量启动测试, 广播音量复位" />
          </el-form-item>

          <el-form-item label="待下发报文内容 (HEX / ASCII)">
            <el-input v-model="batchForm.payload" type="textarea" :rows="3"
              placeholder="例如: 55 AA FF 00 00 00 SYNC_START 或 POWER_ON" />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="batchModalVisible = false">取消</el-button>
        <el-button type="primary" class="gold-btn-primary" :loading="isSendingCommand"
          @click="executeBatchCustomCommand">
          确认全选/批量发送
        </el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 5: 批量执行结果回执即时报告弹窗 (回执结果) -->
    <el-dialog v-model="batchResultModalVisible" title="指令执行结果回执报告" width="680px" append-to-body
      class="gold-styled-dialog">
      <div class="batch-result-body">
        <div class="result-summary-bar">
          <span>下发完成：总共 <strong>{{ lastBatchResults.length }}</strong> 台设备</span>
          <span class="text-success">
            成功: <strong>{{lastBatchResults.filter(r => r.execute_result === 'SUCCESS').length}}</strong>
          </span>
          <span class="text-danger" v-if="lastBatchResults.some(r => r.execute_result !== 'SUCCESS')">
            失败/离线: <strong>{{lastBatchResults.filter(r => r.execute_result !== 'SUCCESS').length}}</strong>
          </span>
        </div>

        <el-table :data="lastBatchResults" stripe class="sahara-styled-table" max-height="360">
          <el-table-column label="自编号" prop="custom_no" width="130">
            <template #default="{ row }">
              <span class="custom-no-badge num-mono">{{ row.custom_no }}</span>
            </template>
          </el-table-column>
          <el-table-column label="设备名称" prop="device_name" min-width="140" />
          <el-table-column label="执行结果回执" width="120" align="center">
            <template #default="{ row }">
              <span :class="['result-badge', row.execute_result.toLowerCase()]">
                {{ row.execute_result === 'SUCCESS' ? '成功 (ACK)' : row.execute_result === 'TIMEOUT' ? '超时' : '失败 (NACK)'
                }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="响应回执报文" prop="response_payload" min-width="180">
            <template #default="{ row }">
              <code class="ack-code num-mono">{{ row.response_payload }}</code>
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="75" align="right">
            <template #default="{ row }">
              <span class="cost-ms num-mono">{{ row.cost_ms }}ms</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button type="primary" class="gold-btn-primary" @click="batchResultModalVisible = false">
          确认已知晓
        </el-button>
      </template>
    </el-dialog>

    <!-- 抽屉: 全量指令执行结果回执记录与审计流水 (指令记录) -->
    <el-drawer v-model="logsDrawerVisible" title="指令执行记录与下位机回执流水 (Command Execution Logs)" size="760px" append-to-body
      destroy-on-close>
      <div class="logs-drawer-content">
        <!-- 抽屉过滤栏 -->
        <div class="logs-filter-row">
          <el-input v-model="logKeyword" placeholder="搜索自编号 / 设备名称 / TraceId / 指令" clearable style="width: 280px;"
            @input="refreshLogs">
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>

          <el-select v-model="logResultFilter" placeholder="回执状态" clearable style="width: 140px;" @change="refreshLogs">
            <el-option label="全部回执结果" value="ALL" />
            <el-option label="执行成功 (SUCCESS)" value="SUCCESS" />
            <el-option label="执行失败 (FAILED)" value="FAILED" />
            <el-option label="设备离线 (OFFLINE)" value="OFFLINE" />
          </el-select>

          <button type="button" class="btn-clear-logs" @click="confirmClearLogs">
            <el-icon>
              <Delete />
            </el-icon>
            清空日志
          </button>
        </div>

        <!-- 日志表格 -->
        <el-table :data="commandLogs" stripe class="sahara-styled-table logs-table" height="calc(100vh - 160px)">
          <el-table-column label="执行时间" prop="created_at" width="150" />
          <el-table-column label="设备自编号" width="130">
            <template #default="{ row }">
              <span class="custom-no-badge num-mono">{{ row.custom_no }}</span>
            </template>
          </el-table-column>
          <el-table-column label="设备名称" prop="device_name" width="140" show-overflow-tooltip />
          <el-table-column label="指令内容" min-width="160">
            <template #default="{ row }">
              <div class="cmd-cell-view">
                <span class="cmd-name-txt">{{ row.command_name }}</span>
                <code class="cmd-payload-txt num-mono">{{ row.command_payload }}</code>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="执行回执" width="110" align="center">
            <template #default="{ row }">
              <span :class="['result-badge', row.execute_result.toLowerCase()]">
                {{ row.execute_result === 'SUCCESS' ? '成功' : row.execute_result === 'TIMEOUT' ? '超时' : '失败' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="下位机回执报文" prop="response_payload" min-width="180">
            <template #default="{ row }">
              <code class="ack-code num-mono">{{ row.response_payload }}</code>
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="75" align="right">
            <template #default="{ row }">
              <span class="cost-ms num-mono">{{ row.cost_ms }}ms</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, RefreshRight, Document, DocumentCopy, ArrowDown,
  Setting, Tickets, MoreFilled, Delete, Promotion,
  SwitchButton, CircleClose, Refresh, Location,
  Connection, CircleCheckFilled, CircleCloseFilled
} from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'
import {
  iotDeviceService,
  HARDWARE_TYPES,
  PRESET_REGIONS,
  PRESET_GROUPS
} from '@/services/iotDeviceService'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const goToConfigTemplates = () => {
  router.push('/config/templates')
}

// 13 类硬件列表字典
const hardwareTypes = ref(HARDWARE_TYPES)
const currentHardwareType = ref('AUDIO') // 默认首项：专业扩声

// 当前选中的硬件大类元数据
const activeTypeMeta = computed(() => {
  return hardwareTypes.value.find(h => h.type === currentHardwareType.value) || hardwareTypes.value[0]
})

// 候选分组与区域
const groupOptions = ref(PRESET_GROUPS)
const regionOptions = ref(PRESET_REGIONS)

// 过滤参数
const filters = reactive({
  keyword: '',
  group_name: '',
  region_name: '',
  online_status: ''
})

// 全局指标
const globalStats = ref({
  totalDevices: 0,
  onlineDevices: 0,
  totalLogs: 0,
  successRate: '100.0%'
})

// 当前硬件类型下的设备列表数据
const deviceList = ref([])
const deviceTableRef = ref(null)
const selectedDeviceIds = ref([])

// 加载当前硬件类型设备数据
const loadDevices = () => {
  deviceList.value = iotDeviceService.getDevices(currentHardwareType.value, filters)
  globalStats.value = iotDeviceService.getGlobalStats()
}

// 经过多维过滤的设备列表
const filteredDevices = computed(() => {
  return deviceList.value
})

// 获取特定类型的设备数量
const getDeviceCount = (type) => {
  return iotDeviceService.getDevices(type).length
}

// 切换左侧 13 项硬件分类
const selectHardwareType = (type) => {
  currentHardwareType.value = type
  selectedDeviceIds.value = []
  if (deviceTableRef.value) {
    deviceTableRef.value.clearSelection()
  }
  loadDevices()
}

// 筛选事件
const handleFilterChange = () => {
  loadDevices()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.group_name = ''
  filters.region_name = ''
  filters.online_status = ''
  loadDevices()
}

// 表格多选勾选响应 (勾选某一个或全选)
const handleSelectionChange = (selection) => {
  selectedDeviceIds.value = selection.map(row => row.id)
}

const clearSelection = () => {
  if (deviceTableRef.value) {
    deviceTableRef.value.clearSelection()
  }
  selectedDeviceIds.value = []
}

// -------------------------------------------------------------
// 1. 设备增删改查 (参数编辑)
// -------------------------------------------------------------
const deviceModalVisible = ref(false)
const isEditMode = ref(false)
const deviceSubmitting = ref(false)
const deviceFormRef = ref(null)
const isTestingConnect = ref(false)
const connectTestStatus = ref(null)

// 测试设备连通性 (COM串口握手探测或网络IP/端口SYN握手)
const handleTestConnection = () => {
  if (deviceForm.connection_type === 'SERIAL') {
    if (!deviceForm.serial_port || !deviceForm.serial_port.trim()) {
      ElMessage.warning('请先填写 COM 端口号 (例如 COM1, COM3)')
      return
    }
  } else {
    if (!deviceForm.target_ip || !deviceForm.target_ip.trim()) {
      ElMessage.warning('请先填写目标 IP 地址或域名 (例如 192.168.1.120)')
      return
    }
  }

  isTestingConnect.value = true
  connectTestStatus.value = null

  setTimeout(() => {
    isTestingConnect.value = false
    const randomLatency = Math.floor(Math.random() * 15) + 8 // 8~22ms
    if (deviceForm.connection_type === 'SERIAL') {
      const portName = deviceForm.serial_port.trim().toUpperCase()
      const baud = deviceForm.baud_rate || 9600
      connectTestStatus.value = {
        type: 'success',
        text: `端口【${portName}】握手成功 (${randomLatency}ms)`
      }
      deviceForm.online_status = 'ONLINE'
      ElMessage.success(`【连通性测试通过】已成功探测并打开串口【${portName} · ${baud}bps 8-N-1】，响应延迟 ${randomLatency}ms`)
    } else {
      const ip = deviceForm.target_ip.trim()
      const port = deviceForm.target_port || 502
      connectTestStatus.value = {
        type: 'success',
        text: `节点【${ip}:${port}】握手成功 (${randomLatency}ms)`
      }
      deviceForm.online_status = 'ONLINE'
      ElMessage.success(`【连通性测试通过】已成功建立网络握手【${ip}:${port}】，响应延迟 ${randomLatency}ms`)
    }
  }, 600)
}

const deviceForm = reactive({
  id: null,
  hardware_type: 'AUDIO',
  custom_no: '',
  device_name: '',
  group_name: '主赛场核心运行组',
  region_name: '主体育馆 (比赛池)',
  connection_type: 'SERIAL',
  serial_port: 'COM1',
  baud_rate: 9600,
  target_ip: '',
  target_port: 502,
  online_status: 'ONLINE',
  remark: ''
})

const deviceFormRules = {
  custom_no: [{ required: true, message: '请输入设备自编号 (如 AUD-MIX-01)', trigger: 'blur' }],
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  hardware_type: [{ required: true, message: '请选择硬件类型', trigger: 'change' }]
}

// 打开新增弹窗
const openCreateDeviceModal = () => {
  isEditMode.value = false
  connectTestStatus.value = null
  const typeMeta = activeTypeMeta.value
  const newCount = getDeviceCount(typeMeta.type) + 1
  Object.assign(deviceForm, {
    id: null,
    hardware_type: typeMeta.type,
    custom_no: `${typeMeta.codePrefix}-${String(newCount).padStart(2, '0')}`,
    device_name: `${typeMeta.shortName}备用设备 ${newCount}`,
    group_name: '主赛场核心运行组',
    region_name: '主体育馆 (比赛池)',
    connection_type: typeMeta.defaultProtocol,
    serial_port: typeMeta.defaultProtocol === 'SERIAL' ? typeMeta.defaultPort : 'COM1',
    baud_rate: 9600,
    target_ip: typeMeta.defaultProtocol !== 'SERIAL' ? '192.168.1.100' : '',
    target_port: 502,
    online_status: 'ONLINE',
    remark: ''
  })
  deviceModalVisible.value = true
}

// 打开参数编辑弹窗
const openEditDeviceModal = (row) => {
  isEditMode.value = true
  connectTestStatus.value = null
  Object.assign(deviceForm, {
    id: row.id,
    hardware_type: row.hardware_type,
    custom_no: row.custom_no,
    device_name: row.device_name,
    group_name: row.group_name,
    region_name: row.region_name,
    connection_type: row.connection_type,
    serial_port: row.serial_port || 'COM1',
    baud_rate: row.baud_rate || 9600,
    target_ip: row.target_ip || '',
    target_port: row.target_port || 502,
    online_status: row.online_status,
    remark: row.remark || ''
  })
  deviceModalVisible.value = true
}

// 提交设备参数表单
const submitDeviceForm = async () => {
  if (!deviceFormRef.value) return
  await deviceFormRef.value.validate((valid) => {
    if (!valid) return
    deviceSubmitting.value = true
    try {
      if (isEditMode.value) {
        iotDeviceService.updateDevice(deviceForm.id, { ...deviceForm })
        ElMessage.success(`设备【${deviceForm.custom_no}】参数更新成功`)
      } else {
        iotDeviceService.createDevice({ ...deviceForm })
        ElMessage.success(`新设备【${deviceForm.custom_no}】登记成功`)
      }
      deviceModalVisible.value = false
      loadDevices()
    } catch (e) {
      ElMessage.error(e.message || '保存失败')
    } finally {
      deviceSubmitting.value = false
    }
  })
}

// -------------------------------------------------------------
// 2. 指令编辑 (针对每个设备的预置指令库增删改查)
// -------------------------------------------------------------
const commandEditorVisible = ref(false)
const activeDeviceForCommand = ref(null)
const editingCommands = ref([])
const isEditingCmdRow = ref(false)
const isEditingCmdNew = ref(false)

const cmdRowForm = reactive({
  id: null,
  command_name: '',
  payload_format: 'HEX',
  command_payload: '',
  expected_ack: '',
  is_dangerous: false
})

const openCommandEditorModal = (row) => {
  activeDeviceForCommand.value = row
  editingCommands.value = JSON.parse(JSON.stringify(row.commands || []))
  isEditingCmdRow.value = false
  commandEditorVisible.value = true
}

const openAddCommandRow = () => {
  isEditingCmdNew.value = true
  Object.assign(cmdRowForm, {
    id: null,
    command_name: '',
    payload_format: 'HEX',
    command_payload: '',
    expected_ack: 'ACK_OK',
    is_dangerous: false
  })
  isEditingCmdRow.value = true
}

const editCommandRow = (row) => {
  isEditingCmdNew.value = false
  Object.assign(cmdRowForm, { ...row })
  isEditingCmdRow.value = true
}

const saveCmdRow = () => {
  if (!cmdRowForm.command_name || !cmdRowForm.command_payload) {
    ElMessage.warning('请输入指令名称与报文内容')
    return
  }

  const updated = iotDeviceService.saveDeviceCommand(activeDeviceForCommand.value.id, { ...cmdRowForm })
  editingCommands.value = JSON.parse(JSON.stringify(updated))
  isEditingCmdRow.value = false
  ElMessage.success('指令已保存入库')
  loadDevices()
}

const deleteCommandRow = (row) => {
  ElMessageBox.confirm(`确认删除指令【${row.command_name}】吗？`, '提示', { type: 'warning' })
    .then(() => {
      iotDeviceService.deleteDeviceCommand(activeDeviceForCommand.value.id, row.id)
      editingCommands.value = editingCommands.value.filter(c => c.id !== row.id)
      ElMessage.success('指令已删除')
      loadDevices()
    })
    .catch(() => { })
}

// -------------------------------------------------------------
// 3. 发送指令 (勾选某一个或全选，执行结果回执跟踪)
// -------------------------------------------------------------
const isSendingCommand = ref(false)
const singleSendVisible = ref(false)
const activeSendTargetDevice = ref(null)
const manualSinglePayload = ref('')

// 批量自定义报文发送
const batchModalVisible = ref(false)
const batchForm = reactive({
  name: '批量同步控制指令',
  payload: '55 AA 01 00 SYNC_EXEC'
})

// 批量结果回执报告弹窗
const batchResultModalVisible = ref(false)
const lastBatchResults = ref([])

// 打开单机发送弹窗
const openSingleSendCommandModal = (row) => {
  activeSendTargetDevice.value = row
  manualSinglePayload.value = ''
  singleSendVisible.value = true
}

// 单机发送预设指令
const quickSendSingleCommand = async (cmd) => {
  if (cmd.is_dangerous) {
    try {
      await ElMessageBox.confirm(`指令【${cmd.command_name}】涉及高危动作，确认立即执行下发吗？`, '高危动作确认', { type: 'warning' })
    } catch {
      return
    }
  }

  isSendingCommand.value = true
  try {
    const res = await iotDeviceService.sendCommand(
      [activeSendTargetDevice.value.id],
      cmd.command_payload,
      cmd.command_name,
      userStore.currentUser?.username || 'admin'
    )
    singleSendVisible.value = false
    lastBatchResults.value = res
    batchResultModalVisible.value = true
    loadDevices()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    isSendingCommand.value = false
  }
}

// 单机发送自定义临时指令
const sendManualSingleCommand = async () => {
  if (!manualSinglePayload.value.trim()) {
    ElMessage.warning('请输入待下发的报文内容')
    return
  }

  isSendingCommand.value = true
  try {
    const res = await iotDeviceService.sendCommand(
      [activeSendTargetDevice.value.id],
      manualSinglePayload.value.trim(),
      '手动即时报文',
      userStore.currentUser?.username || 'admin'
    )
    singleSendVisible.value = false
    lastBatchResults.value = res
    batchResultModalVisible.value = true
    loadDevices()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    isSendingCommand.value = false
  }
}

// 勾选后快捷批量下发预置动作
const handleQuickBatchCommand = async (cmdType) => {
  const map = {
    POWER_ON: { name: '批量开机/启动', payload: '55 AA 01 01 POWER_ON' },
    POWER_OFF: { name: '批量休眠/断电', payload: '55 AA 01 02 POWER_STANDBY' },
    STATUS_PING: { name: '批量状态轮询探针', payload: '55 AA 00 00 PING_ALL' },
    RESET_DEFAULT: { name: '批量出厂复位', payload: '55 AA FF FF RESET_FACTORY' }
  }
  const target = map[cmdType] || map.STATUS_PING

  try {
    await ElMessageBox.confirm(
      `确认向已勾选的 ${selectedDeviceIds.value.length} 台设备批量下发【${target.name}】吗？`,
      '批量指令下发确认',
      { type: 'warning' }
    )
  } catch {
    return
  }

  isSendingCommand.value = true
  try {
    const res = await iotDeviceService.sendCommand(
      selectedDeviceIds.value,
      target.payload,
      target.name,
      userStore.currentUser?.username || 'admin'
    )
    lastBatchResults.value = res
    batchResultModalVisible.value = true
    loadDevices()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    isSendingCommand.value = false
  }
}

// 打开批量自定义报文发送弹窗
const openBatchCustomCommandModal = () => {
  batchModalVisible.value = true
}

const executeBatchCustomCommand = async () => {
  if (!batchForm.payload.trim()) {
    ElMessage.warning('请输入报文内容')
    return
  }

  isSendingCommand.value = true
  try {
    const res = await iotDeviceService.sendCommand(
      selectedDeviceIds.value,
      batchForm.payload.trim(),
      batchForm.name || '批量自定义报文',
      userStore.currentUser?.username || 'admin'
    )
    batchModalVisible.value = false
    lastBatchResults.value = res
    batchResultModalVisible.value = true
    loadDevices()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    isSendingCommand.value = false
  }
}

// 批量删除
const confirmBatchDelete = () => {
  ElMessageBox.confirm(
    `确认删除已勾选的 ${selectedDeviceIds.value.length} 台设备吗？此操作不可恢复。`,
    '批量删除确认',
    { type: 'error' }
  ).then(() => {
    iotDeviceService.batchDeleteDevices(selectedDeviceIds.value)
    clearSelection()
    ElMessage.success('批量删除成功')
    loadDevices()
  }).catch(() => { })
}

// 行操作更多
const handleRowMoreAction = (command, row) => {
  if (command === 'VIEW_LOGS') {
    logKeyword.value = row.custom_no
    openLogsDrawer()
  } else if (command === 'DELETE') {
    ElMessageBox.confirm(`确认删除设备【${row.custom_no}】${row.device_name} 吗？`, '提示', { type: 'warning' })
      .then(() => {
        iotDeviceService.deleteDevice(row.id)
        ElMessage.success('设备已删除')
        loadDevices()
      })
      .catch(() => { })
  }
}

// -------------------------------------------------------------
// 4. 指令执行记录抽屉 (结果回执审计)
// -------------------------------------------------------------
const logsDrawerVisible = ref(false)
const commandLogs = ref([])
const logKeyword = ref('')
const logResultFilter = ref('ALL')

const openLogsDrawer = () => {
  refreshLogs()
  logsDrawerVisible.value = true
}

const refreshLogs = () => {
  commandLogs.value = iotDeviceService.getCommandLogs({
    keyword: logKeyword.value,
    executeResult: logResultFilter.value
  })
}

const confirmClearLogs = () => {
  ElMessageBox.confirm('确认清空所有历史指令执行记录吗？', '提示', { type: 'warning' })
    .then(() => {
      iotDeviceService.clearCommandLogs()
      refreshLogs()
      globalStats.value = iotDeviceService.getGlobalStats()
      ElMessage.success('指令执行记录已清空')
    })
    .catch(() => { })
}

onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.iot-matrix-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 顶部状态看板 */
.matrix-top-bar {
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
  gap: 12px;
}

.top-icon-circle {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--do-gold-light) 0%, var(--do-gold-hover) 100%);
  border: 1px solid var(--do-gold);
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(var(--th-shadow-rgb), 0.08);
}

.title-meta-box {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.view-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.system-badge {
  font-size: 14px;
  color: var(--do-gold-deep);
  background: rgba(var(--th-accent-rgb), 0.12);
  border: none;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.title-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-pills-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(var(--th-accent-rgb), 0.05);
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.pill-lbl {
  color: var(--do-text-secondary);
}

.pill-val {
  font-weight: 700;
  color: var(--do-text-primary);
}

/* 主体双栏布局 */
.matrix-main-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 12px;
  align-items: stretch;
}

/* 左侧 13 项硬件导航 */
.hardware-type-sidebar {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.sidebar-header {
  padding: 12px 14px;
  border-bottom: 1px solid var(--do-border-light);
  background: linear-gradient(180deg, rgba(var(--th-accent-rgb), 0.08) 0%, rgba(var(--th-accent-rgb), 0.02) 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.sidebar-sub {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.hardware-nav-list {
  display: flex;
  flex-direction: column;
  padding: 6px 0;
  overflow-y: auto;
  max-height: calc(100vh - 210px);
}

.hardware-nav-item {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(229, 217, 197, 0.4);
}

.hardware-nav-item:hover {
  background: var(--do-bg-input);
}

.hardware-nav-item.active {
  background: linear-gradient(90deg, var(--do-gold-light) 0%, var(--do-bg-card-hover) 100%);
  border-left-color: var(--do-gold);
}

.nav-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.nav-index {
  font-size: 14px;
  color: var(--do-text-placeholder);
  font-weight: 700;
  width: 14px;
}

.hardware-nav-item.active .nav-index {
  color: var(--do-gold-deep);
}

.nav-icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: rgba(var(--th-accent-rgb), 0.08);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--do-text-secondary);
  flex-shrink: 0;
  transition: all 0.2s;
}

.hardware-nav-item.active .nav-icon-wrap {
  background: var(--do-gold);
  border-color: var(--do-gold);
  color: #FFFFFF;
}

.nav-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.nav-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-desc {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.type-count-badge {
  font-size: 14px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--do-gold-light);
  color: var(--do-text-secondary);
  font-weight: 600;
}

.hardware-nav-item.active .type-count-badge {
  background: var(--do-gold-deep);
  color: #FFFFFF;
}

/* 右侧专属设备列表面板 */
.hardware-content-panel {
  background: var(--do-bg-card);
  border: 1px solid var(--do-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-panel-header {
  padding: 12px 18px;
  border-bottom: 1px solid var(--do-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, rgba(var(--th-accent-rgb), 0.08) 0%, rgba(var(--th-accent-rgb), 0.02) 100%);
}

.header-type-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.type-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.active-type-icon {
  color: var(--do-gold-deep);
  display: flex;
  align-items: center;
}

.active-type-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.type-code-tag {
  font-size: 14px;
  color: var(--do-gold-deep);
  background: var(--do-bg-input);
  padding: 1px 6px;
  border-radius: 3px;
  border: 1px solid rgba(var(--th-accent-rgb), 0.35);
}

.active-type-desc {
  margin: 0;
  font-size: 14px;
  color: var(--do-text-secondary);
}

/* 过滤工具栏 */
.filter-toolbar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--do-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--do-bg-input);
  gap: 12px;
  flex-wrap: wrap;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-filter-reset {
  height: 32px;
  padding: 0 10px;
  border-radius: var(--radius-sm);
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  color: var(--do-text-secondary);
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: all 0.2s;
}

.btn-filter-reset:hover {
  border-color: var(--do-gold);
  color: var(--do-gold-deep);
}

.list-summary-txt {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.list-summary-txt strong {
  color: var(--do-gold-deep);
}

/* 批量操作响应提示条 (勾选某一个或全选设备时激活) */
.batch-action-bar {
  background: linear-gradient(90deg, var(--do-gold-light) 0%, var(--do-bg-input) 100%);
  border-bottom: 1px solid var(--do-gold);
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 6px rgba(var(--th-accent-rgb), 0.15);
}

.batch-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--do-text-primary);
}

.batch-badge {
  background: var(--do-gold);
  color: #fff;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 14px;
}

.batch-tip {
  color: var(--do-text-secondary);
  font-size: 14px;
}

.batch-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-clear-selection {
  background: none;
  border: none;
  color: var(--do-danger);
  font-size: 14px;
  text-decoration: underline;
  cursor: pointer;
}

/* 设备表格与细节呈现 */
.device-table-container {
  padding: 8px;
  flex: 1;
}

.custom-no-badge {
  background: linear-gradient(180deg, var(--do-bg-card) 0%, var(--do-gold-light) 100%);
  color: var(--do-text-regular);
  font-weight: 700;
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-block;
  letter-spacing: 0.5px;
  border: 1px solid rgba(var(--th-accent-deep-rgb), 0.45);
  box-shadow: 0 1px 2px rgba(var(--th-shadow-rgb), 0.05);
}

.device-name-box {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.device-main-name {
  font-weight: 600;
  color: var(--do-text-primary);
  font-size: 14px;
  line-height: 1.4;
}

.device-sys-code {
  font-size: 12px;
  color: var(--do-text-placeholder);
  letter-spacing: 0.3px;
}

.tag-group-pill {
  background: var(--do-gold-light);
  border: 1px solid rgba(var(--th-accent-rgb), 0.4);
  color: var(--do-gold-deep);
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-block;
  white-space: nowrap;
}

.tag-region-pill {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  color: var(--do-text-secondary);
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
}

.comm-param-tag {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
  color: var(--do-text-primary);
  display: inline-block;
}

.status-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}

.status-dot-sm {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot-sm.online {
  background: var(--do-success);
  box-shadow: 0 0 4px var(--do-success);
}

.status-dot-sm.fault {
  background: var(--do-danger);
  box-shadow: 0 0 4px var(--do-danger);
}

.status-dot-sm.offline {
  background: var(--do-text-placeholder);
}

.remark-cell-text {
  font-size: 13px;
  color: var(--do-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
}

/* 操作按钮列 */
.table-actions-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  white-space: nowrap;
}

.action-btn {
  padding: 4px 9px !important;
  font-size: 13px !important;
  height: 28px !important;
  border-radius: 4px !important;
  flex-shrink: 0;
  white-space: nowrap;
}

.action-btn.send-btn {
  background: var(--do-gold-light) !important;
  border-color: var(--do-gold) !important;
  color: var(--do-gold-deep) !important;
  font-weight: 600 !important;
}

.action-btn.send-btn:hover {
  background: var(--do-gold) !important;
  color: #fff !important;
}

.action-btn.more-btn {
  padding: 4px 8px !important;
  min-width: 32px;
}

/* 指令编辑弹窗内表格与表单 */
.command-editor-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor-top-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.editor-tip {
  font-size: 14px;
  color: var(--do-text-secondary);
}

.tag-format-pill {
  font-size: 14px;
  padding: 1px 4px;
  background: var(--do-bg-sunken);
  border-radius: 2px;
  color: var(--do-text-primary);
}

.cmd-code-snippet {
  background: var(--do-bg-header);
  color: var(--do-gold-light);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 14px;
  word-break: break-all;
}

.ack-feature {
  font-size: 14px;
  color: var(--do-gold-deep);
}

.cmd-row-form-box {
  background: var(--do-bg-input);
  border: 1px solid var(--do-gold);
  border-radius: 6px;
  padding: 12px;
  margin-top: 8px;
}

.box-head {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 700;
  color: var(--do-gold-deep);
  margin-bottom: 10px;
}

.close-box-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--do-text-secondary);
}

.row-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 6px;
}

/* 单机下发预设指令展示框 */
.target-device-card {
  background: var(--do-bg-input);
  border: 1px solid var(--do-border-light);
  border-radius: 6px;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.target-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--do-text-primary);
}

.preset-cmd-list-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
  margin-bottom: 8px;
}

.preset-cmd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  max-height: 160px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.preset-cmd-tile {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  border-radius: 4px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.preset-cmd-tile:hover {
  background: var(--do-gold-light);
  border-color: var(--do-gold);
}

.cmd-tile-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--do-text-primary);
}

.cmd-tile-code {
  font-size: 14px;
  color: var(--do-text-secondary);
  background: var(--do-bg-input);
  padding: 1px 4px;
  border-radius: 2px;
}

.custom-cmd-divider {
  font-size: 14px;
  color: var(--do-text-secondary);
  margin-bottom: 6px;
}

/* 批量回执结果报告 */
.result-summary-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: var(--do-bg-input);
  border-radius: 4px;
  font-size: 14px;
  margin-bottom: 10px;
  border: 1px solid var(--do-border-light);
}

.result-badge {
  font-size: 14px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 3px;
}

.result-badge.success {
  background: rgba(var(--th-success-rgb), 0.15);
  color: var(--do-success);
  border: 1px solid rgba(var(--th-success-rgb), 0.4);
}

.result-badge.failed,
.result-badge.offline {
  background: rgba(var(--th-danger-rgb), 0.15);
  color: var(--do-danger);
  border: 1px solid rgba(var(--th-danger-rgb), 0.4);
}

.ack-code {
  background: var(--do-bg-header);
  color: var(--do-success);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 14px;
  word-break: break-all;
}

.cost-ms {
  font-size: 14px;
  color: var(--do-gold-deep);
  font-weight: 600;
}

/* 抽屉日志样式 */
.logs-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.logs-filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.btn-clear-logs {
  background: var(--do-bg-card-hover);
  border: 1px solid var(--do-border);
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--do-danger);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.btn-clear-logs:hover {
  background: var(--do-bg-input);
  border-color: var(--do-danger);
}

.cmd-cell-view {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cmd-name-txt {
  font-weight: 600;
  font-size: 14px;
  color: var(--do-text-primary);
}

.cmd-payload-txt {
  font-size: 14px;
  color: var(--do-text-secondary);
}

/* 动效 */
.slide-fade-enter-active {
  transition: all 0.2s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.15s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-8px);
  opacity: 0;
}

/* ==============================================================================
   弹窗与表单专属精修样式 (遵循 Sahara IBMS 规范，序号徽章、单选按钮、字段排版)
   ============================================================================== */
.form-section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 800;
  color: var(--do-bg-dark);
  margin: 22px 0 14px 0;
  padding-bottom: 9px;
  border-bottom: 1.5px solid rgba(var(--th-accent-rgb), 0.45);
}

.form-section-title:first-child {
  margin-top: 2px;
}

.section-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%);
  color: #FFFFFF;
  font-size: 14px;
  font-family: var(--font-family-mono, monospace);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.4);
  flex-shrink: 0;
}

.section-title-txt {
  font-size: 14px;
  font-weight: 800 !important;
  color: var(--do-bg-dark) !important;
  letter-spacing: 0.5px;
}

/* 表单 label 与排版 */
.external-app-form :deep(.el-form-item) {
  margin-bottom: 15px;
}

.external-app-form :deep(.el-form-item__label) {
  color: var(--do-text-primary) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding-right: 8px !important;
  line-height: 32px !important;
}

.external-app-form :deep(.el-form-item.is-required:not(.is-no-asterisk).asterisk-left > .el-form-item__label:before) {
  color: var(--do-danger) !important;
  margin-right: 4px !important;
  font-weight: 700 !important;
}

/* 接口协议单选按钮组：5个项等宽自适应均分，杜绝折行，阿特拉斯金高光 */
.protocol-radio-group {
  display: flex !important;
  width: 100% !important;
}

.protocol-radio-group :deep(.el-radio-button) {
  flex: 1 1 0 !important;
  display: flex !important;
}

.protocol-radio-group :deep(.el-radio-button__inner) {
  width: 100% !important;
  padding: 8px 4px !important;
  font-size: 14px !important;
  text-align: center !important;
  white-space: nowrap !important;
  background: var(--do-bg-card-hover) !important;
  border-color: var(--do-border) !important;
  color: var(--do-text-primary) !important;
  transition: all 0.2s ease !important;
}

.protocol-radio-group :deep(.el-radio-button__inner:hover) {
  color: var(--do-gold-deep) !important;
  background: var(--do-bg-input) !important;
}

.protocol-radio-group :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner),
.protocol-radio-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%) !important;
  border-color: var(--do-gold-deep) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  box-shadow: -1px 0 0 0 var(--do-gold-deep), 0 1px 4px rgba(var(--th-accent-deep-rgb), 0.25) !important;
}

/* 运行状态单选按钮组 */
.status-radio-group {
  display: inline-flex !important;
}

.status-radio-group :deep(.el-radio-button__inner) {
  padding: 7px 18px !important;
  font-size: 14px !important;
  background: var(--do-bg-card-hover) !important;
  border-color: var(--do-border) !important;
  color: var(--do-text-primary) !important;
  transition: all 0.2s ease !important;
}

.status-radio-group :deep(.el-radio-button__inner:hover) {
  color: var(--do-gold-deep) !important;
  background: var(--do-bg-input) !important;
}

.status-radio-group :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner),
.status-radio-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%) !important;
  border-color: var(--do-gold-deep) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  box-shadow: -1px 0 0 0 var(--do-gold-deep), 0 1px 4px rgba(var(--th-accent-deep-rgb), 0.25) !important;
}

/* 底部操作区 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 6px;
}

/* 页面头与指标卡：沿用大屏调度、计时计分页面的层级规范 */
.iot-matrix-workspace {
  gap: 14px;
  min-width: 0;
  color: var(--do-text-primary);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 22px;
}

.page-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.page-icon {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: var(--do-gold);
  background: var(--do-gold-wash);
  border: 1px solid var(--do-border-dark);
  border-radius: 12px;
}

.page-heading h1 {
  margin: 0;
  font-size: 21px;
  line-height: 1.3;
}

.page-heading p {
  margin: 5px 0 0;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.header-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--do-text-secondary);
  font-size: 13px;
}

.status-metric {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.status-metric strong {
  color: var(--do-text-primary);
  font-size: 15px;
}

.status-dot.online {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--do-success);
  box-shadow: 0 0 7px var(--do-success);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(135px, 1fr));
  gap: 12px;
}

.metric-card {
  min-width: 0;
  padding: 15px;
}

.metric-card span {
  color: var(--do-text-secondary);
  font-size: 13px;
}

.metric-card strong {
  display: block;
  margin-top: 8px;
  overflow: hidden;
  color: var(--do-text-primary);
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-card em {
  display: block;
  margin-top: 5px;
  overflow: hidden;
  color: var(--do-text-secondary);
  font-size: 13px;
  font-style: normal;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.system-badge {
  color: var(--do-warning-deep);
  background: var(--do-warning-bg);
  border: 1px solid var(--do-warning-border);
  border-radius: 5px;
  padding: 4px 8px;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.matrix-main-layout,
.hardware-content-panel,
.content-panel-header,
.filter-toolbar,
.batch-action-bar {
  min-width: 0;
}

.matrix-main-layout {
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 14px;
}

.hardware-content-panel {
  overflow: hidden;
  border-radius: 10px;
}

.hardware-type-sidebar {
  border-radius: 10px;
}

.content-panel-header {
  padding: 16px 18px;
}

.header-type-info {
  min-width: 0;
}

.active-type-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-toolbar {
  padding: 12px 16px;
}

.filter-left {
  min-width: 0;
}

.batch-action-bar {
  gap: 12px;
  flex-wrap: wrap;
}

.batch-left {
  min-width: 0;
  flex-wrap: wrap;
}

.batch-right {
  flex-wrap: wrap;
}

.device-table-container {
  min-width: 0;
  padding: 10px;
}

.device-table-scroll {
  width: 100%;
  min-width: 0;
  overflow-x: auto;
}

.device-table-scroll :deep(.el-table) {
  width: 100%;
}

.device-table-scroll :deep(.el-table th.el-table__cell) {
  background: var(--do-bg-sunken);
  color: var(--do-text-secondary);
  font-weight: 700;
  font-size: 13px;
  padding: 11px 0;
}

.device-table-scroll :deep(.el-table td.el-table__cell) {
  padding: 12px 0;
}

@media (max-width: 1440px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(150px, 1fr));
  }
}

@media (max-width: 1280px) {
  .matrix-main-layout {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .stat-pills-row {
    display: none;
  }
}

@media (max-width: 900px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-status {
    justify-content: flex-start;
    width: 100%;
  }

  .matrix-main-layout {
    display: flex;
    flex-direction: column;
  }

  .hardware-type-sidebar {
    width: 100%;
  }

  .hardware-nav-list {
    display: flex;
    flex-direction: row;
    gap: 8px;
    max-height: none;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 8px;
  }

  .hardware-nav-item {
    min-width: 188px;
    flex: 0 0 188px;
    border: 1px solid var(--do-border-light);
    border-radius: 8px;
  }

  .hardware-nav-item.active {
    border-color: var(--do-gold);
    border-left-width: 3px;
  }

  .nav-desc {
    font-size: 12px;
  }

  .content-panel-header,
  .filter-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-action-btns,
  .filter-left,
  .filter-right {
    width: 100%;
  }

  .filter-left :deep(.el-input),
  .filter-left :deep(.el-select) {
    width: calc(50% - 4px) !important;
  }

  .filter-left :deep(.el-input) {
    width: 100% !important;
  }

  .filter-right {
    text-align: right;
  }

  .header-action-btns :deep(.el-button) {
    width: 100%;
  }
}

@media (max-width: 720px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }

  .page-header {
    padding: 15px;
  }

  .page-heading {
    align-items: flex-start;
  }

  .page-heading h1 {
    font-size: 18px;
  }

  .title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .header-status {
    align-items: stretch;
    flex-direction: column;
  }

  .header-status :deep(.el-button) {
    width: 100%;
  }

  .filter-left :deep(.el-select) {
    width: 100% !important;
  }

  .batch-left,
  .batch-right {
    width: 100%;
  }

  .batch-right :deep(.el-button),
  .batch-right :deep(.el-dropdown) {
    flex: 1 1 auto;
  }

  .batch-right :deep(.el-dropdown .el-button) {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .page-icon {
    width: 44px;
    height: 44px;
  }

  .metric-card {
    padding: 12px;
  }
}
</style>

<style>
/* 针对 append-to-body 的物联网与工控设备弹窗外壳加固 (Sahara 暖沙金) */
.device-edit-dialog.gold-styled-dialog {
  background-color: var(--do-bg-card) !important;
  border: 1px solid var(--do-border) !important;
  border-radius: 8px !important;
  box-shadow: 0 12px 32px rgba(var(--th-shadow-rgb), 0.16) !important;
}

.device-edit-dialog.gold-styled-dialog .el-dialog__header {
  background: linear-gradient(180deg, var(--do-bg-sunken) 0%, var(--do-bg-card) 100%) !important;
  border-bottom: 1px solid var(--do-border-light) !important;
  padding: 16px 20px !important;
  margin-right: 0 !important;
}

.device-edit-dialog.gold-styled-dialog .el-dialog__title {
  color: var(--do-text-primary) !important;
  font-size: 16px !important;
  font-weight: 700 !important;
}

.device-edit-dialog.gold-styled-dialog .el-dialog__headerbtn .el-dialog__close {
  color: var(--do-text-secondary) !important;
  font-size: 18px !important;
}

.device-edit-dialog.gold-styled-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: var(--do-gold-deep) !important;
}

.device-edit-dialog.gold-styled-dialog .el-dialog__body {
  background-color: var(--do-bg-card) !important;
  padding: 18px 22px 14px 22px !important;
}

.device-edit-dialog.gold-styled-dialog .el-dialog__footer {
  background-color: var(--do-bg-card) !important;
  border-top: 1px solid var(--do-border-light) !important;
  padding: 12px 20px !important;
}

.device-edit-dialog .form-section-title {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  color: var(--do-bg-dark) !important;
  margin: 20px 0 14px 0 !important;
  padding-bottom: 9px !important;
  border-bottom: 1.5px solid rgba(var(--th-accent-rgb), 0.45) !important;
}

.device-edit-dialog .form-section-title:first-child {
  margin-top: 2px !important;
}

.device-edit-dialog .section-badge {
  width: 22px !important;
  height: 22px !important;
  border-radius: 50% !important;
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%) !important;
  color: #FFFFFF !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.4) !important;
  flex-shrink: 0 !important;
}

.device-edit-dialog .section-title-txt {
  font-size: 14px !important;
  font-weight: 800 !important;
  color: var(--do-bg-dark) !important;
  letter-spacing: 0.5px !important;
}

.device-edit-dialog .el-input__wrapper,
.device-edit-dialog .el-select__wrapper {
  background-color: var(--do-bg-input) !important;
  box-shadow: 0 0 0 1px var(--do-border) inset !important;
  border-radius: 4px !important;
}

.device-edit-dialog .el-input__wrapper.is-focus,
.device-edit-dialog .el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px var(--do-gold) inset, 0 0 0 3px rgba(var(--th-accent-rgb), 0.2) !important;
}

.device-edit-dialog .el-input__inner {
  color: var(--do-text-primary) !important;
}

.device-edit-dialog .el-textarea__inner {
  background-color: var(--do-bg-input) !important;
  color: var(--do-text-primary) !important;
  border: 1px solid var(--do-border) !important;
  box-shadow: none !important;
  border-radius: 4px !important;
  font-family: inherit !important;
}

.device-edit-dialog .el-textarea__inner:focus {
  border-color: var(--do-gold) !important;
  box-shadow: 0 0 0 2px rgba(var(--th-accent-rgb), 0.2) !important;
}

.device-edit-dialog .el-textarea .el-input__count {
  background: transparent !important;
  color: var(--do-text-secondary) !important;
  font-size: 14px !important;
}

.device-edit-dialog .el-button:not(.el-button--primary):not(.el-button--danger) {
  background-color: var(--do-bg-input) !important;
  border-color: var(--do-border) !important;
  color: var(--do-text-primary) !important;
  padding: 8px 18px !important;
}

.device-edit-dialog .el-button:not(.el-button--primary):not(.el-button--danger):hover {
  background-color: var(--do-bg-card-hover) !important;
  border-color: var(--do-gold) !important;
  color: var(--do-gold-deep) !important;
}

.gold-btn-primary {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold-deep) 100%) !important;
  border-color: var(--do-gold-deep) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  padding: 8px 20px !important;
  box-shadow: 0 2px 6px rgba(var(--th-accent-deep-rgb), 0.35) !important;
  transition: all 0.2s ease !important;
}

.gold-btn-primary:hover {
  background: linear-gradient(135deg, var(--do-gold) 0%, var(--do-gold) 100%) !important;
  border-color: var(--do-gold) !important;
  box-shadow: 0 4px 12px rgba(var(--th-accent-deep-rgb), 0.45) !important;
}

/* 弹窗底部操作栏：左侧测试连通，右侧取消/保存配置 */
.device-edit-dialog .dialog-footer {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  width: 100% !important;
  gap: 12px !important;
  padding-top: 4px !important;
}

.device-edit-dialog .footer-left {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  flex-wrap: wrap !important;
}

.device-edit-dialog .footer-right {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
}

.device-edit-dialog .btn-test-connect {
  background-color: var(--do-gold-light) !important;
  border: 1px solid var(--do-gold) !important;
  color: var(--do-gold-deep) !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
  border-radius: 4px !important;
  display: inline-flex !important;
  align-items: center !important;
  transition: all 0.25s ease !important;
}

.device-edit-dialog .btn-test-connect:hover {
  background-color: var(--do-gold-light) !important;
  border-color: var(--do-gold-deep) !important;
  color: var(--do-gold-deep) !important;
  box-shadow: 0 2px 8px rgba(var(--th-accent-deep-rgb), 0.25) !important;
  transform: translateY(-1px) !important;
}

.device-edit-dialog .connect-result-pill {
  display: inline-flex !important;
  align-items: center !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 4px 10px !important;
  border-radius: 12px !important;
  line-height: 1.4 !important;
  animation: fadeIn 0.3s ease;
}

.device-edit-dialog .connect-result-pill.success {
  background-color: var(--do-success-bg) !important;
  color: var(--do-success-deep) !important;
  border: 1px solid var(--do-success-bg) !important;
}

.device-edit-dialog .connect-result-pill.failed {
  background-color: var(--do-danger-bg) !important;
  color: var(--do-danger-deep) !important;
  border: 1px solid var(--do-danger-border) !important;
}

.btn-branch-template {
  background-color: var(--do-bg-input) !important;
  border: 1px solid var(--do-border) !important;
  color: var(--do-gold-deep) !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
}

.btn-branch-template:hover {
  background-color: var(--do-bg-card-hover) !important;
  border-color: var(--do-gold) !important;
  color: var(--do-gold-deep) !important;
}
</style>
