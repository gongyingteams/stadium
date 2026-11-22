-- ==============================================================================
-- 体育场馆应用集成管理系统 - 物联网控制13项硬件设备、分组、区域、自编号及执行回执数据库增量迁移脚本
-- 依据用户需求：
-- 1. 13项硬件设备每一项支持：分组(group_name)、分区域(region_name)、自编号(custom_no)、备注(remark)，增删改查
-- 2. 设备专属指令表 (iot_device_command)：参数编辑与指令编辑
-- 3. 指令执行结果回执表 (iot_command_log)：成功/失败回执追踪
-- ==============================================================================

SET NAMES utf8mb4;

-- 1. 扩充 iot_device_instance 字段
ALTER TABLE `iot_device_instance`
  ADD COLUMN IF NOT EXISTS `hardware_type` VARCHAR(64) NOT NULL DEFAULT 'AUDIO' COMMENT '13项硬件设备类型' AFTER `id`,
  ADD COLUMN IF NOT EXISTS `custom_no` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '用户自定义自编号' AFTER `hardware_type`,
  ADD COLUMN IF NOT EXISTS `group_name` VARCHAR(64) NOT NULL DEFAULT '默认主控组' COMMENT '设备分组名称' AFTER `device_name`,
  ADD COLUMN IF NOT EXISTS `region_name` VARCHAR(128) NOT NULL DEFAULT '主体育馆' COMMENT '物理安装区域' AFTER `group_name`,
  ADD COLUMN IF NOT EXISTS `remark` TEXT COMMENT '备注信息与施工维保备忘' AFTER `last_seen_at`,
  ADD COLUMN IF NOT EXISTS `params_json` TEXT COMMENT '通信扩展参数JSON' AFTER `remark`;

-- 增加高效检索索引
ALTER TABLE `iot_device_instance`
  ADD INDEX IF NOT EXISTS `idx_hardware_type` (`hardware_type`),
  ADD INDEX IF NOT EXISTS `idx_custom_no` (`custom_no`),
  ADD INDEX IF NOT EXISTS `idx_group_region` (`group_name`, `region_name`);

-- 2. 创建设备专属控制指令库表 (针对每个设备的预设指令维护)
CREATE TABLE IF NOT EXISTS `iot_device_command` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `device_id` BIGINT UNSIGNED NOT NULL COMMENT '关联iot_device_instance ID',
  `command_name` VARCHAR(64) NOT NULL COMMENT '指令名称(例如: 开机/全场照明/音量复位)',
  `command_code` VARCHAR(64) NOT NULL COMMENT '指令代号',
  `payload_format` VARCHAR(16) NOT NULL DEFAULT 'HEX' COMMENT '报文格式: HEX/ASCII/JSON',
  `command_payload` TEXT NOT NULL COMMENT '具体发送报文内容',
  `expected_ack` VARCHAR(128) DEFAULT '' COMMENT '期望回执响应特征或切片',
  `timeout_ms` INT NOT NULL DEFAULT 1500 COMMENT '执行超时等待(毫秒)',
  `is_dangerous` TINYINT NOT NULL DEFAULT 0 COMMENT '是否高危操作(需二次确认): 0=否, 1=是',
  `remark` VARCHAR(255) DEFAULT '' COMMENT '指令说明',
  `sort_order` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备专属控制指令库表';

-- 3. 创建指令执行流水与结果回执审计记录表 (支持执行结果回执成功/失败追踪)
CREATE TABLE IF NOT EXISTS `iot_command_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `trace_id` VARCHAR(64) NOT NULL COMMENT '下发链路唯一追踪ID',
  `device_id` BIGINT UNSIGNED NOT NULL COMMENT '目标设备ID',
  `custom_no` VARCHAR(64) DEFAULT '' COMMENT '目标设备自编号',
  `device_name` VARCHAR(128) NOT NULL COMMENT '目标设备名称',
  `hardware_type` VARCHAR(64) NOT NULL COMMENT '硬件类型',
  `command_name` VARCHAR(64) NOT NULL COMMENT '指令动作名称',
  `command_payload` TEXT NOT NULL COMMENT '下发报文数据',
  `execute_result` VARCHAR(32) NOT NULL DEFAULT 'SUCCESS' COMMENT '执行结果回执: SUCCESS(成功)/FAILED(失败)/TIMEOUT(超时)/OFFLINE(设备离线)',
  `response_payload` TEXT COMMENT '下位机执行结果回执响应报文',
  `cost_ms` INT NOT NULL DEFAULT 0 COMMENT '响应耗时(毫秒)',
  `operator_name` VARCHAR(64) NOT NULL DEFAULT 'admin' COMMENT '操作人账号',
  `is_batch` TINYINT NOT NULL DEFAULT 0 COMMENT '是否为勾选多选批量下发: 0=单机, 1=批量',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下发执行时间',
  PRIMARY KEY (`id`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_hardware_type` (`hardware_type`),
  KEY `idx_execute_result` (`execute_result`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='指令执行流水与结果回执审计表';
