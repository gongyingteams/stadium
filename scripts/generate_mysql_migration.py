import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_COUNTRIES = ROOT / "src" / "data" / "countries_197.json"
JSON_ASSETS = ROOT / "src" / "data" / "media_assets_197.json"
OUTPUT_SQL = ROOT / "sql" / "migration_add_197_countries.sql"

def escape(val):
    if val is None:
        return "NULL"
    return "'" + str(val).replace("\\", "\\\\").replace("'", "''") + "'"

def generate():
    with open(JSON_COUNTRIES, "r", encoding="utf-8") as f:
        countries = json.load(f)
    with open(JSON_ASSETS, "r", encoding="utf-8") as f:
        assets = json.load(f)

    lines = [
        "-- ==============================================================================",
        "-- 体育场馆应用集成管理系统 (IBMS) 197个主权国家与地区标准资料库及素材库升级脚本",
        "-- 包含：197国标准中英文、ISO Alpha-2、ISO Alpha-3、大洲区域、国歌、国旗、时长及素材绑定",
        "-- 对应物理文件路径：",
        "--   国旗SVG: public/uploads/flags/{CODE}.svg",
        "--   国歌MP3: public/uploads/audio/{CODE}.mp3",
        "-- ==============================================================================",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "",
        "-- 1. 国家与地区全量标准资料库表",
        "DROP TABLE IF EXISTS `biz_country`;",
        "CREATE TABLE `biz_country` (",
        "  `id` VARCHAR(16) NOT NULL COMMENT '国家代码主键(ISO Alpha-2，如 CN/US/JP)',",
        "  `code` VARCHAR(16) NOT NULL COMMENT '二字缩写 (ISO Alpha-2)',",
        "  `code_alpha3` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '三字缩写 (ISO Alpha-3 / IOC缩写)',",
        "  `name_cn` VARCHAR(128) NOT NULL COMMENT '中文规范全称或常用名',",
        "  `name_en` VARCHAR(128) NOT NULL COMMENT '英文官方国际全称',",
        "  `region` VARCHAR(32) NOT NULL DEFAULT '亚洲' COMMENT '所属大洲区域(亚洲/欧洲/非洲/北美洲/南美洲/大洋洲/其他)',",
        "  `pattern` VARCHAR(32) NOT NULL DEFAULT 'solid' COMMENT '几何国旗回退类型(cn/sun/cross/stars/tricolor/triband-h/solid)',",
        "  `c1` VARCHAR(16) NOT NULL DEFAULT '#2563EB' COMMENT '主色调1',",
        "  `c2` VARCHAR(16) NOT NULL DEFAULT '#FFFFFF' COMMENT '主色调2',",
        "  `c3` VARCHAR(16) NOT NULL DEFAULT '#0F172A' COMMENT '主色调3',",
        "  `flag_desc` VARCHAR(255) DEFAULT '' COMMENT '国旗图案规范描述',",
        "  `image_url` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '国旗标准SVG矢量图访问路径',",
        "  `flag_asset_id` VARCHAR(64) DEFAULT '' COMMENT '关联biz_media_asset国旗资源ID',",
        "  `flag_asset_name` VARCHAR(128) DEFAULT '' COMMENT '国旗素材名称',",
        "  `flag_source_type` VARCHAR(32) DEFAULT 'asset' COMMENT '素材来源类型',",
        "  `anthem_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '国歌中文名',",
        "  `anthem_en` VARCHAR(255) DEFAULT '' COMMENT '国歌原文名或英文名',",
        "  `anthem_duration` INT NOT NULL DEFAULT 46 COMMENT '标准升旗演奏时长(秒)',",
        "  `anthem_url` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '国歌MP3音频访问路径',",
        "  `anthem_asset_id` VARCHAR(64) DEFAULT '' COMMENT '关联biz_media_asset国歌资源ID',",
        "  `anthem_asset_name` VARCHAR(128) DEFAULT '' COMMENT '国歌素材名称',",
        "  `anthem_file_name` VARCHAR(128) DEFAULT '' COMMENT '原始音频文件名',",
        "  `anthem_source_type` VARCHAR(32) DEFAULT 'asset' COMMENT '国歌来源类型',",
        "  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序权重',",
        "  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',",
        "  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,",
        "  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,",
        "  PRIMARY KEY (`id`),",
        "  UNIQUE KEY `uk_country_code` (`code`),",
        "  KEY `idx_country_region` (`region`),",
        "  KEY `idx_code_alpha3` (`code_alpha3`)",
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='国家与地区全量标准资料库表';",
        "",
        "-- 2. 插入 197 个国家基础数据"
    ]

    for idx, c in enumerate(countries):
        vals = [
            escape(c["id"]),
            escape(c["code"]),
            escape(c["codeAlpha3"]),
            escape(c["nameCn"]),
            escape(c["nameEn"]),
            escape(c["region"]),
            escape(c["pattern"]),
            escape(c["c1"]),
            escape(c["c2"]),
            escape(c["c3"]),
            escape(c.get("flagDesc", "")),
            escape(c["imageUrl"]),
            escape(c["flagAssetId"]),
            escape(c["flagAssetName"]),
            escape(c.get("flagSourceType", "asset")),
            escape(c["anthemName"]),
            escape(c.get("anthemEn", "")),
            str(c["anthemDuration"]),
            escape(c["anthemUrl"]),
            escape(c["anthemAssetId"]),
            escape(c["anthemAssetName"]),
            escape(c.get("anthemFileName", "")),
            escape(c.get("anthemSourceType", "asset")),
            str(idx + 1),
            "1"
        ]
        stmt = f"INSERT INTO `biz_country` (`id`, `code`, `code_alpha3`, `name_cn`, `name_en`, `region`, `pattern`, `c1`, `c2`, `c3`, `flag_desc`, `image_url`, `flag_asset_id`, `flag_asset_name`, `flag_source_type`, `anthem_name`, `anthem_en`, `anthem_duration`, `anthem_url`, `anthem_asset_id`, `anthem_asset_name`, `anthem_file_name`, `anthem_source_type`, `sort_order`, `status`) VALUES ({', '.join(vals)});"
        lines.append(stmt)

    lines.append("")
    lines.append("-- 3. 确保媒体业务分组包含 flag (国旗) 与 anthem (国歌)")
    lines.append("INSERT IGNORE INTO `biz_media_group` (`group_code`, `category_code`, `group_name`, `is_builtin`, `sort_order`, `description`) VALUES")
    lines.append("('flag', 'document', '国旗', 1, 2, '用于升旗仪式仿真、大屏展示的国旗国徽高清矢量文件与规范'),")
    lines.append("('anthem', 'audio', '国歌', 1, 1, '用于自动升旗、仪式典礼奏唱的标准权威音源');")
    lines.append("")
    lines.append("-- 4. 灌入 197国 国旗SVG 与 国歌MP3 素材资源")

    for a in assets:
        vals = [
            escape(a["name"]),
            escape(a["categoryCode"]),
            escape(a["groupCode"]),
            escape(a["fileType"]),
            str(a["fileSizeBytes"]),
            escape(a["fileSizeFormatted"]),
            str(a["durationSec"]),
            escape(a["durationFormatted"]),
            escape(a["resolution"]),
            escape(a["fileHash"]),
            escape(a["storageDriver"]),
            escape(a["storageBucket"]),
            escape(a["storagePath"]),
            escape(a["accessUrl"]),
            str(a["refCount"]),
            escape(a["remark"]),
            escape(a["createdBy"])
        ]
        stmt = f"INSERT IGNORE INTO `biz_media_asset` (`asset_name`, `category_code`, `group_code`, `file_type`, `file_size_bytes`, `file_size_formatted`, `duration_sec`, `duration_formatted`, `resolution`, `file_hash`, `storage_driver`, `storage_bucket`, `storage_path`, `access_url`, `ref_count`, `remark`, `created_by`) VALUES ({', '.join(vals)});"
        lines.append(stmt)

    lines.append("")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("-- 升级完成")

    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Generated MySQL migration: {OUTPUT_SQL} ({len(lines)} lines)")

if __name__ == "__main__":
    generate()
