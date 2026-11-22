-- ==============================================================================
-- 体育场馆应用集成管理系统 (IBMS / 集中控制台) 全量数据库安装脚本
-- 依据标准：《01_需求设计：开发功能清单和整体进度规划.md》《02_项目原型：UI设计规范与全页面设计要求.md》《03_界面规划：系统菜单和页面规划及数据库.md》
-- 版本：v1.0.0
-- 字符集：utf8mb4 / 排序规则：utf8mb4_unicode_ci
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. 用户、角色、权限与审计域
-- ------------------------------------------------------------------------------

-- 用户表
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户主键ID',
  `username` VARCHAR(64) NOT NULL COMMENT '登录账号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希值(BCrypt/Argon2)',
  `display_name` VARCHAR(64) NOT NULL COMMENT '真实姓名/显示名称',
  `avatar` VARCHAR(255) DEFAULT '' COMMENT '头像URL',
  `phone` VARCHAR(20) DEFAULT '' COMMENT '联系电话',
  `email` VARCHAR(128) DEFAULT '' COMMENT '电子邮箱',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
  `last_login_at` DATETIME DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` VARCHAR(45) DEFAULT '' COMMENT '最后登录IP',
  `created_by` VARCHAR(64) DEFAULT 'system' COMMENT '创建人',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` VARCHAR(64) DEFAULT 'system' COMMENT '更新人',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` DATETIME DEFAULT NULL COMMENT '软删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

-- 角色表
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色主键ID',
  `role_code` VARCHAR(64) NOT NULL COMMENT '角色唯一编码(admin/ops/operator/viewer)',
  `role_name` VARCHAR(64) NOT NULL COMMENT '角色名称',
  `role_desc` VARCHAR(255) DEFAULT '' COMMENT '角色描述',
  `is_builtin` TINYINT NOT NULL DEFAULT 0 COMMENT '是否内置系统角色: 0=否, 1=是(不可删除)',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_code` (`role_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统角色表';

-- 权限定义表
DROP TABLE IF EXISTS `sys_permission`;
CREATE TABLE `sys_permission` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '权限主键ID',
  `permission_code` VARCHAR(128) NOT NULL COMMENT '全局唯一权限编码',
  `permission_name` VARCHAR(128) NOT NULL COMMENT '权限名称',
  `resource_type` VARCHAR(32) NOT NULL COMMENT '资源类型: SYSTEM/SUBSYSTEM/DEVICE/PAGE/BUTTON/ACTION',
  `action_code` VARCHAR(64) NOT NULL COMMENT '动作编码: VIEW/EXECUTE/STOP/CONFIG/EXPORT/DELETE/MOCK',
  `terminal_scope` VARCHAR(32) NOT NULL DEFAULT 'ALL' COMMENT '终端范围: PC/TABLET/ALL',
  `parent_code` VARCHAR(128) DEFAULT NULL COMMENT '父级权限编码',
  `description` VARCHAR(255) DEFAULT '' COMMENT '权限描述',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_perm_code` (`permission_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='细粒度权限定义表';

-- 用户-角色关联表
DROP TABLE IF EXISTS `sys_user_role`;
CREATE TABLE `sys_user_role` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `role_id` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  KEY `idx_role_id` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- 角色-权限关联表
DROP TABLE IF EXISTS `sys_role_permission`;
CREATE TABLE `sys_role_permission` (
  `role_id` BIGINT UNSIGNED NOT NULL,
  `permission_id` BIGINT UNSIGNED NOT NULL,
  `resource_id` VARCHAR(64) DEFAULT '*' COMMENT '资源限定ID(*为通配)',
  PRIMARY KEY (`role_id`, `permission_id`),
  KEY `idx_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- 操作审计日志表 (不可篡改追加写)
DROP TABLE IF EXISTS `sys_audit_log`;
CREATE TABLE `sys_audit_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '审计日志ID',
  `trace_id` VARCHAR(64) NOT NULL COMMENT '全局链路追踪TraceID',
  `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
  `username` VARCHAR(64) NOT NULL DEFAULT 'anonymous' COMMENT '操作人账号',
  `role_code` VARCHAR(64) DEFAULT '' COMMENT '操作时所属角色',
  `terminal_type` VARCHAR(32) NOT NULL DEFAULT 'PC' COMMENT '终端类型: PC/TABLET/API',
  `client_ip` VARCHAR(45) NOT NULL DEFAULT '127.0.0.1' COMMENT '客户端IP',
  `event_type` VARCHAR(64) NOT NULL COMMENT '事件类型: LOGIN/SLO/CMD_EXEC/CONFIG_CHANGE/MOCK_TOGGLE/ALARM_HANDLE/MEDIA_OP/EXPORT',
  `target_subsystem` VARCHAR(64) DEFAULT '' COMMENT '目标子系统编码',
  `target_device` VARCHAR(128) DEFAULT '' COMMENT '目标设备标识/名称',
  `action_name` VARCHAR(128) NOT NULL COMMENT '业务动作名称',
  `request_summary` TEXT COMMENT '请求指令报文或参数摘要',
  `response_summary` TEXT COMMENT '回传响应报文或结果摘要',
  `execute_result` VARCHAR(32) NOT NULL DEFAULT 'SUCCESS' COMMENT '执行结果: SUCCESS/FAILED/TIMEOUT/BLOCKED',
  `cost_ms` INT NOT NULL DEFAULT 0 COMMENT '执行耗时(毫秒)',
  `config_version` VARCHAR(64) DEFAULT 'v1.0' COMMENT '关联系统配置版本',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '审计记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_username` (`username`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_trace_id` (`trace_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计不可篡改日志表';

-- 系统基础配置与对象存储设置表 (键值对 + 分类扩展)
DROP TABLE IF EXISTS `sys_setting`;
CREATE TABLE `sys_setting` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `setting_key` VARCHAR(64) NOT NULL COMMENT '配置唯一键名',
  `setting_value` TEXT COMMENT '配置值(文本/JSON格式)',
  `setting_category` VARCHAR(32) NOT NULL DEFAULT 'SYSTEM' COMMENT '配置大类: SYSTEM(系统基础)/COPYRIGHT(版权信息)/OPERATOR(开发运营)/STORAGE(文件存储)',
  `setting_desc` VARCHAR(255) DEFAULT '' COMMENT '配置描述说明',
  `is_public` TINYINT NOT NULL DEFAULT 1 COMMENT '是否前端公开可见: 1=公开, 0=敏感保密',
  `updated_by` VARCHAR(64) DEFAULT 'admin' COMMENT '最后更新人',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_setting_key` (`setting_key`),
  KEY `idx_category` (`setting_category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统基础配置与对象存储设置表';

-- ------------------------------------------------------------------------------
-- 2. 菜单导航、路由与 Portal 聚合域 (支柱二)
-- ------------------------------------------------------------------------------

-- 系统菜单与路由表
DROP TABLE IF EXISTS `sys_menu`;
CREATE TABLE `sys_menu` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `menu_code` VARCHAR(64) NOT NULL COMMENT '全局唯一菜单编码',
  `parent_id` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '父级菜单ID(0为根)',
  `menu_name` VARCHAR(64) NOT NULL COMMENT '显示完整全称',
  `short_name` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '规范缩写别名(统一4字对齐)',
  `route_name` VARCHAR(64) DEFAULT '' COMMENT '前端Vue路由名称',
  `route_path` VARCHAR(128) NOT NULL COMMENT '前端路由地址',
  `component_name` VARCHAR(128) DEFAULT '' COMMENT 'Vue组件路径',
  `icon_code` VARCHAR(64) NOT NULL DEFAULT 'SvgDefault' COMMENT '纯矢量SVG图标组件名',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '菜单排序权重',
  `terminal_scope` VARCHAR(32) NOT NULL DEFAULT 'ALL' COMMENT '终端范围: PC/TABLET/ALL',
  `baseline_flag` TINYINT NOT NULL DEFAULT 1 COMMENT '是否属于附件基线: 1=基线, 0=扩展项',
  `dynamic_flag` TINYINT NOT NULL DEFAULT 0 COMMENT '是否为配置动态生成: 1=动态, 0=静态',
  `permission_code` VARCHAR(128) DEFAULT '' COMMENT '所需访问权限编码',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_menu_code` (`menu_code`),
  KEY `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统菜单与路由导航表';

-- 第三方应用导航门户表 (Portal)
DROP TABLE IF EXISTS `portal_app`;
CREATE TABLE `portal_app` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '应用ID',
  `app_code` VARCHAR(64) NOT NULL COMMENT '应用编码',
  `app_name` VARCHAR(64) NOT NULL COMMENT '第三方系统中文名',
  `subsystem_code` VARCHAR(64) NOT NULL COMMENT '对应基线13类子系统编码',
  `integration_mode` VARCHAR(32) NOT NULL DEFAULT 'API' COMMENT '接入模式: API(开放接口)/IFRAME_FALLBACK(无接口降级内嵌)',
  `entry_url` VARCHAR(512) NOT NULL COMMENT '入口URL或代理目标地址',
  `app_category` VARCHAR(64) NOT NULL DEFAULT 'OPERATION' COMMENT '分类: OPERATION/MEDIA/SAFETY/SERVICE',
  `sso_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用SSO免密: 1=是, 0=否',
  `sso_protocol` VARCHAR(32) DEFAULT 'OAUTH2' COMMENT 'SSO协议: OAUTH2/CAS/TICKET_TOKEN/CUSTOM',
  `icon_svg` VARCHAR(64) DEFAULT 'SvgPortal' COMMENT '图标SVG',
  `description` VARCHAR(255) DEFAULT '' COMMENT '功能简述',
  `sort_order` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_app_code` (`app_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='第三方应用聚合门户表';

-- 代理安全域名与路径白名单表
DROP TABLE IF EXISTS `portal_domain_whitelist`;
CREATE TABLE `portal_domain_whitelist` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `app_id` BIGINT UNSIGNED NOT NULL COMMENT '关联portal_app ID',
  `target_domain` VARCHAR(255) NOT NULL COMMENT '允许代理的域名或IP:Port',
  `allowed_path_prefix` VARCHAR(255) NOT NULL DEFAULT '/' COMMENT '允许的前缀路径',
  `allowed_protocols` VARCHAR(64) NOT NULL DEFAULT 'HTTP,HTTPS' COMMENT '协议白名单',
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_app_id` (`app_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Portal代理安全白名单表';

-- SSO 会话与短时效 Ticket 表
DROP TABLE IF EXISTS `sso_ticket`;
CREATE TABLE `sso_ticket` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `ticket_hash` VARCHAR(128) NOT NULL COMMENT '短时效一次性Ticket哈希摘要',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `app_id` BIGINT UNSIGNED NOT NULL COMMENT '目标应用ID',
  `perm_scope` VARCHAR(255) DEFAULT '*' COMMENT '最小权限范围',
  `expires_at` DATETIME NOT NULL COMMENT '过期时间(通常60秒)',
  `used_at` DATETIME DEFAULT NULL COMMENT '使用核销时间',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态: 0=有效待用, 1=已核销, 2=已失效',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ticket_hash` (`ticket_hash`),
  KEY `idx_user_app` (`user_id`, `app_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SSO单点登录一次性Ticket凭据表';

-- SLO 单点登出明细与注销跟踪表
DROP TABLE IF EXISTS `slo_logout_result`;
CREATE TABLE `slo_logout_result` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id` VARCHAR(128) NOT NULL COMMENT '主会话Session标识',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `app_id` BIGINT UNSIGNED NOT NULL COMMENT '第三方应用ID',
  `app_name` VARCHAR(64) NOT NULL,
  `logout_status` VARCHAR(32) NOT NULL COMMENT '结果: SUCCESS/FAILED/TIMEOUT/DESTROYED',
  `fail_reason` VARCHAR(255) DEFAULT '',
  `retry_count` INT NOT NULL DEFAULT 0,
  `completed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SLO单点登出执行回执跟踪表';

-- ------------------------------------------------------------------------------
-- 3. 物联网子系统、设备与全协议配置中心 (支柱一与支柱三)
-- ------------------------------------------------------------------------------

-- 13类基线子系统总表
DROP TABLE IF EXISTS `iot_subsystem`;
CREATE TABLE `iot_subsystem` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `subsystem_code` VARCHAR(64) NOT NULL COMMENT '基线13类子系统编码',
  `subsystem_name` VARCHAR(64) NOT NULL COMMENT '子系统中文名称',
  `baseline_flag` TINYINT NOT NULL DEFAULT 1 COMMENT '1=附件必须覆盖的13类基线, 0=可选扩展',
  `default_protocol` VARCHAR(32) NOT NULL DEFAULT 'SERIAL' COMMENT '主协议: SERIAL/TCP/UDP/HTTP/MODBUS/RTSP',
  `primary_route` VARCHAR(128) NOT NULL COMMENT 'PC主控制台路由',
  `icon_code` VARCHAR(64) NOT NULL DEFAULT 'SvgIotControl',
  `description` VARCHAR(255) DEFAULT '',
  `status` TINYINT NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_subsystem_code` (`subsystem_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='13大基线子系统总表';

-- 设备实例表 (支持13项硬件、自编号、分组、区域、备注、通信配置)
DROP TABLE IF EXISTS `iot_device_instance`;
CREATE TABLE `iot_device_instance` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `hardware_type` VARCHAR(64) NOT NULL DEFAULT 'AUDIO' COMMENT '13项硬件设备类型(AUDIO/LIGHTING/SCREEN/SCORE/FLAG/CLOCK/VIDEO/MEDIA/ENERGY/HVAC/SECURITY/BROADCAST/ENVIRONMENT)',
  `custom_no` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '用户自定义自编号(例如: AMP-POOL-01, LIGHT-W01)',
  `device_code` VARCHAR(64) NOT NULL COMMENT '系统唯一设备编码',
  `device_name` VARCHAR(128) NOT NULL COMMENT '设备名称',
  `group_name` VARCHAR(64) NOT NULL DEFAULT '默认主控组' COMMENT '设备分组名称',
  `region_name` VARCHAR(128) NOT NULL DEFAULT '主体育馆' COMMENT '物理安装区域',
  `subsystem_id` BIGINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '关联iot_subsystem ID',
  `manufacturer` VARCHAR(64) NOT NULL DEFAULT 'Generic' COMMENT '厂商名称',
  `model_name` VARCHAR(64) DEFAULT '' COMMENT '设备硬件型号',
  `connection_type` VARCHAR(32) NOT NULL DEFAULT 'SERIAL' COMMENT '通信连接: SERIAL/TCP/UDP/HTTP/MODBUS/RTSP',
  `online_status` VARCHAR(32) NOT NULL DEFAULT 'ONLINE' COMMENT '状态: ONLINE/OFFLINE/FAULT/STANDBY',
  `heartbeat_period` INT NOT NULL DEFAULT 5 COMMENT '轮询心跳周期(秒)',
  `last_seen_at` DATETIME DEFAULT NULL COMMENT '最后通信响应时间',
  `remark` TEXT COMMENT '备注信息与施工维保备忘',
  `params_json` TEXT COMMENT '通信扩展参数JSON',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_device_code` (`device_code`),
  KEY `idx_hardware_type` (`hardware_type`),
  KEY `idx_custom_no` (`custom_no`),
  KEY `idx_group_region` (`group_name`, `region_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物联网设备实例资产表';

-- 设备专属控制指令库表 (针对每个设备的预设指令维护)
DROP TABLE IF EXISTS `iot_device_command`;
CREATE TABLE `iot_device_command` (
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

-- 指令执行流水与结果回执审计记录表 (支持执行结果回执成功/失败追踪)
DROP TABLE IF EXISTS `iot_command_log`;
CREATE TABLE `iot_command_log` (
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

-- 协议配置明细表 (含动态参数与校验规则)
DROP TABLE IF EXISTS `iot_protocol_profile`;
CREATE TABLE `iot_protocol_profile` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `device_id` BIGINT UNSIGNED NOT NULL COMMENT '关联设备实例ID',
  `protocol_type` VARCHAR(32) NOT NULL COMMENT 'SERIAL/TCP/UDP/HTTP/MODBUS/RTSP/EXE',
  -- 串口参数
  `serial_port` VARCHAR(32) DEFAULT 'COM1' COMMENT '本地COM口或网络串口映射',
  `baud_rate` INT DEFAULT 9600 COMMENT '波特率(1200~115200)',
  `data_bits` TINYINT DEFAULT 8 COMMENT '数据位: 5/6/7/8',
  `stop_bits` VARCHAR(8) DEFAULT '1' COMMENT '停止位: 1/1.5/2',
  `parity` VARCHAR(16) DEFAULT 'NONE' COMMENT '校验位: NONE/ODD/EVEN',
  -- 网络参数
  `target_ip` VARCHAR(64) DEFAULT '' COMMENT 'IP地址或域名',
  `target_port` INT DEFAULT 0 COMMENT '通信端口号',
  `timeout_ms` INT NOT NULL DEFAULT 1500 COMMENT '超时等待时间(毫秒)',
  `retry_count` INT NOT NULL DEFAULT 3 COMMENT '失败重试次数',
  -- HTTP/RESTful 参数
  `http_method` VARCHAR(16) DEFAULT 'GET' COMMENT 'GET/POST/PUT/DELETE',
  `http_headers_json` TEXT COMMENT '请求头JSON',
  `http_auth_token` VARCHAR(255) DEFAULT '' COMMENT '鉴权Token(脱敏或加密)',
  -- 报文格式与校验解析
  `payload_format` VARCHAR(16) NOT NULL DEFAULT 'HEX' COMMENT 'HEX/ASCII/JSON',
  `checksum_type` VARCHAR(16) DEFAULT 'CRC16' COMMENT 'CRC16/LRC/CHECKSUM/NONE',
  `response_regex` VARCHAR(255) DEFAULT '' COMMENT '回传响应提取正则表达式或切片规则',
  -- RTSP与音视频
  `stream_url` VARCHAR(512) DEFAULT '' COMMENT '流媒体地址摘要',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_device_profile` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备通信协议参数配置表';

-- 动态低代码控制面板与菜单分组表
DROP TABLE IF EXISTS `iot_menu_group`;
CREATE TABLE `iot_menu_group` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `group_code` VARCHAR(64) NOT NULL COMMENT '分组编码',
  `group_name` VARCHAR(64) NOT NULL COMMENT '分组名称(如 跳水池灯控组)',
  `parent_id` BIGINT UNSIGNED NOT NULL DEFAULT 0,
  `icon_code` VARCHAR(64) NOT NULL DEFAULT 'SvgDynamicDevice',
  `sort_order` INT NOT NULL DEFAULT 0,
  `terminal_scope` VARCHAR(32) NOT NULL DEFAULT 'ALL' COMMENT '终端范围: PC/TABLET/ALL',
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_code` (`group_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态菜单与低代码面板分组表';

-- 自定义操作按钮与指令动作表
DROP TABLE IF EXISTS `iot_action_button`;
CREATE TABLE `iot_action_button` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `group_id` BIGINT UNSIGNED NOT NULL COMMENT '关联菜单分组ID',
  `device_id` BIGINT UNSIGNED NOT NULL COMMENT '下发目标设备ID',
  `button_name` VARCHAR(64) NOT NULL COMMENT '按钮文字',
  `button_style` VARCHAR(32) NOT NULL DEFAULT 'primary' COMMENT 'primary/success/warning/danger/info',
  `icon_name` VARCHAR(64) DEFAULT '' COMMENT '按钮图标',
  `action_type` VARCHAR(32) NOT NULL DEFAULT 'IMMEDIATE' COMMENT '执行时间: IMMEDIATE(立即)/DELAY(延时)/CRON(定时)/MACRO(宏场景)',
  `delay_ms` INT NOT NULL DEFAULT 0 COMMENT '延时时长(毫秒)',
  `cron_expr` VARCHAR(64) DEFAULT '' COMMENT 'Cron定时表达式',
  `is_estop` TINYINT NOT NULL DEFAULT 0 COMMENT '是否为最高优先级急停指令: 1=是, 0=否',
  `requires_confirm` TINYINT NOT NULL DEFAULT 0 COMMENT '是否需要二次确认(高危动作): 1=是, 0=否',
  `command_format` VARCHAR(16) NOT NULL DEFAULT 'HEX' COMMENT 'HEX/ASCII/JSON',
  `command_payload` TEXT NOT NULL COMMENT '具体指令报文或API参数',
  `parse_rule` VARCHAR(255) DEFAULT '' COMMENT '响应回传解析规则',
  `permission_code` VARCHAR(128) NOT NULL DEFAULT 'iot:action:execute' COMMENT '所需权限',
  `sort_order` INT NOT NULL DEFAULT 0,
  `status` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_group_id` (`group_id`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自定义操作按钮与指令表';

-- 设备状态轮询与心跳巡检任务表
DROP TABLE IF EXISTS `iot_poll_task`;
CREATE TABLE `iot_poll_task` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `device_id` BIGINT UNSIGNED NOT NULL,
  `task_name` VARCHAR(64) NOT NULL,
  `poll_interval_sec` INT NOT NULL DEFAULT 5 COMMENT '轮询间隔(秒)',
  `poll_command` VARCHAR(512) NOT NULL COMMENT '轮询探测报文',
  `expected_response` VARCHAR(255) DEFAULT '' COMMENT '期望响应特征',
  `timeout_ms` INT NOT NULL DEFAULT 1000,
  `max_retries` INT NOT NULL DEFAULT 3,
  `status_mapping_json` TEXT COMMENT '状态回显规则映射字典',
  `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启动轮询',
  `last_result` VARCHAR(32) DEFAULT 'OK',
  `last_polled_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备状态轮询巡检任务表';

-- 外置硬件适配登记台账表
DROP TABLE IF EXISTS `iot_hardware_adapter`;
CREATE TABLE `iot_hardware_adapter` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `adapter_name` VARCHAR(128) NOT NULL COMMENT '适配设备名称(如: 研华4口串口服务器)',
  `model_spec` VARCHAR(64) NOT NULL COMMENT '具体型号规格',
  `conversion_type` VARCHAR(64) NOT NULL COMMENT '转换类型: USB转RS485/网口转RS232/光电隔离',
  `wiring_definition` TEXT COMMENT 'DB9/RJ45引脚定义与接线说明',
  `topology_desc` VARCHAR(255) DEFAULT '' COMMENT '连接拓扑位置说明',
  `diagram_path` VARCHAR(255) DEFAULT '' COMMENT '接线拓扑示意图路径',
  `responsible_person` VARCHAR(64) NOT NULL DEFAULT '运维班' COMMENT '责任运维人员',
  `contact_phone` VARCHAR(32) DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外置硬件适配与接线台账表';

-- ------------------------------------------------------------------------------
-- 4. 告警监控与通知渠道域
-- ------------------------------------------------------------------------------

-- 实时告警事件记录表 (原始记录不可物理删除)
DROP TABLE IF EXISTS `alarm_event`;
CREATE TABLE `alarm_event` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `event_no` VARCHAR(64) NOT NULL COMMENT '告警唯一流水号',
  `subsystem_code` VARCHAR(64) NOT NULL COMMENT '所属基线子系统',
  `device_id` BIGINT UNSIGNED NOT NULL COMMENT '发生设备ID',
  `device_name` VARCHAR(128) NOT NULL,
  `alarm_level` VARCHAR(16) NOT NULL DEFAULT 'WARNING' COMMENT '级别: EMERGENCY(紧急红)/WARNING(警告黄)/INFO(提示蓝)',
  `alarm_title` VARCHAR(128) NOT NULL COMMENT '告警标题',
  `alarm_content` VARCHAR(512) NOT NULL COMMENT '详细故障诊断描述',
  `alarm_status` VARCHAR(32) NOT NULL DEFAULT 'NEW' COMMENT '状态: NEW(新建)/CONFIRMED(已确认)/PROCESSING(处理中)/RECOVERED(已恢复)/CLOSED(已关闭)',
  `first_occurred_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次发生时间',
  `last_occurred_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最近发生时间',
  `recovered_at` DATETIME DEFAULT NULL COMMENT '自动或手动恢复时间',
  `confirmed_by` VARCHAR(64) DEFAULT NULL COMMENT '确认处置人',
  `is_muted` TINYINT NOT NULL DEFAULT 0 COMMENT '是否静音',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_event_no` (`event_no`),
  KEY `idx_alarm_status` (`alarm_status`),
  KEY `idx_alarm_level` (`alarm_level`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警事件记录表';

-- 通知渠道配置表
DROP TABLE IF EXISTS `notification_channel`;
CREATE TABLE `notification_channel` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `channel_type` VARCHAR(32) NOT NULL COMMENT '渠道类型: EMAIL_SMTP/WECHAT_WORK/WECHAT_MP',
  `channel_name` VARCHAR(64) NOT NULL COMMENT '渠道名称',
  `config_params_json` TEXT NOT NULL COMMENT '配置参数(SMTP服务器/Webhook/模板ID/凭据加密)',
  `is_enabled` TINYINT NOT NULL DEFAULT 1,
  `last_test_at` DATETIME DEFAULT NULL,
  `last_test_result` VARCHAR(32) DEFAULT 'UNTESTED',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_channel_type` (`channel_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多通道告警推送配置表';

-- ------------------------------------------------------------------------------
-- 5. 专业业务域 (时钟、升旗、成绩推屏、媒体与能耗)
-- ------------------------------------------------------------------------------

-- 标准时钟：全场子钟明细与分类拓扑表
DROP TABLE IF EXISTS `iot_sub_clock`;
CREATE TABLE `iot_sub_clock` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `master_device_id` BIGINT UNSIGNED NOT NULL COMMENT '关联母钟设备ID',
  `clock_code` VARCHAR(64) NOT NULL COMMENT '子钟物理编号',
  `clock_type` VARCHAR(32) NOT NULL COMMENT '子钟类型: SINGLE_SIDED(单面钟)/DOUBLE_SIDED(双面钟)/DIGITAL_LED(数码钟)',
  `install_area` VARCHAR(64) NOT NULL COMMENT '安装区域: 看台A区/比赛大厅/热身馆/裁判台/媒体中心',
  `ip_address` VARCHAR(45) DEFAULT '',
  `run_status` VARCHAR(32) NOT NULL DEFAULT 'NORMAL' COMMENT '状态: NORMAL(正常)/FAULT(故障)/OFFLINE(离线)',
  `drift_ms` INT NOT NULL DEFAULT 0 COMMENT '与母钟时间差(毫秒)',
  `fault_reason` VARCHAR(255) DEFAULT '',
  `last_heartbeat_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_clock_code` (`clock_code`),
  KEY `idx_master_device` (`master_device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标准时钟全场子钟拓扑表';

-- 标准时钟：母钟授时比对与同步日志表
DROP TABLE IF EXISTS `biz_clock_sync_log`;
CREATE TABLE `biz_clock_sync_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `master_device_id` BIGINT UNSIGNED NOT NULL,
  `satellite_count` INT NOT NULL DEFAULT 12 COMMENT '北斗/GPS捕获有效卫星颗数',
  `time_zone` VARCHAR(32) NOT NULL DEFAULT 'UTC+8',
  `master_clock_time` VARCHAR(32) NOT NULL COMMENT '母钟标准时间',
  `local_server_time` VARCHAR(32) NOT NULL COMMENT '平台服务器本地时间',
  `drift_ms` INT NOT NULL DEFAULT 0 COMMENT '时钟偏差(毫秒)',
  `sync_status` VARCHAR(32) NOT NULL DEFAULT 'SYNCED' COMMENT '同步状态: SYNCED/DRIFT_WARN',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='母钟卫星授时与时间同步日志表';

-- 媒体库：资源分类字典表 (支持音频、视频、文件、其他及自定义增删改)
DROP TABLE IF EXISTS `biz_media_category`;
CREATE TABLE `biz_media_category` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类主键ID',
  `category_code` VARCHAR(64) NOT NULL COMMENT '分类唯一英文标识(audio/video/document/other...)',
  `category_name` VARCHAR(64) NOT NULL COMMENT '分类显示名称',
  `icon_code` VARCHAR(64) NOT NULL DEFAULT 'SvgMediaPlayer' COMMENT '分类矢量图标名',
  `is_builtin` TINYINT NOT NULL DEFAULT 1 COMMENT '是否系统内置默认分类: 1=是, 0=自定义',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `description` VARCHAR(255) DEFAULT '' COMMENT '分类描述说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_code` (`category_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体与资源分类字典表';

-- 媒体库：资源业务分组字典表 (支持国歌、国旗、宣传片、其他及自定义增删改)
DROP TABLE IF EXISTS `biz_media_group`;
CREATE TABLE `biz_media_group` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分组主键ID',
  `group_code` VARCHAR(64) NOT NULL COMMENT '分组唯一英文标识(anthem/flag/promo/other...)',
  `group_name` VARCHAR(64) NOT NULL COMMENT '分组业务显示名称',
  `is_builtin` TINYINT NOT NULL DEFAULT 1 COMMENT '是否系统内置默认分组: 1=是, 0=自定义',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `description` VARCHAR(255) DEFAULT '' COMMENT '分组业务描述说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_code` (`group_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体与资源业务分组字典表';

-- 媒体库：全分类全分组数字资产总表 (深度对接本地文件系统/阿里云OSS/腾讯云COS)
DROP TABLE IF EXISTS `biz_media_asset`;
CREATE TABLE `biz_media_asset` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '素材主键ID',
  `asset_name` VARCHAR(128) NOT NULL COMMENT '素材资源名称',
  `category_code` VARCHAR(64) NOT NULL COMMENT '关联资源分类编码(audio/video/document/other)',
  `group_code` VARCHAR(64) NOT NULL COMMENT '关联业务分组编码(anthem/flag/promo/other)',
  `file_type` VARCHAR(32) NOT NULL DEFAULT 'mp3' COMMENT '文件扩展名(mp3/wav/mp4/pdf/svg/...)',
  `file_size_bytes` BIGINT NOT NULL DEFAULT 0 COMMENT '文件字节大小',
  `file_size_formatted` VARCHAR(32) DEFAULT '' COMMENT '格式化显示大小(如 3.66MB)',
  `duration_sec` INT NOT NULL DEFAULT 0 COMMENT '音视频时长(秒)',
  `duration_formatted` VARCHAR(32) DEFAULT '' COMMENT '格式化时长(如 00:46)',
  `resolution` VARCHAR(64) DEFAULT '' COMMENT '采样率/分辨率/规格描述',
  `file_hash` VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'SHA256文件哈希校验码',
  `storage_driver` VARCHAR(32) NOT NULL DEFAULT 'LOCAL' COMMENT '存储驱动: LOCAL(本地文件)/ALIYUN(阿里云OSS)/TENCENT(腾讯云COS)',
  `storage_bucket` VARCHAR(128) DEFAULT '' COMMENT '存储桶名称或本地服务器标识',
  `storage_path` VARCHAR(512) NOT NULL COMMENT '物理落盘绝对路径或云端Object Key',
  `access_url` VARCHAR(1024) NOT NULL COMMENT '外部反代或CDN访问URL',
  `ref_count` INT NOT NULL DEFAULT 0 COMMENT '被升旗、投屏或播控引用的次数',
  `remark` VARCHAR(255) DEFAULT '' COMMENT '备注说明',
  `created_by` VARCHAR(64) NOT NULL DEFAULT 'admin' COMMENT '上传录入人',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_cat_grp` (`category_code`, `group_code`),
  KEY `idx_storage_driver` (`storage_driver`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体与数字资产核心总表';

-- 媒体库：兼容旧版音频素材库视图/表
DROP TABLE IF EXISTS `biz_audio_library`;
CREATE TABLE `biz_audio_library` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `audio_name` VARCHAR(128) NOT NULL COMMENT '音频文件名称',
  `category` VARCHAR(64) NOT NULL DEFAULT 'ANTHEM' COMMENT '分类: ANTHEM(国歌)/AWARD(颁奖曲)/CEREMONY(仪式)/BGM(背景音乐)',
  `file_path` VARCHAR(255) NOT NULL COMMENT '文件物理/虚拟路径',
  `file_hash` VARCHAR(64) NOT NULL COMMENT 'SHA256哈希校验码',
  `duration_ms` INT NOT NULL COMMENT '实际准确音频时长(毫秒)',
  `sample_rate` INT NOT NULL DEFAULT 44100 COMMENT '采样率(Hz)',
  `file_size_bytes` BIGINT NOT NULL DEFAULT 0,
  `ref_count` INT NOT NULL DEFAULT 0 COMMENT '被升旗或播放列表引用的次数',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='音频素材库明细表';

-- 媒体库：兼容旧版视频素材库视图/表
DROP TABLE IF EXISTS `biz_video_library`;
CREATE TABLE `biz_video_library` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `video_name` VARCHAR(128) NOT NULL COMMENT '视频文件名称',
  `category` VARCHAR(64) NOT NULL DEFAULT 'PROMO' COMMENT '分类: PROMO(宣传片)/OPENING(开场)/LOOP(循环垫片)',
  `file_path` VARCHAR(255) NOT NULL,
  `file_hash` VARCHAR(64) NOT NULL,
  `resolution` VARCHAR(32) NOT NULL DEFAULT '1920x1080',
  `bitrate_kbps` INT NOT NULL DEFAULT 8000,
  `duration_sec` INT NOT NULL DEFAULT 60,
  `file_size_bytes` BIGINT NOT NULL DEFAULT 0,
  `ref_count` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频素材库明细表';

-- 自动升旗控制与执行流水记录表
DROP TABLE IF EXISTS `biz_flag_record`;
CREATE TABLE `biz_flag_record` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `pole_no` INT NOT NULL DEFAULT 1 COMMENT '旗杆编号(1=主旗杆, 2=左旗杆, 3=右旗杆)',
  `audio_id` BIGINT UNSIGNED NOT NULL COMMENT '关联biz_audio_library ID',
  `audio_name` VARCHAR(128) NOT NULL,
  `duration_ms` INT NOT NULL COMMENT '音频总毫秒',
  `target_height_m` DECIMAL(5,2) NOT NULL DEFAULT 12.00 COMMENT '上升总高度(米)',
  `calculated_speed` DECIMAL(6,4) NOT NULL COMMENT '智能计算上升速度(m/s)',
  `start_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_time` DATETIME DEFAULT NULL,
  `is_estop` TINYINT NOT NULL DEFAULT 0 COMMENT '是否触发紧急停止: 1=是, 0=否',
  `exec_status` VARCHAR(32) NOT NULL DEFAULT 'COMPLETED' COMMENT 'RUNNING/COMPLETED/ESTOPPED/FAILED',
  `operator_name` VARCHAR(64) NOT NULL,
  `device_receipt` VARCHAR(255) DEFAULT 'PLC_ACK_OK',
  PRIMARY KEY (`id`),
  KEY `idx_start_time` (`start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动升旗动作执行与音画同步记录表';

-- 赛事计时计分成绩记录表
DROP TABLE IF EXISTS `biz_match_score_record`;
CREATE TABLE `biz_match_score_record` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `event_name` VARCHAR(128) NOT NULL COMMENT '比赛项目(如: 男子100米自由泳决赛)',
  `lane_no` INT NOT NULL COMMENT '泳道号/跑道号',
  `athlete_name` VARCHAR(64) NOT NULL COMMENT '运动员姓名',
  `team_name` VARCHAR(64) NOT NULL COMMENT '代表队/国家',
  `split_time` VARCHAR(32) DEFAULT '' COMMENT '分段计时',
  `final_result` VARCHAR(32) NOT NULL COMMENT '最终完赛成绩(如: 47.85s)',
  `rank_no` INT NOT NULL COMMENT '名次(1/2/3...)',
  `is_pushed_to_screen` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已推送大屏: 1=是, 0=否',
  `pushed_at` DATETIME DEFAULT NULL,
  `received_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_event_name` (`event_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='赛事成绩捕获与推屏记录表';

-- 场地照明电表能耗采样数据表
DROP TABLE IF EXISTS `biz_lighting_energy_sample`;
CREATE TABLE `biz_lighting_energy_sample` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `device_id` BIGINT UNSIGNED NOT NULL,
  `active_power_kw` DECIMAL(8,2) NOT NULL COMMENT '瞬时有功功率(kW)',
  `total_energy_kwh` DECIMAL(12,2) NOT NULL COMMENT '累计耗电量(kWh)',
  `sample_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_device_sample` (`device_id`, `sample_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='场地照明能耗历史采样表';

-- ------------------------------------------------------------------------------
-- 5.1 用户专属外部集成与本地软件管理域 (支柱二)
-- ------------------------------------------------------------------------------

-- 用户专属外部集成软件表 (支持 B/S, C/S, 未知类型，用户间完全隔离)
DROP TABLE IF EXISTS `sys_user_external_app`;
CREATE TABLE `sys_user_external_app` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '集成软件ID',
  `username` VARCHAR(64) NOT NULL COMMENT '所属用户名(多用户独立可见)',
  `app_name` VARCHAR(128) NOT NULL COMMENT '软件系统名称',
  `app_type` VARCHAR(32) NOT NULL DEFAULT 'BS' COMMENT '架构类型: BS(B/S网页系统), CS(C/S桌面软件), UNKNOWN(未知/脚本工具)',
  `target_path` VARCHAR(512) NOT NULL COMMENT '访问地址或本地安装可执行路径 (如 D:\\antigravity\\Antigravity IDE 或 http://...)',
  `start_args` VARCHAR(255) DEFAULT '' COMMENT '启动参数/附加参数',
  `app_desc` VARCHAR(255) DEFAULT '' COMMENT '功能描述与用途备注',
  `auth_username` VARCHAR(64) DEFAULT '' COMMENT '登录账号(选填)',
  `auth_password` VARCHAR(255) DEFAULT '' COMMENT '登录密码(选填/凭据备注)',
  `icon_type` VARCHAR(16) NOT NULL DEFAULT 'PRESET' COMMENT '图标类型: PRESET(内置工控图标), CUSTOM(自定义图片URL/Base64)',
  `icon` VARCHAR(64) DEFAULT 'SvgAppGrid' COMMENT '内置图标编码',
  `custom_icon_url` MEDIUMTEXT DEFAULT NULL COMMENT '自定义图标图片URL或Base64(选填)',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_type` (`username`, `app_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户专属外部集成软件管理表';

-- ------------------------------------------------------------------------------
-- 6. 配置模板与脱机沙箱 Mock 域 (支柱三)
-- ------------------------------------------------------------------------------

-- 完整系统配置模板表
DROP TABLE IF EXISTS `config_template`;
CREATE TABLE `config_template` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `template_code` VARCHAR(64) NOT NULL COMMENT '模板编码',
  `template_name` VARCHAR(128) NOT NULL COMMENT '模板名称',
  `venue_type` VARCHAR(64) NOT NULL DEFAULT 'AQUATICS_CENTER' COMMENT '场馆类型',
  `baseline_flag` TINYINT NOT NULL DEFAULT 1 COMMENT '1=附件13类基线标准模板, 0=扩展模板',
  `schema_version` VARCHAR(32) NOT NULL DEFAULT 'v1.0.0',
  `total_devices` INT NOT NULL DEFAULT 0,
  `total_buttons` INT NOT NULL DEFAULT 0,
  `config_json` MEDIUMTEXT NOT NULL COMMENT '完整导出的JSON配置报文(凭据脱敏)',
  `created_by` VARCHAR(64) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_code` (`template_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='低代码配置模板与JSON备份表';

-- 脱机沙箱 Mock 运行作用域与配置表
DROP TABLE IF EXISTS `mock_scope`;
CREATE TABLE `mock_scope` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `scope_type` VARCHAR(32) NOT NULL DEFAULT 'GLOBAL' COMMENT '作用域: GLOBAL(全局)/DEVICE(单设备)/SESSION(单会话)',
  `target_id` VARCHAR(64) DEFAULT '*' COMMENT '限定目标ID(*为全部)',
  `is_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '1=开启Mock, 0=真实硬件模式',
  `toggle_by` VARCHAR(64) NOT NULL DEFAULT 'admin',
  `toggle_reason` VARCHAR(255) DEFAULT '现场脱机联调',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通信模拟沙箱控制状态表';

-- ------------------------------------------------------------------------------
-- 初始种子模拟数据注入 (覆盖全部模块、真实感且饱满)
-- ------------------------------------------------------------------------------

-- 1. 预置系统角色
INSERT INTO `sys_role` (`id`, `role_code`, `role_name`, `role_desc`, `is_builtin`, `sort_order`, `status`) VALUES
(1, 'admin', '系统管理员', '全系统最高管理权限，可修改协议、导入导出与配置用户', 1, 1, 1),
(2, 'ops', '运维工程师', '负责设备连通性排查、告警处置、模拟沙箱及参数微调', 1, 2, 1),
(3, 'operator', '场馆操作员', '日常赛事运行、音响升旗照明大屏控制，严禁修改底层通信参数', 1, 3, 1),
(4, 'viewer', '只读查看者', '各级领导及调度坐席，仅具有仪表盘与运行状态查看权限', 1, 4, 1);

-- 2. 预置系统用户 (默认密码哈希为 bcrypt("admin123"))
INSERT INTO `sys_user` (`id`, `username`, `password_hash`, `display_name`, `avatar`, `phone`, `email`, `status`) VALUES
(1, 'admin', '$2a$10$wT8B1K9k7d/i7aQZJ1v12uC6C4rI8uA6G7M8F9xK0yO5Z6H7J8L9.', '总控管理员', '', '13800000001', 'admin@venue.com', 1),
(2, 'ops_chen', '$2a$10$wT8B1K9k7d/i7aQZJ1v12uC6C4rI8uA6G7M8F9xK0yO5Z6H7J8L9.', '陈工 (机电运维)', '', '13800000002', 'chen@venue.com', 1),
(3, 'operator_liu', '$2a$10$wT8B1K9k7d/i7aQZJ1v12uC6C4rI8uA6G7M8F9xK0yO5Z6H7J8L9.', '刘主管 (赛事音控)', '', '13800000003', 'liu@venue.com', 1),
(4, 'viewer_guest', '$2a$10$wT8B1K9k7d/i7aQZJ1v12uC6C4rI8uA6G7M8F9xK0yO5Z6H7J8L9.', '观摩坐席', '', '13800000004', 'guest@venue.com', 1);

INSERT INTO `sys_user_role` (`user_id`, `role_id`) VALUES (1, 1), (2, 2), (3, 3), (4, 4);

-- 3. 预置 13 大基线子系统
INSERT INTO `iot_subsystem` (`id`, `subsystem_code`, `subsystem_name`, `baseline_flag`, `default_protocol`, `primary_route`, `icon_code`, `description`) VALUES
(1, 'AUDIO_MATRIX', '扩声系统', 1, 'SERIAL', '/iot/audio', 'SvgSoundMatrix', '数字调音台推子控制、音源矩阵切换与场景音效'),
(2, 'LIGHTING', '场地照明及控制系统', 1, 'SERIAL', '/iot/lighting', 'SvgLighting', '赛事/训练/演播场景灯光、智能配电与实时能耗采集'),
(3, 'LED_SCREEN', 'LED大屏系统', 1, 'HTTP', '/iot/screen', 'SvgLedScreen', '多路输入信号源切换、播控状态与监视窗回显'),
(4, 'MATCH_SCORE', '计时计分及现场成绩处理系统', 1, 'TCP', '/iot/score', 'SvgMatchScore', '实时捕获比赛成绩、道次用时与自动/一键推屏'),
(5, 'TICKETING', '售验票系统', 1, 'HTTP', '/portal/app/ticketing', 'SvgPortal', '门禁闸机核验、票务出验票API与降级iframe内嵌'),
(6, 'STANDARD_CLOCK', '标准时钟系统', 1, 'TCP', '/iot/clock', 'SvgMasterClock', '北斗/GPS卫星双模授时、毫秒比对与全场子钟网络'),
(7, 'FLAG_SYSTEM', '自动升旗控制系统', 1, 'SERIAL', '/iot/flag', 'SvgFlagSystem', '国歌音画同步智能测速、高精度上升与立即急停'),
(8, 'FIELD_VIDEO', '现场影像采集回放系统', 1, 'RTSP', '/iot/video', 'SvgCameraMatrix', '比赛现场全景摄像机、录像回放与画面抓拍'),
(9, 'UNDERWATER_VISION', '水下影像采集识别系统', 1, 'RTSP', '/iot/video', 'SvgCameraMatrix', '游泳跳水特种水下高速摄像机与裁判辅助视窗'),
(10, 'TV_BROADCAST', '电视转播系统', 1, 'LOCAL_EXE', '/iot/video', 'SvgCameraMatrix', '广电级SDI/HDMI信号采集源与转播画面监视'),
(11, 'INFO_PUBLISH', '信息发布系统', 1, 'HTTP', '/portal/app/info_publish', 'SvgPortal', '大厅导视屏、公共多媒体终端赛程节目单推送'),
(12, 'AUDIO_PLAYBACK', '音频播放服务', 1, 'HTTP', '/iot/media', 'SvgMediaPlayer', '高保真国歌、颁奖进行曲与环境背景音乐播控'),
(13, 'VIDEO_PLAYBACK', '视频播放服务', 1, 'HTTP', '/iot/media', 'SvgMediaPlayer', '赛事宣传片、回放视频多路大屏定向投屏');

-- 4. 预置典型异构设备实例
INSERT INTO `iot_device_instance` (`id`, `device_code`, `device_name`, `subsystem_id`, `manufacturer`, `model_name`, `install_location`, `connection_type`, `online_status`, `heartbeat_period`, `last_seen_at`) VALUES
(1, 'DEV_AUDIO_01', '比赛大厅主调音台 (Soundcraft)', 1, 'Soundcraft', 'Vi3000-RS232', '总控声控室', 'SERIAL', 'ONLINE', 3, NOW()),
(2, 'DEV_LIGHT_01', '场地比赛照明主控制器', 2, 'Lutron', 'Quantum-Hub', '高压配电机房', 'SERIAL', 'ONLINE', 5, NOW()),
(3, 'DEV_SCREEN_01', '东侧中央主LED大屏拼接器', 3, 'Novastar', 'NovaPro-UHD', '大屏控制机柜', 'HTTP', 'ONLINE', 2, NOW()),
(4, 'DEV_SCORE_01', '游泳跳水主计时计分机', 4, 'Omega', 'ARES21-LAN', '裁判长总席', 'TCP', 'ONLINE', 1, NOW()),
(5, 'DEV_CLOCK_01', '北斗/GPS标准授时主母钟', 6, 'TimeMaster', 'TS-9000-NTP', '弱电核心机房', 'TCP', 'ONLINE', 5, NOW()),
(6, 'DEV_FLAG_01', '自动升旗PLC主控制电机', 7, 'Siemens', 'S7-1200-RS485', '主席台升旗基座', 'SERIAL', 'ONLINE', 2, NOW()),
(7, 'DEV_CAM_FIELD_01', '比赛泳池50米主看台全景枪机', 8, 'Hikvision', 'DS-2CD-8K', '主看台顶部', 'RTSP', 'ONLINE', 5, NOW()),
(8, 'DEV_CAM_UW_01', '4号跳台深水池水下抓拍摄像机', 9, 'SubC', 'AquaCam-4K', '跳水池南侧水下视窗', 'RTSP', 'ONLINE', 5, NOW()),
(9, 'DEV_MEDIA_SRV_01', '场馆多媒体综合播控服务器', 12, 'Advantech', 'IPC-610', '媒体播控中心', 'HTTP', 'ONLINE', 3, NOW());

-- 5. 预置设备协议参数
INSERT INTO `iot_protocol_profile` (`id`, `device_id`, `protocol_type`, `serial_port`, `baud_rate`, `data_bits`, `stop_bits`, `parity`, `target_ip`, `target_port`, `timeout_ms`, `payload_format`, `checksum_type`) VALUES
(1, 1, 'SERIAL', 'COM3', 115200, 8, '1', 'NONE', '', 0, 300, 'HEX', 'CRC16'),
(2, 2, 'SERIAL', 'COM1', 9600, 8, '1', 'NONE', '', 0, 500, 'HEX', 'CRC16'),
(3, 3, 'HTTP', '', 0, 8, '1', 'NONE', '192.168.10.88', 8080, 1000, 'JSON', 'NONE'),
(4, 4, 'TCP', '', 0, 8, '1', 'NONE', '192.168.10.99', 5000, 500, 'ASCII', 'NONE'),
(5, 5, 'TCP', '', 0, 8, '1', 'NONE', '192.168.10.100', 1230, 800, 'HEX', 'CRC16'),
(6, 6, 'SERIAL', 'COM2', 19200, 8, '1', 'EVEN', '', 0, 200, 'HEX', 'LRC');

-- 6. 预置全场子钟明细
INSERT INTO `iot_sub_clock` (`id`, `master_device_id`, `clock_code`, `clock_type`, `install_area`, `ip_address`, `run_status`, `drift_ms`, `fault_reason`) VALUES
(1, 5, 'CLK-EAST-01', 'DOUBLE_SIDED', '东侧比赛大厅看台', '192.168.10.101', 'NORMAL', 2, ''),
(2, 5, 'CLK-WEST-02', 'DOUBLE_SIDED', '西侧贵宾主席台', '192.168.10.102', 'NORMAL', 5, ''),
(3, 5, 'CLK-JUDGE-03', 'DIGITAL_LED', '裁判长与仲裁席', '192.168.10.103', 'NORMAL', 1, ''),
(4, 5, 'CLK-WARMUP-04', 'SINGLE_SIDED', '地下运动员热身馆', '192.168.10.104', 'NORMAL', 8, ''),
(5, 5, 'CLK-MEDIA-05', 'SINGLE_SIDED', '新闻媒体发布厅', '192.168.10.105', 'NORMAL', 3, ''),
(6, 5, 'CLK-HALL-06', 'DIGITAL_LED', '南侧观众安检入场大厅', '192.168.10.106', 'FAULT', 1450, '时钟晶振漂移过大需校准');

-- 7. 预置音频素材库
INSERT INTO `biz_audio_library` (`id`, `audio_name`, `category`, `file_path`, `file_hash`, `duration_ms`, `sample_rate`, `file_size_bytes`, `ref_count`) VALUES
(1, '中华人民共和国国歌 (标准管乐演奏版)', 'ANTHEM', '/assets/audio/march_of_the_volunteers.mp3', 'a1b2c3d4e5f6001', 46000, 48000, 2200000, 2),
(2, '奥运颁奖进行曲 (加冕仪式专用)', 'AWARD', '/assets/audio/olympic_award_march.mp3', 'a1b2c3d4e5f6002', 180000, 48000, 8600000, 1),
(3, '运动健儿进行曲 (运动员入场)', 'CEREMONY', '/assets/audio/sportsman_entry.mp3', 'a1b2c3d4e5f6003', 240000, 44100, 11400000, 0),
(4, '场馆环境轻音乐 (间歇舒缓氛围)', 'BGM', '/assets/audio/ambient_warmup.mp3', 'a1b2c3d4e5f6004', 320000, 44100, 15300000, 1);

-- 8. 预置近期告警记录
INSERT INTO `alarm_event` (`id`, `event_no`, `subsystem_code`, `device_id`, `device_name`, `alarm_level`, `alarm_title`, `alarm_content`, `alarm_status`, `first_occurred_at`) VALUES
(1, 'ALM-20261011-001', 'STANDARD_CLOCK', 5, '标准时钟子钟 CLK-HALL-06', 'WARNING', '观众大厅子钟时间漂移过大', '检测到观众大厅数码子钟时间漂移达1450ms，超过阈值500ms', 'CONFIRMED', DATE_SUB(NOW(), INTERVAL 25 MINUTE)),
(2, 'ALM-20261011-002', 'LIGHTING', 2, '场地比赛照明主控制器', 'WARNING', '配电箱回路B3过流波动', '训练模式切换时瞬时电流出现微幅突变，已自愈稳定', 'RECOVERED', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(3, 'ALM-20261011-003', 'FIELD_VIDEO', 7, '全景摄像机 CAM-FIELD-01', 'INFO', 'RTSP码流重连提示', '交换机端口抖动触发自愈重拉流机制，耗时1.2s恢复', 'CLOSED', DATE_SUB(NOW(), INTERVAL 5 HOUR));

-- 9. 预置最新赛事成绩
INSERT INTO `biz_match_score_record` (`id`, `event_name`, `lane_no`, `athlete_name`, `team_name`, `split_time`, `final_result`, `rank_no`, `is_pushed_to_screen`, `pushed_at`) VALUES
(1, '男子 100米自由泳 决赛', 4, '潘展乐', '中国 (CHN)', '22.80s / 46.80s', '46.80s', 1, 1, NOW()),
(2, '男子 100米自由泳 决赛', 5, '波波维奇', '罗马尼亚 (ROU)', '23.05s / 46.90s', '46.90s', 2, 1, NOW()),
(3, '男子 100米自由泳 决赛', 3, '查默斯', '澳大利亚 (AUS)', '23.12s / 47.48s', '47.48s', 3, 1, NOW()),
(4, '男子 100米自由泳 决赛', 6, '阿列克西', '法国 (FRA)', '23.30s / 47.62s', '47.62s', 4, 0, NULL),
(5, '男子 100米自由泳 决赛', 2, '涅梅特', '匈牙利 (HUN)', '23.45s / 47.89s', '47.89s', 5, 0, NULL);

-- 10. 预置 Mock 沙箱默认状态
INSERT INTO `mock_scope` (`id`, `scope_type`, `target_id`, `is_enabled`, `toggle_by`, `toggle_reason`) VALUES
(1, 'GLOBAL', '*', 0, 'admin', '初始化系统为正常真实硬件运行模式');

-- 11. 预置系统菜单与路由导航完整数据 (全量带统一 4 字规范缩写别名 short_name)
INSERT INTO `sys_menu` (`id`, `menu_code`, `parent_id`, `menu_name`, `short_name`, `route_name`, `route_path`, `component_name`, `icon_code`, `sort_order`, `terminal_scope`, `baseline_flag`, `dynamic_flag`, `permission_code`, `status`) VALUES
-- 【一级主分类导航 (5大主模块，均严格统一定义4字规范别名)】
(1, 'MOD_DASHBOARD', 0, '综合态势', '综合态势', '', '/dashboard', '', 'SvgDashboard', 1, 'PC', 1, 0, '', 1),
(2, 'MOD_PORTAL', 0, '应用门户', '应用门户', '', '/portal', '', 'SvgPortal', 2, 'PC', 1, 0, '', 1),
(3, 'MOD_IOT', 0, '物联控制', '物联控制', '', '/iot', '', 'SvgIotControl', 3, 'PC', 1, 0, '', 1),
(4, 'MOD_CONFIG', 0, '配置中心', '配置中心', '', '/config', '', 'SvgLowCodeConfig', 4, 'PC', 1, 0, '', 1),
(5, 'MOD_OPS', 0, '运维安全', '运维安全', '', '/ops', '', 'SvgSecurityShield', 5, 'PC', 1, 0, '', 1),

-- 【二级业务菜单：1. 综合态势】
(101, 'MENU_DASHBOARD_OVERVIEW', 1, '场馆综合态势总览工作台', '态势总览', 'Dashboard', '/dashboard', 'DashboardOverview.vue', 'SvgDashboard', 1, 'PC', 1, 0, 'view:dashboard', 1),

-- 【二级业务菜单：2. 应用门户】
(201, 'MENU_PORTAL_NAV', 2, '场馆应用与网站聚合导航大厅', '应用导航', 'PortalNav', '/portal/nav', 'PortalNavGrid.vue', 'SvgAppGrid', 1, 'PC', 1, 0, 'portal:nav:view', 1),
(202, 'MENU_PORTAL_EXTERNAL', 2, '外部系统与本地软件集成中心', '外部集成', 'ExternalIntegration', '/portal/external', 'ExternalIntegrationView.vue', 'SvgIframeApp', 2, 'PC', 1, 0, 'portal:external:view', 1),

-- 【二级业务菜单：3. 物联控制】
(301, 'MENU_IOT_AUDIO', 3, '扩声调音与场景音效控制台', '专业扩声', 'AudioMatrixControl', '/iot/audio', 'AudioMatrixControl.vue', 'SvgSoundMatrix', 1, 'PC', 1, 0, 'iot:audio:control', 1),
(302, 'MENU_IOT_LIGHTING', 3, '场地照明场景与能耗监测台', '场地照明', 'LightingEnergyControl', '/iot/lighting', 'LightingEnergyControl.vue', 'SvgLighting', 2, 'PC', 1, 0, 'iot:lighting:control', 1),
(303, 'MENU_IOT_SCREEN', 3, 'LED大屏与推屏调度控制台', '大屏调度', 'ScreenScoreControl', '/iot/screen', 'ScreenScoreControl.vue', 'SvgLedScreen', 3, 'PC', 1, 0, 'iot:screen:control', 1),
(304, 'MENU_IOT_SCORE', 3, '赛事计时计分接收与大屏推屏', '计时计分', 'MatchScoreBoard', '/iot/score', 'MatchScoreBoard.vue', 'SvgMatchScore', 4, 'PC', 1, 0, 'iot:score:control', 1),
(305, 'MENU_IOT_FLAG', 3, '自动升旗仪式与音画同步仿真台', '智能升旗', 'FlagAutoControl', '/iot/flag', 'FlagAutoControl.vue', 'SvgFlagSystem', 5, 'PC', 1, 0, 'iot:flag:control', 1),
(306, 'MENU_IOT_CLOCK', 3, '标准时钟卫星授时与子钟监测台', '时钟同步', 'ClockSyncMonitor', '/iot/clock', 'ClockSyncMonitor.vue', 'SvgMasterClock', 6, 'PC', 1, 0, 'iot:clock:view', 1),
(307, 'MENU_IOT_VIDEO', 3, '现场水下监控与转播监视台', '视频监控', 'VideoLiveMatrix', '/iot/video', 'VideoLiveMatrix.vue', 'SvgCameraMatrix', 7, 'PC', 1, 0, 'iot:video:view', 1),
(308, 'MENU_IOT_MEDIA', 3, '媒体播控台(背景音乐与视频投屏)', '媒体播控', 'MediaPlayConsole', '/iot/media', 'MediaPlayConsole.vue', 'SvgMediaPlayer', 8, 'PC', 1, 0, 'iot:media:control', 1),
(309, 'MENU_IOT_DYNAMIC', 3, '动态低代码通用设备控制台', '动态设备', 'DynamicDeviceConsole', '/iot/dynamic/:groupId', 'DynamicDeviceConsole.vue', 'SvgDynamicDevice', 9, 'PC', 1, 1, 'iot:dynamic:control', 1),

-- 【二级业务菜单：4. 配置中心】
(401, 'MENU_CONFIG_DEVICES', 4, '异构设备与全协议通信配置中心', '设备配置', 'DeviceConfigCenter', '/config/devices', 'DeviceConfigCenter.vue', 'SvgDeviceSetting', 1, 'PC', 1, 0, 'config:devices:manage', 1),
(402, 'MENU_CONFIG_ACTIONS', 4, '菜单分组与自定义操作按钮配置', '动作编排', 'ActionDynamicConfig', '/config/actions', 'ActionDynamicConfig.vue', 'SvgButtonAction', 2, 'PC', 1, 0, 'config:actions:manage', 1),
(403, 'MENU_CONFIG_ADAPTERS', 4, '外置硬件适配与接线登记台账', '硬件适配', 'HardwareAdapterBook', '/config/adapters', 'HardwareAdapterBook.vue', 'SvgAdapterBook', 3, 'PC', 1, 0, 'config:adapters:manage', 1),
(404, 'MENU_CONFIG_MEDIA', 4, '音频与视频媒体素材资源库', '媒体素材', 'MediaResourceLibrary', '/config/media', 'MediaResourceLibrary.vue', 'SvgMediaLibrary', 4, 'PC', 1, 0, 'config:media:manage', 1),
(405, 'MENU_CONFIG_TEMPLATES', 4, '配置模板与JSON导入导出中心', '配置模板', 'ConfigTemplateCenter', '/config/templates', 'ConfigTemplateCenter.vue', 'SvgConfigTemplate', 5, 'PC', 1, 0, 'config:templates:manage', 1),
(406, 'MENU_CONFIG_SANDBOX', 4, '通信沙箱与模拟调试控制台', '协议沙箱', 'ProtocolMockSandbox', '/config/sandbox', 'ProtocolMockSandbox.vue', 'SvgMockSandbox', 6, 'PC', 1, 0, 'config:sandbox:manage', 1),
(407, 'MENU_SYS_SETTINGS', 4, '平台系统设置与对象存储中心', '系统设置', 'SystemSetting', '/system/settings', 'SystemSetting.vue', 'SvgSettingGear', 7, 'PC', 1, 0, 'sys:settings:manage', 1),

-- 【二级业务菜单：5. 运维安全】
(501, 'MENU_OPS_ALARMS', 5, '全链路保活监控与实时告警中心', '链路告警', 'AlarmMonitorCenter', '/ops/alarms', 'AlarmMonitorCenter.vue', 'SvgAlarmBell', 1, 'PC', 1, 0, 'ops:alarms:view', 1),
(502, 'MENU_OPS_CHANNELS', 5, '告警规则与通知渠道配置中心', '告警通道', 'AlarmChannelConfig', '/ops/channels', 'AlarmChannelConfig.vue', 'SvgNotifyChannel', 2, 'PC', 1, 0, 'ops:channels:manage', 1),
(503, 'MENU_OPS_AUDIT', 5, '操作审计日志与导出留存中心', '审计日志', 'AuditLogManager', '/ops/audit', 'AuditLogManager.vue', 'SvgAuditLog', 3, 'PC', 1, 0, 'ops:audit:view', 1),
(504, 'MENU_SYS_USERS', 5, '用户角色管理与细粒度权限配置', '角色权限', 'UserRolePermission', '/system/users', 'UserRolePermission.vue', 'SvgUserRole', 4, 'PC', 1, 0, 'sys:users:manage', 1),

-- 【专属终端与公开路由节点】
(601, 'MENU_TABLET_OPERATIONS', 0, '移动平板现场操作横屏工作台', '平板控制', 'TabletControl', '/tablet/control', 'TabletOperationsView.vue', 'SvgTablet', 99, 'TABLET', 1, 0, 'tablet:operations:view', 1),
(701, 'MENU_AUTH_LOGIN', 0, '统一身份认证登录页', '身份认证', 'Login', '/login', 'LoginPage.vue', 'SvgPortal', 0, 'ALL', 1, 0, '', 1);

-- 12. 预置用户专属外部集成软件 (多用户物理隔离示例数据)
INSERT INTO `sys_user_external_app` (`id`, `username`, `app_name`, `app_type`, `target_path`, `start_args`, `app_desc`, `auth_username`, `auth_password`, `icon_type`, `icon`, `custom_icon_url`, `sort_order`, `status`) VALUES
(1, 'admin', 'Antigravity IDE 智能开发环境', 'CS', 'D:\\antigravity\\Antigravity IDE\\antigravity.exe', '--portable', '场馆工控协议自动化二次开发与调测环境', 'admin', 'dev@2026', 'PRESET', 'SvgDynamicDevice', '', 1, 1),
(2, 'admin', '票务检票闸机综合管控后台', 'BS', 'http://192.168.1.88:8080/ticketing/gate', '', '东区与南区观众安检通道智能闸机核销控制系统', 'gate_admin', 'TicketPass#88', 'PRESET', 'SvgAppGrid', '', 2, 1),
(3, 'admin', 'Novastar NovaLCT 屏幕配置工具', 'CS', 'C:\\Program Files\\Novastar\\NovaLCT\\NovaLCT.exe', '', '全彩主大屏箱体映射、灰度校准与多路网口发送卡配置端', '', '', 'PRESET', 'SvgLedScreen', '', 3, 1),
(4, 'admin', 'PLC 备用电源自动化巡检脚本', 'UNKNOWN', 'D:\\scripts\\plc_battery_check.bat', '--fast-check', '双回路UPS与柴油发电机状态探针诊断批处理', '', '', 'PRESET', 'SvgDeviceSetting', '', 4, 1),
(5, 'operator', 'ARES-21 赛事计时计分现场终端', 'CS', 'C:\\Program Files\\Ares21\\Client\\ares21.exe', '--event=swimming', '游泳跳水大项终点触板与发令台脉冲接收工作站', 'op_timing', 'Timing@2026', 'PRESET', 'SvgMatchScore', '', 1, 1),
(6, 'operator', '场馆公共广播与背景音乐播放系统', 'BS', 'http://192.168.1.66:8888/broadcasting', '', '看台与热身池分区分区音频广播Web客户端', 'audio_op', 'Broadcast#99', 'PRESET', 'SvgSoundMatrix', '', 2, 1);

-- 13. 预置系统基础设置与存储配置
INSERT INTO `sys_setting` (`setting_key`, `setting_value`, `setting_category`, `setting_desc`, `is_public`, `updated_by`) VALUES
('system_name', '体育场馆应用集成管控平台', 'SYSTEM', '平台系统全称', 1, 'admin'),
('version', 'v1.0.0', 'SYSTEM', '系统版本号', 1, 'admin'),
('system_logo', '', 'SYSTEM', '系统自定义Logo Base64/URL', 1, 'admin'),
('system_logo_preset', 'SvgSettingGear', 'SYSTEM', '系统预设内置图标名', 1, 'admin'),
('copyright_text', '© 2026 体育场馆集成管控中心 保留所有权利', 'COPYRIGHT', '版权声明正文', 1, 'admin'),
('copyright_owner', '国家奥林匹克体育中心 / 智慧场馆运营保障联合指挥部', 'COPYRIGHT', '版权所属单位', 1, 'admin'),
('copyright_year', '2026', 'COPYRIGHT', '版权声明年份', 1, 'admin'),
('icp_license', '京ICP备20268888号-1', 'COPYRIGHT', '工信部ICP备案号', 1, 'admin'),
('security_record', '京公网安备 11010502030110号', 'COPYRIGHT', '公安机关互联网站备案号', 1, 'admin'),
('commercial_license', 'SP2026-STAD-09921', 'COPYRIGHT', '商业运营许可或特许资质编号', 1, 'admin'),
('storage_driver', 'LOCAL', 'STORAGE', '存储驱动方式: LOCAL(本地存储) / OSS(阿里云OSS对象存储)', 1, 'admin'),
('local_storage_config', '{"baseDir":"/data/ibms/uploads","urlPrefix":"/uploads/","maxFileSizeMb":50,"allowedExtensions":["jpg","jpeg","png","gif","svg","mp3","wav","mp4","pdf","json","xlsx"]}', 'STORAGE', '本地文件存储配置详情', 1, 'admin'),
('oss_storage_config', '{"provider":"ALIYUN","endpoint":"oss-cn-beijing.aliyuncs.com","bucketName":"olympic-stadium-ibms","accessKeyId":"LTAI5t********K6Wz","accessKeySecret":"w8Kz9x********9B2e","cdnDomain":"https://cdn.olympic-stadium.cn","basePath":"ibms/attachments/","aclPolicy":"public-read"}', 'STORAGE', 'OSS对象存储配置详情', 0, 'admin');

-- 14. 预置媒体资源分类、业务分组与核心资产库初始数据
INSERT INTO `biz_media_category` (`id`, `category_code`, `category_name`, `icon_code`, `is_builtin`, `sort_order`, `description`) VALUES
(1, 'audio', '音频', 'SvgSoundMatrix', 1, 1, '赛事国歌、仪式颁奖乐、背景音乐与广播音频'),
(2, 'video', '视频', 'SvgMediaPlayer', 1, 2, '场馆官方宣传片、赛事精彩集锦与推屏视频'),
(3, 'document', '文件', 'SvgConfigTemplate', 1, 3, '国旗标准规程、竞赛方案、应急预案与技术文档'),
(4, 'other', '其他', 'SvgAppGrid', 1, 4, '场馆SVG徽标、全景漫游包与综合附件资源');

INSERT INTO `biz_media_group` (`id`, `group_code`, `group_name`, `is_builtin`, `sort_order`, `description`) VALUES
(1, 'anthem', '国歌', 1, 1, '用于自动升旗、仪式典礼奏唱的标准权威国歌音视频'),
(2, 'flag', '国旗', 1, 2, '用于升旗仪式仿真、大屏展示的国旗国徽高清矢量文件与规范'),
(3, 'promo', '宣传片', 1, 3, '用于全彩主大屏、观众大厅导视屏轮播展播的形象片与广告片'),
(4, 'other', '其他', 1, 4, '综合备用音源、临时推流物料与通用辅助素材文件');

INSERT INTO `biz_media_asset` (`id`, `asset_name`, `category_code`, `group_code`, `file_type`, `file_size_bytes`, `file_size_formatted`, `duration_sec`, `duration_formatted`, `resolution`, `file_hash`, `storage_driver`, `storage_bucket`, `storage_path`, `access_url`, `ref_count`, `remark`, `created_by`, `created_at`) VALUES
(2, '国际奥委会会歌 (奥林匹克颂歌交响版)', 'audio', 'anthem', 'mp3', 5359743, '5.11 MB', 223, '03:43', '44.1kHz 立体声 (192kbps)', '5b77fa9ecc7314a70c66b37027dcf6d5b74d3957e7c137736092ba484a47ab17', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/audio/olympic_hymn_full.mp3', 'http://192.168.1.100:3001/uploads/audio/olympic_hymn_full.mp3', 1, '公有领域录音（Wikimedia Commons《Olympic Anthem》，Spyridon Samaras 作曲），适用于开闭幕式与颁奖典礼奏唱', 'admin', '2026-10-18 10:15:00'),
(6, '重大赛事国旗升降标准技术规程与尺寸规范', 'document', 'flag', 'pdf', 3200000, '3.05 MB', 0, '-', '共 18 页 / PDF A4', '8f434346648f6b96df89dda901c5176b10e6d0ceec3e6a81e2dd4f04760417b8', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/document/flag_ceremony_manual_2026.pdf', 'http://192.168.1.100:3001/uploads/document/flag_ceremony_manual_2026.pdf', 0, '体育总局标准升旗仪式流程与旗手协同作业指南', 'admin', '2026-10-20 15:45:00'),
(7, '颁奖仪式仪仗进行曲 (国家象征·铜管乐版)', 'audio', 'other', 'mp3', 4623008, '4.41 MB', 182, '03:02', '44.1kHz 立体声 (203kbps)', 'cddc80a0087fd49840194547bc7fef7e261c9eca8b0ea5ff6dd1edc9a7646cdc', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/audio/award_ceremony_march.mp3', 'http://192.168.1.100:3001/uploads/audio/award_ceremony_march.mp3', 1, '公有领域录音（Wikimedia Commons《National Emblem》，美国空军仪仗队演奏），用于颁奖加冕环节', 'admin', '2026-10-21 08:30:00'),
(8, '场馆重大赛事弱电及音视频应急广播保障方案', 'document', 'other', 'pdf', 4250000, '4.05 MB', 0, '-', '共 26 页 / PDF A4', 'd7a8fbb307d7809469ca933b02d8cf5ff2a62300deb8d4a459c07978ac2f788a', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/document/emergency_broadcast_sop.pdf', 'http://192.168.1.100:3001/uploads/document/emergency_broadcast_sop.pdf', 0, '突发火情/强电故障时公共广播系统一键强切调度预案', 'admin', '2026-10-21 09:10:00');

SET FOREIGN_KEY_CHECKS = 1;

