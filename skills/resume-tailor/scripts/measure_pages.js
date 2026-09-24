/**
 * measure_pages.js —— 用真实浏览器测量简历页数与每页填充率
 *
 * 为什么需要它：
 *   density.py 是按 CSS 参数推算的**估算值**，不是实测值。模型会漂移——
 *   改一个 margin、换一种字体、加一条长 bullet，估算就可能偏半页。
 *   没有实测校准，"篇幅达标"这四个字就是自欺欺人。
 *
 *   本脚本打开渲染后的 HTML，等分页 JS 跑完，量出真实的：
 *     页数 / 每页内容高度 / 每页填充率 / 是否有残页
 *
 * 用法：
 *   NODE_PATH=<workspace>/node_modules node scripts/measure_pages.js <html路径> [...]
 *   node scripts/measure_pages.js people/张三/output/resume-final.html --json
 *
 * 依赖 playwright（已装在隔离工作区，不污染用户环境）
 */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

// 已下载的 chromium 版本与 playwright 包版本常常对不上（本机 1223/1228 vs 包要 1234）。
// 与其要求用户下载新浏览器，不如自动发现已有的任何一个 —— 测量只需要能跑 WebKit 布局。
function findChromium() {
  const base = path.join(process.env.LOCALAPPDATA || '', 'ms-playwright');
  if (!fs.existsSync(base)) return undefined;
  const dirs = fs.readdirSync(base)
    .filter(d => /^chromium(-headless_shell)?-\d+$/.test(d))
    .sort()
    .reverse();                       // 版本号大的优先
  for (const d of dirs) {
    for (const rel of ['chrome-win64/chrome.exe', 'chrome-win/chrome.exe',
                       'chrome-headless-shell-win64/chrome-headless-shell.exe']) {
      const p = path.join(base, d, rel);
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined;
}

const FILES = process.argv.slice(2).filter(a => !a.startsWith('--'));
const AS_JSON = process.argv.includes("--json");
const DETAIL = process.argv.includes("--detail");

if (!FILES.length) {
  console.error('用法: node scripts/measure_pages.js <html路径> [--json]');
  process.exit(2);
}

// A4 内容区高度（mm）：297 - 上下 padding 15*2 = 267
const CONTENT_H_MM = 267;

async function measure(page, file, DETAIL) {
  const url = 'file:///' + path.resolve(file).replace(/\\/g, '/');
  await page.goto(url, { waitUntil: 'load' });
  // 等分页 JS 完成（它同步执行，load 后即完成；留一帧确保布局稳定）
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));

  return await page.evaluate((arg) => {
    const CONTENT_H_MM = arg.CONTENT_H_MM, DETAIL = arg.DETAIL;
    const pages = Array.from(document.querySelectorAll('.page'));
    const MM = 3.779528;

    // 每页「内容实际占用高度」：最后一个子元素的 bottom - 第一个子元素的 top
    function contentHeight(p) {
      const kids = Array.from(p.children).filter(
        el => !(el.classList && el.classList.contains('noprint')) &&
              getComputedStyle(el).display !== 'none'
      );
      if (!kids.length) return 0;
      const top = kids[0].getBoundingClientRect().top;
      let bottom = -Infinity;
      kids.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.bottom > bottom) bottom = r.bottom;
      });
      return bottom - top;
    }

    const rows = pages.map((p, i) => {
      const hPx = contentHeight(p);
      const hMm = hPx / MM;
      return {
        page: i + 1,
        height_px: Math.round(hPx),
        height_mm: Math.round(hMm),
        fill: +(hMm / CONTENT_H_MM).toFixed(3),
        blocks: p.children.length,
      };
    });

    // 内容总量（不含页间 padding，故为下界）
    const total_mm = rows.reduce((a, r) => a + r.height_mm, 0);
    // 「末页 ≥55%」在数学上做不做得到？
    //   两页都 ≥55% 至少需要 pages × 0.55 × H 的内容；总量不够时，
    //   再怎么均衡也达不到 —— 此时报 ❌ 是误报，且会误导人去调分页参数，
    //   真正的结论应该是「内容不够撑满 N 页，压到 N-1 页或补内容」。
    const orphan_floor = rows.length * 0.55 * CONTENT_H_MM;
    const min_pages = Math.max(1, Math.ceil(total_mm / CONTENT_H_MM));
    // 压到上一档页数还差多少（差得少才值得提，差得多说明就是 N 页的量）
    const slim_gap = rows.length > 1
      ? +(total_mm - (rows.length - 1) * CONTENT_H_MM).toFixed(1)
      : null;

    const out = {
      file: document.title,
      pages: rows.length,
      rows,
      total_mm: +total_mm.toFixed(1),
      min_pages,
      slim_gap,
      last_fill: rows.length ? rows[rows.length - 1].fill : 0,
      // 残页：最后一页填充 < 55%
      orphan: rows.length > 1 && rows[rows.length - 1].fill < 0.55,
      // 残页是否可修（均衡能解决 = 内容量够）
      orphan_fixable: rows.length > 1 &&
                      rows[rows.length - 1].fill < 0.55 &&
                      total_mm >= orphan_floor,
      // 打印溢出：任何一页内容超过内容区高度（说明分页没兜住）
      overflow: rows.some(r => r.height_mm > CONTENT_H_MM + 2),
    };

    // --detail：逐块实测，用于校准 density.py 的高度模型。
    // 估算不准的篇幅引擎比没有更危险 —— 它会给出错误的「还差几行」。
    if (DETAIL) {
      const blocks = [];
      document.querySelectorAll('.page').forEach((p, pi) => {
        Array.from(p.children).forEach(el => {
          if (el.classList && el.classList.contains('noprint')) return;
          const cs = getComputedStyle(el);
          const r = el.getBoundingClientRect();
          blocks.push({
            page: pi + 1,
            tag: el.tagName.toLowerCase(),
            cls: el.className || '',
            h: +r.height.toFixed(1),
            mt: +(parseFloat(cs.marginTop) || 0).toFixed(1),
            mb: +(parseFloat(cs.marginBottom) || 0).toFixed(1),
            lines: Math.round(r.height / (parseFloat(cs.fontSize) * 1.7)),
            text: (el.textContent || '').trim().slice(0, 26).replace(/\s+/g, ' '),
          });
        });
      });
      out.blocks = blocks;
      out.total_mm = +(rows.reduce((a, r) => a + r.height_mm, 0)).toFixed(1);
    }
    return out;
  }, { CONTENT_H_MM: CONTENT_H_MM, DETAIL: DETAIL });
}

(async () => {
  let browser;
  try {
    browser = await chromium.launch({ args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  } catch (e) {
    const exe = findChromium();
    if (!exe) throw e;
    browser = await chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  }
  const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });
  const results = [];
  for (const f of FILES) {
    try {
      results.push({ path: f, ...(await measure(page, f, DETAIL)) });
    } catch (e) {
      results.push({ path: f, error: String(e && e.message || e) });
    }
  }
  browser.close().catch(() => {});

  if (AS_JSON) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const r of results) {
      console.log('='.repeat(58));
      if (r.error) { console.log(`${r.path}\n  ERROR: ${r.error}`); continue; }
      console.log(`${r.path}`);
      console.log(`  页数 ${r.pages}   末页填充 ${(r.last_fill * 100).toFixed(0)}%`);
      r.rows.forEach(p => {
        const bar = '█'.repeat(Math.max(0, Math.round(p.fill * 20))).padEnd(20, '·');
        console.log(`    第${p.page}页  ${bar} ${(p.fill * 100).toFixed(0)}%  ` +
                    `${p.height_mm}mm/${CONTENT_H_MM}mm  ${p.blocks} 块`);
      });
      if (r.overflow) console.log('    ⚠ 有页内容超出 A4 内容区，分页未兜住');
      else if (r.orphan && r.orphan_fixable)
        console.log('    ❌ 残页：末页内容不足 55%（内容量够，均衡即可修）');
      else if (r.orphan) {
        console.log(`    ⚠ 内容不足：总量 ${r.total_mm}mm 撑不满 ${r.pages} 页` +
                    `（需 ${Math.round(r.pages * 0.55 * CONTENT_H_MM)}mm），均衡无解`);
        if (r.slim_gap !== null && r.slim_gap > 0 && r.slim_gap <= 30)
          console.log(`      压到 ${r.pages - 1} 页只差 ${r.slim_gap}mm —— 精简 1 条 bullet 即可`);
        else if (r.slim_gap !== null && r.slim_gap > 0)
          console.log(`      压到 ${r.pages - 1} 页需再删 ${r.slim_gap}mm 内容`);
        else
          console.log(`      建议补内容，或接受当前 ${r.pages} 页`);
      }
      else console.log('    ✅ 篇幅达标');
    }
  }
  process.exit(0);
})();
