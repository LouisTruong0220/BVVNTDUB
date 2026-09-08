/**
 * Chạy thử TRỌN luồng dẫn đường trên bản thử (demo/thu-nghiem.html), tự động.
 *
 *   node tools/thu-luong-dan-duong.mjs
 *
 * Vì sao cần: ba màn quan trọng nhất của app chỉ xuất hiện KHI ĐANG DẪN ĐƯỜNG —
 * màn đang dẫn, màn chỉ đường, thanh robot tự về sảnh. Bấm tay thì mỗi lần đổi
 * một dòng CSS lại phải ngồi bấm lại sáu bước; để đây thì chạy một lệnh.
 *
 * Nó kiểm bằng TRẠNG THÁI THẬT của app (màn nào đang hiện, robot nói câu gì),
 * không phải chỉ chụp ảnh rồi bảo là xong.
 */
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, '..');
const PW = join(APP, '..', '..', 'tools', 'html-video', 'packages',
                'adapter-hyperframes', 'node_modules', 'playwright', 'index.mjs');
if (!existsSync(PW)) { console.error('Khong thay playwright tai:\n  ' + PW); process.exit(1); }
const { chromium } = await import(pathToFileURL(PW).href);

const RA = join(APP, 'demo', 'anh-soi', 'luong-dan-duong');
mkdirSync(RA, { recursive: true });

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
const loi = [];
p.on('pageerror', e => loi.push('LOI JS: ' + e.message));
p.on('console', m => { if (m.type() === 'error') loi.push('console: ' + m.text()); });

await p.goto(pathToFileURL(join(APP, 'demo', 'thu-nghiem.html')).href, { waitUntil: 'load' });
await p.waitForTimeout(700);

let hong = 0;
const man = () => p.evaluate(() => (document.querySelector('.man-hinh.hien') || {}).id);
const noi = () => p.evaluate(() => (document.querySelector('#gl-noi') || {}).textContent);
const veCho = () => p.evaluate(() => document.querySelector('#ve-cho').classList.contains('hien'));

async function kiem(nhan, dieuKien, anh) {
  const ok = await dieuKien();
  console.log((ok ? '✓ ' : '✗ ') + nhan);
  if (!ok) hong++;
  if (anh) await p.screenshot({ path: join(RA, anh + '.png') });
}

/* Chờ tới khi điều kiện đúng, tối đa `han` ms.
   Dùng cái này thay vì waitForTimeout với một con số đoán: câu robot đọc dài ngắn
   khác nhau, mà đồng hồ "về chỗ" chỉ chạy SAU khi đọc xong. Hẹn giờ cứng thì bài
   kiểm lúc đạt lúc trượt tuỳ độ dài câu — trượt kiểu đó không nói lên điều gì. */
async function cho(dieuKien, han = 20000) {
  const het = Date.now() + han;
  while (Date.now() < het) {
    if (await dieuKien()) return true;
    await p.waitForTimeout(250);
  }
  return false;
}

console.log('\n── A. Khoa NGOÀI khu: dẫn ra đầu hành lang rồi chỉ đường ──');

// Rút quãng đường xuống 3 giây cho nhanh
await p.evaluate(() => { GIA_LAP.giay = 3; GIA_LAP.tatDongHo = true; });
await p.evaluate(() => { thoiCho(); });
await p.evaluate(() => { const d = DU_LIEU.dich.find(x => x.ten === 'Khoa Nhi'); moChiTiet(d.id, 0); });
await p.waitForTimeout(300);

await kiem('Màn chi tiết hiện nút dẫn đường (giả lập đã cấp CAU)',
  async () => (await p.locator('#nut-dan').count()) === 1, '01-co-nut-dan');

await p.click('#nut-dan');
await p.waitForTimeout(400);
await kiem('Bấm dẫn → sang màn ĐANG DẪN', async () => (await man()) === 'mh-dan', '02-dang-dan');
await kiem('Robot nói đúng một câu "Xin mời đi theo tôi"',
  async () => /Xin mời đi theo tôi/.test(await noi() || ''));

await p.waitForTimeout(1100);   // qua mốc 30% — có vật cản
const tin = await p.evaluate(() => document.querySelector('#dan-tin').textContent);
await kiem('Diễn biến dọc đường hiện thành CHỮ: "' + tin + '"', async () => tin.length > 0);
await kiem('Dọc đường robot KHÔNG đọc thêm câu nào (đúng quy tắc im lặng)',
  async () => { const n = await noi(); return n === '—' || /Xin mời đi theo tôi/.test(n); });

await p.waitForTimeout(2600);   // tới nơi
await kiem('Tới nơi → sang màn CHỈ ĐƯỜNG', async () => (await man()) === 'mh-chi', '03-chi-duong');
await kiem('Màn chỉ đường ghi đúng toà và tầng của Khoa Nhi (Nhà DI, tầng 2)',
  async () => await p.evaluate(() =>
    document.querySelector('#chi-toa').textContent === 'DI' &&
    document.querySelector('#chi-tang').textContent === 'Tầng 2'));
await kiem('Tới nơi robot MỚI đọc câu chỉ đường',
  async () => /Đã tới nơi/.test(await noi() || ''));
/* Robot dừng ở đầu hành lang, còn cách các toà một quãng — nên phải chỉ bằng THỨ TỰ
   toà nhà, không bằng tên. Khoa Nhi ở nhà DI = toà nhà ĐẦU TIÊN. */
await kiem('Chỉ đường bằng THỨ TỰ toà nhà, không bằng tên — DI là toà "đầu tiên"',
  async () => /toà nhà đầu tiên/i.test(await noi() || ''));
await kiem('Màn hình cũng ghi thứ tự toà nhà',
  async () => /ĐẦU TIÊN/i.test(await p.evaluate(() => document.querySelector('#chi-di').textContent)));

await kiem('Đọc xong → hiện thanh "robot về chỗ" đếm ngược',
  async () => await cho(veCho), '04-thanh-ve-cho');
await kiem('Đồng hồ đang đếm ngược thật (số giây giảm dần)',
  async () => {
    const a = await p.evaluate(() => +document.querySelector('#vc-dem').textContent);
    await p.waitForTimeout(1600);
    const c = await p.evaluate(() => +document.querySelector('#vc-dem').textContent);
    return c < a;
  });

await p.click('#ve-cho button');   // "Về ngay"
await p.waitForTimeout(500);
await kiem('Bấm "Về ngay" → robot về sảnh, app về màn chờ',
  async () => (await man()) === 'mh-cho', '05-ve-man-cho');
await kiem('Giả lập ghi nhận robot tự đi về điểm "Sanh cho"',
  async () => await p.evaluate(() => /Sanh cho/.test(document.querySelector('#gl-log').textContent)));

console.log('\n── B. Chỗ TRONG khu lễ tân: dẫn thẳng tới nơi ──');
await p.evaluate(() => { thoiCho(); const d = DU_LIEU.dich.find(x => x.diem === 'nha-thuoc'); moChiTiet(d.id); });
await p.waitForTimeout(300);
await p.click('#nut-dan');
await kiem('Tới nơi → KHÔNG qua màn chỉ đường, về thẳng màn chi tiết',
  async () => await cho(async () => (await man()) === 'mh-ct' && !(await p.evaluate(
    () => document.querySelector('#mh-dan').classList.contains('hien')))),
  '06-trong-khu-toi-noi');

console.log('\n── B2. Toà DII và DIII phải được gọi là toà thứ hai / thứ ba ──');
for (const [khoa, iVt, mongDoi] of [['Khoa Sơ Sinh', 0, /toà nhà thứ hai/i],
                                    ['Khoa Phụ Sản', 2, /toà nhà thứ ba/i]]) {
  const noiDung = await p.evaluate(([k, i]) => {
    const d = DU_LIEU.dich.find(x => x.ten === k);
    return d.vi_tri[i].chi_duong;
  }, [khoa, iVt]);
  await kiem(khoa + ' → ' + noiDung.match(/[Tt]oà nhà (đầu tiên|thứ hai|thứ ba)/)?.[0],
    async () => mongDoi.test(noiDung));
}

/* Bốn chỗ ở nhà A · B · C · F KHÔNG nằm dọc hành lang ba toà D. Đếm thứ tự cho
   chúng là chỉ sai chỗ — mà cách đếm ấy có mặt ở ba nơi (dữ liệu, màn chỉ đường,
   PERSONA của mô hình) nên rất dễ lọt. */
console.log('\n── B3. Nhà A · B · C · F: dẫn tới TẬN NƠI, và tuyệt đối không đếm thứ tự ──');
const dsToaKhac = await p.evaluate(() =>
  DU_LIEU.dich.filter(x => x.loai === 'toa-khac' || x.loai === 'cap-cuu')
    .map(x => ({ ten: x.ten, loai: x.loai, diem: x.diem, toa: x.vi_tri[0].toa,
                 doc: x.doc, toiNoi: x.vi_tri[0].doc_toi_noi || '' })));

await kiem('Có đủ bốn chỗ mới (A · B · C · F)', async () => dsToaKhac.length === 4);
for (const d of dsToaKhac) {
  await kiem(d.ten + ' (nhà ' + d.toa + ') KHÔNG đếm thứ tự toà nhà',
    async () => !/toà nhà (đầu tiên|thứ hai|thứ ba)/i.test(d.doc + ' ' + d.toiNoi));
  await kiem(d.ten + ' có gắn điểm bản đồ riêng',
    async () => !!d.diem && d.diem !== 'truoc-hanh-lang');
}

// Đi trọn luồng thật với Khoa Răng Hàm Mặt — chỗ vừa chuyển từ DI tầng 4 sang nhà B
await p.evaluate(() => { veTrangChu(); thoiCho();
  const d = DU_LIEU.dich.find(x => x.ten === 'Khoa Răng Hàm Mặt'); moChiTiet(d.id); });
await p.waitForTimeout(300);
await kiem('Khoa Răng Hàm Mặt: màn chi tiết có nút dẫn',
  async () => (await p.locator('#nut-dan').count()) === 1, '08-rang-ham-mat');
await p.click('#nut-dan');
await kiem('Tới nơi → KHÔNG mở màn chỉ đường (robot đã đứng ngay đó)',
  async () => await cho(async () => (await man()) === 'mh-ct'), '09-rhm-toi-noi');
/* Chờ câu "Đã tới nơi" được phát hẳn rồi mới soi nội dung. Đọc ngay sau khi đổi
   màn thì lúc đạt lúc trượt tuỳ máy nhanh chậm — trượt kiểu đó không nói lên gì. */
await kiem('Robot đọc câu "Đã tới nơi" sau khi dẫn xong',
  async () => await cho(async () => /Đã tới nơi/.test(await noi() || '')));
const cauToiNoi = await noi() || '';
await kiem('Câu tới nơi nhắc đúng nhà B và số phòng D7',
  async () => /toà nhà bê/i.test(cauToiNoi) && /đê bảy/i.test(cauToiNoi));
await kiem('Câu tới nơi KHÔNG bảo "lên tầng một" (robot đang đứng ở tầng 1)',
  async () => !/lên tầng một/i.test(cauToiNoi));

console.log('\n── C. Cấp cứu: tuyệt đối không có nút dẫn ──');
await p.evaluate(() => { veTrangChu(); moNhom('cap-cuu'); });
await p.waitForTimeout(400);
await kiem('Màn cấp cứu đang hiện', async () => (await man()) === 'mh-cc');
await kiem('Màn cấp cứu KHÔNG có nút dẫn đường nào',
  async () => (await p.locator('#mh-cc #nut-dan').count()) === 0, '07-cap-cuu-khong-dan');
/* Khoa cấp cứu đổi hẳn 08/09/2026: C1 · tầng 1 · Nhà C. Khoa Hồi Sức Cấp Cứu Nội
   cũ (D23-D24, Nhà DIII) đã bỏ. Sai chỗ này là người đang nguy kịch chạy nhầm nhà. */
await kiem('Màn cấp cứu chỉ về Nhà C, phòng C1, tầng 1', async () => await p.evaluate(() =>
  document.querySelector('#cc-toa').textContent === 'C' &&
  document.querySelector('#cc-tang').textContent === '1' &&
  document.querySelector('#cc-ma').textContent.includes('C1')));
await kiem('Khoa Hồi Sức Cấp Cứu Nội cũ đã bỏ hẳn khỏi dữ liệu',
  async () => await p.evaluate(() => !DU_LIEU.dich.some(x => /Hồi [Ss]ức/.test(x.ten))));
await kiem('Không còn mã D23 / D24 trong danh mục',
  async () => await p.evaluate(() =>
    !DU_LIEU.dich.some(x => x.ma.includes('D23') || x.ma.includes('D24'))));

console.log('\n── D. Robot chưa sẵn sàng thì phải nói ra ──');
await p.evaluate(() => { GIA_LAP.lyDoChan = 'Robot chưa định vị được trên bản đồ.'; });
await p.evaluate(() => { veTrangChu(); const d = DU_LIEU.dich.find(x => x.ten === 'Khoa Mắt'); moChiTiet(d.id); });
await p.waitForTimeout(300);
await kiem('Nút dẫn bị làm mờ và hiện lý do',
  async () => await p.evaluate(() =>
    document.querySelector('#nut-dan').classList.contains('tat') &&
    document.querySelector('.ly-do') !== null), '08-chua-san-sang');
await p.evaluate(() => { GIA_LAP.lyDoChan = ''; });

console.log('\n── E. Nút mic chỉ hiện khi AI trả lời được ──');
await p.evaluate(() => { veTrangChu(); });
await p.waitForTimeout(200);
await kiem('AI đang TẮT → nút mic ẩn',
  async () => await p.evaluate(() => !document.querySelector('#mic1').classList.contains('co')));
await p.evaluate(() => { GIA_LAP.aiSanSang = true; window.baoAISanSang(true); });
await p.waitForTimeout(300);
await kiem('Bật AI → nút mic tự hiện, không phải tải lại trang',
  async () => await p.evaluate(() => document.querySelector('#mic1').classList.contains('co')),
  '09-mic-hien');

console.log('\n── F. Ba lớp chặn của bộ điều phối hội thoại ──');
/* Ba biểu thức chặn này nằm ở MainApplication.kt và được dựng lại y hệt trong
   gia-lap-robot.js. Bộ thử chạy qua bản giả lập, nên nó kiểm được ĐÚNG những câu
   phải bị chặn — thứ không thể bấm tay mà chắc chắn được. */
await p.evaluate(() => { GIA_LAP.aiSanSang = true; veTrangChu(); moChat(); });
await p.waitForTimeout(200);

/* Đọc câu robot THỰC SỰ NÓI, không đọc khung chat: khung chat chỉ nhận chữ khi đang
   ở màn Trò chuyện, mà câu quan trọng nhất (cấp cứu) lại chuyển sang màn đỏ ngay
   trước khi nói — bản đầu của bộ thử này báo trượt cả bảy phép kiểm vì lý do đó. */
async function kiemChan(cau, phaiCo, nhan) {
  await p.evaluate(() => { GIA_LAP.daNoi.length = 0; veTrangChu(); moChat(); });
  await p.evaluate(c => { document.querySelector('#chat-nhap').value = c; guiChat(); }, cau);
  await cho(async () => (await p.evaluate(() => GIA_LAP.daNoi.length)) > 0, 8000);
  const dap = (await p.evaluate(() => GIA_LAP.daNoi.join(' '))) || '';
  await kiem(nhan + '  «' + cau + '»', async () => phaiCo.test(dap));
  if (!phaiCo.test(dap)) console.log('    robot nói: ' + (dap.slice(0, 120) || '(im lặng)'));
}

await kiemChan('Có người ngất xỉu ở ngoài kia', /đi ngay, đừng chờ tôi dẫn/i, 'Cấp cứu → hô ngay, không dẫn');
await kiemChan('Tôi bị bệnh gì vậy',            /không khám bệnh và không đoán bệnh/i, 'Hỏi bệnh → từ chối');
await kiemChan('Khám ở đây hết bao nhiêu tiền', /chưa được nạp dữ liệu/i, 'Chưa có dữ liệu → nói thẳng');
await kiemChan('Bệnh viện mấy giờ mở cửa',      /chưa được nạp dữ liệu/i, 'Giờ làm việc → nói thẳng');
await kiemChan('Thời tiết hôm nay thế nào',     /chưa có trong dữ liệu|không dám đoán/i,
               'Câu vô nghĩa → KHÔNG được bịa ra một khoa');
await kiemChan('Tôi muốn đưa con đi khám',      /Khoa Nhi/i, 'Câu thật → chỉ đúng khoa');
await kiemChan('Phòng thu viện phí ở đâu',      /viện phí/i, 'Hỏi chỗ nộp tiền → KHÔNG bị chặn nhầm');

if (loi.length) { console.log('\n✗ Lỗi JS bắt được:'); loi.forEach(x => console.log('   ' + x)); hong += loi.length; }
console.log('\n' + (hong ? '✗ ' + hong + ' phép kiểm KHÔNG đạt' : '✓ Tất cả phép kiểm đều đạt'));
console.log('Ảnh: ' + RA);
await b.close();
process.exit(hong ? 1 : 0);
