/* ═══════════════════════════════════════════════════════════════════════
   GIẢ LẬP ROBOT — chỉ dùng cho bản thử trên máy tính (demo/thu-nghiem.html).
   File này KHÔNG được đóng vào APK. Trên robot thật, đối tượng CAU do tầng
   Android cấp qua addJavascriptInterface.

   Vì sao phải có: bản demo thường không có CAU, nên app tự ẩn nút dẫn đường —
   nghĩa là ba màn quan trọng nhất (đang dẫn · chỉ đường · robot tự về sảnh)
   KHÔNG THỬ ĐƯỢC trên máy tính, phải chờ mang máy ra bệnh viện mới biết đúng sai.
   Giả lập này dựng lại đúng bộ hàm và đúng trình tự báo trạng thái mà Cau.kt gửi
   lên, kèm bảng điều khiển để bắt robot gặp vật cản, gặp lỗi, hoặc tới nơi ngay.

   ⚠ Giả lập chỉ dựng lại GIAO DIỆN và TRÌNH TỰ. Nó không kiểm được bản đồ thật,
     tên điểm thật, hay robot có lách qua được lối đi hẹp không. Chạy đúng ở đây
     KHÔNG có nghĩa là chạy đúng ở bệnh viện.
   ═══════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var GL = {
    aiSanSang: false,      // AI đám mây trả lời được chưa → quyết định nút mic có hiện không
    micMo: false,
    giay: 6,               // quãng đường mô phỏng dài bao nhiêu giây
    tatDongHo: false,      // tắt đồng hồ 5 phút vắng người cho đỡ vướng lúc thử
    lyDoChan: '',          // đặt chuỗi khác rỗng để mô phỏng robot chưa sẵn sàng
    diemVeCho: '(chưa đặt)',
    dangDi: null,
    dangDoc: null,
    daNoi: []              // mọi câu robot đã nói — bộ thử tự động đọc ở đây
  };
  window.GIA_LAP = GL;

  /* Bộ thử tự động gọi GIA_LAP.khachNoi('...') để mô phỏng người bệnh nói một vế.
     Định nghĩa thật nằm trong CAU._khachNoi bên dưới; nối vào đây sau khi dựng CAU. */

  var DIEM_GIA = ['Tiep don', 'Vien phi', 'Nha thuoc', 'Can tin',
                  'Nha ve sinh', 'Truoc hanh lang', 'Sanh cho', 'Tram sac',
                  /* Bốn điểm ở toà A · B · C · F, thêm 08/09/2026 */
                  'Khoa cap cuu', 'Khu Tham do chuc nang',
                  'Khoa Rang Ham Mat', 'Khoa chan doan hinh anh'];

  /* ── Ghi nhật ký ra bảng điều khiển ───────────────────────────────── */
  function ghi(loai, chu) {
    var o = document.getElementById('gl-log');
    if (!o) return;
    var d = document.createElement('div');
    d.className = 'gl-d gl-' + loai;
    var t = new Date();
    d.textContent = ('0' + t.getMinutes()).slice(-2) + ':' + ('0' + t.getSeconds()).slice(-2) +
                    '  ' + chu;
    o.insertBefore(d, o.firstChild);
    while (o.childNodes.length > 60) o.removeChild(o.lastChild);
  }

  function batVe(id, chu) {
    var e = document.getElementById(id);
    if (e) e.textContent = chu;
  }

  /* ── Đọc thành tiếng ──────────────────────────────────────────────────
     Đồng hồ là thứ QUYẾT ĐỊNH, không phải speechSynthesis. Máy Windows thường
     không cài giọng tiếng Việt; dựa vào sự kiện onend của trình duyệt thì có
     máy không bao giờ bắn, và window.robotDocXong() sẽ không được gọi —
     kéo theo đồng hồ "robot về chỗ" không bao giờ chạy. Giọng chỉ là phần thêm. */
  function doc(vanBan) {
    dungDoc();
    ghi('noi', '🔊 ' + vanBan);
    batVe('gl-noi', vanBan);
    /* Giữ lại mọi câu robot đã nói. Bộ thử tự động đọc mảng này thay vì đọc khung
       chat: khung chat chỉ nhận chữ khi đang ở màn Trò chuyện, mà mấy câu quan
       trọng nhất (cấp cứu) lại chuyển sang màn khác ngay trước khi nói. */
    GL.daNoi.push(vanBan);
    if (GL.daNoi.length > 50) GL.daNoi.shift();
    try {
      var u = new SpeechSynthesisUtterance(vanBan);
      u.lang = 'vi-VN'; u.rate = 1;
      speechSynthesis.speak(u);
    } catch (e) { /* không có giọng cũng không sao, đã hiện chữ rồi */ }

    var giay = Math.max(1.2, vanBan.length / 15);     // ~15 ký tự mỗi giây
    GL.dangDoc = setTimeout(function () {
      GL.dangDoc = null;
      batVe('gl-noi', '—');
      if (window.robotDocXong) window.robotDocXong();
    }, giay * 1000);
  }

  function dungDoc() {
    if (GL.dangDoc) { clearTimeout(GL.dangDoc); GL.dangDoc = null; }
    try { speechSynthesis.cancel(); } catch (e) {}
    batVe('gl-noi', '—');
  }

  /* ── Dẫn đường ────────────────────────────────────────────────────────
     Dựng lại đúng trình tự Cau.kt gửi lên:
       bat-dau  →  (nhiều lần) dang-di  →  toi-noi | loi | da-dung
     và đúng quy tắc IM LẶNG dọc đường: chỉ nói một câu lúc bắt đầu, các mốc
     giữa đường chỉ đẩy CHỮ, không đọc thành tiếng. */
  function danDuongToiDiem(ten) {
    ten = (ten || '').trim();
    ghi('lenh', 'CAU.danDuongToiDiem("' + ten + '")');
    if (!ten) { window.baoDanDuong('loi', 'Chưa cấu hình điểm đến cho chỗ này.'); return; }
    if (GL.lyDoChan) {
      window.baoDanDuong('loi', GL.lyDoChan);
      doc(GL.lyDoChan);
      return;
    }
    dungDanDuong(true);
    batVe('gl-dich', ten);

    window.baoDanDuong('bat-dau', '');
    doc('Xin mời đi theo tôi.');

    var moc = [
      [0.30, 'Phía trước đang có vật cản, tôi đi vòng qua.'],
      [0.55, 'Đường đã thông, tôi đi tiếp.'],
      [0.85, 'Sắp tới nơi rồi ạ.']
    ];
    var hen = [];
    moc.forEach(function (m) {
      hen.push(setTimeout(function () {
        window.baoDanDuong('dang-di', m[1]);
      }, GL.giay * 1000 * m[0]));
    });
    hen.push(setTimeout(function () {
      GL.dangDi = null;
      batVe('gl-dich', '—');
      ghi('ok', '📍 Robot tới ' + ten);
      window.baoDanDuong('toi-noi', '');
    }, GL.giay * 1000));
    GL.dangDi = { ten: ten, hen: hen };
  }

  function huyHen() {
    if (GL.dangDi) { GL.dangDi.hen.forEach(clearTimeout); GL.dangDi = null; }
    batVe('gl-dich', '—');
  }

  function dungDanDuong(imLang) {
    huyHen();
    if (!imLang) {
      ghi('lenh', 'CAU.dungDanDuong()');
      window.baoDanDuong('da-dung', 'Tôi dừng lại rồi ạ.');
    }
  }

  /* ── Robot tự về sảnh ─────────────────────────────────────────────────
     Trên máy thật chuyến này IM LẶNG HOÀN TOÀN và không báo gì lên giao diện.
     Ở đây cũng vậy — chỉ ghi vào nhật ký để người thử biết nó có xảy ra. */
  function veCho() {
    huyHen();
    ghi('ok', '🏠 Robot tự đi về "' + GL.diemVeCho + '" (im lặng, không báo lên màn hình)');
  }

  /* ═══════════ Dựng lại BA LỚP CHẶN của TraLoi.kt ═══════════
     Ba biểu thức dưới đây phải KHỚP với ba biểu thức trong MainApplication.kt.
     Sửa một bên thì sửa cả hai — không thì bản thử nói khác robot thật, mà đó đúng
     là kiểu sai lầm khiến người ta yên tâm nhầm rồi mang máy ra bệnh viện mới vỡ.

     Ở đây chỉ dựng lại phần CHẶN. Phần gọi mô hình thì giả lập bằng câu dẫn cố định,
     vì trên máy tính không có đường lên đám mây của hãng. */
  var TU_CAP_CUU = /cấp cứu|cap cuu|nguy kịch|nguy kich|ngất|ngat xiu|bất tỉnh|bat tinh|co giật|co giat|đột quỵ|dot quy|tai biến|tai bien|không thở được|khong tho duoc|khó thở quá|kho tho qua|ngạt thở|ngat tho|chảy máu nhiều|chay mau nhieu|băng huyết|bang huyet|ngộ độc|ngo doc|hóc|sặc|tai nạn|tai nan|đau ngực dữ dội|dau nguc du doi/i;
  var TU_HOI_Y_TE = /tôi bị (bệnh )?gì|toi bi gi|em bị gì|cháu bị gì|có nặng không|co nang khong|có nguy hiểm không|co nguy hiem khong|có sao không|co sao khong|có việc gì không|uống thuốc gì|uong thuoc gi|nên uống|nen uong|dùng thuốc gì|dung thuoc gi|có phải mổ|co phai mo|có nên mổ|co nen mo|có cần mổ|chẩn đoán|chan doan|xem (giúp|hộ|giùm).{0,12}kết quả|kết quả (xét nghiệm|siêu âm|chụp).{0,20}(sao|thế nào|gì)/i;
  var TU_CHUA_CO = /bao nhiêu tiền|bao nhieu tien|hết bao nhiêu|het bao nhieu|giá khám|gia kham|chi phí|chi phi|mất bao nhiêu|mấy giờ|may gio|giờ làm việc|gio lam viec|giờ mở cửa|mở cửa lúc|đóng cửa lúc|bác sĩ nào|bac si nao|bác sỹ nào|bác sĩ tên gì|ai trực|lịch trực|lich truc|số điện thoại|so dien thoai|hotline|đặt lịch|dat lich|đặt hẹn|dat hen|đăng ký online|dang ky online|còn giường|con giuong|giường trống|giuong trong|còn chỗ nằm|bao giờ (tới|đến) lượt|khi nào (tới|đến) lượt|lịch mổ|lich mo/i;

  var LOI_CAP_CUU = 'Cấp cứu thì quý vị đi ngay, đừng chờ tôi dẫn, tôi đi chậm hơn quý vị. ' +
    'Khoa Hồi sức Cấp cứu Nội ở tầng hai, toà nhà đê ba, phòng đê hai mươi ba và đê hai mươi tư. ' +
    'Quý vị đi thẳng qua sân, sang toà nhà đê ba, lên tầng hai.';
  var LOI_HOI_Y_TE = 'Tôi là robot chỉ đường, tôi không khám bệnh và không đoán bệnh được đâu ạ. ' +
    'Quý vị cho tôi biết cần tới khoa nào, tôi chỉ đường giúp. Còn bệnh tình thì bác sĩ ở phòng khám ' +
    'mới là người trả lời được.';
  var LOI_CHUA_CO = 'Phần này tôi chưa được nạp dữ liệu nên không dám nói, sợ sai thì quý vị mất công. ' +
    'Mời quý vị hỏi quầy lễ tân giúp tôi ạ.';
  var KHONG_CO_TRONG_KHO = 'Việc này tôi chưa có trong dữ liệu nên không dám đoán, sợ chỉ sai thì ' +
    'quý vị đi nhầm cả toà nhà. Mời quý vị hỏi quầy lễ tân giúp tôi ạ.';

  function noiRaMan(cau) {
    if (window.nhanLoiNoi) window.nhanLoiNoi('robot', cau, true);
    doc(cau);
  }

  function traLoi(cau) {
    // ① cấp cứu — chặn trước mọi thứ, kể cả trước khi tra cứu
    if (TU_CAP_CUU.test(cau)) {
      ghi('loi', '⛔ CHẶN CẤP CỨU');
      if (window.moManCapCuuTuAI) window.moManCapCuuTuAI();
      noiRaMan(LOI_CAP_CUU); return;
    }
    // ② hỏi bệnh — robot không phải bác sĩ
    if (TU_HOI_Y_TE.test(cau)) { ghi('loi', '⛔ CHẶN HỎI BỆNH'); noiRaMan(LOI_HOI_Y_TE); return; }
    // ③ bệnh viện chưa cung cấp dữ liệu
    if (TU_CHUA_CO.test(cau)) { ghi('loi', '⛔ CHẶN CHƯA CÓ DỮ LIỆU'); noiRaMan(LOI_CHUA_CO); return; }

    // ④ tra kho khoa phòng — cùng hàm traCuu() mà tầng Android gọi xuống
    var r = window.traCuu ? window.traCuu(cau, 3) : null;
    if (!r || r.muc === 'ma-khong-co') {
      noiRaMan(r ? ('Tôi không tìm thấy phòng ' + r.ma + ' trong bệnh viện. Ở đây chỉ có mã phòng ' +
        'từ đê một đến đê hai mươi tư.') : KHONG_CO_TRONG_KHO);
      return;
    }
    if (r.muc === 'khong-thay' || !r.ds.length) {
      ghi('lenh', 'tra cứu: khong-thay → robot nói thẳng là không biết');
      noiRaMan(KHONG_CO_TRONG_KHO); return;
    }
    ghi('lenh', 'tra cứu: ' + r.muc + ' (d0=' + r.d0 + ', phủ=' + (r.phu || 0).toFixed(2) + ')');
    var d = r.ds[0];
    if (r.muc === 'chua-chac' && r.ds.length > 1) {
      noiRaMan('Quý vị cho tôi hỏi rõ hơn được không ạ? Có mấy nơi hợp với câu của quý vị: ' +
               r.ds.map(function (x) { return x.ten; }).join(', ') + '.');
      return;
    }
    /* Mở màn qua ĐÚNG cửa mà Cau.guiGoiYSangManHinh dùng, đừng gọi thẳng moChiTiet:
       cửa đó mở màn mà KHÔNG đọc, vì câu vị trí đã nằm sẵn trong câu TraLoi.kt đọc
       ngay dưới đây. Gọi thẳng moChiTiet là màn tự đọc thêm một lần — người bệnh
       nghe câu vị trí hai lần chồng nhau. */
    if (window.goiYTuRobot) window.goiYTuRobot(cau);
    // Câu dẫn giả lập + câu vị trí lấy NGUYÊN VĂN từ dữ liệu, đúng như TraLoi.kt ghép
    noiRaMan('Dạ tôi hiểu rồi ạ. ' + (d.vi_tri.length === 1 ? d.vi_tri[0].doc : d.doc));
  }

  /* ── Bộ hàm CAU, đúng chữ ký như Cau.kt ───────────────────────────── */
  window.CAU = {
    doc: doc,
    dungDoc: dungDoc,

    danDuongToiDiem: danDuongToiDiem,
    dungDanDuong: function () { dungDanDuong(false); },
    veCho: veCho,
    datDiemVeCho: function (t) {
      GL.diemVeCho = (t || '').trim() || '(chưa đặt)';
      ghi('lenh', 'CAU.datDiemVeCho("' + GL.diemVeCho + '")');
    },
    lyDoChuaDanDuongDuoc: function () { return GL.lyDoChan; },
    robotSanSang: function () { return !GL.lyDoChan; },
    kiemTraBanDo: function () {
      var j = JSON.stringify({ daDinhVi: true, danhSachDiem: DIEM_GIA });
      ghi('lenh', 'CAU.kiemTraBanDo() → ' + DIEM_GIA.length + ' điểm (giả lập)');
      if (window.baoTinhTrangBanDo) window.baoTinhTrangBanDo(j);
    },

    /* ── MICRO BẤM-MỚI-NGHE ──
       Dựng lại đủ hai đồng hồ bên Kotlin, không thì bản thử trên máy tính chạy
       một kiểu còn robot chạy một kiểu — mà chính chỗ lệch đó là chỗ hay hỏng.
         · 15 giây : bấm mic rồi không nói gì  → tự tắt
         · 1 giây  : dứt câu                   → tắt mic rồi mới gửi câu đi
       Bên Kotlin còn GOM VẾ: mỗi `final` mới đặt lại đồng hồ một giây. Giả lập
       cũng gom, để thử được câu nói ngắt quãng. */
    batMic: function () {
      GL.micMo = true; ghi('lenh', 'CAU.batMic()'); veBang();
      GL._ve = '';          // quên vế dở của lượt trước — ĐÚNG CHỖ, xem MainApplication
      clearTimeout(GL._henMic);
      GL._henMic = setTimeout(function () {
        if (!GL.micMo) return;
        ghi('lenh', 'Mở mic 15000 ms mà không nghe được gì — tự tắt');
        GL.micMo = false; veBang();
        if (window.baoMicTuTat) window.baoMicTuTat();
      }, 15000);
    },
    tatMic: function () {
      /* ⚠ KHÔNG xoá GL._ve ở đây. Trình tự thật là: dứt câu → tắt mic → RỒI MỚI
         gửi câu đã gom. Xoá ở đây là câu bốc hơi trước khi kịp gửi, robot đứng im
         sau khi nghe xong — đúng lỗi đã dính trên máy thật ngày 08/09/2026. */
      GL.micMo = false;
      clearTimeout(GL._henMic); GL._henMic = null;
      ghi('lenh', 'CAU.tatMic()'); veBang();
    },
    micDangMo: function () { return GL.micMo; },

    /* Mô phỏng một vế người bệnh vừa nói — thay cho onASRResult bên Kotlin.
       Bộ thử gọi GIA_LAP.khachNoi('...') để đi đúng đường thật:
         mic đóng → BỎ câu · mic mở → gom vế, hẹn 1 giây rồi tắt mic và gửi đi.
       Đặt ở giả lập chứ không ở lớp web là cố ý: bên robot thật đường này cũng
       nằm bên Kotlin, lớp web không hề biết tới nó. */
    _khachNoi: function (chu) {
      if (!GL.micMo) {
        ghi('lenh', "Nghe được '" + chu + "' nhưng mic đang đóng — bỏ qua");
        return;
      }
      if (window.nhanLoiNoi) window.nhanLoiNoi('nguoi', chu, true);
      GL._ve = (GL._ve ? GL._ve + ' ' : '') + chu;      // gom vế
      clearTimeout(GL._henMic);
      GL._henMic = setTimeout(function () {
        if (!GL.micMo) return;
        ghi('lenh', 'Người bệnh dứt câu — tự tắt mic sau 1000 ms');
        /* Gọi ĐÚNG hàm tatMic của cầu nối, rồi MỚI lấy câu ra — y hệt thứ tự bên
           Kotlin (tatMicro → guiCauDaGom). Mô phỏng bằng cách tự xoá cờ ở đây thì
           bộ thử không bao giờ bắt được lỗi "câu bị xoá trước khi gửi". */
        window.CAU.tatMic();
        if (window.baoMicTuTat) window.baoMicTuTat();
        var cau = GL._ve; GL._ve = '';
        if (cau) traLoi(cau);
        else ghi('loi', '⚠ Vế đã bị xoá trước khi kịp gửi — robot sẽ đứng im');
      }, 1000);
    },
    hoiRobot: function (c) {
      ghi('lenh', 'CAU.hoiRobot("' + c + '") → TraLoi.hoi()');
      setTimeout(function () { traLoi(c); }, 900);   // mô phỏng độ trễ gọi mô hình
    },
    xoaNguCanh: function () { ghi('lenh', 'CAU.xoaNguCanh()'); },
    moTaManHinh: function (m) { ghi('man', '🖥 ' + m); },
    thongTinAI: function () {
      return JSON.stringify({
        appId: 'app_GIA_LAP', coAgent: true,
        agentSanSang: GL.aiSanSang, micDangMo: GL.micMo
      });
    },
    thuLLM: function (c, k) {
      ghi('lenh', 'CAU.thuLLM("' + c + '", ' + k + ')');
      setTimeout(function () {
        if (window.nhanLoiNoi) {
          window.nhanLoiNoi('robot', GL.aiSanSang
            ? '[chẩn đoán] Mô hình trả lời được (status=1).'
            : '[chẩn đoán] Mô hình KHÔNG trả lời (status=0).', true);
        }
      }, 900);
    }
  };

  /* ═══════════ Bảng điều khiển ═══════════
     Dùng px chứ không dùng rem: app tự đặt lại font-size của <html> theo kích
     thước cửa sổ, bảng này mà dùng rem thì co giãn theo và méo. */
  var CSS = [
    '#gl-bang{position:fixed;left:12px;bottom:12px;z-index:9999;width:330px;',
    '  font:13px/1.45 "Segoe UI",system-ui,sans-serif;color:#E8F0EF;',
    '  background:rgba(8,26,28,.95);border:1px solid rgba(255,255,255,.22);',
    '  border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.45);overflow:hidden}',
    '#gl-bang.gon{width:auto}',
    '#gl-bang.gon .gl-than{display:none}',
    '#gl-dau{display:flex;align-items:center;gap:8px;padding:9px 12px;cursor:pointer;',
    '  background:linear-gradient(100deg,#0E5A63,#12857A);font-weight:700}',
    '#gl-dau b{flex:1}',
    '.gl-than{padding:10px 12px;max-height:70vh;overflow-y:auto}',
    '.gl-hang{display:flex;align-items:center;gap:8px;margin-bottom:7px}',
    '.gl-hang label{flex:1;opacity:.85}',
    '.gl-than button{background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.28);',
    '  border-radius:7px;padding:5px 9px;font:inherit;cursor:pointer}',
    '.gl-than button:hover{background:rgba(255,255,255,.28)}',
    '.gl-than button.tat{opacity:.45}',
    '.gl-o{background:rgba(255,255,255,.08);border-radius:7px;padding:6px 9px;margin-bottom:7px}',
    '.gl-o span{opacity:.7}',
    '.gl-vach{height:1px;background:rgba(255,255,255,.16);margin:9px 0}',
    '#gl-log{font:11px/1.4 Consolas,monospace;max-height:170px;overflow-y:auto;',
    '  background:rgba(0,0,0,.35);border-radius:7px;padding:6px 8px}',
    '.gl-d{padding:1px 0;border-bottom:1px solid rgba(255,255,255,.06);white-space:pre-wrap}',
    '.gl-noi{color:#7FE3D6}.gl-lenh{color:#FFD79A}.gl-ok{color:#9CE39C}',
    '.gl-man{color:#B9B0E6}.gl-loi{color:#FF9A9A}',
    '.gl-nhac{font-size:11px;opacity:.6;margin-top:8px;line-height:1.4}'
  ].join('');

  var HTML = [
    '<div id="gl-dau"><span>🔧</span><b>Bảng thử — giả lập robot</b><span id="gl-mui">▸</span></div>',
    '<div class="gl-than">',
    '  <div class="gl-o">Robot đang nói: <span id="gl-noi">—</span></div>',
    '  <div class="gl-o">Đang dẫn tới: <span id="gl-dich">—</span></div>',
    '  <div class="gl-hang"><label>Quãng đường dài</label>',
    '    <button data-giay="3">3 s</button><button data-giay="6" class="chon">6 s</button>',
    '    <button data-giay="20">20 s</button></div>',
    '  <div class="gl-hang"><label>Đang đi thì…</label>',
    '    <button id="gl-toi">Tới nơi ngay</button>',
    '    <button id="gl-loi">Báo lỗi</button></div>',
    '  <div class="gl-vach"></div>',
    '  <div class="gl-hang"><label>AI đám mây trả lời được<br><span style="opacity:.6">bật thì nút mic mới hiện</span></label>',
    '    <button id="gl-ai">TẮT</button></div>',
    '  <div class="gl-hang"><label>Robot sẵn sàng đi</label>',
    '    <button id="gl-san">CÓ</button></div>',
    '  <div class="gl-hang"><label>Đồng hồ 5 phút vắng người</label>',
    '    <button id="gl-dh">BẬT</button></div>',
    '  <div class="gl-hang"><label>Điểm robot về đứng</label>',
    '    <span id="gl-vecho" style="opacity:.8">—</span></div>',
    '  <div class="gl-vach"></div>',
    '  <div id="gl-log"></div>',
    '  <div class="gl-nhac">Đây là bản THỬ trên máy tính. Robot ở đây là giả lập —',
    '  nó dựng lại giao diện và trình tự, không kiểm được bản đồ thật hay lối đi thật.</div>',
    '</div>'
  ].join('');

  function veBang() {
    var b = document.getElementById('gl-ai');
    if (!b) return;
    b.textContent = GL.aiSanSang ? 'BẬT' : 'TẮT';
    b.className = GL.aiSanSang ? '' : 'tat';
    document.getElementById('gl-san').textContent = GL.lyDoChan ? 'KHÔNG' : 'CÓ';
    document.getElementById('gl-san').className = GL.lyDoChan ? 'tat' : '';
    document.getElementById('gl-dh').textContent = GL.tatDongHo ? 'TẮT' : 'BẬT';
    document.getElementById('gl-dh').className = GL.tatDongHo ? 'tat' : '';
    document.getElementById('gl-vecho').textContent = GL.diemVeCho;
  }

  GL.khachNoi = function (chu) { window.CAU._khachNoi(chu); };

  function dungBang() {
    var s = document.createElement('style'); s.textContent = CSS;
    document.head.appendChild(s);
    var d = document.createElement('div'); d.id = 'gl-bang'; d.innerHTML = HTML;
    /* Mở lên là THU GỌN sẵn. Bảng này nằm đè lên góc dưới-trái, mà đó đúng là chỗ
       màn chỉ đường đặt mũi tên và câu "Mời quý vị đi thẳng" — để bung sẵn thì
       người duyệt giao diện nhìn không ra app trông thế nào. */
    d.className = 'gon';
    document.body.appendChild(d);

    document.getElementById('gl-dau').onclick = function () {
      d.classList.toggle('gon');
      document.getElementById('gl-mui').textContent = d.classList.contains('gon') ? '▸' : '▾';
    };
    Array.prototype.forEach.call(d.querySelectorAll('[data-giay]'), function (b) {
      b.onclick = function () {
        GL.giay = +b.dataset.giay;
        Array.prototype.forEach.call(d.querySelectorAll('[data-giay]'),
          function (x) { x.className = x === b ? 'chon' : ''; });
        ghi('lenh', 'Quãng đường mô phỏng = ' + GL.giay + ' giây');
      };
    });
    document.getElementById('gl-toi').onclick = function () {
      if (!GL.dangDi) { ghi('loi', 'Robot có đang đi đâu mà tới nơi'); return; }
      var ten = GL.dangDi.ten; huyHen();
      ghi('ok', '📍 Robot tới ' + ten + ' (bấm tay)');
      window.baoDanDuong('toi-noi', '');
    };
    document.getElementById('gl-loi').onclick = function () {
      if (!GL.dangDi) { ghi('loi', 'Robot không đi thì lấy gì mà lỗi'); return; }
      huyHen();
      var loi = 'Tôi không tìm được đường tới đó. Mời quý vị hỏi quầy lễ tân giúp tôi.';
      ghi('loi', '✗ ' + loi);
      window.baoDanDuong('loi', loi);
      doc(loi);
    };
    document.getElementById('gl-ai').onclick = function () {
      GL.aiSanSang = !GL.aiSanSang;
      ghi('lenh', 'AI sẵn sàng = ' + GL.aiSanSang);
      veBang();
      if (window.baoAISanSang) window.baoAISanSang(GL.aiSanSang);
    };
    document.getElementById('gl-san').onclick = function () {
      GL.lyDoChan = GL.lyDoChan ? ''
        : 'Robot chưa định vị được trên bản đồ. Mời quý vị hỏi quầy lễ tân giúp tôi.';
      ghi('lenh', 'Robot sẵn sàng = ' + !GL.lyDoChan);
      veBang();
    };
    document.getElementById('gl-dh').onclick = function () {
      GL.tatDongHo = !GL.tatDongHo;
      ghi('lenh', 'Đồng hồ 5 phút = ' + (GL.tatDongHo ? 'TẮT' : 'BẬT'));
      veBang();
    };
    veBang();
    ghi('ok', 'Giả lập robot đã bật. Mở một khoa rồi bấm nút dẫn đường.');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', dungBang);
  } else {
    dungBang();
  }

  /* Tắt đồng hồ 5 phút khi người thử yêu cầu: chặn ngay ở setTimeout thay vì
     sửa mã app — bản thử phải chạy đúng mã của bản thật, không được rẽ nhánh. */
  var setTimeoutGoc = window.setTimeout;
  window.setTimeout = function (f, ms) {
    if (GL.tatDongHo && ms === 5 * 60 * 1000) return -1;
    return setTimeoutGoc.apply(window, arguments);
  };
})();
