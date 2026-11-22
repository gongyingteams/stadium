import fs from 'fs';
import path from 'path';

// Clean duration suffix in country-国家数据/国歌mp3
const baseMp3 = 'country-国家数据/国歌mp3';
const dirs = fs.readdirSync(baseMp3);
for (const d of dirs) {
  const full = path.join(baseMp3, d);
  if (fs.statSync(full).isDirectory()) {
    for (const f of fs.readdirSync(full)) {
      if (f.includes("'") || /\d+'\d+/.test(f)) {
        const cleanName = f.replace(/\d+'\d+/g, '').replace(/'/g, '');
        const oldP = path.join(full, f);
        const newP = path.join(full, cleanName);
        fs.renameSync(oldP, newP);
        console.log(`Renamed [${d}/${f}] -> [${d}/${cleanName}]`);
      }
    }
  }
}
