/**
 * Nạp Playwright cho ba bộ thử (soi-man-hinh · thu-luong-dan-duong · thu-tim-kiem).
 *
 * Hai đường, thử lần lượt:
 *   ① Trong workspace nội bộ Roboworld: mượn bản có sẵn ở tools/html-video, không cài riêng.
 *   ② Kho clone độc lập từ GitHub: bản cài bằng `npm install` ở gốc kho
 *      (package.json đã khai playwright), rồi `npx playwright install chromium` một lần.
 *
 * Trước đây ba bộ thử CHỈ biết đường ①, nên ai clone kho về là không chạy được bộ thử nào.
 */
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const APP = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PW_WORKSPACE = join(APP, '..', '..', 'tools', 'html-video', 'packages',
                          'adapter-hyperframes', 'node_modules', 'playwright', 'index.mjs');

let pw;
if (existsSync(PW_WORKSPACE)) {
  pw = await import(pathToFileURL(PW_WORKSPACE).href);
} else {
  try {
    pw = await import('playwright');
  } catch {
    console.error('Khong thay Playwright. Chay mot lan o goc kho:\n' +
                  '  npm install\n  npx playwright install chromium');
    process.exit(1);
  }
}

export const chromium = pw.chromium;
