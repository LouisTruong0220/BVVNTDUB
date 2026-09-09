# -*- coding: utf-8 -*-
"""Sinh du-lieu/app-data.json cho app lễ tân Bệnh viện Việt Nam – Thụy Điển Uông Bí.

Nguồn: 10-project/Benh-vien-Uong-Bi/01-khao-sat/huong-dan-robot-le-tan-ai-benh-vien.docx
       (bệnh viện cung cấp — 24 mã phòng D1–D24, 16 khoa, 3 toà DI/DII/DIII)
       + sơ đồ mặt bằng vẽ tay 01-khao-sat/anh/so-do-mat-bang-ve-tay.jpg

Vì sao bảng gõ thẳng vào script chứ không đọc từ DOCX: bảng chỉ có 24 dòng và gần như
không đổi. Đọc DOCX thì mỗi lần bệnh viện gửi bản Word mới lại phải sửa bộ bóc bảng —
tốn hơn là sửa 24 dòng ở đây. Đổi cơ cấu khoa phòng thì sửa BANG_KHOA rồi chạy lại.

Chạy:  python dung-du-lieu.py     (rồi chạy tiếp dung-app.py)
"""
import io, os, re, sys, json, unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(HERE, "du-lieu", "app-data.json")

# ═══════════════════════════════════════════════════════════════════════
#  ĐIỂM TRÊN BẢN ĐỒ ROBOT
#
#  ⚠ `diem_ban_do` phải trùng TỪNG KÝ TỰ với tên điểm kỹ thuật đặt lúc quét map:
#    không dấu tiếng Việt, đúng hoa/thường, đúng một dấu cách. Sai một ký tự là
#    robot ném ERROR_DESTINATION_NOT_EXIST và đứng im.
#    Xem huong-dan-dat-ten-diem-ban-do.md.
#
#  Khảo sát xong thấy quãng sảnh → trước cửa DI có bậc/dốc/không mái che thì
#  ĐỔI ĐÚNG MỘT DÒNG dưới đây (điểm 'truoc-hanh-lang' lùi về 'Cua sanh'), không phải sửa code.
# ═══════════════════════════════════════════════════════════════════════
#
#  ⚠ KHÔNG dùng màu ĐỎ ở bảng này. Đỏ được giữ riêng cho màn cấp cứu — một màn đỏ toàn
#    khung chỉ còn sức cảnh báo khi phần còn lại của app không đỏ.
DIEM = {
    "tiep-don":     {"ten": "Quầy tiếp đón · Đăng ký khám", "diem_ban_do": "Tiep don",     "mau": "#B5651D"},
    "vien-phi":     {"ten": "Phòng thu viện phí",           "diem_ban_do": "Vien phi",     "mau": "#B8860B"},
    "nha-thuoc":    {"ten": "Nhà thuốc bệnh viện",          "diem_ban_do": "Nha thuoc",    "mau": "#1F6F5C"},
    "can-tin":      {"ten": "Căn tin",                      "diem_ban_do": "Can tin",      "mau": "#7A5AA6"},
    "nha-ve-sinh":  {"ten": "Nhà vệ sinh",                  "diem_ban_do": "Nha ve sinh",  "mau": "#2B5C9B"},
    # ⚠ Robot dừng ở ĐẦU HÀNH LANG, chưa tới cửa toà DI. Đổi 17/08/2026 sau khi anh
    #   Trường xem lại mặt bằng. Vì thế câu chỉ đường KHÔNG được nói "toà nhà trước mặt"
    #   nữa mà phải ĐẾM THỨ TỰ toà nhà dọc hành lang — xem cau_chi_duong().
    "truoc-hanh-lang": {"ten": "Đầu hành lang", "diem_ban_do": "Truoc hanh lang", "mau": "#0E5A63"},

    # ── Bốn chỗ ở các toà A · B · C · F (bổ sung 08/09/2026) ─────────────
    # Khác 16 khoa trong ba toà D: mấy chỗ này robot ĐI TỚI TẬN NƠI, không
    # dừng ở đầu hành lang rồi chỉ đường. Anh Trường xác nhận bản đồ robot
    # ĐÃ CÓ sẵn hai điểm cấp cứu và chẩn đoán hình ảnh; hai điểm còn lại
    # anh đặt thêm.
    # ⚠ Tên dưới đây phải khớp tên THẬT trên bản đồ. App không tự sửa tên,
    #   nhưng RobotHelper nay dò khớp mềm (bỏ dấu, không phân biệt hoa
    #   thường) nên viết "Khoa cap cuu" hay "Khoa Cấp cứu" đều tìm ra.
    #   Kiểm bằng CAU.kiemTraBanDo() trên máy thật, đừng tin bằng mắt.
    "khoa-cap-cuu":   {"ten": "Khoa Cấp cứu",             "diem_ban_do": "Khoa cap cuu",              "mau": "#7A4B2A"},
    "tham-do-cn":     {"ten": "Khu Thăm dò chức năng",    "diem_ban_do": "Khu Tham do chuc nang",     "mau": "#5A6E8C"},
    "rang-ham-mat":   {"ten": "Khoa Răng Hàm Mặt",        "diem_ban_do": "Khoa Rang Ham Mat",         "mau": "#3F7A6B"},
    # ⚠ "chuẩn đoán" là lỗi chính tả rất phổ biến của "chẩn đoán" — và đó chính là
    #   tên đang đặt trên bản đồ bệnh viện. Dò mềm chỉ bỏ DẤU, không sửa CHÍNH TẢ:
    #   "chuan doan" và "chan doan" là hai chuỗi khác nhau. Xem BI_DANH_DIEM.
    "chan-doan-ha":   {"ten": "Khoa Chẩn đoán hình ảnh",  "diem_ban_do": "Khoa chan doan hinh anh",   "mau": "#6B5B95"},
}

# ═══════════════════════════════════════════════════════════════════════
#  BÍ DANH ĐIỂM BẢN ĐỒ — những tên KHÁC mà cùng chỉ một chỗ
#
#  ⚠ VÌ SAO CẦN (09/09/2026): anh Trường báo mọi khoa dẫn đường được, riêng Khoa
#    Chẩn đoán hình ảnh thì không. Đó là điểm DUY NHẤT đã có sẵn trên bản đồ từ
#    trước — ba điểm kia bệnh viện mới đặt theo tên app đưa ra.
#
#    Bản đồ bệnh viện đặt tên CÓ DẤU, và dấu KHÔNG phải vấn đề: bộ dò mềm của
#    RobotHelper bỏ dấu trước khi so, đã đo cả 12 điểm đều khớp. Thứ nó KHÔNG làm
#    được là sửa CHÍNH TẢ:
#        "khoa chuan doan hinh anh"  ≠  "khoa chan doan hinh anh"
#    Robot nhận lệnh rồi ném ERROR_DESTINATION_NOT_EXIST và đứng im — nhìn từ ngoài
#    y hệt máy hỏng, mà lại chỉ hỏng đúng một khoa nên rất khó lần ra.
#
#  Khai bí danh ở đây thì app chạy được với CẢ HAI cách viết, không phải nhờ ai ra
#  hiện trường sửa lại bản đồ. Viết bí danh y như nó nằm trên bản đồ; so khớp vẫn
#  bỏ dấu và không phân biệt hoa thường nên không cần khai đủ mọi biến thể.
#
#  ⚠ Bí danh là cái LƯỚI ĐỠ, không phải cách đặt tên. Bản đồ mới thì cứ đặt đúng
#    tên ở cột diem_ban_do — xem huong-dan-dat-ten-diem-ban-do.md.
# ═══════════════════════════════════════════════════════════════════════
BI_DANH_DIEM = {
    "chan-doan-ha": [
        "Khoa chuan doan hinh anh",   # lỗi chính tả phổ biến, đang dùng trên bản đồ BV
        "Chan doan hinh anh",         # thiếu chữ "Khoa"
        "Chuan doan hinh anh",
        "Khoa CDHA",
    ],
    "khoa-cap-cuu": ["Cap cuu", "Khoa cap cuu C1", "Phong cap cuu"],
    "tham-do-cn":   ["Tham do chuc nang", "Khoa Tham do chuc nang"],
    "rang-ham-mat": ["Rang Ham Mat", "Khoa rang ham mat D7"],
}
for _k, _bd in BI_DANH_DIEM.items():
    if _k not in DIEM:
        print("   ! BI_DANH_DIEM khai điểm '%s' không có trong DIEM" % _k)
        raise SystemExit(1)
    DIEM[_k]["bi_danh"] = _bd
for _k in DIEM:
    DIEM[_k].setdefault("bi_danh", [])
DIEM_VE_CHO = "Sanh cho"   # chỗ robot tự quay về sau khi dẫn xong

# ═══════════════════════════════════════════════════════════════════════
#  MƯỜI NHÓM TRÊN MÀN HÌNH CHÍNH
#
#  Chia theo cách NGƯỜI BỆNH tự mô tả, không theo tên khoa. Người dân biết mình
#  "đau bụng", "đưa con đi khám", "đi đẻ" — không ai biết "Khoa Ngoại Tiêu Hoá Tổng Hợp".
# ═══════════════════════════════════════════════════════════════════════
NHOM = [
    {"ma": "me-be",        "ten": "Mẹ và bé",                  "icon": "👶",
     "goi_y": "Đi đẻ, khám thai, trẻ sơ sinh"},
    {"ma": "tre-em",       "ten": "Trẻ em",                    "icon": "🧒",
     "goi_y": "Đưa con đi khám, bé sốt, bé ho"},
    {"ma": "mat-tai-rang", "ten": "Mắt · Tai mũi họng · Răng", "icon": "👁️",
     "goi_y": "Đau mắt, viêm họng, đau răng"},
    {"ma": "noi-khoa",     "ten": "Khám bên trong (nội khoa)", "icon": "🫁",
     "goi_y": "Đau bụng, dạ dày, ho, khó thở, thận"},
    {"ma": "ngoai-khoa",   "ten": "Phải mổ (ngoại khoa)",      "icon": "🔪",
     "goi_y": "Mổ ruột thừa, sỏi thận, chấn thương đầu"},
    {"ma": "xuong-khop",   "ten": "Xương khớp · Thần kinh · Đông y", "icon": "🦴",
     "goi_y": "Đau lưng, thoát vị đĩa đệm, châm cứu"},
    {"ma": "cap-cuu",      "ten": "CẤP CỨU",                   "icon": "🚨",
     "goi_y": "Nguy kịch, cần cấp cứu ngay"},
    {"ma": "tien-ich",     "ten": "Viện phí · Thuốc · Tiện ích", "icon": "💳",
     "goi_y": "Đóng tiền, lấy thuốc, căn tin, nhà vệ sinh"},
    {"ma": "chieu-chup",   "ten": "Xét nghiệm · Chiếu chụp",   "icon": "🩻",
     "goi_y": "Chụp X-quang, siêu âm, điện tim, nội soi"},
    {"ma": "hanh-chinh",   "ten": "Hành chính · Khác",         "icon": "🏛️",
     "goi_y": "Phòng ban, giải phẫu bệnh, xin giấy tờ"},
]

# ═══════════════════════════════════════════════════════════════════════
#  BẢNG KHOA PHÒNG — nguồn DOCX của bệnh viện
#
#  vi_tri: mỗi phần tử là một chỗ khoa đó có mặt. Nhiều hơn một phần tử nghĩa là
#          khoa nằm ở nhiều toà — app sẽ hỏi lại người bệnh đang theo dõi ở toà nào,
#          đúng như mục IV của tài liệu bệnh viện yêu cầu.
# ═══════════════════════════════════════════════════════════════════════
BANG_KHOA = [
    # ── Mẹ và bé ──────────────────────────────────────────────────────
    dict(ten="Khoa Phụ Sản", nhom="me-be", ghi_chu="Sản phụ khoa, sinh đẻ",
         vi_tri=[("DI", 1, ["D1", "D2"]), ("DII", 1, ["D11", "D12"]), ("DIII", 1, ["D21", "D22"])],
         tu_dan="de sinh con sinh de kham thai bau chua thai san phu khoa mang thai sieu am thai "
                "chuyen da vo oi dau de san khoa"),
    dict(ten="Khoa Sơ Sinh", nhom="me-be", ghi_chu="Chăm sóc trẻ sơ sinh",
         vi_tri=[("DII", 2, ["D14"])],
         tu_dan="tre so sinh em be moi de be moi sinh long ap so sinh vang da tre thieu thang"),

    # ── Trẻ em ────────────────────────────────────────────────────────
    dict(ten="Khoa Nhi", nhom="tre-em", ghi_chu="Nhi khoa, trẻ em",
         vi_tri=[("DI", 2, ["D3", "D4"]), ("DII", 2, ["D13"])],
         tu_dan="tre em con nho em be chau be nhi khoa be sot be ho be tieu chay "
                "dua con di kham kham cho con tre nho"),

    # ── Mắt · Tai mũi họng · Răng ─────────────────────────────────────
    dict(ten="Khoa Mắt", nhom="mat-tai-rang", ghi_chu="Nhãn khoa",
         vi_tri=[("DI", 5, ["D9"])],
         tu_dan="mat dau mat mo mat can thi vien duc thuy tinh the mong thit nhan khoa "
                "do mat ngua mat kham mat do kinh"),
    dict(ten="Khoa Tai Mũi Họng", nhom="mat-tai-rang", ghi_chu="Tai, mũi, họng (TMH)",
         vi_tri=[("DI", 5, ["D10"])],
         tu_dan="tai mui hong tmh viem hong u tai ngat mui viem xoang amidan "
                "khan tieng chay mau cam diec noi soi tai mui hong"),
    # Khoa Răng Hàm Mặt ĐÃ CHUYỂN sang Nhà B tầng 1 — xem BANG_TOA_KHAC bên dưới.
    # Anh Trường chốt 08/09/2026 theo tài liệu mới của bệnh viện; tài liệu gốc
    # ghi D7 ở Nhà DI tầng 4, nay không còn đúng.

    # ── Nội khoa ──────────────────────────────────────────────────────
    dict(ten="Khoa Nội Tiêu Hóa", nhom="noi-khoa", ghi_chu="Tiêu hóa nội khoa",
         vi_tri=[("DI", 4, ["D8"])],
         tu_dan="dau bung da day dai trang tieu hoa o chua tao bon gan "
                "noi soi da day viem loet da day roi loan tieu hoa dau da day"),
    dict(ten="Khoa Nội Phổi – Tiết Niệu – Hô Hấp", nhom="noi-khoa", ghi_chu="Hô hấp, phổi, tiết niệu",
         vi_tri=[("DII", 4, ["D17", "D18"])],
         tu_dan="ho kho tho phoi hen suyen viem phoi ho hap than tieu buot soi than "
                "tiet nieu tuc nguc lao phoi kho tho ve dem di tieu nhieu "
                # Cách người bệnh thật sự kể bệnh — thêm 08/09/2026 sau khi bộ thử
                # tra cứu bắt được "tôi bị ho kéo dài" không ra khoa nào.
                "ho keo dai ho lau ngay ho ra mau ho khan tuc nguc kho tho khi gang suc"),

    # ── Ngoại khoa ────────────────────────────────────────────────────
    dict(ten="Khoa Ngoại Thận – Tiết Niệu", nhom="ngoai-khoa", ghi_chu="Phẫu thuật thận, tiết niệu",
         vi_tri=[("DI", 3, ["D5"])],
         tu_dan="mo than soi than tan soi mo tiet nieu phi dai tuyen tien liet "
                "ngoai than soi nieu quan soi bang quang"),
    dict(ten="Khoa Ngoại Tiêu Hóa – Tổng Hợp", nhom="ngoai-khoa", ghi_chu="Ngoại tiêu hóa tổng hợp",
         vi_tri=[("DI", 3, ["D6"])],
         tu_dan="mo ruot thua mo bung thoat vi tri mo da day ngoai tong hop "
                "phau thuat mo noi soi o bung cat tui mat"),
    dict(ten="Khoa Ngoại Thần Kinh", nhom="ngoai-khoa", ghi_chu="Ngoại thần kinh, não bộ",
         vi_tri=[("DII", 3, ["D16"])],
         tu_dan="chan thuong so nao mo nao u nao cot song ngoai than kinh "
                "nga dap dau chan thuong dau mo cot song"),

    # ── Xương khớp · Thần kinh · Đông y ───────────────────────────────
    dict(ten="Khoa Tâm Thần Kinh – Cơ Xương Khớp", nhom="xuong-khop", ghi_chu="Tâm thần, xương khớp",
         vi_tri=[("DII", 5, ["D19", "D20"])],
         # "dau dau" để ở đây chứ không để bên Ngoại Thần Kinh: đau đầu không do va đập
         # là chuyện nội khoa, còn Ngoại Thần Kinh là nơi mổ. Cả hai vẫn cùng hiện trong
         # danh sách kết quả, chỉ khác thứ tự.
         tu_dan="dau lung thoat vi dia dem khop dau khop tai bien dot quy mat ngu "
                "tam than than kinh dau vai gay te chan te tay gut viem khop "
                "dau dau hoa mat chong mat run tay"),
    dict(ten="Khoa Y Học Cổ Truyền", nhom="xuong-khop", ghi_chu="Y học cổ truyền, châm cứu",
         vi_tri=[("DII", 3, ["D15"])],
         tu_dan="dong y cham cuu thuoc nam thuoc bac bam huyet xoa bop "
                "phuc hoi chuc nang y hoc co truyen keo gian cot song"),

    # ── Cấp cứu ───────────────────────────────────────────────────────
    # Khoa Hồi Sức Cấp Cứu Nội (D23-D24, tầng 2 Nhà DIII) ĐÃ BỎ KHỎI APP
    # ngày 08/09/2026 theo yêu cầu anh Trường.
    #
    # ⚠ Đó là khoa KHÁC với "Khoa Cấp cứu" C1 ở Nhà C: một bên là nơi tiếp
    #   nhận người nguy kịch, một bên là khoa hồi sức điều trị nội trú. Để cả
    #   hai trong nút CẤP CỨU thì người đang hoảng phải đọc và chọn — mất đúng
    #   những giây quý nhất. Nay nút cấp cứu chỉ ra một chỗ duy nhất: C1, Nhà C.
    #   Khoa cấp cứu nằm ở BANG_TOA_KHAC bên dưới.

    # ── Hành chính · Khác ─────────────────────────────────────────────
    dict(ten="Khoa Giải Phẫu Bệnh", nhom="hanh-chinh", ghi_chu="Giải phẫu, sinh thiết bệnh lý",
         vi_tri=[("DIII", 2, [])],
         tu_dan="sinh thiet giai phau benh xet nghiem mo te bao ket qua sinh thiet"),
    dict(ten="Các Phòng Ban Hành Chính", nhom="hanh-chinh",
         ghi_chu="Kế hoạch tổng hợp, điều dưỡng, chăm sóc khách hàng, marketing, truyền thông",
         vi_tri=[("DIII", 3, [])],
         tu_dan="hanh chinh ke hoach tong hop dieu duong cham soc khach hang marketing "
                "truyen thong giam doc ban lanh dao xin giay to xac nhan phong ban"),
]

# ═══════════════════════════════════════════════════════════════════════
#  BỐN CHỖ Ở CÁC TOÀ A · B · C · F — robot dẫn THẲNG tới nơi
#  (bổ sung 08/09/2026, nguồn: "Thông tin phòng cần thêm.docx")
#
#  Khác 16 khoa trong ba toà D ở chỗ nào: ba toà D nằm cuối hành lang, robot
#  chỉ đi được tới ĐẦU hành lang rồi đứng đó chỉ đường bằng lời. Còn bốn chỗ
#  này bản đồ robot có điểm riêng nên robot đi tới TẬN NƠI — người bệnh chỉ
#  việc đi theo, không phải nhớ "toà thứ mấy, tầng mấy".
#
#  ⚠ Vì robot đi thật nên quãng đường tới bốn chỗ này phải đạt điều kiện của
#    máy trong nhà: bậc ≤ 2 cm · dốc ≤ 5° · sàn phẳng liền mạch · có mái che.
#    Chỗ nào không đạt thì BỎ trường `diem` của chỗ đó đi (để None), app sẽ tự
#    chuyển sang chỉ đường bằng lời thay vì dẫn.
# ═══════════════════════════════════════════════════════════════════════
BANG_TOA_KHAC = [
    dict(ten="Khoa Cấp cứu", nhom="cap-cuu", diem="khoa-cap-cuu", loai="cap-cuu",
         toa="C", tang=1, ma=["C1"],
         ghi_chu="Tiếp nhận, xử trí ban đầu ca nguy kịch — trực 24/7",
         tu_dan="cap cuu khan cap nguy kich ngat xiu ngat xiu bat tinh co giat "
                "tai nan giao thong tai nan lao dong ngo doc dot quy ngung tuan hoan "
                "kho tho nang chay mau nhieu sap chet cuu voi"),

    dict(ten="Khu Thăm dò chức năng", nhom="chieu-chup", diem="tham-do-cn",
         toa="A", tang=1, ma=[],
         ghi_chu="Điện tim, siêu âm tim, điện cơ, điện não, nội soi thường",
         tu_dan="tham do chuc nang dien tim sieu am tim dien co dien nao noi soi "
                "do dien tim dien tam do do chuc nang"),

    dict(ten="Khoa Răng Hàm Mặt", nhom="mat-tai-rang", diem="rang-ham-mat",
         toa="B", tang=1, ma=["D7"],
         ghi_chu="Sâu răng, viêm tuỷ, nhổ răng khôn, chỉnh hình hàm mặt",
         tu_dan="rang dau rang nho rang sau rang ham mat nha khoa nieng rang "
                "chua rang han rang lam rang loi sung viem tuy rang khon chinh hinh ham mat"),

    dict(ten="Khoa Chẩn đoán hình ảnh", nhom="chieu-chup", diem="chan-doan-ha",
         toa="F", tang=1, ma=["CĐHA"],
         ghi_chu="X-quang, siêu âm, CT, MRI",
         tu_dan="chan doan hinh anh chup x quang xquang chup phim sieu am chup ct "
                "chup em ra ai mri chieu chup chup chieu chup cat lop cong huong tu"),
]

# ═══════════════════════════════════════════════════════════════════════
#  TIỆN ÍCH TRONG KHU LỄ TÂN — robot dẫn THẲNG tới nơi
# ═══════════════════════════════════════════════════════════════════════
BANG_TIEN_ICH = [
    dict(ten="Quầy tiếp đón · Đăng ký khám", nhom="tien-ich", diem="tiep-don",
         ghi_chu="Lấy số, xuất trình bảo hiểm, đăng ký khám",
         tu_dan="dang ky kham lay so kham lan dau bao hiem bhyt the bao hiem tiep don "
                "phieu kham dat lich chua co phieu moi den kham",
         doc="Quầy tiếp đón ở ngay trong khu lễ tân. Quý vị tới đó lấy số, xuất trình thẻ bảo hiểm "
             "và đăng ký khám. Tôi dẫn quý vị tới nơi."),
    dict(ten="Phòng thu viện phí", nhom="tien-ich", diem="vien-phi",
         ghi_chu="Đóng tiền, thanh toán viện phí, lấy hoá đơn",
         tu_dan="dong tien thanh toan vien phi thu ngan nop tien hoa don thanh toan vien phi "
                "tra tien quyet toan bao hiem",
         doc="Phòng thu viện phí ở trong khu lễ tân. Tôi dẫn quý vị tới nơi."),
    dict(ten="Nhà thuốc bệnh viện", nhom="tien-ich", diem="nha-thuoc",
         ghi_chu="Lấy thuốc theo đơn, mua thuốc",
         tu_dan="lay thuoc mua thuoc nha thuoc quay thuoc don thuoc hieu thuoc "
                "linh thuoc thuoc bao hiem",
         doc="Nhà thuốc bệnh viện ở trong khu lễ tân. Quý vị nhớ mang theo đơn thuốc. "
             "Tôi dẫn quý vị tới nơi."),
    dict(ten="Căn tin", nhom="tien-ich", diem="can-tin",
         ghi_chu="Ăn uống, nước, đồ dùng cho người nhà",
         tu_dan="an uong nuoc com can tin cang tin quan an do an mua nuoc chao chay",
         doc="Căn tin ở trong khu lễ tân. Tôi dẫn quý vị tới nơi."),
    dict(ten="Nhà vệ sinh", nhom="tien-ich", diem="nha-ve-sinh",
         ghi_chu="Nhà vệ sinh khu lễ tân",
         tu_dan="nha ve sinh wc toilet di ve sinh nha xi rua tay di nang di nhe",
         doc="Nhà vệ sinh ở trong khu lễ tân. Tôi dẫn quý vị tới nơi."),
]

# Quy trình 4 bước cho người tới khám lần đầu.
# ⚠ Robot KHÔNG đoán bệnh, không tư vấn y tế — chỉ chỉ đúng chỗ đăng ký.
QUY_TRINH_KHAM = {
    "tieu_de": "Quý vị đến khám lần đầu, chưa có phiếu",
    "diem": "tiep-don",
    "buoc": [
        ["Đăng ký khám", "Tới quầy tiếp đón, lấy số, xuất trình căn cước và thẻ bảo hiểm y tế nếu có."],
        ["Vào khám",     "Nhân viên ghi phiếu khám có mã phòng, quý vị mang phiếu tới đúng phòng đó."],
        ["Xét nghiệm, chiếu chụp", "Bác sĩ chỉ định thì quý vị làm theo phiếu, xong quay lại phòng khám."],
        ["Đóng tiền, lấy thuốc", "Đóng viện phí tại phòng thu, rồi tới nhà thuốc lấy thuốc theo đơn."],
    ],
    "doc": "Quý vị đến khám lần đầu thì mời tới quầy tiếp đón trước. Ở đó quý vị lấy số, "
           "xuất trình căn cước và thẻ bảo hiểm y tế. Nhân viên sẽ ghi phiếu khám có mã phòng. "
           "Quý vị mang phiếu đó tới đúng phòng khám. Khám xong, đóng tiền tại phòng thu viện phí, "
           "rồi tới nhà thuốc lấy thuốc. Bây giờ tôi dẫn quý vị tới quầy tiếp đón.",
}

# ═══════════════════════════════════════════════════════════════════════
#  Công cụ
# ═══════════════════════════════════════════════════════════════════════
SO_CHU = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười"]

# Ba toà D nằm cuối hành lang — robot chỉ ra tới đầu hành lang rồi chỉ đường.
# Bốn toà A · B · C · F có điểm riêng trên bản đồ — robot đi tới tận nơi.
TOA_CHU = {"DI": "đê một", "DII": "đê hai", "DIII": "đê ba",
           "A": "a", "B": "bê", "C": "xê", "F": "ép"}
TOA_TEN = {"DI": "Nhà DI", "DII": "Nhà DII", "DIII": "Nhà DIII",
           "A": "Nhà A", "B": "Nhà B", "C": "Nhà C", "F": "Nhà F"}
TOA_TANG = {"DI": 5, "DII": 5, "DIII": 8}   # số tầng, chỉ ba toà D là biết chắc

# ⚠ CHỖ CẦN ĐIỀN SAU KHẢO SÁT — hướng đi tới bốn toà mới, tính từ chỗ robot
#   đứng. Để rỗng thì robot chỉ đọc tên toà (an toàn, không chỉ sai). Điền vào
#   thì robot nói thêm hướng, ví dụ "bên tay phải quý vị" / "phía đài phun nước".
#   ĐỪNG đoán bừa: chỉ sai hướng cho một ca cấp cứu là mất những giây quý nhất.
HUONG_TOA = {"A": "", "B": "", "C": "", "F": ""}

# Thứ tự các toà nhà tính từ ĐẦU HÀNH LANG — chỗ robot dừng lại.
# ⚠ Đây là thứ người bệnh thật sự dùng để tìm đường: đứng ở đầu hành lang thì ba toà
#   nhà trông giống hệt nhau, đọc tên "DII" trên biển thì xa quá không thấy, nhưng
#   đếm "toà thứ hai" thì ai cũng đếm được. Khảo sát lại mặt bằng mà thứ tự khác đi
#   thì sửa đúng bảng này.
TOA_THU_TU = {"DI": 1, "DII": 2, "DIII": 3}
THU_TU_CHU = {1: "đầu tiên", 2: "thứ hai", 3: "thứ ba"}


def khong_dau(s):
    """Bỏ dấu tiếng Việt, hạ chữ thường, chỉ giữ chữ-số-khoảng trắng."""
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d").replace("Đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


# Mã phòng không theo khuôn "chữ cái + số" thì khai thẳng cách đọc ở đây.
# CĐHA là viết tắt của Chẩn đoán hình ảnh — đánh vần từng chữ cái thì người
# nghe không hiểu, mà đọc trại cũng không ra. Đọc luôn nghĩa của nó.
# None = có mã, nhưng KHÔNG đọc ra tiếng. CĐHA là viết tắt của chính tên khoa
# nên đọc lên thành "Khoa Chẩn đoán hình ảnh... phòng chẩn đoán hình ảnh" — lặp.
# Mã vẫn hiện trên màn hình và vẫn tìm kiếm được.
MA_DOC_RIENG = {"CĐHA": None}

# Chữ cái đầu mã phòng đọc thành lời. D là "đê" chứ không phải "dê" —
# người bệnh đối chiếu với phiếu khám nên phải nghe ra đúng chữ.
CHU_DOC = {"D": "đê", "C": "xê", "A": "a", "B": "bê", "F": "ép", "E": "e", "G": "giê"}


def so_doc(n):
    """Số 0-99 đọc thành chữ.

    ⚠ Hai chỗ tiếng Việt đổi chữ khi ghép số, máy đọc sai là người bệnh nghe ra
      mã khác:
      · đơn vị 5 sau hàng chục đọc là "lăm", không phải "năm" — 15 là "mười lăm".
      · đơn vị 1 từ hai mươi trở lên đọc là "mốt" — 21 là "hai mươi mốt" (nhưng
        11 vẫn là "mười một").
    """
    if n <= 10:
        return SO_CHU[n]
    chuc, don = divmod(n, 10)
    dau = "mười" if chuc == 1 else SO_CHU[chuc] + " mươi"
    if don == 0:
        duoi = ""
    elif don == 1:
        duoi = "một" if chuc == 1 else "mốt"
    elif don == 5:
        duoi = "lăm"
    else:
        duoi = SO_CHU[don]
    return (dau + " " + duoi).strip()


def ma_doc(ma):
    """Mã phòng D3 → 'đê ba', C1 → 'xê một' để máy đọc."""
    if ma in MA_DOC_RIENG:
        return MA_DOC_RIENG[ma]
    m = re.match(r"^([A-Za-z])(\d+)$", ma)
    if not m:
        # Mã lạ chưa khai cách đọc — đọc nguyên văn còn hơn đọc sai, và in
        # cảnh báo để người thêm mã biết mà khai vào MA_DOC_RIENG.
        print("   ! Mã '%s' chưa biết cách đọc — khai vào MA_DOC_RIENG" % ma)
        return ma
    chu, so = m.group(1).upper(), int(m.group(2))
    return "%s %s" % (CHU_DOC.get(chu, chu.lower()), so_doc(so))


def ds_ma_doc(ma):
    ma = [m for m in ma if MA_DOC_RIENG.get(m, "") is not None]
    if not ma:
        return ""
    if len(ma) == 1:
        return "Phòng " + ma_doc(ma[0]) + "."
    return "Phòng " + " hoặc ".join(ma_doc(m) for m in ma) + "."


def cau_vi_tri(ten, toa, tang, ma):
    """Câu robot đọc lúc mở màn chi tiết — chưa đi, mới nói vị trí."""
    c = "%s ở tầng %s, toà nhà %s. %s" % (ten, SO_CHU[tang], TOA_CHU[toa], ds_ma_doc(ma))
    return c.strip() + " Tôi dẫn quý vị ra đầu hành lang, rồi chỉ đường tiếp."


def cau_toa_thu_tu(toa):
    """'toà nhà đầu tiên, đó là toà đê một' — cách chỉ đường DUY NHẤT dùng được ở đây.

    Robot dừng ở đầu hành lang, còn cách các toà nhà một quãng. Đứng chỗ đó nhìn lên
    thì ba toà trông giống hệt nhau và biển tên thì xa quá không đọc nổi — nhất là
    người già, người đang ôm con. Đếm thứ tự thì ai cũng đếm được.
    """
    return "toà nhà %s, đó là toà %s" % (THU_TU_CHU[TOA_THU_TU[toa]], TOA_CHU[toa])


def cau_cap_cuu(ten, toa, tang, ma):
    """Câu robot hô khi người nhà bấm CẤP CỨU.

    ⚠ KHÔNG có chữ "tôi dẫn quý vị" ở đây. Robot đi 0,5–0,8 m/s, chậm hơn người
      chạy — bảo người đang cấp cứu đi theo robot là làm chậm họ. Robot chỉ hô to
      và chỉ hướng, còn người nhà tự chạy.
    """
    return ("%s ở tầng %s, toà nhà %s. %s "
            "Quý vị cần cấp cứu thì xin đi ngay, đừng chờ tôi dẫn. "
            "Xin mời đi thẳng, %s, rồi lên tầng %s."
            % (ten, SO_CHU[tang], TOA_CHU[toa], ds_ma_doc(ma),
               cau_toa_thu_tu(toa), SO_CHU[tang]))


def cau_chi_duong(ten, toa, tang, ma):
    """Câu robot đọc KHI ĐÃ TỚI đầu hành lang — lúc quan trọng nhất của cả app.

    Người bệnh đứng ở đầu hành lang, trước mặt là ba toà nhà, và chỉ nhớ được đúng
    những gì nghe được ở đây. Nên câu này đếm thứ tự toà nhà trước, rồi mới tới tầng
    và số phòng.
    """
    p = (" Tìm " + ds_ma_doc(ma).lower().replace(".", "") + ".") if ma else ""
    return ("Đã tới nơi. Xin mời quý vị đi thẳng. %s. "
            "Quý vị vào đó, lên tầng %s, vào %s.%s Chúc quý vị mau khoẻ."
            % (cau_toa_thu_tu(toa).capitalize(), SO_CHU[tang], ten, p))


def cum_huong(toa):
    """Phần chỉ hướng, rỗng khi chưa khảo sát — xem HUONG_TOA."""
    h = HUONG_TOA.get(toa, "").strip()
    return (" " + h.rstrip(".") + ".") if h else ""


def cau_toi_noi_toa_khac(ten, toa, tang, ma):
    """Robot đã dẫn tới tận cửa toà nhà — nói nốt phần nó không đi theo được."""
    p = (" Tìm " + ds_ma_doc(ma).lower().replace(".", "") + ".") if ds_ma_doc(ma) else ""
    # Tầng 1 thì KHÔNG nói "lên tầng một" — robot đang đứng ngay đó, bảo người ta
    # lên tầng một là câu vô nghĩa và làm người già bối rối đi tìm cầu thang.
    len_tang = "" if tang == 1 else " lên tầng %s," % SO_CHU[tang]
    return ("Đã tới nơi. Đây là toà nhà %s. Quý vị%s vào %s.%s Chúc quý vị mau khoẻ."
            % (TOA_CHU[toa], len_tang, ten, p))


def cau_chi_duong_toa_khac(ten, toa, tang, ma):
    """Câu đọc KHI ĐÃ TỚI NƠI — chỉ dùng nếu bỏ `diem` vì robot không đi được.

    Không đếm thứ tự toà nhà như ba toà D: A · B · C · F không nằm cùng một
    hàng dọc hành lang nên đếm thứ tự là chỉ sai.
    """
    p = (" " + ds_ma_doc(ma)) if ma else ""
    return ("%s ở tầng %s, toà nhà %s.%s%s Chúc quý vị mau khoẻ."
            % (ten, SO_CHU[tang], TOA_CHU[toa], p, cum_huong(toa))).replace("  ", " ")


def cau_dan_thang(ten, toa, tang, ma):
    """Câu robot đọc lúc mở màn chi tiết của bốn chỗ ở toà A · B · C · F.

    Khác cau_vi_tri() ở chỗ KHÔNG hứa "ra đầu hành lang rồi chỉ đường tiếp" —
    mấy chỗ này bản đồ có điểm riêng nên robot đi tới tận nơi.
    """
    p = (" " + ds_ma_doc(ma)) if ma else ""
    return ("%s ở tầng %s, %s.%s%s Tôi dẫn quý vị tới nơi."
            % (ten, SO_CHU[tang], "toà nhà " + TOA_CHU[toa],
               p, cum_huong(toa))).replace("  ", " ")


def cau_cap_cuu_toa(ten, toa, tang, ma):
    """Câu robot HÔ khi người nhà bấm CẤP CỨU.

    ⚠ Vẫn KHÔNG có chữ "tôi dẫn quý vị", dù bản đồ nay đã có điểm Khoa Cấp cứu.
      Robot đi 0,5–0,8 m/s, chậm hơn người chạy — bảo người đang cấp cứu đi theo
      robot là làm chậm họ. Robot hô to và chỉ chỗ, còn người nhà tự chạy.
      Muốn đổi ý thì mở nút dẫn ở màn cấp cứu, dữ liệu đã có sẵn `diem`.
    """
    p = (" " + ds_ma_doc(ma)) if ma else ""
    return ("%s ở tầng %s, %s.%s%s "
            "Quý vị cần cấp cứu thì xin đi ngay, đừng chờ tôi dẫn."
            % (ten, SO_CHU[tang], "toà nhà " + TOA_CHU[toa],
               p, cum_huong(toa))).replace("  ", " ")


def mo_ta_ma():
    """'D1 đến D22, C1 và CĐHA' — gộp dải số liên tục, liệt kê phần còn lại."""
    ds = sorted({m for k in BANG_KHOA for _, _, ma in k["vi_tri"] for m in ma}
                | {m for k in BANG_TOA_KHAC for m in k["ma"]})
    so_d = sorted(int(m[1:]) for m in ds if re.match(r"^D\d+$", m))
    khac = [m for m in ds if not re.match(r"^D\d+$", m)]
    phan = []
    if so_d:
        lien_tuc = so_d == list(range(so_d[0], so_d[-1] + 1))
        phan.append("D%d đến D%d" % (so_d[0], so_d[-1]) if lien_tuc
                    else ", ".join("D%d" % n for n in so_d))
    phan += khac
    if len(phan) == 1:
        return phan[0]
    return ", ".join(phan[:-1]) + " và " + phan[-1]


def mo_ta_ma_doc():
    """Bản ĐỌC của dải mã phòng: 'đê một đến đê hai mươi hai, và xê một'.

    ⚠ Khác mo_ta_ma() ở chỗ này là câu ROBOT NÓI RA, nên phải đọc thành chữ —
      "D1" để máy đọc thì nó phát ra "dê một" hoặc "đi một", người bệnh đang cầm
      phiếu ghi chữ D sẽ không đối chiếu được.

    ⚠ Bỏ những mã khai MA_DOC_RIENG = None (CĐHA): mã đó có thật, hiện trên màn
      hình và tìm kiếm được, nhưng cố ý không đọc ra tiếng vì nó là viết tắt của
      chính tên khoa.
    """
    ds = sorted({m for k in BANG_KHOA for _, _, ma in k["vi_tri"] for m in ma}
                | {m for k in BANG_TOA_KHAC for m in k["ma"]})
    ds = [m for m in ds if MA_DOC_RIENG.get(m, "") is not None]
    so_d = sorted(int(m[1:]) for m in ds if re.match(r"^D\d+$", m))
    khac = [m for m in ds if not re.match(r"^D\d+$", m)]
    phan = []
    if so_d:
        lien_tuc = so_d == list(range(so_d[0], so_d[-1] + 1))
        phan.append("%s đến %s" % (ma_doc("D%d" % so_d[0]), ma_doc("D%d" % so_d[-1]))
                    if lien_tuc else ", ".join(ma_doc("D%d" % n) for n in so_d))
    phan += [ma_doc(m) for m in khac]
    if len(phan) == 1:
        return phan[0]
    return ", ".join(phan[:-1]) + " và " + phan[-1]

# ═══════════════════════════════════════════════════════════════════════
#  Dựng
# ═══════════════════════════════════════════════════════════════════════
dich = []
_id = 0

for k in BANG_KHOA:
    _id += 1
    loai = k.get("loai", "ngoai-khu")
    vi_tri = []
    for toa, tang, ma in k["vi_tri"]:
        vi_tri.append({
            "toa": toa, "toa_ten": TOA_TEN[toa], "tang": tang, "ma": ma,
            "doc": (cau_cap_cuu if loai == "cap-cuu" else cau_vi_tri)(k["ten"], toa, tang, ma),
            "chi_duong": cau_chi_duong(k["ten"], toa, tang, ma),
        })
    moi_ma = [m for _, _, ma in k["vi_tri"] for m in ma]
    dich.append({
        "id": _id,
        "ten": k["ten"],
        "nhom": k["nhom"],
        "loai": loai,
        # Cấp cứu không dẫn đường nên không gắn điểm bản đồ nào
        "diem": None if loai == "cap-cuu" else "truoc-hanh-lang",
        "ghi_chu": k["ghi_chu"],
        "ma": moi_ma,
        "vi_tri": vi_tri,
        # Câu đọc khi khoa nằm ở nhiều toà — phải hỏi lại trước đã
        "doc": (vi_tri[0]["doc"] if len(vi_tri) == 1 else
                "%s có ở %s toà. Quý vị đang theo dõi ở toà nào ạ?" % (k["ten"], SO_CHU[len(vi_tri)])),
        "tim": khong_dau(k["ten"] + " " + k["ghi_chu"] + " " + " ".join(moi_ma)) + " " + k["tu_dan"],
    })

for t in BANG_TIEN_ICH:
    _id += 1
    dich.append({
        "id": _id,
        "ten": t["ten"],
        "nhom": t["nhom"],
        "loai": "trong-khu",
        "diem": t["diem"],
        "ghi_chu": t["ghi_chu"],
        "ma": [],
        "vi_tri": [],
        "doc": t["doc"],
        "tim": khong_dau(t["ten"] + " " + t["ghi_chu"]) + " " + t["tu_dan"],
    })

# ── Bốn chỗ ở toà A · B · C · F ──────────────────────────────────────────
# loai = "toa-khac": robot ĐI TỚI TẬN NƠI (có điểm bản đồ riêng), khác
# "ngoai-khu" là dừng ở đầu hành lang rồi chỉ đường bằng lời.
for k in BANG_TOA_KHAC:
    _id += 1
    loai = k.get("loai", "toa-khac")
    toa, tang, ma = k["toa"], k["tang"], k["ma"]
    dich.append({
        "id": _id,
        "ten": k["ten"],
        "nhom": k["nhom"],
        "loai": loai,
        # Cấp cứu CÓ điểm bản đồ nhưng app cố ý không hiện nút dẫn —
        # xem cau_cap_cuu_toa(). Giữ điểm ở đây để bật lên chỉ là một dòng.
        "diem": k["diem"],
        "ghi_chu": k["ghi_chu"],
        "ma": ma,
        # Sinh `vi_tri` một phần tử y hệt khuôn của 16 khoa trong ba toà D —
        # cố ý, để lớp giao diện không phải học thêm một hình dạng dữ liệu thứ ba.
        # Chỗ DUY NHẤT khác nhau là lúc tới nơi: "ngoai-khu" mở màn chỉ đường,
        # còn "toa-khac" thì robot đã tới tận nơi nên đọc lại từ đầu.
        "vi_tri": [{
            "toa": toa, "toa_ten": TOA_TEN[toa], "tang": tang, "ma": ma,
            "doc": (cau_cap_cuu_toa if loai == "cap-cuu" else cau_dan_thang)(
                    k["ten"], toa, tang, ma),
            # Dùng tới khi khảo sát thấy robot KHÔNG đi được tới chỗ đó và
            # phải bỏ trường `diem` — lúc ấy app quay về lối chỉ đường bằng lời.
            "chi_duong": cau_chi_duong_toa_khac(k["ten"], toa, tang, ma),
            # Câu robot đọc KHI ĐÃ ĐỨNG trước toà nhà. Khác chi_duong ở chỗ
            # không chỉ đường nữa — chỉ nhắc tầng và số phòng, là hai thứ robot
            # không đi theo lên được.
            "doc_toi_noi": cau_toi_noi_toa_khac(k["ten"], toa, tang, ma),
        }],
        "doc": (cau_cap_cuu_toa if loai == "cap-cuu" else cau_dan_thang)(
                k["ten"], toa, tang, ma),
        "tim": khong_dau(k["ten"] + " " + k["ghi_chu"] + " " + " ".join(ma))
               + " " + k["tu_dan"],
    })


# ═══════════════════════════════════════════════════════════════════════
#  KHO HỎI–ĐÁP CHUNG — phần kiến thức KHÔNG gắn với một khoa nào
#
#  ⚠ VÌ SAO KHỐI NÀY TỒN TẠI (09/09/2026):
#    Trước đây toàn bộ hỏi–đáp chỉ nằm trên cổng OrionStar. Mà `LLMConfig.fileSearch`
#    — tham số cho phép `AgentCore.llm()` đọc kho tri thức trên cổng — đã bị máy chủ
#    hãng BỎ từ 26/08/2025 (xem MainApplication.hoiMoHinh). Nghĩa là kho trên cổng
#    KHÔNG còn tham gia vào đường trả lời chính của app này nữa: robot trả lời khoa
#    phòng được là nhờ bảng `dich` nằm sẵn trong APK, không nhờ cổng.
#
#    Còn đúng mấy mảng dưới đây là chưa có đường nào vào máy: quy trình khám lần đầu,
#    phạm vi robot đi được, giới thiệu bệnh viện. Đưa vào app-data.json thì chúng đi
#    theo index.html vào assets/ của APK, robot trả lời được mà không cần cổng.
#
#  ⚠ CỐ Ý KHÔNG ĐƯA hỏi–đáp về VỊ TRÍ KHOA vào đây. Hai lý do:
#    · Trùng: bảng `dich` đã trả lời được rồi, và trả lời TỐT HƠN — nó còn mở màn
#      chỉ đường có mã phòng chữ to, thứ một câu văn không làm được.
#    · Nguy: câu đáp gắn cứng "tầng 2, Nhà DI" mà bệnh viện đổi tầng thì có hai bản
#      sự thật trong cùng một file, robot nói một đằng màn hình hiện một nẻo.
#    Muốn đổi vị trí khoa thì sửa BANG_KHOA, chỗ duy nhất.
#
#  ⚠ Câu `dap` là câu robot ĐỌC NGUYÊN VĂN. Nó không đi qua mô hình ngôn ngữ lần
#    nào — cùng một luật với trường `doc` của bảng khoa phòng. Viết ở đây thế nào
#    thì người bệnh nghe đúng thế.
#
#  Trường `tu` là từ khoá tìm thêm, ngoài chính mấy câu hỏi mẫu. Viết KHÔNG DẤU.
# ═══════════════════════════════════════════════════════════════════════
_cc = next(d for d in dich if d["loai"] == "cap-cuu")
_vcc = _cc["vi_tri"][0]
_toa_khac = [d for d in dich if d["loai"] == "toa-khac"]

HOI_DAP_CHUNG = [
    {
        "nhom": "kham-lan-dau",
        "hoi": ["Tôi đến khám lần đầu thì làm gì?", "Tôi chưa có phiếu khám",
                "Đăng ký khám ở đâu?", "Khám bệnh bắt đầu từ đâu?",
                "Tôi chưa biết mình khám khoa nào", "Thủ tục khám bệnh thế nào?",
                "Lần đầu tới đây tôi phải làm sao?"],
        "tu": "kham lan dau thu tuc dang ky lay so phieu kham quy trinh bat dau "
              "chua co phieu can cuoc bao hiem y te the bhyt",
        "dap": QUY_TRINH_KHAM["doc"],
    },
    {
        "nhom": "pham-vi-robot",
        "hoi": ["Robot dẫn tôi lên tầng được không?", "Bạn đưa tôi vào phòng khám nhé",
                "Robot đi được tới đâu?", "Bạn dẫn tôi vào nhà DII được không?",
                "Bạn đi thang máy được không?", "Bạn dẫn tôi tới tận phòng nhé"],
        "tu": "robot dan len tang thang may vao trong toa nha tan phong di toi dau pham vi",
        "dap": "Tôi đi lại trong khu lễ tân thôi ạ. Với ba toà DI, DII và DIII thì tôi ra "
               "tới đầu hành lang rồi đứng đó chỉ đường; với Nhà A, Nhà B và Nhà F thì tôi "
               "dẫn quý vị tới tận nơi. Tôi không vào trong toà nhà và không lên tầng được.",
    },
    {
        "nhom": "gioi-thieu-robot",
        "hoi": ["Bạn là ai?", "Bạn tên gì?", "Bạn làm được những gì?",
                "Robot giúp được gì cho tôi?"],
        "tu": "ban la ai ten gi robot lam duoc gi giup gioi thieu",
        "dap": "Tôi là robot lễ tân của bệnh viện. Tôi giúp quý vị tìm khoa, tìm phòng và "
               "dẫn đường trong khu lễ tân. Quý vị cứ nói tên khoa, mã phòng trên phiếu "
               "khám, hoặc kể triệu chứng, tôi tìm giúp ạ.",
    },
    {
        "nhom": "so-toa-nha",
        "hoi": ["Bệnh viện có mấy toà nhà?", "Ở đây có những toà nào?",
                "Khu khám bệnh gồm mấy nhà?"],
        "tu": "may toa nha gom nhung nao khu kham benh bao nhieu toa",
        "dap": "Khu khám và điều trị có ba toà xếp dọc hành lang: %s. Ngoài ra còn %s."
               % (", ".join("%s %s tầng" % (TOA_TEN[m], SO_CHU[TOA_TANG[m]])
                            for m in ("DI", "DII", "DIII")),
                  ", ".join("%s ở %s" % (d["ten"], d["vi_tri"][0]["toa_ten"])
                            for d in _toa_khac + [_cc])),
    },
    {
        "nhom": "danh-muc-khoa",
        "hoi": ["Bệnh viện có những khoa nào?", "Ở đây khám được những gì?",
                "Cho tôi xem danh sách khoa"],
        "tu": "nhung khoa nao danh sach danh muc kham duoc gi co bao nhieu khoa",
        # ⚠ Cố ý KHÔNG đọc cả dải mã phòng ra tiếng. Hơn hai mươi mã đọc liền một hơi
        #   thì không ai nhớ nổi, mà nghe xong vẫn phải nhìn màn hình. Dải mã để MẮT đọc.
        "dap": "Bệnh viện có nhiều khoa ạ. Quý vị nói tên khoa, đọc mã phòng ghi trên "
               "phiếu khám, hoặc kể triệu chứng thì tôi tìm giúp. Danh sách đầy đủ đang "
               "hiện trên màn hình để quý vị chạm chọn.",
    },
    {
        "nhom": "khong-phai-bac-si",
        "hoi": ["Tôi bị bệnh gì?", "Bệnh của tôi có nặng không?", "Tôi nên uống thuốc gì?",
                "Xem giúp tôi kết quả này với", "Tôi có cần mổ không?",
                "Bạn chẩn đoán giúp tôi"],
        "tu": "toi bi benh gi nang khong uong thuoc ket qua can mo chan doan kham giup",
        "dap": "Tôi là robot chỉ đường, tôi không khám bệnh và không đoán bệnh được ạ. "
               "Tôi chỉ giúp quý vị tìm đúng khoa, còn bác sĩ ở phòng khám mới là người "
               "xem và quyết định.",
    },
    {
        "nhom": "chua-co-du-lieu",
        "hoi": ["Bệnh viện làm việc mấy giờ?", "Hôm nay bác sĩ nào trực?",
                "Khám ở đây hết bao nhiêu tiền?", "Số điện thoại bệnh viện là gì?",
                "Kết quả xét nghiệm của tôi thế nào?", "Còn giường trống không?",
                "Bác sĩ nào giỏi nhất khoa này?", "Bao giờ tới lượt tôi?",
                "Tôi đặt lịch khám online được không?", "Bệnh viện thành lập năm nào?"],
        "tu": "may gio lam viec lich truc bac si nao bao nhieu tien gia kham so dien thoai "
              "ket qua xet nghiem giuong trong gioi nhat toi luot dat lich online thanh lap",
        "dap": "Thông tin này tôi chưa có trong dữ liệu nên không dám đoán ạ. "
               "Mời quý vị hỏi quầy lễ tân giúp tôi.",
    },
    {
        "nhom": "cap-cuu",
        "hoi": ["Cấp cứu ở đâu?", "Tôi cần cấp cứu", "Khoa cấp cứu đi lối nào?",
                "Cấp cứu có trực ban đêm không?", "Tai nạn thì vào đâu?"],
        "tu": "cap cuu khan nguy kich tai nan truc dem 24 24",
        "dap": "%s ở %s. Quý vị cần cấp cứu thì xin đi ngay, ĐỪNG chờ tôi dẫn — "
               "tôi đi chậm hơn người chạy."
               % (_cc["ten"], "tầng %s, %s%s"
                  % (SO_CHU[_vcc["tang"]], _vcc["toa_ten"],
                     ", phòng " + " hoặc ".join(_vcc["ma"]) if _vcc["ma"] else "")),
    },
]

hoi_dap = []
for _i, _g in enumerate(HOI_DAP_CHUNG, 1):
    hoi_dap.append({
        "id": _i,
        "nhom": _g["nhom"],
        "hoi": _g["hoi"],
        "dap": _g["dap"],
        # Từ dẫn = mọi câu hỏi mẫu + từ khoá thêm, bỏ dấu. Bộ tìm bên khung-app.html
        # khớp TRỌN TỪ trên chuỗi này, y hệt cách nó tìm khoa phòng.
        "tim": khong_dau(" ".join(_g["hoi"])) + " " + _g["tu"],
    })


D = {
    "don_vi": "Bệnh viện Việt Nam – Thụy Điển Uông Bí",
    "khu_vuc": "Khu lễ tân",
    "nguon": "Tài liệu hướng dẫn robot lễ tân do bệnh viện cung cấp — "
             "10-project/Benh-vien-Uong-Bi/01-khao-sat/",
    "cap_nhat": "08/09/2026",
    "diem": DIEM,
    "diem_ve_cho": DIEM_VE_CHO,
    "toa": [{"ma": m, "ten": TOA_TEN[m], "so_tang": TOA_TANG[m],
             "thu_tu": TOA_THU_TU[m], "thu_tu_chu": THU_TU_CHU[TOA_THU_TU[m]]}
            for m in ("DI", "DII", "DIII")],
    "nhom": NHOM,
    # Câu mô tả danh mục mã phòng, sinh từ chính dữ liệu. Trước đây bốn chỗ trong
    # giao diện ghi cứng "D1 đến D24" — bỏ D23/D24 xong là cả bốn chỗ nói sai mà
    # không có gì báo. Sinh ở đây thì đổi danh mục là mọi chỗ đổi theo.
    "mo_ta_ma": mo_ta_ma(),
    # Bản đọc thành tiếng của dải mã trên — dùng khi người bệnh đọc một mã không
    # có thật. Trước đây câu đó ghi cứng trong TraLoi.kt là "đê một đến đê hai mươi
    # tư", và khi bệnh viện bỏ D23–D24 thì robot vẫn nói dải cũ.
    "mo_ta_ma_doc": mo_ta_ma_doc(),
    "quy_trinh_kham": QUY_TRINH_KHAM,
    # Kho hỏi–đáp chung — xem khối HOI_DAP_CHUNG bên trên.
    "hoi_dap": hoi_dap,
    "dich": dich,
}

os.makedirs(os.path.dirname(RA), exist_ok=True)
with io.open(RA, "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=1)

so_ma = sum(len(d["ma"]) for d in dich)
print("→ %s" % RA)
print("   %d đích  ·  %d mã phòng  ·  %d nhóm  ·  %d điểm bản đồ  ·  %d mục hỏi–đáp"
      % (len(dich), so_ma, len(NHOM), len(DIEM), len(hoi_dap)))

# ── Cổng kiểm: kho hỏi–đáp chung ──
# Mục rỗng thì bộ tìm bên khung-app.html vẫn khớp được rồi robot ĐỌC RA CHUỖI RỖNG:
# đứng câm giữa lúc người bệnh đang chờ, mà không tầng nào báo lỗi.
for _h in hoi_dap:
    if not _h["dap"].strip() or not _h["tim"].strip() or not _h["hoi"]:
        print("   ! Mục hỏi–đáp '%s' thiếu câu đáp, từ dẫn hoặc câu hỏi mẫu" % _h["nhom"])
        raise SystemExit(1)
_trung = [n for n in {h["nhom"] for h in hoi_dap}
          if sum(1 for h in hoi_dap if h["nhom"] == n) > 1]
if _trung:
    print("   ! Nhóm hỏi–đáp trùng tên: %s" % ", ".join(sorted(_trung)))
    raise SystemExit(1)
# ── Cổng kiểm: mã phòng phải đủ, không thừa không thiếu ──
# Danh mục hiện hành sau khi bệnh viện cập nhật 08/09/2026:
#   D1-D22 ở ba toà D  ·  D7 đã chuyển sang Nhà B  ·  C1 ở Nhà C
#   CĐHA ở Nhà F  ·  D23-D24 (Hồi Sức Cấp Cứu Nội) đã BỎ khỏi app
MONG_DOI = {"D%d" % i for i in range(1, 23)} | {"C1", "CĐHA"}
dang_co = {m for d in dich for m in d["ma"]}
thieu, thua = sorted(MONG_DOI - dang_co), sorted(dang_co - MONG_DOI)
if thieu or thua:
    print("   ! Mã phòng LỆCH danh mục — thiếu: %s · thừa: %s"
          % (", ".join(thieu) or "không", ", ".join(thua) or "không"))
    raise SystemExit(1)
print("   Mã phòng khớp danh mục: D1–D22 · C1 · CĐHA (D23–D24 đã bỏ theo yêu cầu)")

# Mọi đích có dẫn đường đều phải trỏ vào một điểm CÓ THẬT trong bảng DIEM —
# gõ sai khoá ở đây thì app im lặng bỏ qua nút dẫn, không báo lỗi gì.
lac = sorted({d["diem"] for d in dich if d["diem"] and d["diem"] not in DIEM})
if lac:
    print("   ! Đích trỏ vào điểm không có trong bảng DIEM: %s" % ", ".join(lac))
    raise SystemExit(1)
