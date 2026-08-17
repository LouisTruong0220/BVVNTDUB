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
}
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
    dict(ten="Khoa Răng Hàm Mặt", nhom="mat-tai-rang", ghi_chu="Nha khoa, hàm mặt",
         vi_tri=[("DI", 4, ["D7"])],
         tu_dan="rang dau rang nho rang sau rang ham mat nha khoa nieng rang "
                "chua rang han rang lam rang loi sung"),

    # ── Nội khoa ──────────────────────────────────────────────────────
    dict(ten="Khoa Nội Tiêu Hóa", nhom="noi-khoa", ghi_chu="Tiêu hóa nội khoa",
         vi_tri=[("DI", 4, ["D8"])],
         tu_dan="dau bung da day dai trang tieu hoa o chua tao bon gan "
                "noi soi da day viem loet da day roi loan tieu hoa dau da day"),
    dict(ten="Khoa Nội Phổi – Tiết Niệu – Hô Hấp", nhom="noi-khoa", ghi_chu="Hô hấp, phổi, tiết niệu",
         vi_tri=[("DII", 4, ["D17", "D18"])],
         tu_dan="ho kho tho phoi hen suyen viem phoi ho hap than tieu buot soi than "
                "tiet nieu tuc nguc lao phoi kho tho ve dem di tieu nhieu"),

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
    dict(ten="Khoa Hồi Sức Cấp Cứu Nội", nhom="cap-cuu", ghi_chu="Cấp cứu nội khoa", loai="cap-cuu",
         vi_tri=[("DIII", 2, ["D23", "D24"])],
         # ⚠ "ngat xiu" phải nằm ở đây. Bỏ dấu thì "ngất" và "ngạt" (ngạt mũi) là một
         #   chữ, mà Tai Mũi Họng có "ngat mui" — người nhà gõ "ngất xỉu" lại ra khoa
         #   tai mũi họng trước khoa cấp cứu. Có thêm "xiu" thì cấp cứu thắng rõ.
         tu_dan="cap cuu nguy kich hoi suc ngat xiu ngat xiu choang dot quy cap cuu noi "
                "kho tho nang bat tinh co giat tai nan khan cap nguy hiem sap chet"),

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
TOA_CHU = {"DI": "đê một", "DII": "đê hai", "DIII": "đê ba"}
TOA_TEN = {"DI": "Nhà DI", "DII": "Nhà DII", "DIII": "Nhà DIII"}
TOA_TANG = {"DI": 5, "DII": 5, "DIII": 8}

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


def ma_doc(ma):
    """Mã phòng D3 → 'đê ba' để máy đọc. Người ta đối chiếu với phiếu khám nên phải đọc rõ."""
    n = int(ma[1:])
    if n <= 10:
        return "đê " + SO_CHU[n]
    if n < 20:
        return "đê mười " + (SO_CHU[n - 10] if n % 10 else "")
    chuc, don = divmod(n, 10)
    return ("đê " + SO_CHU[chuc] + " mươi " + (SO_CHU[don] if don else "")).strip()


def ds_ma_doc(ma):
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

D = {
    "don_vi": "Bệnh viện Việt Nam – Thụy Điển Uông Bí",
    "khu_vuc": "Khu lễ tân",
    "nguon": "Tài liệu hướng dẫn robot lễ tân do bệnh viện cung cấp — "
             "10-project/Benh-vien-Uong-Bi/01-khao-sat/",
    "cap_nhat": "11/08/2026",
    "diem": DIEM,
    "diem_ve_cho": DIEM_VE_CHO,
    "toa": [{"ma": m, "ten": TOA_TEN[m], "so_tang": TOA_TANG[m],
             "thu_tu": TOA_THU_TU[m], "thu_tu_chu": THU_TU_CHU[TOA_THU_TU[m]]}
            for m in ("DI", "DII", "DIII")],
    "nhom": NHOM,
    "quy_trinh_kham": QUY_TRINH_KHAM,
    "dich": dich,
}

os.makedirs(os.path.dirname(RA), exist_ok=True)
with io.open(RA, "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=1)

so_ma = sum(len(d["ma"]) for d in dich)
print("→ %s" % RA)
print("   %d đích  ·  %d mã phòng  ·  %d nhóm  ·  %d điểm bản đồ"
      % (len(dich), so_ma, len(NHOM), len(DIEM)))
thieu = sorted({"D%d" % i for i in range(1, 25)} - {m for d in dich for m in d["ma"]})
print("   Mã phòng thiếu so với D1–D24: %s" % (", ".join(thieu) if thieu else "không thiếu mã nào"))
