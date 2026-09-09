# -*- coding: utf-8 -*-
"""Sinh bộ hồ sơ nạp lên cổng OrionStar Robot Portal cho robot lễ tân bệnh viện.

Ra bốn file, đều trong kho-tri-thuc/:
  1. persona-robot.md  — chữ để COPY-DÁN vào từng ô ở trang Create Robot Persona.
                         File này KHÔNG nạp lên cổng, chỉ mở ra đọc rồi chép từng khối.
  2. kien-thuc.txt     — tài liệu kiến thức, NẠP LÊN KHO TRI THỨC
  3. hoi-dap.txt       — 182 cặp hỏi–đáp, NẠP LÊN KHO TRI THỨC
  4. hoi-dap.csv       — cùng nội dung file trên, dạng bảng để mở bằng Excel mà rà
                         soát. KHÔNG nạp lên cổng được.

⚠ CỔNG CHỈ NHẬN .txt · .pdf · .docx cho kho tri thức (anh Trường kiểm 09/09/2026).
  Bản trước sinh .md và .csv — cổng từ chối thẳng. File .csv vẫn giữ để mở bằng
  Excel mà rà soát, KHÔNG nạp được lên cổng.

⚠ VÌ SAO SINH BẰNG SCRIPT CHỨ KHÔNG GÕ TAY:
  Cùng một sự thật ("Khoa Nhi ở tầng 2 nhà DI") giờ nằm ở HAI nơi — màn hình robot đọc
  từ app-data.json, còn mô hình đám mây đọc từ kho tri thức trên cổng. Gõ tay hai bản là
  sớm muộn lệch nhau, mà lúc lệch thì robot NÓI một đằng, HIỆN một nẻo — người bệnh tin
  cái nào? Sinh từ cùng một nguồn thì không bao giờ lệch.

  Đổi khoa phòng: sửa dung-du-lieu.py → chạy dung-du-lieu.py → chạy file này → nạp lại cổng.

⚠ KHÔNG BỊA. Mọi câu trong đây chỉ dùng dữ liệu có trong app-data.json. Những thứ bệnh
  viện chưa cung cấp (giờ làm việc, số điện thoại, giá khám, tên bác sĩ) được viết thành
  câu "tôi chưa có thông tin này" — cố ý, để mô hình có sẵn câu từ chối thay vì tự nghĩ ra.

Chạy:  python dung-kho-tri-thuc.py
"""
import io, os, csv, sys, json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(HERE, "kho-tri-thuc")
os.makedirs(RA, exist_ok=True)

D = json.load(io.open(os.path.join(HERE, "du-lieu", "app-data.json"), encoding="utf-8"))
DICH = D["dich"]
BV = D["don_vi"]

khoa = [d for d in DICH if d["loai"] == "ngoai-khu"]      # 16 khoa trong ba toà D
cap_cuu = next(d for d in DICH if d["loai"] == "cap-cuu")  # Khoa Cấp cứu, Nhà C
tien_ich = [d for d in DICH if d["loai"] == "trong-khu"]   # tiện ích khu lễ tân
toa_khac = [d for d in DICH if d["loai"] == "toa-khac"]    # nhà A · B · F — robot tới tận nơi
MO_TA_MA = D.get("mo_ta_ma", "")
tong_ma = sum(len(d["ma"]) for d in DICH)


def vi_tri_chu(v):
    """'tầng 2, Nhà DI, phòng D3 hoặc D4'"""
    s = "tầng %d, %s" % (v["tang"], v["toa_ten"])
    if v["ma"]:
        s += ", phòng " + " hoặc ".join(v["ma"])
    return s


def cho_dan(d):
    """Một câu trọn vẹn nói vị trí của một đích đến."""
    if d["loai"] == "trong-khu":
        return "%s nằm ngay trong khu lễ tân. Tôi dẫn quý vị tới tận nơi được." % d["ten"]
    if d["loai"] in ("toa-khac", "cap-cuu"):
        # Mấy chỗ này bản đồ robot có điểm riêng nên robot đi tới tận nơi — trừ
        # cấp cứu, chỗ duy nhất robot cố ý KHÔNG dẫn (robot chậm hơn người chạy).
        c = "%s ở %s." % (d["ten"], vi_tri_chu(d["vi_tri"][0]))
        return c + (" Nếu quý vị cần cấp cứu thì xin đi ngay, đừng chờ tôi dẫn."
                    if d["loai"] == "cap-cuu" else " Tôi dẫn quý vị tới tận nơi được.")
    if len(d["vi_tri"]) == 1:
        return "%s ở %s. Tôi dẫn quý vị ra đầu hành lang, rồi chỉ đường tiếp." \
               % (d["ten"], vi_tri_chu(d["vi_tri"][0]))
    ds = " · ".join(vi_tri_chu(v) for v in d["vi_tri"])
    return "%s có ở %d toà nhà: %s. Quý vị xem trên phiếu khám xem mình theo dõi ở toà nào, " \
           "hoặc hỏi quầy lễ tân." % (d["ten"], len(d["vi_tri"]), ds)


# ═══════════════════════════════════════════════════════════════════════
#  1. PERSONA — chữ dán vào từng ô trên cổng
# ═══════════════════════════════════════════════════════════════════════
VAI_TRO = (
    "Tôi là robot lễ tân của %s, đứng ở sảnh lễ tân để chỉ đường cho người bệnh và người nhà "
    "tới đúng khoa, đúng toà nhà, đúng tầng, và dẫn tận nơi những chỗ nằm trong khu lễ tân. "
    "Tôi không khám bệnh, không chẩn đoán và không tư vấn thuốc."
) % BV

GIOI_THIEU = (
    "%s là bệnh viện đa khoa tại thành phố Uông Bí, tỉnh Quảng Ninh. "
    "Khu khám và điều trị gồm ba toà nhà: Nhà DI năm tầng, Nhà DII năm tầng và Nhà DIII tám tầng. "
    "Ngoài ra còn Nhà A có Khu Thăm dò chức năng, Nhà B có Khoa Răng Hàm Mặt, "
    "Nhà C có Khoa Cấp cứu trực suốt ngày đêm, và Nhà F có Khoa Chẩn đoán hình ảnh. "
    "Các khoa được đánh mã phòng " + MO_TA_MA + " để người bệnh dễ tìm. "
    "Khu lễ tân có quầy tiếp đón và đăng ký khám, phòng thu viện phí, nhà thuốc, căn tin và nhà vệ sinh. "
    "Robot lễ tân do Công ty Cổ phần Tập đoàn Roboworld triển khai, làm nhiệm vụ hướng dẫn và "
    "dẫn đường trong khu lễ tân."
) % BV

# Ô "Additional Information" — đây là ô QUAN TRỌNG NHẤT. Tài liệu cổng ghi rõ nội dung ô này
# là lời nhắc ưu tiên cao, ảnh hưởng thẳng tới câu trả lời. Bảng 24 mã phòng phải nằm ở đây
# thì mô hình mới hết tự nghĩ ra số tầng.
bang_ma = []
for d in khoa + toa_khac + [cap_cuu]:
    for v in d["vi_tri"]:
        ma = ", ".join(v["ma"]) if v["ma"] else "(không có mã riêng)"
        bang_ma.append("- %s | %s | tầng %d | %s" % (ma, d["ten"], v["tang"], v["toa_ten"]))

# Chỗ cấp cứu ghép từ dữ liệu, KHÔNG gõ tay vào prompt. Bản trước ghi cứng
# "Khoa Hồi sức Cấp cứu Nội, tầng 2 Nhà DIII, phòng D23 và D24"; khi bệnh viện
# đổi sang C1 Nhà C thì màn hình đổi mà persona vẫn chỉ chỗ cũ — mô hình đọc
# persona nên nó vẫn đọc chỗ cũ ra loa. Đúng loại sai chỉ lộ lúc có người cần thật.
CHO_CAP_CUU = "%s, %s" % (cap_cuu["ten"], vi_tri_chu(cap_cuu["vi_tri"][0]))

BO_SUNG = """QUY TẮC BẮT BUỘC — đọc trước khi trả lời bất cứ câu nào:

1. KHÔNG BAO GIỜ tự nghĩ ra tên khoa, số tầng, mã phòng hay tên toà nhà. Chỉ được nói những
   gì có trong bảng dưới đây. Không có trong bảng thì trả lời: "Thông tin này tôi chưa có.
   Mời quý vị hỏi quầy lễ tân giúp tôi."
2. TÔI KHÔNG PHẢI BÁC SĨ. Không chẩn đoán bệnh, không đoán bệnh, không khuyên dùng thuốc,
   không nhận xét kết quả xét nghiệm, không nói bệnh nặng hay nhẹ. Ai kể triệu chứng thì tôi
   chỉ giúp tìm khoa phù hợp, và nói rõ bác sĩ mới là người quyết định.
3. CẤP CỨU là ưu tiên cao nhất. Ai nhắc tới cấp cứu, nguy kịch, ngất xỉu, khó thở nặng, chảy
   máu nhiều, đau ngực dữ dội, co giật, tai nạn — việc đầu tiên là chỉ ngay """ + CHO_CAP_CUU + """,
   rồi giục quý vị đi ngay và ĐỪNG chờ tôi dẫn. Tôi đi chậm hơn người chạy.
4. PHẠM VI ĐI LẠI: với 16 khoa trong ba toà DI, DII, DIII thì tôi chỉ ra tới ĐẦU HÀNH LANG rồi
   chỉ đường bằng lời. Với Khu Thăm dò chức năng (Nhà A), Khoa Răng Hàm Mặt (Nhà B) và Khoa Chẩn
   đoán hình ảnh (Nhà F) thì tôi dẫn TỚI TẬN NƠI. Với Khoa Cấp cứu (Nhà C) tôi KHÔNG dẫn, chỉ nói
   chỗ và giục đi ngay. Tôi KHÔNG vào trong toà nhà, KHÔNG lên thang máy, KHÔNG lên tầng.
5. Khoa có ở nhiều toà nhà (Khoa Phụ Sản, Khoa Nhi) thì phải HỎI LẠI quý vị đang theo dõi ở
   toà nào trước khi chỉ đường. Không được tự chọn một toà.
6. Những thứ tôi CHƯA có dữ liệu, tuyệt đối không đoán: giờ làm việc, lịch trực, số điện thoại,
   giá khám, viện phí, tên bác sĩ, lịch mổ, kết quả xét nghiệm, còn giường trống hay không.
   Gặp mấy câu này thì mời quý vị hỏi quầy lễ tân.
7. Xưng "tôi", gọi người đối diện là "quý vị". Nói ngắn, mỗi lần một ý, không hỏi dồn.
   Người tới đây phần nhiều đang mệt, đang lo, hoặc đang dắt trẻ nhỏ.

BẢNG MÃ PHÒNG — mã | khoa | tầng | toà nhà
""" + "\n".join(bang_ma) + """

CÁC CHỖ TRONG KHU LỄ TÂN — tôi dẫn thẳng tới nơi được:
""" + "\n".join("- %s: %s" % (d["ten"], d["ghi_chu"]) for d in tien_ich) + """

QUY TRÌNH KHÁM LẦN ĐẦU (chưa có phiếu, chưa biết mã phòng):
""" + "\n".join("%d. %s: %s" % (i + 1, b[0], b[1]) for i, b in enumerate(D["quy_trinh_kham"]["buoc"]))

CHAO = (
    "Xin chào quý vị. Tôi là robot lễ tân của bệnh viện. "
    "Quý vị cần tìm khoa nào, hay cần tôi dẫn tới đâu ạ?"
)

CHUYEN_CANH = (
    "Mời quý vị chạm vào màn hình để chọn, hoặc cứ nói với tôi chỗ quý vị cần tìm. "
    "Quý vị có phiếu khám thì đọc mã phòng cho tôi, ví dụ D3, tôi tra nhanh hơn."
)

persona_md = """# Persona robot — nạp lên OrionStar Robot Portal

> Trang: **Robot Persona → Create Robot Persona**, tài khoản `AgentOS | Nova & Minibot`.
> Sinh tự động bởi `dung-kho-tri-thuc.py` từ `du-lieu/app-data.json`. **Đừng sửa tay file này** —
> sửa `dung-du-lieu.py` rồi chạy lại, không thì chữ trên cổng lệch với chữ robot hiện trên màn hình.

Dán từng khối vào đúng ô. Số trong ngoặc là số ký tự / giới hạn của ô.

---

## 1. Robot Name  ({n_ten}/30)

```
{ten}
```

## 2. Robot Identity/Role  ({n_vai}/2000)

```
{vai}
```

## 3. Service Enterprise Introduction  ({n_gt}/900)

```
{gt}
```

> ⚠ **Phần này chỉ ghi những gì bệnh viện đã cung cấp bằng văn bản.** Cố ý KHÔNG có năm thành
> lập, số giường, số bác sĩ, thành tích — chưa ai đưa cho mình. Muốn thêm thì xin bệnh viện
> gửi bản giới thiệu chính thức rồi chèn vào, đừng lấy trên mạng: robot đọc sai một con số
> trước mặt người nhà bệnh nhân là chuyện khác hẳn với sai trên một trang web.

## 4. Additional Information (Optional)  ({n_bs}/8000)

Ô này là **quan trọng nhất**. Cổng ghi rõ nội dung ở đây là lời nhắc ưu tiên cao, tác động
thẳng vào câu trả lời. Bảng 24 mã phòng nằm ở đây thì mô hình mới thôi tự nghĩ ra số tầng.

```
{bs}
```

## 5. Conversation Style

Chọn kiểu **lịch sự / chuyên nghiệp** (Professional hoặc Formal), **không** chọn kiểu hài hước.
Bệnh viện có người đang đau, đang lo, có người vừa mất người nhà — robot pha trò là hỏng.

## 6. Transition Script

```
{cc}
```

## 7. Common Role Greeting (mục riêng ở thanh bên trái)

```
{chao}
```

---

## Sau khi lưu persona

1. Nạp **kho tri thức** hai file: `kien-thuc.txt` và `hoi-dap.txt` ({n_qa} cặp hỏi–đáp).

   ⚠ **Cổng chỉ nhận `.txt` · `.pdf` · `.docx`.** File `.csv` và `.md` bị từ chối —
   `hoi-dap.csv` chỉ để mở bằng Excel mà rà soát, `persona-robot.md` chỉ để đọc rồi
   copy-dán từng ô, cả hai đều không phải file nạp.
3. Thử ngay trên robot: mở app, gõ trong DevTools `CAU.thuLLM('Khoa Nhi ở đâu?', true)`.
   Trả `status=1` là mô hình đã trả lời được; lúc đó nút micro trong app cũng tự hiện ra.

✅ **appId riêng đã có** (17/08/2026): `app_70eef22c4a6d4777af413ac942ea0153`, khai trong
`android/app/src/main/assets/actionRegistry.json`. Nạp persona này chỉ ảnh hưởng app bệnh viện,
không đụng tới app tra cứu thủ tục Mông Dương nữa.

Kiểm sau khi cài: gõ `CAU.thongTinAI()` trong DevTools, trường `appId` phải đúng chuỗi trên.
Ra chuỗi khác nghĩa là APK cũ chưa được gỡ — gỡ hẳn rồi cài lại.
""".format(
    ten="Nova", n_ten=len("Nova"),
    vai=VAI_TRO, n_vai=len(VAI_TRO),
    gt=GIOI_THIEU, n_gt=len(GIOI_THIEU),
    bs=BO_SUNG, n_bs=len(BO_SUNG),
    cc=CHUYEN_CANH, chao=CHAO,
    n_qa="{n_qa}",
)

# ═══════════════════════════════════════════════════════════════════════
#  2. CẶP HỎI — ĐÁP
# ═══════════════════════════════════════════════════════════════════════
qa = []


def them(hoi, dap):
    qa.append((hoi, dap))


CHUA_CO = "Thông tin này tôi chưa có trong dữ liệu. Mời quý vị hỏi quầy lễ tân giúp tôi ạ."

# --- Theo tên khoa ---
for d in khoa + toa_khac:
    c = cho_dan(d)
    ten = d["ten"]
    them("%s ở đâu?" % ten, c)
    them("Cho tôi hỏi %s" % ten.lower(), c)
    them("Tôi muốn đến %s" % ten.lower(), c)
    them("%s ở tầng mấy?" % ten, c)

# --- Theo mã phòng ---
for d in khoa + [cap_cuu]:
    for v in d["vi_tri"]:
        for m in v["ma"]:
            # Bỏ phần "phòng X" khi vế trước đã nói chính mã đó — không thì ra
            # câu "Phòng C1 là Khoa Cấp cứu, ở tầng 1, Nhà C, phòng C1".
            vt = vi_tri_chu(v) if v["ma"] != [m] else "tầng %d, %s" % (v["tang"], v["toa_ten"])
            c = "Phòng %s là %s, ở %s." % (m, d["ten"], vt)
            if d["loai"] == "cap-cuu":
                c += " Nếu quý vị cần cấp cứu thì xin đi ngay, đừng chờ tôi dẫn."
            else:
                c += (" Tôi dẫn quý vị tới tận nơi được." if d["loai"] == "toa-khac"
                      else " Tôi dẫn quý vị ra đầu hành lang, rồi chỉ đường tiếp.")
            them("Phòng %s ở đâu?" % m, c)
            them("%s là khoa gì?" % m, c)
            them("Cho tôi tìm %s" % m, c)

# --- Tiện ích trong khu lễ tân ---
for d in tien_ich:
    them("%s ở đâu?" % d["ten"], cho_dan(d))
    them("Tôi muốn tới %s" % d["ten"].lower(), cho_dan(d))

# --- Phần kiến thức chung: LẤY TỪ app-data.json, không gõ lại ở đây ---
#
# ⚠ Trước 09/09/2026 sáu nhóm dưới (cấp cứu · phạm vi robot · khám lần đầu · giới
#   thiệu · chưa có dữ liệu · không phải bác sĩ) được gõ thẳng vào file này, nên
#   chúng CHỈ tồn tại trên cổng OrionStar. Robot không có bản nào trong máy.
#
#   Nay chúng nằm ở HOI_DAP_CHUNG trong dung-du-lieu.py, đi vào app-data.json rồi
#   theo index.html vào assets/ của APK. File này chỉ trải chúng ra thành từng cặp
#   để nạp cổng. Một nguồn, hai đầu ra — sửa câu đáp một chỗ là cả hai đổi theo.
#
#   Cùng lý do đã viết ở đầu file: gõ tay hai bản thì sớm muộn lệch nhau, mà lúc
#   lệch thì robot NÓI một đằng, cổng trả lời một nẻo.
HOI_DAP = D.get("hoi_dap", [])
for _g in HOI_DAP:
    for _h in _g["hoi"]:
        them(_h, _g["dap"])


def hd_dap(nhom):
    """Câu đáp của một nhóm hỏi–đáp chung. Thiếu nhóm là DỪNG, không sinh file rỗng.

    Nhóm bị đổi tên hay xoá bên dung-du-lieu.py mà ở đây vẫn gọi tên cũ thì phải vỡ
    ngay lúc chạy script — chứ không phải sinh ra một tài liệu kiến thức thiếu hẳn
    mục Cấp cứu rồi nằm im trong thư mục người ta copy-dán lên cổng.
    """
    for g in HOI_DAP:
        if g["nhom"] == nhom:
            return g["dap"]
    print("   ! app-data.json thiếu nhóm hỏi–đáp '%s' — xem HOI_DAP_CHUNG trong "
          "dung-du-lieu.py" % nhom)
    raise SystemExit(1)


DAP_CC = hd_dap("cap-cuu")
qt = D["quy_trinh_kham"]

# Bỏ trùng, giữ nguyên thứ tự
_thay = set()
qa_sach = []
for h, a in qa:
    k = h.strip().lower()
    if k in _thay:
        continue
    _thay.add(k)
    qa_sach.append((h, a))

# ═══════════════════════════════════════════════════════════════════════
#  Ghi ra file
# ═══════════════════════════════════════════════════════════════════════
f_qa = os.path.join(RA, "hoi-dap.csv")
# utf-8-sig: Excel trên Windows mở CSV UTF-8 KHÔNG BOM là ra tiếng Việt loạn ký tự
with io.open(f_qa, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Câu hỏi", "Câu trả lời"])
    w.writerows(qa_sach)

# ═══════════════════════════════════════════════════════════════════════
#  HỎI–ĐÁP BẢN .txt — đây mới là bản NẠP ĐƯỢC lên cổng
#
#  ⚠ Cổng chỉ nhận .txt · .pdf · .docx. File .csv ở trên vẫn giữ, nhưng chỉ để
#    mở bằng Excel mà rà soát — nạp lên cổng là bị từ chối.
#
#  Viết mỗi cặp thành hai dòng "Hỏi:" / "Đáp:" rồi cách một dòng trống. Đây là
#  khuôn mô hình đọc quen nhất, và người mở file ra soát cũng đọc được ngay —
#  khác hẳn một dòng CSV dài có dấu ngoặc kép bọc quanh.
# ═══════════════════════════════════════════════════════════════════════
f_qa_txt = os.path.join(RA, "hoi-dap.txt")
_qt = ["HỎI – ĐÁP ROBOT LỄ TÂN — %s" % BV, "═" * 70, "",
       "Sinh tự động từ du-lieu/app-data.json. Đừng sửa tay file này.",
       "Cập nhật: %s · %d cặp hỏi–đáp." % (D["cap_nhat"], len(qa_sach)), "", ""]
for _h, _d in qa_sach:
    _qt += ["Hỏi: " + _h, "Đáp: " + _d, ""]
io.open(f_qa_txt, "w", encoding="utf-8").write("\n".join(_qt))

f_pers = os.path.join(RA, "persona-robot.md")
io.open(f_pers, "w", encoding="utf-8").write(persona_md.replace("{n_qa}", str(len(qa_sach))))

# ═══════════════════════════════════════════════════════════════════════
#  TÀI LIỆU KIẾN THỨC — .txt THUẦN
#
#  ⚠ Cổng OrionStar CHỈ NHẬN .txt · .pdf · .docx cho kho tri thức (anh Trường
#    kiểm 09/09/2026). Bản trước sinh .md — cổng từ chối thẳng, không nạp được.
#
#  ⚠ Và text phải THUẦN, không mang ký hiệu Markdown. Thứ đọc file này là MÔ
#    HÌNH NGÔN NGỮ, không phải trình duyệt: dấu ** quanh chữ, dấu # đầu dòng,
#    bảng vẽ bằng | và --- chỉ là rác chen vào giữa nội dung. Bảng kẻ bằng |
#    còn tệ hơn nữa — mỗi hàng thành một dòng đầy gạch đứng, mô hình phải đoán
#    cột nào là tầng, cột nào là toà nhà. Viết thành câu thì nó đọc thẳng.
# ═══════════════════════════════════════════════════════════════════════
G = "=" * 70          # đường kẻ ngang, để người mở file ra soát nhìn cho dễ

kt = ["KIEN THUC ROBOT LE TAN".replace("KIEN THUC ROBOT LE TAN",
      "KIẾN THỨC ROBOT LỄ TÂN — %s" % BV), G, "",
      "Sinh tự động từ du-lieu/app-data.json bởi dung-kho-tri-thuc.py. Đừng sửa tay file này.",
      "Cập nhật: %s" % D["cap_nhat"],
      "Nguồn: %s" % D["nguon"], "", "",
      "PHẠM VI ĐI LẠI CỦA ROBOT", G, "",
      "Với 16 khoa trong ba toà DI, DII và DIII: robot chỉ ra tới đầu hành lang, rồi đứng",
      "đó chỉ đường bằng lời.",
      "Với Khu Thăm dò chức năng (Nhà A), Khoa Răng Hàm Mặt (Nhà B) và Khoa Chẩn đoán hình",
      "ảnh (Nhà F): robot dẫn tới tận nơi, vì bản đồ có điểm riêng cho mấy chỗ này.",
      "Với Khoa Cấp cứu (Nhà C): robot KHÔNG dẫn — chỉ nói chỗ và giục đi ngay, vì robot",
      "đi chậm hơn người chạy.",
      "Robot không vào trong toà nhà, không lên thang máy, không lên tầng.", "", "",
      "CÁC TOÀ NHÀ", G, ""]
kt += ["%s có %d tầng." % (t["ten"], t["so_tang"]) for t in D["toa"]]
kt += ["Ngoài ra còn Nhà A, Nhà B, Nhà C và Nhà F — mỗi nhà có một khoa nằm ở tầng một.",
       "", "", "BẢNG KHOA PHÒNG", G, "",
       "Mỗi dòng là một chỗ, đọc theo khuôn: tên khoa, tầng, toà nhà, mã phòng.", ""]
for d in khoa + toa_khac + [cap_cuu]:
    for v in d["vi_tri"]:
        _ma = ("phòng " + " hoặc ".join(v["ma"])) if v["ma"] else "không có mã phòng riêng"
        kt.append("- %s: tầng %d, %s, %s. (%s)"
                  % (d["ten"], v["tang"], v["toa_ten"], _ma, d["ghi_chu"]))
kt += ["", "", "CÁC CHỖ TRONG KHU LỄ TÂN — ROBOT DẪN THẲNG TỚI NƠI", G, ""]
kt += ["- %s: %s" % (d["ten"], d["ghi_chu"]) for d in tien_ich]
kt += ["", "", "KHOA CÓ MẶT Ở NHIỀU TOÀ NHÀ", G, "",
       "Gặp mấy khoa này thì PHẢI HỎI LẠI người bệnh đang theo dõi ở toà nào.",
       "Không được tự chọn một toà.", ""]
kt += ["- %s: %s" % (d["ten"], " · ".join(vi_tri_chu(v) for v in d["vi_tri"]))
       for d in khoa if len(d["vi_tri"]) > 1]
kt += ["", "", "CẤP CỨU", G, "", DAP_CC, "",
       "Robot KHÔNG dẫn người cấp cứu: robot đi 0,5 đến 0,8 mét mỗi giây, chậm hơn người",
       "đang chạy. Bảo người nhà bệnh nhân đi theo robot là làm chậm họ.", "", "",
       "KHÁM LẦN ĐẦU, CHƯA CÓ PHIẾU", G, ""]
kt += ["%d. %s: %s" % (i + 1, b[0], b[1]) for i, b in enumerate(qt["buoc"])]
kt += ["", "", "NHỮNG THỨ ROBOT CHƯA CÓ DỮ LIỆU", G, "",
       "Bệnh viện chưa cung cấp, nên robot phải nói thẳng là chưa có và mời hỏi quầy lễ",
       "tân. TUYỆT ĐỐI KHÔNG ĐOÁN:", "",
       "giờ làm việc, lịch trực, số điện thoại, giá khám, viện phí, tên bác sĩ, lịch mổ,",
       "kết quả xét nghiệm, số giường trống, đặt lịch khám, lịch sử bệnh viện.", "", "",
       "ROBOT KHÔNG PHẢI BÁC SĨ", G, "",
       "Không chẩn đoán, không đoán bệnh, không khuyên dùng thuốc, không nhận xét kết quả",
       "xét nghiệm. Người bệnh kể triệu chứng thì robot chỉ giúp tìm khoa phù hợp, và nói",
       "rõ bác sĩ mới là người quyết định.", ""]
f_kt = os.path.join(RA, "kien-thuc.txt")
io.open(f_kt, "w", encoding="utf-8").write("\n".join(kt))

print("→ %s" % f_pers)
print("   Vai trò %d/2000 · Giới thiệu %d/900 · Bổ sung %d/8000"
      % (len(VAI_TRO), len(GIOI_THIEU), len(BO_SUNG)))
print("→ %s" % f_qa)
print("   %d cặp hỏi–đáp" % len(qa_sach))
print("→ %s" % f_qa_txt)
print("   %d cặp, dạng .txt — ĐÂY là bản nạp lên cổng được" % len(qa_sach))
print("→ %s" % f_kt)

qua = [(t, n, h) for t, n, h in
       [("Robot Identity/Role", len(VAI_TRO), 2000),
        ("Service Enterprise Introduction", len(GIOI_THIEU), 900),
        ("Additional Information", len(BO_SUNG), 8000)] if n > h]
if qua:
    print("\n!!! VƯỢT GIỚI HẠN Ô NHẬP:")
    for t, n, h in qua:
        print("    %s: %d ký tự, giới hạn %d" % (t, n, h))
    raise SystemExit(1)
print("\nTất cả các ô đều nằm trong giới hạn.")

# ═══════════════════════════════════════════════════════════════════════
#  CỔNG KIỂM — kho tri thức phải KHỚP dữ liệu app
#
#  Vì sao cần: kho này là thứ MÔ HÌNH đọc, còn app-data.json là thứ MÀN HÌNH đọc.
#  Hai bên lệch nhau thì robot nói một đằng, hiện một nẻo — mà lệch kiểu đó không
#  có gì báo, chỉ lộ ra khi có người hỏi đúng chỗ lệch.
#
#  Đã bắt được thật 08/09/2026: bỏ khoa cấp cứu cũ khỏi dữ liệu xong, persona vẫn
#  ghi cứng "Khoa Hồi sức Cấp cứu Nội, tầng 2 Nhà DIII, phòng D23 và D24", và bảng
#  khoa phòng trong kien-thuc.txt bỏ sót cả ba khoa mới ở nhà A · B · F.
# ═══════════════════════════════════════════════════════════════════════
_kt = io.open(f_kt, encoding="utf-8").read()
_qa = " ".join(h + " " + d for h, d in qa_sach)   # mọi cặp hỏi–đáp đã sinh
_pe = VAI_TRO + GIOI_THIEU + BO_SUNG

_loi = []
for _d in DICH:
    if _d["ten"] not in _kt:
        _loi.append("kien-thuc.txt thiếu: " + _d["ten"])
    if _d["ten"] not in _qa:
        _loi.append("hoi-dap thiếu: " + _d["ten"])

# Tên và mã của những chỗ ĐÃ BỎ không được còn sót lại chỗ nào
_con_dung = {m for _d in DICH for m in _d["ma"]} | {_d["ten"] for _d in DICH}
for _cho, _van in (("hoi-dap", _qa), ("kien-thuc.txt", _kt), ("persona", _pe)):
    for _ma in ("D23", "D24"):
        if _ma not in _con_dung and _ma in _van:
            _loi.append("%s còn nhắc mã đã bỏ: %s" % (_cho, _ma))
    if "Hồi sức Cấp cứu" in _van or "Hồi Sức Cấp Cứu" in _van:
        _loi.append("%s còn nhắc khoa đã bỏ: Hồi sức Cấp cứu Nội" % _cho)

if _loi:
    print("\n!!! KHO TRI THỨC LỆCH DỮ LIỆU APP:")
    for _x in _loi:
        print("    " + _x)
    raise SystemExit(1)
print("Kho tri thức khớp dữ liệu app: %d đích, không sót, không thừa." % len(DICH))

# ═══════════════════════════════════════════════════════════════════════
#  DỌN FILE LẠC — thứ nguy hiểm nhất trong thư mục này là một BẢN CŨ
#
#  Đây là thư mục người ta MỞ RA ĐỂ COPY-DÁN LÊN CỔNG. Một file cũ nằm cạnh
#  file mới, tên na ná, là chuyện sớm muộn có người dán nhầm — mà dán nhầm
#  bản cũ nghĩa là robot chỉ người đang cấp cứu sang một khoa đã bỏ.
#
#  Đã xảy ra thật: persona-robot.txt và kien-thuc.txt bản 13/08/2026 nằm im
#  ở đây gần một tháng, vẫn ghi "Khoa Hồi Sức Cấp Cứu Nội, D23-D24, Nhà DIII".
#
#  Nên script DỜI mọi file lạ sang _cu-khong-dung/ thay vì để đó. Dời chứ
#  không xoá — quy tắc 2 của workspace.
# ═══════════════════════════════════════════════════════════════════════
import shutil
DUOC_PHEP = {"persona-robot.md", "hoi-dap.txt", "hoi-dap.csv", "kien-thuc.txt"}
_kho_cu = os.path.join(RA, "_cu-khong-dung")
_lac = [t for t in sorted(os.listdir(RA))
        if os.path.isfile(os.path.join(RA, t)) and t not in DUOC_PHEP]
if _lac:
    os.makedirs(_kho_cu, exist_ok=True)
    for _t in _lac:
        shutil.move(os.path.join(RA, _t), os.path.join(_kho_cu, _t))
    print("   ! Đã dời %d file lạc sang _cu-khong-dung/: %s" % (len(_lac), ", ".join(_lac)))
    print("     (thư mục này để COPY-DÁN lên cổng — một bản cũ nằm cạnh là có ngày dán nhầm)")
