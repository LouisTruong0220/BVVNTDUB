# -*- coding: utf-8 -*-
"""Sinh bộ hồ sơ nạp lên cổng OrionStar Robot Portal cho robot lễ tân bệnh viện.

Ra ba thứ, đều trong kho-tri-thuc/:
  1. persona-robot.md      — chữ để COPY-DÁN vào từng ô ở trang Create Robot Persona
  2. hoi-dap.csv           — cặp Hỏi–Đáp nạp vào mục Knowledge Q&A (UTF-8 có BOM)
  3. kien-thuc.md          — tài liệu kiến thức nạp vào kho tri thức (bản người đọc được)

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

1. Nạp **Knowledge Q&A** từ `hoi-dap.csv` ({n_qa} cặp hỏi–đáp).
2. Nạp **tài liệu kiến thức** từ `kien-thuc.md`.
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

# --- Cấp cứu ---
v_cc = cap_cuu["vi_tri"][0]
# ⚠ Lấy TÊN từ dữ liệu, đừng gõ tay: bản trước ghi cứng "Khoa Hồi sức Cấp cứu Nội"
#   và khi bệnh viện đổi khoa cấp cứu sang C1 Nhà C thì câu này vẫn chỉ về chỗ cũ —
#   đúng loại sai không ai phát hiện cho tới lúc có người cần thật.
DAP_CC = ("%s ở %s. Quý vị cần cấp cứu thì xin đi ngay, ĐỪNG chờ tôi dẫn — "
          "tôi đi chậm hơn người chạy."
          % (cap_cuu["ten"], vi_tri_chu(v_cc)))
for h in ["Cấp cứu ở đâu?", "Tôi cần cấp cứu", "Có người ngất xỉu", "Khoa cấp cứu đi lối nào?",
          "Người nhà tôi khó thở nặng", "Chảy máu nhiều thì đi đâu?", "Tai nạn thì vào đâu?",
          "Ngộ độc thì đi đâu?", "Có người đột quỵ", "Phòng C1 ở đâu?",
          "Tai nạn giao thông đưa vào đâu?", "Cấp cứu có trực ban đêm không?"]:
    them(h, DAP_CC)

# --- Phạm vi robot ---
PHAM_VI = ("Tôi đi lại trong khu lễ tân. Với ba toà DI, DII, DIII thì tôi ra tới đầu hành lang; "
           "với Nhà A, Nhà B và Nhà F thì tôi dẫn tới tận nơi. Tôi không vào "
           "trong toà nhà và không lên tầng được. Tôi dẫn quý vị tới rồi chỉ đường "
           "để quý vị đi tiếp.")
for h in ["Robot dẫn tôi lên tầng được không?", "Bạn đưa tôi vào phòng khám nhé",
          "Robot đi được tới đâu?", "Bạn dẫn tôi vào nhà DII được không?"]:
    them(h, PHAM_VI)

# --- Khám lần đầu ---
qt = D["quy_trinh_kham"]
DAP_QT = ("Quý vị đến khám lần đầu thì mời tới quầy tiếp đón trước. " +
          " ".join("%d) %s: %s" % (i + 1, b[0], b[1]) for i, b in enumerate(qt["buoc"])) +
          " Quý vị nhớ mang căn cước và thẻ bảo hiểm y tế nếu có. Tôi dẫn quý vị tới quầy tiếp đón được.")
for h in ["Tôi đến khám lần đầu thì làm gì?", "Tôi chưa có phiếu khám", "Đăng ký khám ở đâu?",
          "Khám bệnh bắt đầu từ đâu?", "Tôi chưa biết mình khám khoa nào"]:
    them(h, DAP_QT)

# --- Giới thiệu ---
them("Bạn là ai?", "Tôi là robot lễ tân của %s. Tôi giúp quý vị tìm khoa, tìm phòng và dẫn "
                   "đường trong khu lễ tân." % BV)
them("Bệnh viện có mấy toà nhà?",
     "Khu khám và điều trị có ba toà: %s. Ngoài ra còn %s."
     % (", ".join("%s %d tầng" % (t["ten"], t["so_tang"]) for t in D["toa"]),
        ", ".join("%s ở %s" % (d["ten"], d["vi_tri"][0]["toa_ten"]) for d in toa_khac + [cap_cuu])))
them("Bệnh viện có những khoa nào?",
     "Bệnh viện có %d khoa với %d mã phòng %s: %s."
     % (len(khoa) + len(toa_khac) + 1, tong_ma, MO_TA_MA,
        ", ".join(d["ten"] for d in khoa + toa_khac + [cap_cuu])))

# --- Những thứ CHƯA CÓ dữ liệu: cố ý dạy mô hình cách từ chối ---
for h in ["Bệnh viện làm việc mấy giờ?", "Hôm nay bác sĩ nào trực?", "Khám ở đây hết bao nhiêu tiền?",
          "Số điện thoại bệnh viện là gì?", "Kết quả xét nghiệm của tôi thế nào?",
          "Còn giường trống không?", "Bác sĩ nào giỏi nhất khoa này?", "Bao giờ tới lượt tôi?",
          "Tôi đặt lịch khám online được không?", "Bệnh viện thành lập năm nào?"]:
    them(h, CHUA_CO)

# --- Không phải bác sĩ ---
KHONG_KHAM = ("Tôi là robot chỉ đường, tôi không khám bệnh và không đoán bệnh được. "
              "Tôi chỉ giúp quý vị tìm đúng khoa, còn bác sĩ ở phòng khám mới là người quyết định.")
for h in ["Tôi bị bệnh gì?", "Bệnh của tôi có nặng không?", "Tôi nên uống thuốc gì?",
          "Xem giúp tôi kết quả này với", "Tôi có cần mổ không?"]:
    them(h, KHONG_KHAM)

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

f_pers = os.path.join(RA, "persona-robot.md")
io.open(f_pers, "w", encoding="utf-8").write(persona_md.replace("{n_qa}", str(len(qa_sach))))

# --- Tài liệu kiến thức ---
kt = ["# Kiến thức robot lễ tân — %s" % BV, "",
      "> Sinh tự động từ `du-lieu/app-data.json` bởi `dung-kho-tri-thuc.py`. Đừng sửa tay.",
      "> Cập nhật: %s · Nguồn: %s" % (D["cap_nhat"], D["nguon"]), "",
      "## Phạm vi hoạt động của robot", "",
      "16 khoa trong ba toà **DI · DII · DIII**: robot ra tới **đầu hành lang** rồi chỉ đường bằng lời.",
      "**Nhà A · Nhà B · Nhà F**: robot dẫn **tới tận nơi** — bản đồ có điểm riêng.",
      "**Khoa Cấp cứu (Nhà C)**: robot **không dẫn**, chỉ hô to và chỉ chỗ — robot chậm hơn người chạy.",
      "Robot **không** vào trong toà nhà, **không** lên thang máy, **không** lên tầng.", "",
      "## Các toà nhà", ""]
kt += ["- **%s** — %d tầng" % (t["ten"], t["so_tang"]) for t in D["toa"]]
kt += ["", "## Bảng khoa phòng", "",
       "| Mã phòng | Khoa | Tầng | Toà nhà | Ghi chú |", "|---|---|---:|---|---|"]
for d in khoa + toa_khac + [cap_cuu]:
    for v in d["vi_tri"]:
        kt.append("| %s | %s | %d | %s | %s |" % (
            ", ".join(v["ma"]) if v["ma"] else "—", d["ten"], v["tang"], v["toa_ten"], d["ghi_chu"]))
kt += ["", "## Các chỗ trong khu lễ tân — robot dẫn thẳng tới nơi", "",
       "| Nơi | Làm gì ở đó |", "|---|---|"]
kt += ["| %s | %s |" % (d["ten"], d["ghi_chu"]) for d in tien_ich]
kt += ["", "## Khoa có mặt ở nhiều toà nhà", "",
       "Gặp mấy khoa này thì **phải hỏi lại** người bệnh đang theo dõi ở toà nào, không được tự chọn.", ""]
kt += ["- **%s**: %s" % (d["ten"], " · ".join(vi_tri_chu(v) for v in d["vi_tri"]))
       for d in khoa if len(d["vi_tri"]) > 1]
kt += ["", "## Cấp cứu", "", DAP_CC, "",
       "Robot **không dẫn** người cấp cứu: robot đi 0,5–0,8 m/s, chậm hơn người chạy.", "",
       "## Khám lần đầu", ""]
kt += ["%d. **%s** — %s" % (i + 1, b[0], b[1]) for i, b in enumerate(qt["buoc"])]
kt += ["", "## Những thứ robot CHƯA có dữ liệu", "",
       "Bệnh viện chưa cung cấp, nên robot phải nói thẳng là chưa có và mời hỏi quầy lễ tân —",
       "**không được đoán**:", "",
       "giờ làm việc · lịch trực · số điện thoại · giá khám và viện phí · tên bác sĩ ·",
       "lịch mổ · kết quả xét nghiệm · số giường trống · đặt lịch khám · lịch sử bệnh viện", "",
       "## Robot không phải bác sĩ", "",
       "Không chẩn đoán, không đoán bệnh, không khuyên dùng thuốc, không nhận xét kết quả",
       "xét nghiệm. Người bệnh kể triệu chứng thì robot chỉ giúp tìm khoa phù hợp và nói rõ",
       "bác sĩ mới là người quyết định.", ""]
f_kt = os.path.join(RA, "kien-thuc.md")
io.open(f_kt, "w", encoding="utf-8").write("\n".join(kt))

print("→ %s" % f_pers)
print("   Vai trò %d/2000 · Giới thiệu %d/900 · Bổ sung %d/8000"
      % (len(VAI_TRO), len(GIOI_THIEU), len(BO_SUNG)))
print("→ %s" % f_qa)
print("   %d cặp hỏi–đáp" % len(qa_sach))
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
#  khoa phòng trong kien-thuc.md bỏ sót cả ba khoa mới ở nhà A · B · F.
# ═══════════════════════════════════════════════════════════════════════
_kt = io.open(f_kt, encoding="utf-8").read()
_qa = " ".join(h + " " + d for h, d in qa_sach)   # mọi cặp hỏi–đáp đã sinh
_pe = VAI_TRO + GIOI_THIEU + BO_SUNG

_loi = []
for _d in DICH:
    if _d["ten"] not in _kt:
        _loi.append("kien-thuc.md thiếu: " + _d["ten"])
    if _d["ten"] not in _qa:
        _loi.append("hoi-dap.csv thiếu: " + _d["ten"])

# Tên và mã của những chỗ ĐÃ BỎ không được còn sót lại chỗ nào
_con_dung = {m for _d in DICH for m in _d["ma"]} | {_d["ten"] for _d in DICH}
for _cho, _van in (("hoi-dap.csv", _qa), ("kien-thuc.md", _kt), ("persona", _pe)):
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
DUOC_PHEP = {"persona-robot.md", "hoi-dap.csv", "kien-thuc.md"}
_kho_cu = os.path.join(RA, "_cu-khong-dung")
_lac = [t for t in sorted(os.listdir(RA))
        if os.path.isfile(os.path.join(RA, t)) and t not in DUOC_PHEP]
if _lac:
    os.makedirs(_kho_cu, exist_ok=True)
    for _t in _lac:
        shutil.move(os.path.join(RA, _t), os.path.join(_kho_cu, _t))
    print("   ! Đã dời %d file lạc sang _cu-khong-dung/: %s" % (len(_lac), ", ".join(_lac)))
    print("     (thư mục này để COPY-DÁN lên cổng — một bản cũ nằm cạnh là có ngày dán nhầm)")
