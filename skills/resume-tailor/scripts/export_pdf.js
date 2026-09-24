/**
 * export_pdf.js —— 用真实浏览器把渲染后的 HTML 打印成 PDF（带文字层，ATS 可解析）
 *
 * 为什么用浏览器而不是 python 库：
 *   简历 HTML 自带 @page A4 + 分页 JS（按实测高度重排成多个 .page div，
 *   page-break-after:always）。只有真实浏览器能复刻这套分页，python 库要重排布局，
 *   必然和屏幕上/出片 HTML 不一致。
 *   本机已装 node playwright + chromium（见 measure_pages.js），直接复用，不再下载。
 *
 * 用法：
 *   NODE_PATH=<workspace>/node_modules node scripts/export_pdf.js <html路径> [--out <pdf>]
 *   node scripts/export_pdf.js people/张三/output/resume-final.html --out people/张三/output/resume-final.pdf
 *
 * 依赖 playwright（已装在隔离工作区，不污染用户环境）
 */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

// 与 measure_pages.js 同款：自动发现已下载的 chromium（版本号不必与包严格一致）
function findChromium() {
  const base = path.join(process.env.LOCALAPPDATA || '', 'ms-playwright');
  if (!fs.existsSync(base)) return undefined;
  const dirs = fs.readdirSync(base)
    .filter(d => /^chromium(-headless_shell)?-\d+$/.test(d))
    .sort()
    .reverse();
  for (const d of dirs) {
    for (const rel of ['chrome-win64/chrome.exe', 'chrome-win/chrome.exe',
                       'chrome-headless-shell-win64/chrome-headless-shell.exe']) {
      const p = path.join(base, d, rel);
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined;
}

const ARGV = process.argv.slice(2);
const OUT_IDX = ARGV.indexOf('--out');
// 过滤掉「--」开头的参数，以及紧跟在 --out 后面的那个取值（否则会被当成输入 HTML）
const FILES = ARGV.filter((a, i) => !a.startsWith('--') && !(OUT_IDX >= 0 && i === OUT_IDX + 1));
const OUT = OUT_IDX >= 0 ? ARGV[OUT_IDX + 1] : null;

if (!FILES.length) {
  console.error('用法: node scripts/export_pdf.js <html路径> [--out <pdf路径>]');
  process.exit(2);
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

  for (const f of FILES) {
    const html = path.resolve(f);
    if (!fs.existsSync(html)) {
      console.error(`[跳过] 找不到 HTML：${html}`);
      continue;
    }
    const out = OUT || html.replace(/\.html$/i, '.pdf');

    const url = 'file:///' + html.replace(/\\/g, '/');
    await page.goto(url, { waitUntil: 'load' });
    // 等分页 JS 跑完（load 后同步执行，留一帧 + 一小段确保布局稳定）
    await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));
    await page.waitForTimeout(250);
    // 确保分页已生成至少一个 .page
    const nPages = await page.evaluate(() => document.querySelectorAll('.page').length);
    if (!nPages) {
      console.error(`[WARN] ${f}：未检测到 .page 分页，PDF 可能只有一页或版式异常`);
    }

    // ---- 打印版式：用浏览器真实打印引擎自然分页，而非信任屏幕态算出的 .page 切分 ----
    // 根因：PAGINATE_JS 在「屏幕媒体」下跑、用净高判定断页；但 page.pdf() 在「打印媒体」
    // 渲染，同一段落在两种媒体下高度不同（如伯克希尔经历在屏幕 138mm、打印仅 115mm）。
    // 屏幕态把下一页内容（巴菲特合伙，打印 58mm）整块推到下一页，留下首页 50~73mm 空白。
    // 改法：导出 PDF 时把全部 .page 子节点摊平进 body（消除人为的页边界），改由 Chromium
    // 打印引擎在真实打印媒体下连续流式排版、自动断页 —— 没有屏幕/打印高度差，首页自然被
    // 填满；经历块仍用 page-break-inside:avoid 保持完整，段标题用 break-after:avoid 避免
    // 孤悬页底。块间距改到「上边距」，消除页末被白耗的下边距（首页因此能多塞下紧邻的下一段）。
    await page.evaluate(() => {
      // 把每个 .page 的内容提升到 body，删除 .page 包裹层 —— 还原成单一连续流
      document.querySelectorAll('.page').forEach(p => {
        while (p.firstChild) p.parentNode.insertBefore(p.firstChild, p);
        p.parentNode.removeChild(p);
      });
    });
    await page.addStyleTag({ content: `
      @page { size: A4; margin: 15mm 18mm !important; }
      html, body { padding: 0 !important; margin: 0 !important; }
      /* 段间距改到「上边距」：块末的下边距在页末会被白耗，导致首页差几毫米塞不下
         紧邻的下一段（巴菲特合伙差 3mm）。清零下边距、用「下一段的上边距」做间距，
         页末就不再浪费，首页得以填满。 */
      .item { margin-bottom: 0 !important;
              break-inside: avoid !important; page-break-inside: avoid !important; }
      /* 段间距从「下边距」改为「下一段上边距」已消除页末白耗；这里再压一点：
         经历块之间只留 6px（约 2mm），段标题上边距 10px（约 3.5mm）。
         目的：伯克希尔这种巨型经历块紧邻的下一段（巴菲特合伙 60mm）在 16mm 边距下
         只差约 1mm 塞不下、被整块外推留下 ~74mm 空白。根因已通过把 A4 上下边距
         由 16mm 收紧到 15mm（容量模型 density/measure/render 同步改）吸收，
         这里只额外压几毫米段间距作为保险，避免个别简历在边界处重现首页大段空白。 */
      .item + .item { margin-top: 6px !important; }
      .item-cont { margin-bottom: 0 !important;
                   break-inside: avoid !important; page-break-inside: avoid !important; }
      h2 { margin-top: 10px !important; break-after: avoid !important; }
      .skill-line, .edu-item, .gaps {
        break-inside: avoid !important; page-break-inside: avoid !important;
      }
      .noprint { display: none !important; }
    ` });
    // 注入样式后等一帧，确保打印布局重算
    await page.evaluate(() => new Promise(r => requestAnimationFrame(() => r())));

    await page.pdf({
      path: out,
      format: 'A4',
      printBackground: true,        // 保留底色/边框
      margin: { top: '0', bottom: '0', left: '0', right: '0' },
    });

    const sz = fs.statSync(out).size;
    console.log(`[OK] 已生成 PDF：${out}  （${nPages} 个 .page 分页， ${(sz / 1024).toFixed(1)} KiB）`);
  }

  // 显式退出：browser.close() 在部分沙箱环境会挂住，不阻塞退出，
  // node 退出时由 OS 回收浏览器子进程（Windows 下安全）。
  browser.close().catch(() => {});
  process.exit(0);
})().catch(e => {
  console.error('PDF 导出失败：', e && e.message || e);
  process.exit(1);
});
