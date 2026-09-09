/**
 * Bộ thử TẦNG TRA CỨU của app lễ tân bệnh viện.
 *
 *   node tools/thu-tim-kiem.mjs
 *
 * Vì sao tách riêng khỏi thu-luong-dan-duong.mjs: bộ kia thử LUỒNG (bấm nút, đổi
 * màn, robot nói gì). Bộ này thử một câu hỏi vào thì ra khoa nào — thứ quyết định
 * người bệnh có tới đúng chỗ hay không, và là chỗ hay hỏng nhất mỗi lần đụng vào
 * bảng từ dẫn.
 *
 * Nó nạp thẳng demo/index.html rồi gọi đúng hàm app đang chạy trên robot
 * (timDichCoDiem, chamTinCay), không dựng lại logic — dựng lại là thử một bản
 * khác với bản thật.
 *
 * ⚠ Ba loại câu phải có mặt trong danh sách dưới đây, thiếu loại nào là bộ thử
 *   mất tác dụng canh:
 *     ① câu hỏi thật, nói tự nhiên  → phải ra ĐÚNG khoa, và phải "chắc"
 *     ② câu vô nghĩa / ngoài phạm vi → phải KHÔNG THẤY, tuyệt đối không bịa
 *     ③ câu dính bẫy bỏ dấu (đâu/đau · nào/não · đóng/đông · ngất/ngạt)
 */
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, '..');
const PW = join(APP, '..', '..', 'tools', 'html-video', 'packages',
                'adapter-hyperframes', 'node_modules', 'playwright', 'index.mjs');
if (!existsSync(PW)) { console.error('Khong thay playwright tai:\n  ' + PW); process.exit(1); }
const { chromium } = await import(pathToFileURL(PW).href);

/* [câu hỏi, khoa phải ra] — null nghĩa là PHẢI không tìm thấy gì.
   Viết đúng cách người bệnh nói, kể cả từ đệm "cho tôi hỏi", "ở đâu ạ". */
const CAU = [
  // ── ① Câu hỏi thật, nói tự nhiên ─────────────────────────────────
  ['khoa nhi ở đâu',                        'Khoa Nhi'],
  ['cho tôi hỏi khoa nhi ở đâu',            'Khoa Nhi'],
  ['tôi muốn đưa con đi khám',              'Khoa Nhi'],
  ['bé nhà tôi bị sốt',                     'Khoa Nhi'],
  ['tôi đi đẻ',                             'Khoa Phụ Sản'],
  ['khám thai ở đâu ạ',                     'Khoa Phụ Sản'],
  ['vợ tôi chuyển dạ rồi',                  'Khoa Phụ Sản'],
  ['trẻ sơ sinh nằm ở đâu',                 'Khoa Sơ Sinh'],
  ['tôi bị đau bụng',                       'Khoa Nội Tiêu Hóa'],
  ['đau dạ dày khám khoa nào',              'Khoa Nội Tiêu Hóa'],
  ['tôi bị ho kéo dài',                     'Khoa Nội Phổi – Tiết Niệu – Hô Hấp'],
  ['khó thở thì khám ở đâu',                'Khoa Nội Phổi – Tiết Niệu – Hô Hấp'],
  ['đau mắt khám ở đâu',                    'Khoa Mắt'],
  ['khoa mắt ở đâu ạ',                      'Khoa Mắt'],
  ['tôi bị viêm họng',                      'Khoa Tai Mũi Họng'],
  ['cho hỏi tai mũi họng',                  'Khoa Tai Mũi Họng'],
  ['đau răng thì đi đâu',                   'Khoa Răng Hàm Mặt'],
  ['răng hàm mặt ở đâu',                    'Khoa Răng Hàm Mặt'],
  ['nhổ răng khôn',                         'Khoa Răng Hàm Mặt'],
  ['tôi bị sỏi thận',                       'Khoa Ngoại Thận – Tiết Niệu'],
  ['mổ ruột thừa ở khoa nào',               'Khoa Ngoại Tiêu Hóa – Tổng Hợp'],
  ['u não',                                 'Khoa Ngoại Thần Kinh'],
  ['ngã đập đầu',                           'Khoa Ngoại Thần Kinh'],
  ['tôi bị đau lưng',                       'Khoa Tâm Thần Kinh – Cơ Xương Khớp'],
  ['thoát vị đĩa đệm',                      'Khoa Tâm Thần Kinh – Cơ Xương Khớp'],
  ['tôi muốn châm cứu',                     'Khoa Y Học Cổ Truyền'],
  ['đông y ở đâu',                          'Khoa Y Học Cổ Truyền'],

  // ── Bốn chỗ mới ở toà A · B · C · F (08/09/2026) ─────────────────
  ['cấp cứu ở đâu',                         'Khoa Cấp cứu'],
  ['có người ngất xỉu',                     'Khoa Cấp cứu'],
  ['bị tai nạn giao thông',                 'Khoa Cấp cứu'],
  ['phòng C1 ở đâu',                        'Khoa Cấp cứu'],
  ['cho hỏi chỗ chụp x quang',              'Khoa Chẩn đoán hình ảnh'],
  ['tôi cần chụp cắt lớp',                  'Khoa Chẩn đoán hình ảnh'],
  /* Gọi ĐÚNG TÊN khoa, và mã phòng CĐHA — hai đường người bệnh hay dùng nhất
     mà lại hỏng lâu nhất. Xem mục F của tools/thu-luong-dan-duong.mjs. */
  ['khoa chẩn đoán hình ảnh ở đâu',         'Khoa Chẩn đoán hình ảnh'],
  ['chẩn đoán hình ảnh ở tầng mấy',         'Khoa Chẩn đoán hình ảnh'],
  ['phòng CĐHA ở chỗ nào',                  'Khoa Chẩn đoán hình ảnh'],
  ['CĐHA',                                  'Khoa Chẩn đoán hình ảnh'],
  /* Mơ hồ thật: cả ba nơi đều siêu âm. App phải hiện danh sách, không đoán bừa. */
  ['siêu âm ở đâu',                         ['Khoa Chẩn đoán hình ảnh']],
  ['đo điện tim ở đâu',                     'Khu Thăm dò chức năng'],
  ['thăm dò chức năng',                     'Khu Thăm dò chức năng'],

  // ── Tiện ích trong khu lễ tân ────────────────────────────────────
  ['đóng viện phí',                         'Phòng thu viện phí'],
  ['tôi cần nộp tiền',                      'Phòng thu viện phí'],
  ['lấy thuốc ở đâu',                       'Nhà thuốc bệnh viện'],
  ['nhà vệ sinh',                           'Nhà vệ sinh'],
  ['tôi muốn đăng ký khám',                 'Quầy tiếp đón · Đăng ký khám'],
  ['căn tin ở chỗ nào',                     'Căn tin'],

  // ── ② Câu KHÔNG được ra kết quả nào ──────────────────────────────
  ['thời tiết hôm nay thế nào',             null],
  ['bao giờ có tàu về hà nội',              null],
  ['hôm nay là thứ mấy',                    null],
  ['giá vàng bao nhiêu',                    null],
];

/* ③ Bẫy bỏ dấu — mấy câu này từng chỉ SAI thật, giữ riêng để không ai gỡ nhầm.
   [câu, khoa phải ra, khoa TUYỆT ĐỐI không được ra] */
const BAY_BO_DAU = [
  ['khoa nhi ở đâu',            'Khoa Nhi',              'Khoa Ngoại Thần Kinh'],
  ['u não',                     'Khoa Ngoại Thần Kinh',  null],
  ['thời tiết hôm nay thế nào', null,                    'Khoa Ngoại Thần Kinh'],
  ['đóng viện phí',             'Phòng thu viện phí',    'Khoa Y Học Cổ Truyền'],
  ['ngất xỉu',                  'Khoa Cấp cứu',          'Khoa Tai Mũi Họng'],
];

/* ══ KHO HỎI–ĐÁP CHUNG trong APK (09/09/2026) ══════════════════════════
   Mấy chuyện không gắn với khoa nào — quy trình khám, phạm vi robot, giới thiệu.
   Trước đây chúng CHỈ nằm trên cổng OrionStar, mà mô hình không đọc được kho đó
   nữa (fileSearch bị máy chủ bỏ 26/08/2025), nên robot rơi vào khoảng trống.

   [câu hỏi, nhóm phải ra] — null nghĩa là kho hỏi–đáp PHẢI im, để đường khoa
   phòng hoặc mô hình lo. Nhóm thứ hai này quan trọng ngang nhóm đầu: kho chỉ có
   tám mục, mà tám mục nói được về mọi thứ thì nó sẽ cướp việc của màn chỉ đường. */
const HOI_DAP_THU = [
  // ── Phải trả lời được, và trả lời ĐÚNG nhóm ──
  ['thủ tục khám bệnh thế nào',        'kham-lan-dau'],
  ['lần đầu tới đây tôi phải làm sao', 'kham-lan-dau'],
  ['bạn dẫn tôi lên tầng được không',  'pham-vi-robot'],
  ['bạn đi thang máy được không',      'pham-vi-robot'],
  ['robot đi được tới đâu',            'pham-vi-robot'],
  ['bạn là ai',                        'gioi-thieu-robot'],
  ['bạn tên gì',                       'gioi-thieu-robot'],
  ['bạn làm được những gì',            'gioi-thieu-robot'],
  ['bệnh viện có mấy toà nhà',         'so-toa-nha'],
  ['ở đây có những toà nào',           'so-toa-nha'],
  ['bệnh viện có những khoa nào',      'danh-muc-khoa'],
  ['cho tôi xem danh sách khoa',       'danh-muc-khoa'],
  ['tôi nên uống thuốc gì',            'khong-phai-bac-si'],
  ['tôi có cần mổ không',              'khong-phai-bac-si'],
  ['bệnh viện làm việc mấy giờ',       'chua-co-du-lieu'],
  ['khám ở đây hết bao nhiêu tiền',    'chua-co-du-lieu'],
  ['số điện thoại bệnh viện là gì',    'chua-co-du-lieu'],

  // ── Câu hỏi KHOA PHÒNG: kho hỏi–đáp phải IM, không được chen vào ──
  ['khoa nhi ở đâu',                   null],
  ['đau mắt khám ở đâu',               null],
  ['lấy thuốc ở đâu',                  null],
  ['tôi bị đau bụng',                  null],
  ['tôi đi đẻ',                        null],
  ['tôi bị ho kéo dài',                null],
  ['cấp cứu ở đâu',                    null],
  ['phòng D3 ở đâu',                   null],
  /* Ba câu dưới là chốt của luật "tra khoa phòng chắc thì kho hỏi–đáp nhường".
     CẢ HAI đường đều khớp mạnh: tra ra Quầy tiếp đón ở mức chắc, mà nhóm
     kham-lan-dau cũng ăn điểm rất cao. Đường khoa phòng phải thắng, vì nó còn
     mở được màn chỉ đường và dẫn người bệnh tới tận quầy — một câu văn thì không.
     Gỡ luật nhường ra là ba dòng này phải đỏ. */
  ['tôi đến khám lần đầu thì làm gì',  null],
  ['đăng ký khám ở đâu',               null],
  ['tôi chưa có phiếu khám',           null],

  /* ── Câu ngoài phạm vi ──
     'AN_TOAN' = được phép im, HOẶC rơi vào nhóm chua-co-du-lieu — nhưng TUYỆT ĐỐI
     không được rơi vào nhóm nào khác. Câu đáp của nhóm đó là "thông tin này tôi
     chưa có, mời quý vị hỏi quầy lễ tân", nên hỏi giá vàng mà nghe câu ấy là đúng
     việc. Bắt phải im hẳn mới là đặt sai kỳ vọng: im thì câu hỏi rơi xuống mô
     hình, mà mô hình mới là chỗ dễ bịa. */
  ['thời tiết hôm nay thế nào',        'AN_TOAN'],
  ['giá vàng bao nhiêu',               'AN_TOAN'],
  ['hôm nay là thứ mấy',               'AN_TOAN'],
  ['kể tôi nghe một câu chuyện cười',  'AN_TOAN'],
];

/* Ba câu hỏi–đáp mà robot ĐỌC RA, phải khớp từng chữ với dữ liệu — chốt chống
   sửa nhầm câu đáp thành chuỗi rỗng rồi robot đứng câm mà không ai biết. */
const HOI_DAP_PHAI_CO_CHU = ['kham-lan-dau', 'cap-cuu', 'chua-co-du-lieu'];

const b = await chromium.launch();
const p = await b.newPage();
const loiJS = [];
p.on('pageerror', e => loiJS.push('LOI JS: ' + e.message));
await p.goto(pathToFileURL(join(APP, 'demo', 'index.html')).href, { waitUntil: 'load' });
await p.waitForTimeout(400);

let hong = 0;
/* Gọi traCuu() — ĐÚNG hàm app dùng, chứ không gọi thẳng timDichCoDiem.
   Khác biệt không nhỏ: traCuu còn nhận MÃ PHÒNG trước khi chấm điểm, nên
   "phòng C1 ở đâu" đi đường mã, không đi đường từ khoá. Gọi tầng dưới là
   thử một bản khác với bản chạy trên robot. */
const tra = c => p.evaluate(cau => {
  const r = traCuu(cau, 5);
  return { muc: r.muc, ma: r.ma || null,
           ds: r.ds.map(d => ({ ten: d.ten })) };
}, c);

console.log('\n── Câu hỏi phải ra đúng khoa ──');
for (const [cau, mongDoi] of CAU) {
  const r = await tra(cau);
  const dau = r.ds[0];
  let ok;
  if (mongDoi === null) {
    ok = r.muc === 'khong-thay';
  } else if (Array.isArray(mongDoi)) {
    /* Câu MƠ HỒ THẬT (ví dụ "siêu âm ở đâu" — Phụ Sản, Thăm dò và Chẩn đoán
       hình ảnh đều siêu âm). Hành vi đúng là hiện danh sách cho người bệnh
       chọn, không phải đoán bừa một khoa. Chỉ đòi khoa mong đợi CÓ MẶT. */
    ok = r.muc !== 'khong-thay' && mongDoi.every(t => r.ds.some(x => x.ten === t));
  } else {
    /* Đúng khoa VÀ phải đứng đầu. Ra đúng nhưng xếp thứ ba thì người bệnh
       vẫn phải tự chọn giữa mấy khoa — coi như chưa đạt. */
    ok = !!dau && dau.ten === mongDoi && r.muc !== 'khong-thay';
  }
  console.log((ok ? '✓ ' : '✗ ') + '«' + cau + '» → ' +
    (r.muc === 'khong-thay' ? '(không thấy)' : r.ds.slice(0, 3).map(x => x.ten).join(' · ')) +
    (ok ? '' : '   MONG ĐỢI: ' + (mongDoi === null ? '(không thấy)'
              : Array.isArray(mongDoi) ? 'có mặt: ' + mongDoi.join(', ') : mongDoi)));
  if (!ok) hong++;
}

console.log('\n── Bẫy bỏ dấu: đâu/đau · nào/não · đóng/đông · ngất/ngạt ──');
for (const [cau, phaiRa, camRa] of BAY_BO_DAU) {
  const r = await tra(cau);
  const ten = r.ds.map(x => x.ten);
  const dungKhoa = phaiRa === null ? r.muc === 'khong-thay' : ten[0] === phaiRa;
  const sachBay = camRa === null ? true : !(r.muc !== 'khong-thay' && ten.includes(camRa));
  const ok = dungKhoa && sachBay;
  console.log((ok ? '✓ ' : '✗ ') + '«' + cau + '»  ' +
    (phaiRa ? '→ ' + phaiRa : '→ (không thấy)') +
    (camRa ? ', KHÔNG được ra ' + camRa : '') +
    (ok ? '' : '   THỰC TẾ: ' + (r.muc === 'khong-thay' ? '(không thấy)' : ten.join(' · '))));
  if (!ok) hong++;
}

console.log('\n── Kho hỏi–đáp chung nằm trong APK ──');
for (const [cau, mongDoi] of HOI_DAP_THU) {
  /* Gọi qua tomTatChoAI — ĐÚNG cửa mà Kotlin đi vào, nên phép thử này canh cả luật
     "tra khoa phòng chắc thì kho hỏi–đáp phải nhường". Gọi thẳng traHoiDap là bỏ sót
     đúng cái luật quan trọng nhất. */
  const r = await p.evaluate(q => {
    const t = JSON.parse(window.tomTatChoAI(q));
    return { hd: t.hoi_dap ? t.hoi_dap.nhom : null,
             dap: t.hoi_dap ? t.hoi_dap.dap : '' };
  }, cau);
  const ok = mongDoi === 'AN_TOAN'
    ? (r.hd === null || r.hd === 'chua-co-du-lieu')
    : r.hd === mongDoi && (mongDoi === null || r.dap.trim().length > 20);
  console.log((ok ? '✓ ' : '✗ ') + '«' + cau + '» → ' + (r.hd || '(nhường đường khác)') +
    (ok ? '' : '   MONG ĐỢI: ' + (mongDoi === null ? '(phải im)'
              : mongDoi === 'AN_TOAN' ? '(im, hoặc chua-co-du-lieu)' : mongDoi)));
  if (!ok) hong++;
}

console.log('\n── Câu đáp phải có chữ thật, không rỗng ──');
for (const nhom of HOI_DAP_PHAI_CO_CHU) {
  const dap = await p.evaluate(n => {
    const g = (typeof HOI_DAP === 'undefined' ? [] : HOI_DAP).find(x => x.nhom === n);
    return g ? g.dap : null;
  }, nhom);
  const ok = typeof dap === 'string' && dap.trim().length > 40;
  console.log((ok ? '✓ ' : '✗ ') + nhom + ' → ' +
    (dap === null ? 'KHÔNG CÓ NHÓM NÀY' : '"' + dap.slice(0, 60) + '…" (' + dap.length + ' ký tự)'));
  if (!ok) hong++;
}

if (loiJS.length) { console.log(''); loiJS.forEach(x => console.log('✗ ' + x)); hong += loiJS.length; }
const tong = CAU.length + BAY_BO_DAU.length + HOI_DAP_THU.length + HOI_DAP_PHAI_CO_CHU.length;
console.log('\n' + (hong ? '✗ ' + hong + '/' + tong + ' phép kiểm KHÔNG đạt'
                         : '✓ Cả ' + tong + ' phép kiểm đều đạt'));
await b.close();
process.exit(hong ? 1 : 0);
