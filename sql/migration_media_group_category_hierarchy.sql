-- ==============================================================================
-- 数据库增量升级补丁：媒体资源分组层级化 (分组隶属于分类) + 级联删除语义
-- 目标版本：v1.3.0
-- 说明：
--   1. biz_media_group 新增 category_code 列，分组归属于所属分类
--   2. 唯一键由 group_code 改为 (category_code, group_code)，实现"分类内分组编码唯一"
--   3. 回填历史分组所属分类，并灌入新的层级化默认分组
--   4. biz_media_asset 的 (category_code, group_code) 组合即定位到唯一分组
--   5. 语义变更：删除分组/分类为级联删除，其包含的素材一并删除
--      (应用层 mediaAssetService 已实现两步二次确认，数据库层保留引用校验由应用负责)
-- ==============================================================================

SET NAMES utf8mb4;

-- 1. biz_media_group 增加所属分类列
ALTER TABLE `biz_media_group`
  ADD COLUMN `category_code` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '所属资源分类编码(audio/video/document/other)；分组隶属于分类' AFTER `group_code`;

-- 2. 移除旧的全局唯一键 (若存在)
SET @drop_uk := (
  SELECT IF(COUNT(*) > 0,
    'ALTER TABLE `biz_media_group` DROP INDEX `uk_group_code`',
    'DO 0')
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'biz_media_group'
    AND INDEX_NAME = 'uk_group_code'
);
PREPARE stmt_drop_uk FROM @drop_uk;
EXECUTE stmt_drop_uk;
DEALLOCATE PREPARE stmt_drop_uk;

-- 3. 新增分类内联合唯一键
ALTER TABLE `biz_media_group`
  ADD UNIQUE KEY `uk_cat_grp_code` (`category_code`, `group_code`);

-- 4. 按素材实际引用回填历史分组的所属分类
--    同一旧分组若被多个分类引用，则在每个分类下各生成一份
UPDATE `biz_media_group` g
JOIN (
  SELECT DISTINCT `group_code`, `category_code`
  FROM `biz_media_asset`
) a
  ON a.`group_code` = g.`group_code`
SET g.`category_code` = a.`category_code`
WHERE g.`category_code` = '';

-- 5. 未能匹配到素材引用的历史分组，统一归入「其他」分类
UPDATE `biz_media_group`
SET `category_code` = 'other'
WHERE `category_code` = '';

-- 6. 灌入层级化默认分组 (INSERT IGNORE 依赖 uk_cat_grp_code 联合唯一键)
INSERT IGNORE INTO `biz_media_group` (`group_code`, `category_code`, `group_name`, `is_builtin`, `sort_order`, `description`) VALUES
-- 音频
('anthem',    'audio',    '国歌',       1, 1, '用于自动升旗、仪式典礼奏唱的标准权威音源'),
('award',     'audio',    '颁奖音乐',   1, 2, '颁奖、加冕与运动员入场仪式专用配乐'),
('bgm',       'audio',    '背景音乐',   1, 3, '场馆营业与候场时段循环播放的背景音乐'),
('other',     'audio',    '其他音频',   1, 4, '综合备用音源与临时广播物料'),
-- 视频
('promo',     'video',    '宣传片',     1, 1, '全彩主大屏、观众大厅导视屏轮播展播的形象片与广告片'),
('highlight', 'video',    '赛事集锦',   1, 2, '精彩瞬间、破纪录瞬间与慢镜头集锦'),
('guide',     'video',    '导视导播',   1, 3, '观众动线、赛程导播与安全须知短片'),
('other',     'video',    '其他视频',   1, 4, '综合备用推流物料与通用视频附件'),
-- 文件
('flag',      'document', '国旗国徽',   1, 1, '升旗仪式仿真、大屏展示的国旗国徽高清矢量文件与规范'),
('manual',    'document', '技术规程',   1, 2, '设备操作规程、尺寸规范与标准化作业标准'),
('emergency', 'document', '应急预案',   1, 3, '应急预案、处置预案与应急保障方案'),
('other',     'document', '其他文件',   1, 4, '综合附件与通用文档素材'),
-- 其他
('other',     'other',    '其他',       1, 1, '未归入具体分类的综合素材');

-- 7. 素材分组归位：按语义把旧扁平分组迁移到新的层级化分组
UPDATE `biz_media_asset` SET `group_code` = 'manual'    WHERE `id` = 6 AND `category_code` = 'document';
UPDATE `biz_media_asset` SET `group_code` = 'award'     WHERE `id` = 7 AND `category_code` = 'audio';
UPDATE `biz_media_asset` SET `group_code` = 'emergency' WHERE `id` = 8 AND `category_code` = 'document';

-- 8. 约束说明：应用层删除分组/分类时执行级联删除
--    (a) 删除分组 (category_code, group_code) => 删除 biz_media_asset 中同 (category_code, group_code) 的素材
--    (b) 删除分类 category_code               => 删除该分类下全部分组及 biz_media_asset 中该分类的全部素材
--    应用层在执行前必须完成两步二次确认，并单独提示 ref_count > 0 的素材（被升旗/推屏引用）
