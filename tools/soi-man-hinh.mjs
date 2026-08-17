/**
 * Chụp từng màn hình của app ở đúng khung 1920×1080 của robot Nova, để soi bằng mắt
 * trước khi build APK.
 *
 *   node tools/soi-man-hinh.mjs [thu-muc-ra]
 *
 * Vì sao phải chụp thay vì mở Chrome nhìn: bố cục vỡ trên Nova gần như luôn là vỡ
 * theo CHIỀU CAO — màn robot chỉ 1080px mà nội dung xếp dọc thì nút cuối bị co về
 * height 0 và biến mất, không báo lỗi gì. Chụp đúng 1920×1080 mới thấy.
 *
 * Playwright mượn của tools/html-video (giống tools/render-video.mjs), không cài riêng.
 */
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, '..');
const PW = join(APP, '..', '..', 'tools', 'html-video', 'packages',
                'adapter-hyperframes', 'node_modules', 'playwright', 'index.mjs');
if (!existsSync(PW)) {
  console.error(`Khong thay playwright tai:\n  ${PW}\nChay: cd tools/html-video && pnpm install`);
  process.exit(1);
}
const { chromium } = await import(pathToFileURL(PW).href);

const RA = resolve(process.argv[2] || join(APP, 'demo', 'anh-soi'));
mkdirSync(RA, { recursive: true });

const TRANG = pathToFileURL(join(APP, 'demo', 'index.html')).href;

/* Mỗi bước: [ten file, mo ta, ham chay trong trang] */
const BUOC = [
  ['01-man-cho',        'Man cho — video bieu cam',            null],
  ['02-menu',           'Menu 9 nhom + o tim + bang kham lan dau', () => thoiCho()],
  ['03-nhom-me-be',     'Nhom Me va be',                       () => moNhom('me-be')],
  ['04-hoi-toa',        'Hoi lai toa nha (Khoa Phu San)',      () => moChiTiet(1)],
  ['05-chi-tiet-ngoai', 'Chi tiet khoa ngoai khu (Phu San, nha DII)', () => moChiTiet(1, 1)],
  ['06-tim-dau-bung',   'Go "dau bung"',                       () => { veLuoiNhom(); datTim('đau bụng'); }],
  ['07-tim-ma-D3',      'Go ma D3 -> Khoa Nhi',                () => { veLuoiNhom(); datTim('D3'); }],
  ['08-ban-phim-ma',    'Ban phim nhap ma phong',              () => { veTrangChu(); moBanPhim(); }],
  ['09-cap-cuu',        'Man CAP CUU (khong co nut dan duong)', () => { dongBanPhim(); moNhom('cap-cuu'); }],
  ['10-tien-ich',       'Nhom tien ich trong khu le tan',      () => { veTrangChu(); moNhom('tien-ich'); }],
  ['11-chi-tiet-trong', 'Chi tiet diem trong khu (nha thuoc)', () => {
      const d = window.DU_LIEU.dich.find(x => x.diem === 'nha-thuoc'); moChiTiet(d.id); }],
  ['12-kham-lan-dau',   'Kham lan dau — quy trinh 4 buoc',     () => { veTrangChu(); moKhamLanDau(); }],
  ['13-dang-dan',       'Man dang dan duong',                  () => {
      const d = window.DU_LIEU.dich.find(x => x.ten === 'Khoa Nhi');
      moChiTiet(d.id, 0); document.querySelector('#dan-diem').textContent =
        window.DU_LIEU.diem['truoc-hanh-lang'].ten; window.baoDanDuong('bat-dau', ''); }],
  ['14-chi-duong',      'Man CHI DUONG sau khi toi dau hanh lang', () => window.baoDanDuong('toi-noi', '')],
  ['15-tro-chuyen',     'Man tro chuyen (nut mic phai AN)',    () => { veTrangChu(); moChat(); }],
];

const trinhDuyet = await chromium.launch();
const trang = await trinhDuyet.newPage({ viewport: { width: 1920, height: 1080 } });

const loi = [];
trang.on('pageerror', e => loi.push('  ✗ LOI JS: ' + e.message));
trang.on('console', m => { if (m.type() === 'error') loi.push('  ✗ console: ' + m.text()); });

await trang.goto(TRANG, { waitUntil: 'load' });
await trang.waitForTimeout(700);

for (const [ten, mo, ham] of BUOC) {
  if (ham) { await trang.evaluate(ham); await trang.waitForTimeout(450); }
  await trang.screenshot({ path: join(RA, ten + '.png') });

  /* Tu kiem ngay tai cho: co phan tu nao tran ra ngoai khung 1080, hay bi co ve 0 khong */
  const bao = await trang.evaluate(() => {
    const hien = document.querySelector('.man-hinh.hien');
    const r = [];
    if (!hien) return ['KHONG co man hinh nao dang hien'];
    if (document.documentElement.scrollHeight > innerHeight + 2)
      r.push('TRAN CHIEU CAO: ' + document.documentElement.scrollHeight + 'px > 1080px');
    /* Ba thứ app CỐ Ý ẩn: nút mic (ẩn khi Agent SDK chưa bind được), nút trò
       chuyện, và băng "khám lần đầu" (nhường chỗ khi đang xem danh sách kết quả).
       Bỏ qua chúng, không thì bộ soi kêu ầm lên ở mọi màn. */
    const CO_Y_AN = '.nut-mic, .nut-chat, #bang-moi';
    hien.querySelectorAll('button, .the-nhom, .muc, .nut-to, .toa-nut').forEach(e => {
      if (e.closest(CO_Y_AN)) return;
      const ten = (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 34);
      /* Tổ tiên bị ẩn (lưới nhóm đang nhường chỗ cho danh sách kết quả) là chuyện
         bình thường — chỉ báo khi CHÍNH nút bị ẩn còn khung chứa nó vẫn hiện. */
      let cha = e.parentElement, choAn = false;
      while (cha && cha !== hien) {
        if (getComputedStyle(cha).display === 'none') { choAn = true; break; }
        cha = cha.parentElement;
      }
      if (choAn) return;
      const b = e.getBoundingClientRect();
      /* Bắt trường hợp 0×0: nút vẫn nằm trong DOM nhưng bị một luật CSS khác đè
         display:none. Bản đầu của bộ soi chỉ kiểm chiều cao, nên nút "Nghe robot
         đọc lại" mất tăm mà vẫn báo PASS. */
      if (b.width === 0 && b.height === 0)
        r.push('NUT KHONG DUOC VE (0x0, nhiều khả năng bị display:none): "' + ten + '"');
      else if (b.height < 8)
        r.push('NUT BI CO VE 0: "' + ten + '"');
      if (b.bottom > innerHeight + 2)
        r.push('NUT LOT KHOI KHUNG: "' + ten + '"');
    });
    return r;
  });
  const co = bao.length || loi.length;
  console.log((co ? '✗ ' : '✓ ') + ten + '  —  ' + mo);
  bao.forEach(x => console.log('  ✗ ' + x));
  loi.splice(0).forEach(x => console.log(x));
}

await trinhDuyet.close();
console.log('\nAnh o: ' + RA);
