-- ==============================================================================
-- 数据库增量升级补丁：媒体与数字资产分类、业务分组及存储驱动扩展
-- 目标版本：v1.2.0
-- 说明：新增 biz_media_category (分类字典表)、biz_media_group (分组字典表)
--       新增 biz_media_asset (资产核心总表，含 LOCAL / ALIYUN / TENCENT 存储驱动字段)
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 创建资源分类字典表 (默认: 音频、视频、文件、其他)
CREATE TABLE IF NOT EXISTS `biz_media_category` (
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

-- 2. 创建资源业务分组字典表 (默认: 国歌、国旗、宣传片、其他)
CREATE TABLE IF NOT EXISTS `biz_media_group` (
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

-- 3. 创建全分类全分组数字资产总表
CREATE TABLE IF NOT EXISTS `biz_media_asset` (
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

-- 4. 插入默认分类数据 (若已存在则忽略)
INSERT IGNORE INTO `biz_media_category` (`id`, `category_code`, `category_name`, `icon_code`, `is_builtin`, `sort_order`, `description`) VALUES
(1, 'audio', '音频', 'SvgSoundMatrix', 1, 1, '赛事国歌、仪式颁奖乐、背景音乐与广播音频'),
(2, 'video', '视频', 'SvgMediaPlayer', 1, 2, '场馆官方宣传片、赛事精彩集锦与推屏视频'),
(3, 'document', '文件', 'SvgConfigTemplate', 1, 3, '国旗标准规程、竞赛方案、应急预案与技术文档'),
(4, 'other', '其他', 'SvgAppGrid', 1, 4, '场馆SVG徽标、全景漫游包与综合附件资源');

-- 5. 插入默认分组数据 (若已存在则忽略)
INSERT IGNORE INTO `biz_media_group` (`id`, `group_code`, `group_name`, `is_builtin`, `sort_order`, `description`) VALUES
(1, 'anthem', '国歌', 1, 1, '用于自动升旗、仪式典礼奏唱的标准权威国歌音视频'),
(2, 'flag', '国旗', 1, 2, '用于升旗仪式仿真、大屏展示的国旗国徽高清矢量文件与规范'),
(3, 'promo', '宣传片', 1, 3, '用于全彩主大屏、观众大厅导视屏轮播展播的形象片与广告片'),
(4, 'other', '其他', 1, 4, '综合备用音源、临时推流物料与通用辅助素材文件');

-- 6. 插入初始素材资产基础数据
INSERT IGNORE INTO `biz_media_asset` (`id`, `asset_name`, `category_code`, `group_code`, `file_type`, `file_size_bytes`, `file_size_formatted`, `duration_sec`, `duration_formatted`, `resolution`, `file_hash`, `storage_driver`, `storage_bucket`, `storage_path`, `access_url`, `ref_count`, `remark`, `created_by`, `created_at`) VALUES
(2, '国际奥委会会歌 (奥林匹克颂歌交响版)', 'audio', 'anthem', 'mp3', 5359743, '5.11 MB', 223, '03:43', '44.1kHz 立体声 (192kbps)', '5b77fa9ecc7314a70c66b37027dcf6d5b74d3957e7c137736092ba484a47ab17', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/audio/olympic_hymn_full.mp3', 'http://192.168.1.100:3001/uploads/audio/olympic_hymn_full.mp3', 1, '公有领域录音（Wikimedia Commons《Olympic Anthem》，Spyridon Samaras 作曲），适用于开闭幕式与颁奖典礼奏唱', 'admin', '2026-10-18 10:15:00'),
(6, '重大赛事国旗升降标准技术规程与尺寸规范', 'document', 'flag', 'pdf', 3200000, '3.05 MB', 0, '-', '共 18 页 / PDF A4', '8f434346648f6b96df89dda901c5176b10e6d0ceec3e6a81e2dd4f04760417b8', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/document/flag_ceremony_manual_2026.pdf', 'http://192.168.1.100:3001/uploads/document/flag_ceremony_manual_2026.pdf', 0, '体育总局标准升旗仪式流程与旗手协同作业指南', 'admin', '2026-10-20 15:45:00'),
(7, '颁奖仪式仪仗进行曲 (国家象征·铜管乐版)', 'audio', 'other', 'mp3', 4623008, '4.41 MB', 182, '03:02', '44.1kHz 立体声 (203kbps)', 'cddc80a0087fd49840194547bc7fef7e261c9eca8b0ea5ff6dd1edc9a7646cdc', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/audio/award_ceremony_march.mp3', 'http://192.168.1.100:3001/uploads/audio/award_ceremony_march.mp3', 1, '公有领域录音（Wikimedia Commons《National Emblem》，美国空军仪仗队演奏），用于颁奖加冕环节', 'admin', '2026-10-21 08:30:00'),
(8, '场馆重大赛事弱电及音视频应急广播保障方案', 'document', 'other', 'pdf', 4250000, '4.05 MB', 0, '-', '共 26 页 / PDF A4', 'd7a8fbb307d7809469ca933b02d8cf5ff2a62300deb8d4a459c07978ac2f788a', 'LOCAL', '本地工控服务器', '/data/venue-ibms/uploads/document/emergency_broadcast_sop.pdf', 'http://192.168.1.100:3001/uploads/document/emergency_broadcast_sop.pdf', 0, '突发火情/强电故障时公共广播系统一键强切调度预案', 'admin', '2026-10-21 09:10:00');

SET FOREIGN_KEY_CHECKS = 1;
