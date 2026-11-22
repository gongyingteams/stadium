import fs from 'fs';
import path from 'path';

const ISO3_MAP = {
  CN: 'CHN', JP: 'JPN', KR: 'KOR', KP: 'PRK', MN: 'MNG', VN: 'VNM', LA: 'LAO', KH: 'KHM',
  TH: 'THA', MM: 'MMR', MY: 'MYS', SG: 'SGP', ID: 'IDN', PH: 'PHL', BN: 'BRN', TL: 'TLS',
  IN: 'IND', PK: 'PAK', BD: 'BGD', NP: 'NPL', BT: 'BTN', LK: 'LKA', MV: 'MDV', KZ: 'KAZ',
  KG: 'KGZ', TJ: 'TJK', TM: 'TKM', UZ: 'UZB', AF: 'AFG', IR: 'IRN', IQ: 'IRQ', SY: 'SYR',
  LB: 'LBN', IL: 'ISR', PS: 'PSE', JO: 'JOR', SA: 'SAU', YE: 'YEM', OM: 'OMN', AE: 'ARE',
  QA: 'QAT', BH: 'BHR', KW: 'KWT', CY: 'CYP', TR: 'TUR', GE: 'GEO', AM: 'ARM', AZ: 'AZE',
  RU: 'RUS', BY: 'BLR', UA: 'UKR', MD: 'MDA', PL: 'POL', CZ: 'CZE', SK: 'SVK', HU: 'HUN',
  DE: 'DEU', AT: 'AUT', CH: 'CHE', LI: 'LIE', GB: 'GBR', IE: 'IRL', NL: 'NLD', BE: 'BEL',
  LU: 'LUX', FR: 'FRA', MC: 'MCO', ES: 'ESP', PT: 'PRT', AD: 'AND', IT: 'ITA', SM: 'SMR',
  VA: 'VAT', MT: 'MLT', GR: 'GRC', AL: 'ALB', MK: 'MKD', RS: 'SRB', ME: 'MNE', BA: 'BIH',
  HR: 'HRV', SI: 'SVN', BG: 'BGR', RO: 'ROU', NO: 'NOR', SE: 'SWE', FI: 'FIN', DK: 'DNK',
  IS: 'ISL', EE: 'EST', LV: 'LVA', LT: 'LTU',
  EG: 'EGY', ZA: 'ZAF', NG: 'NGA', ET: 'ETH', KE: 'KEN', GH: 'GHA', TZ: 'TZA', DZ: 'DZA',
  MA: 'MAR', SD: 'SDN', SS: 'SSD', UG: 'UGA', RW: 'RWA', BI: 'BDI', CG: 'COG', CD: 'COD',
  CM: 'CMR', AO: 'AGO', ZM: 'ZMB', ZW: 'ZWE', MG: 'MDG', MZ: 'MOZ', BW: 'BWA', NA: 'NAM',
  LS: 'LSO', SZ: 'SWZ', MU: 'MUS', SC: 'SYC', KM: 'COM', MR: 'MRT', ML: 'MLI', BF: 'BFA',
  NE: 'NER', TD: 'TCD', SN: 'SEN', GM: 'GMB', GN: 'GIN', GW: 'GNB', CV: 'CPV', SL: 'SLE',
  LR: 'LBR', CI: 'CIV', TG: 'TGO', BJ: 'BEN', GA: 'GAB', GQ: 'GNQ', ST: 'STP', DJ: 'DJI',
  SO: 'SOM', ER: 'ERI', LY: 'LBY', TN: 'TUN', CF: 'CAF', MW: 'MWI',
  US: 'USA', CA: 'CAN', MX: 'MEX', CU: 'CUB', JM: 'JAM', HT: 'HTI', DO: 'DOM', BS: 'BHS',
  TT: 'TTO', BB: 'BRB', GD: 'GRD', LC: 'LCA', VC: 'VCT', AG: 'ATG', KN: 'KNA', DM: 'DMA',
  BZ: 'BLZ', GT: 'GTM', HN: 'HND', SV: 'SLV', NI: 'NIC', CR: 'CRI', PA: 'PAN',
  BR: 'BRA', AR: 'ARG', CL: 'CHL', CO: 'COL', PE: 'PER', VE: 'VEN', EC: 'ECU', BO: 'BOL',
  PY: 'PRY', UY: 'URY', GY: 'GUY', SR: 'SUR',
  AU: 'AUS', NZ: 'NZL', PG: 'PNG', FJ: 'FJI', SB: 'SLB', VU: 'VUT', WS: 'WSM', TO: 'TON',
  FM: 'FSM', MH: 'MHL', PW: 'PLW', NR: 'NRU', KI: 'KIR', TV: 'TUV', CK: 'COK', NU: 'NIU'
};

const ALIAS_MAP = {
  '阿联酋': ['阿联酋', '阿拉伯联合酋长国'],
  '波斯尼亚和黑塞哥维那': ['波黑'],
  '圣文森特和格林纳丁斯': ['圣文森特格林纳丁斯', '圣文森特'],
  '中非共和国': ['中非'],
  '刚果共和国 - 刚果布': ['刚果'],
  '刚果民主共和国 - 刚果金': ['刚果民主共和国'],
  '斯威士兰 / 埃斯瓦蒂尼': ['斯威士兰'],
  '圣基茨和 Nevis / 圣基茨和尼维斯': ['圣基茨和尼维斯', '圣基茨'],
  '北马其顿': ['马其顿'],
  '莫桑比克': ['莫桑比克共和国', '莫桑比克'],
  '密克罗尼西亚联邦': ['密克罗尼西亚'],
  '萨摩亚': ['萨摩亚'],
  '库克群岛': ['库克群岛'],
  '纽埃': ['纽埃岛', '纽埃'],
  '梵蒂冈': ['梵蒂冈'],
  '巴勒斯坦': ['巴勒斯坦']
};

function getMp3Duration(buffer) {
  let offset = 0;
  if (buffer.slice(0, 3).toString() === 'ID3') {
    const size = ((buffer[6] & 0x7F) << 21) | ((buffer[7] & 0x7F) << 14) | ((buffer[8] & 0x7F) << 7) | (buffer[9] & 0x7F);
    offset = 10 + size;
  }
  for (let i = offset; i < Math.min(buffer.length - 4, offset + 65536); i++) {
    if (buffer[i] === 0xFF && (buffer[i + 1] & 0xE0) === 0xE0) {
      const bitrateIdx = (buffer[i + 2] >> 4) & 15;
      const bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0];
      const bitrate = (bitrates[bitrateIdx] || 128) * 1000;
      const audioSize = buffer.length - offset;
      return Math.max(10, Math.min(300, Math.round(audioSize * 8 / bitrate)));
    }
  }
  return 46;
}

function extractSvgColors(svgText) {
  const hexes = svgText.match(/#[0-9a-fA-F]{3,6}\b/g) || [];
  const counts = {};
  for (const h of hexes) {
    const full = h.length === 4 ? '#' + h[1] + h[1] + h[2] + h[2] + h[3] + h[3] : h;
    const upper = full.toUpperCase();
    counts[upper] = (counts[upper] || 0) + 1;
  }
  const sorted = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  return {
    c1: sorted[0] || '#2563EB',
    c2: sorted[1] || sorted[0] || '#FFFFFF',
    c3: sorted[2] || sorted[1] || '#0F172A'
  };
}

function detectPattern(code, flagDesc) {
  if (code === 'CN' || flagDesc.includes('五星') || flagDesc.includes('大星')) return 'cn';
  if (flagDesc.includes('太阳') || flagDesc.includes('日圆') || flagDesc.includes('圆盘') || flagDesc.includes('太极')) return 'sun';
  if (flagDesc.includes('十字')) return 'cross';
  if (flagDesc.includes('星')) return 'stars';
  if (flagDesc.includes('纵') || (flagDesc.includes('竖') && flagDesc.includes('条'))) return 'tricolor';
  if (flagDesc.includes('条') || flagDesc.includes('横') || flagDesc.includes('带')) return 'triband-h';
  return 'solid';
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}

// 1. Read Markdown file
const mdPath = 'country-国家数据/197个国家.md';
const content = fs.readFileSync(mdPath, 'utf8');
const lines = content.split('\n');

const countries = [];
let currentRegion = '';
let currentCountry = null;

for (let line of lines) {
  line = line.trim();
  if (line.startsWith('### 一、')) currentRegion = '亚洲';
  else if (line.startsWith('### 二、')) currentRegion = '欧洲';
  else if (line.startsWith('### 三、')) currentRegion = '非洲';
  else if (line.startsWith('### 四、')) currentRegion = '北美洲';
  else if (line.startsWith('### 五、')) currentRegion = '南美洲';
  else if (line.startsWith('### 六、')) currentRegion = '大洋洲';
  else if (line.startsWith('### 七、')) currentRegion = '其他';

  if (line.startsWith('* **')) {
    const parts = line.replace('* **', '').split('**');
    const namePart = parts[0];
    const codePart = parts[1] ? parts[1].replace('|', '').trim().toUpperCase() : '';
    let nameCn = namePart;
    let nameEn = '';
    const m = namePart.match(/^(.+?)\s*\((.+?)\)$/);
    if (m) {
      nameCn = m[1].trim();
      nameEn = m[2].trim();
    }
    currentCountry = {
      region: currentRegion,
      nameCn,
      nameEn,
      code: codePart,
      anthemName: '',
      anthemEn: '',
      flagDesc: ''
    };
    countries.push(currentCountry);
  } else if (line.startsWith('* 国歌：') && currentCountry) {
    const raw = line.replace('* 国歌：', '').trim();
    const slashIdx = raw.indexOf('/');
    if (slashIdx !== -1) {
      currentCountry.anthemName = raw.slice(0, slashIdx).trim().replace(/《|》/g, '');
      currentCountry.anthemEn = raw.slice(slashIdx + 1).trim();
    } else {
      currentCountry.anthemName = raw.replace(/《|》/g, '');
    }
  } else if (line.startsWith('* 国旗：') && currentCountry) {
    currentCountry.flagDesc = line.replace('* 国旗：', '').trim();
  }
}

console.log(`Parsed ${countries.length} countries from markdown.`);

// 2. Scan all MP3 files
const baseMp3 = 'country-国家数据/国歌mp3';
const dirs = fs.readdirSync(baseMp3);
const mp3Files = [];
for (const d of dirs) {
  const full = path.join(baseMp3, d);
  if (fs.statSync(full).isDirectory()) {
    for (const f of fs.readdirSync(full)) {
      if (f.endsWith('.mp3')) {
        mp3Files.push({ dir: d, file: f, path: path.join(full, f) });
      }
    }
  }
}

// 3. Prepare target directories
const targetFlagDir = 'country-国家数据/国旗';
const publicFlagDir = 'public/uploads/flags';
const publicAudioDir = 'public/uploads/audio';

fs.mkdirSync(targetFlagDir, { recursive: true });
fs.mkdirSync(publicFlagDir, { recursive: true });
fs.mkdirSync(publicAudioDir, { recursive: true });

const fullCountryList = [];
const mediaAssetsList = [];

for (const c of countries) {
  const code = c.code;
  const alpha3 = ISO3_MAP[code] || code;

  // 1) SVG Flag processing
  const srcSvg = path.join('node_modules/flag-icons/flags/4x3', code.toLowerCase() + '.svg');
  if (!fs.existsSync(srcSvg)) {
    console.error(`Missing SVG flag for ${code} (${c.nameCn})!`);
  }
  const svgText = fs.readFileSync(srcSvg, 'utf8');
  const svgBytes = Buffer.byteLength(svgText, 'utf8');

  // Copy to country-国家数据/国旗 & public/uploads/flags
  fs.writeFileSync(path.join(targetFlagDir, `${code}.svg`), svgText, 'utf8');
  fs.writeFileSync(path.join(publicFlagDir, `${code}.svg`), svgText, 'utf8');

  // Colors & Pattern
  const { c1, c2, c3 } = extractSvgColors(svgText);
  const pattern = detectPattern(code, c.flagDesc);

  // 2) MP3 Anthem processing
  let matchedMp3 = null;
  const aliases = [c.nameCn, ...(ALIAS_MAP[c.nameCn] || [])];
  for (const a of aliases) {
    matchedMp3 = mp3Files.find(m => {
      const fn = m.file.replace(/\.mp3$/i, '').trim();
      return fn === a || fn.replace(/\d+'\d+/g, '').trim() === a;
    });
    if (matchedMp3) break;
  }
  if (!matchedMp3) {
    matchedMp3 = mp3Files.find(m => {
      const fn = m.file.replace(/\.mp3$/i, '').replace(/\d+'\d+/g, '').trim();
      return fn.length >= 2 && (c.nameCn.includes(fn) || fn.includes(c.nameCn));
    });
  }

  let durationSec = 46;
  let audioBytes = 0;
  let originalMp3Name = `${c.nameCn}.mp3`;

  if (matchedMp3) {
    const mp3Buf = fs.readFileSync(matchedMp3.path);
    audioBytes = mp3Buf.length;
    durationSec = getMp3Duration(mp3Buf);
    originalMp3Name = matchedMp3.file;

    // Special official cut overrides
    if (code === 'CN') durationSec = 46; // Official 46s standard flag-raising ceremony cut

    // Copy to public/uploads/audio/${code}.mp3
    fs.writeFileSync(path.join(publicAudioDir, `${code}.mp3`), mp3Buf);
  } else {
    console.error(`Missing MP3 anthem for ${code} (${c.nameCn})!`);
  }

  const countryRecord = {
    id: code,
    code: code,
    codeAlpha3: alpha3,
    nameCn: c.nameCn,
    nameEn: c.nameEn,
    region: c.region,
    pattern: pattern,
    c1: c1,
    c2: c2,
    c3: c3,
    flagDesc: c.flagDesc,
    // 国旗图形资产绑定
    imageUrl: `/uploads/flags/${code}.svg`,
    flagAssetId: `ast_flag_${code}`,
    flagAssetName: `${c.nameCn}国旗标准矢量标样`,
    flagSourceType: 'asset',
    // 国歌音频资产绑定
    anthemName: c.anthemName || `${c.nameCn}国歌`,
    anthemEn: c.anthemEn || '',
    anthemDuration: durationSec,
    anthemUrl: `/uploads/audio/${code}.mp3`,
    anthemAssetId: `ast_anthem_${code}`,
    anthemAssetName: `${c.nameCn}国歌 - ${c.anthemName || '标准演奏版'}`,
    anthemFileName: originalMp3Name,
    anthemSourceType: 'asset'
  };

  fullCountryList.push(countryRecord);

  // Asset records for mediaAssetService
  mediaAssetsList.push({
    id: `ast_flag_${code}`,
    name: `${c.nameCn}国旗 (标准矢量标样)`,
    categoryCode: 'document',
    groupCode: 'flag',
    fileType: 'svg',
    fileSizeBytes: svgBytes,
    fileSizeFormatted: formatBytes(svgBytes),
    durationSec: 0,
    durationFormatted: '-',
    resolution: '矢量无限分辨率 (4:3 标样)',
    fileHash: `sha_${code}_flag_svg`,
    storageDriver: 'LOCAL',
    storageBucket: '本地工控服务器',
    storagePath: `/data/venue-ibms/uploads/flags/${code}.svg`,
    accessUrl: `/uploads/flags/${code}.svg`,
    refCount: 1,
    remark: `${c.nameCn} (${c.nameEn}) 官方标准国旗矢量文件`,
    createdBy: 'system',
    createdAt: '2026-10-30 12:00:00'
  });

  mediaAssetsList.push({
    id: `ast_anthem_${code}`,
    name: `${c.nameCn}国歌 (${c.anthemName || '标准军乐版'})`,
    categoryCode: 'audio',
    groupCode: 'anthem',
    fileType: 'mp3',
    fileSizeBytes: audioBytes,
    fileSizeFormatted: formatBytes(audioBytes),
    durationSec: durationSec,
    durationFormatted: formatDuration(durationSec),
    resolution: '44.1kHz 立体声',
    fileHash: `sha_${code}_anthem_mp3`,
    storageDriver: 'LOCAL',
    storageBucket: '本地工控服务器',
    storagePath: `/data/venue-ibms/uploads/audio/${code}.mp3`,
    accessUrl: `/uploads/audio/${code}.mp3`,
    refCount: 1,
    remark: `${c.nameCn}官方国歌《${c.anthemName}》，标准升旗演奏时长 ${durationSec} 秒`,
    createdBy: 'system',
    createdAt: '2026-10-30 12:00:00'
  });
}

// 4. Save JSON files
fs.mkdirSync('src/data', { recursive: true });
fs.writeFileSync('src/data/countries_197.json', JSON.stringify(fullCountryList, null, 2), 'utf8');
fs.writeFileSync('src/data/media_assets_197.json', JSON.stringify(mediaAssetsList, null, 2), 'utf8');

console.log('Saved src/data/countries_197.json, count:', fullCountryList.length);
console.log('Saved src/data/media_assets_197.json, count:', mediaAssetsList.length);
