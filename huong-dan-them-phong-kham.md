# Thêm / sửa phòng khám, khoa, chỉ đường — làm thủ công

> 📄 **Bản HTML dễ nhìn hơn, có ví dụ tô màu và bảng đối chiếu:**
> [`huong-dan-them-phong-kham.html`](huong-dan-them-phong-kham.html) — mở bằng trình duyệt.

Trang này dành cho người **không lập trình**. Muốn thêm một khoa, đổi tầng, đổi mã phòng,
sửa câu robot đọc — chỉ cần sửa **đúng một file**, rồi chạy **ba lệnh**.

---

## Nguyên tắc: một nguồn sự thật

```
dung-du-lieu.py   ←── CHỖ DUY NHẤT SỬA TAY
      │
      │  python dung-du-lieu.py
      ▼
du-lieu/app-data.json          (máy sinh — đừng sửa tay, sửa xong sẽ bị ghi đè)
      │
      ├─ python dung-app.py ────────▶ demo/index.html · android assets · APK
      └─ python dung-kho-tri-thuc.py ▶ kho-tri-thuc/  → nạp lên cổng OrionStar
```

**Không sửa `app-data.json`, không sửa `khung-app.html`, không sửa file Kotlin.**
Cả ba thứ đó tự ăn theo. Sửa `app-data.json` bằng tay thì lần chạy `dung-du-lieu.py`
kế tiếp là mất sạch.

Vì sao bắt buộc đi qua script: cùng một sự thật *"Khoa Nhi ở tầng 2 nhà DI"* nằm ở **ba nơi** —
màn hình robot, câu robot đọc thành tiếng, và kho tri thức trên đám mây cho phần trò chuyện AI.
Gõ tay ba bản là sớm muộn lệch nhau, mà lúc lệch thì robot **nói một đằng, hiện một nẻo**.

---

## Việc 1 — Thêm một khoa trong toà DI / DII / DIII

Đây là việc hay gặp nhất. Mở `dung-du-lieu.py`, tìm bảng `BANG_KHOA`, thêm một khối
như dưới đây vào đúng cụm phù hợp (file đã chia sẵn các cụm bằng dòng `# ── Nội khoa ──`):

```python
    dict(ten="Khoa Da Liễu", nhom="mat-tai-rang", ghi_chu="Da liễu, bệnh ngoài da",
         vi_tri=[("DII", 4, ["D25"])],
         tu_dan="da lieu ngua di ung noi me day vay nen nam da mun trung ca "
                "benh ngoai da rung toc"),
```

Năm thứ phải điền:

| Trường | Điền gì | Lưu ý |
|---|---|---|
| `ten` | Tên khoa đúng như bệnh viện gọi | Có dấu, viết hoa chữ đầu mỗi từ. Đây là chữ hiện trên màn hình **và** là chữ robot đọc |
| `nhom` | Một mã trong bảng `NHOM` | Chép **đúng ký tự**: `me-be` · `tre-em` · `mat-tai-rang` · `noi-khoa` · `ngoai-khoa` · `xuong-khop` · `cap-cuu` · `tien-ich` · `chieu-chup` · `hanh-chinh`. Gõ sai là khoa đó không hiện trong ô nào |
| `ghi_chu` | Một dòng mô tả ngắn | Hiện dưới tên khoa trong danh sách kết quả |
| `vi_tri` | Danh sách chỗ khoa đó có mặt | Xem ngay dưới |
| `tu_dan` | Từ người dân dùng để tìm | Xem mục riêng — đây là trường quan trọng nhất |

### `vi_tri` — toà, tầng, mã phòng

Mỗi phần tử là `("TOÀ", tầng, ["mã phòng", ...])`:

```python
    vi_tri=[("DII", 4, ["D25"])],                       # một chỗ
    vi_tri=[("DI", 2, ["D3", "D4"]), ("DII", 2, ["D13"])],   # khoa có ở HAI toà
    vi_tri=[("DIII", 3, [])],                           # có tầng, chưa có mã phòng
```

- Toà chỉ nhận **`"DI"` · `"DII"` · `"DIII"`** ở bảng này. Chỗ ở nhà A · B · C · F khai
  ở bảng khác — xem **Việc 1b**.
- Tầng là **số**, không phải chữ: `4`, không phải `"bốn"`. Robot tự đổi sang chữ khi đọc.
- Mã phòng viết y như trên phiếu khám: `"D25"`. Không có mã thì để `[]`.
- **Nhiều hơn một phần tử** thì app tự hiện màn hỏi lại *"Quý vị đang theo dõi ở toà nào?"*
  với các nút to — không phải làm gì thêm.

### `tu_dan` — trường quyết định người dân có tìm ra hay không

Đây là các từ người bệnh **thật sự gõ hoặc nói**, viết **không dấu, chữ thường, cách nhau
bằng dấu cách**. Không ai gõ "Khoa Da Liễu" — người ta gõ "ngứa", "nổi mề đay", "dị ứng".

Bốn điều cần nhớ:

1. **Viết cái người dân nói, không viết tên chuyên môn.** Tên khoa đã tự được đưa vào bộ
   tìm kiếm rồi, không cần chép lại.
2. **Không dấu, chữ thường.** `ngua di ung noi me day`, không phải `Ngứa, dị ứng, nổi mề đay`.
3. **Không dấu phẩy**, chỉ dấu cách.
4. ⚠ **Coi chừng từ trùng nhau khi bỏ dấu.** Đây là loại lỗi đã cắn app này ba lần:

   | Bỏ dấu xong | Trùng với | Hậu quả đã xảy ra |
   |---|---|---|
   | ngất → `ngat` | ngạt (mũi) | "ngất xỉu" ra Khoa Tai Mũi Họng trước Cấp Cứu |
   | đóng → `dong` | đông (y) | "đóng viện phí" ra Khoa Y Học Cổ Truyền |
   | nào → `nao` | não | "thời tiết thế nào" ra Khoa Ngoại Thần Kinh |

   Cách chữa: thêm **cụm hai từ** thay vì từ đơn (`ngat xiu` chứ không phải `ngat`), và
   luôn chạy bộ thử ở bước 3 dưới đây.

### Câu robot đọc — **không phải gõ tay**

Không có trường nào để gõ câu chỉ đường. Máy tự ghép từ `ten` + `vi_tri`, đúng công thức
đã chốt với anh Trường. Khối ví dụ trên sinh ra:

> *"Khoa Da Liễu ở tầng bốn, toà nhà đê hai. Phòng đê hai mươi lăm.
> Tôi dẫn quý vị ra đầu hành lang, rồi chỉ đường tiếp."*

và khi robot **tới nơi**:

> *"Đã tới nơi. Xin mời quý vị đi thẳng. Toà nhà thứ hai, đó là toà đê hai.
> Quý vị vào đó, lên tầng bốn, vào Khoa Da Liễu. Tìm phòng đê hai mươi lăm.
> Chúc quý vị mau khoẻ."*

Muốn đổi **cách nói** cho mọi khoa cùng lúc thì sửa hàm `cau_vi_tri()` / `cau_chi_duong()`
ở nửa dưới file — sửa một chỗ, cả 16 khoa đổi theo.

---

## Việc 1b — Thêm một chỗ ở toà A · B · C · F (robot dẫn tới tận nơi)

Từ 08/09/2026 bệnh viện có thêm bốn chỗ **ngoài ba toà D**: Khu Thăm dò chức năng (Nhà A),
Khoa Răng Hàm Mặt (Nhà B), Khoa Cấp cứu (Nhà C) và Khoa Chẩn đoán hình ảnh (Nhà F).
Mấy chỗ này bản đồ robot **có điểm riêng** nên robot đi tới tận nơi, không dừng ở đầu hành lang.

Thêm vào bảng `BANG_TOA_KHAC`:

```python
    dict(ten="Khoa Vật lý trị liệu", nhom="xuong-khop", diem="vat-ly-tri-lieu",
         toa="A", tang=2, ma=[],
         ghi_chu="Tập phục hồi chức năng sau mổ, sau tai biến",
         tu_dan="vat ly tri lieu phuc hoi chuc nang tap di tap van dong"),
```

Khác `BANG_KHOA` ở ba điểm:

| | `BANG_KHOA` (ba toà D) | `BANG_TOA_KHAC` (A · B · C · F) |
|---|---|---|
| Robot đi tới đâu | Đầu hành lang, rồi chỉ đường bằng lời | **Tới tận nơi** |
| Khai vị trí | `vi_tri=[("DI", 2, ["D3"])]` — nhiều chỗ được | `toa=` `tang=` `ma=` — **đúng một chỗ** |
| Điểm bản đồ | Dùng chung `truoc-hanh-lang` | **Phải khai `diem=`** riêng, và kỹ thuật viên phải đặt điểm đó trên robot |

⚠ **Không đếm thứ tự toà nhà cho nhóm này.** Cách nói *"toà nhà thứ hai"* chỉ đúng với ba
toà D xếp dọc hành lang. Nhà A, B, C, F nằm chỗ khác — script tự biết điều đó, đừng sửa lại.

⚠ **Nhớ khai điểm bản đồ trước** (xem Việc 2, Bước A) rồi mới trỏ `diem=` vào.
Trỏ vào một khoá không có trong bảng `DIEM` thì `dung-du-lieu.py` **dừng và báo lỗi**
chứ không sinh file — cổng kiểm thêm 08/09/2026.

---

## Việc 2 — Thêm một chỗ trong khu lễ tân (robot dẫn thẳng tới nơi)

Ví dụ: thêm **Phòng xét nghiệm** ngay trong sảnh. Khác việc 1 ở chỗ robot đi **tới tận nơi**,
nên phải làm **hai bước**, thiếu bước nào robot cũng đứng im.

**Bước A — khai điểm bản đồ.** Thêm một dòng vào bảng `DIEM`:

```python
    "xet-nghiem":   {"ten": "Phòng xét nghiệm",  "diem_ban_do": "Xet nghiem",   "mau": "#3E6B4F"},
```

- `diem_ban_do` phải **trùng từng ký tự** với tên điểm kỹ thuật viên đặt lúc quét bản đồ:
  không dấu, đúng hoa/thường, đúng một dấu cách. Sai một ký tự → `ERROR_DESTINATION_NOT_EXIST`,
  robot nhận lệnh xong đứng im, nhìn từ ngoài y như máy hỏng.
- `mau` là màu thẻ. **Đừng dùng màu đỏ** — đỏ để riêng cho màn cấp cứu.

**Bước B — khai chỗ đến.** Thêm vào bảng `BANG_TIEN_ICH`:

```python
    dict(ten="Phòng xét nghiệm", nhom="tien-ich", diem="xet-nghiem",
         ghi_chu="Lấy máu, xét nghiệm theo chỉ định",
         tu_dan="xet nghiem lay mau thu mau xn nuoc tieu sinh hoa mau "
                "phieu chi dinh xet nghiem",
         doc="Phòng xét nghiệm ở trong khu lễ tân. Quý vị nhớ mang theo phiếu chỉ định. "
             "Tôi dẫn quý vị tới nơi."),
```

Khác việc 1: ở đây **có** trường `doc` — vì robot dẫn thẳng tới nơi nên câu nói ngắn và
tuỳ chỗ, không theo công thức chung. Viết câu như người nói, **số phải viết bằng chữ**
("tầng hai", không phải "tầng 2").

**Bước C — dặn kỹ thuật viên đặt điểm.** Đây là bước ngoài máy tính, và là bước hay quên nhất.
Robot phải có điểm tên `Xet nghiem` trên bản đồ thật thì lệnh dẫn mới chạy.
Xem [`huong-dan-dat-ten-diem-ban-do.html`](huong-dan-dat-ten-diem-ban-do.html) — nhớ **thêm
điểm mới vào bảng trong tài liệu đó**, không thì lần quét map sau người ta lại quét thiếu.

---

## Việc 3 — Sửa khoa đã có

| Muốn | Sửa gì |
|---|---|
| Khoa chuyển tầng | Sửa số tầng trong `vi_tri` |
| Khoa đổi mã phòng | Sửa danh sách mã trong `vi_tri` |
| Khoa mở thêm ở toà khác | **Thêm** một phần tử vào `vi_tri` — app tự chuyển sang hỏi lại toà |
| Khoa đóng bớt một chỗ | **Bớt** phần tử đó đi. Còn đúng một chỗ thì app thôi hỏi lại |
| Đổi tên khoa | Sửa `ten` |
| Người dân tìm không ra | Thêm từ vào `tu_dan` |
| Khoa ngừng hoạt động | Xoá cả khối `dict(...)`, hoặc thêm `#` vào đầu mỗi dòng để tạm tắt |

---

## Ba lệnh phải chạy sau khi sửa

Mở PowerShell tại thư mục app:

```powershell
cd D:\RBW_Claude\11-app-nova\le-tan-benh-vien-uong-bi
python dung-du-lieu.py        # 1. sinh lại dữ liệu
python dung-app.py            # 2. dựng lại màn hình + chép sang Android
python dung-kho-tri-thuc.py   # 3. dựng lại hồ sơ nạp cổng OrionStar
```

Lệnh 1 in ra dòng tổng kết — **đọc dòng này**, nó là phép kiểm nhanh nhất:

```
   22 đích  ·  25 mã phòng  ·  9 nhóm  ·  6 điểm bản đồ
   Mã phòng khớp danh mục: D1–D22 · C1 · CĐHA (D23–D24 đã bỏ theo yêu cầu)
```

Số đích tăng đúng bằng số khoa vừa thêm thì mới đúng.

⚠ Thêm một mã phòng **kiểu mới** (không phải D1–D22, C1, CĐHA) thì lệnh 1 sẽ **dừng lại**
và báo *"Mã phòng LỆCH danh mục — thừa: …"*. Đó là cổng kiểm cố ý: nó bắt người thêm mã
phải xác nhận danh mục. Sửa tập `MONG_DOI` ở cuối `dung-du-lieu.py` rồi chạy lại.
Mã không theo khuôn "một chữ cái + số" (như `CĐHA`) còn phải khai cách đọc trong
`MA_DOC_RIENG`, không thì robot đọc trọ trẹ từng chữ cái.

Lệnh 3 chỉ cần chạy khi có sửa nội dung, và **phải nạp lại lên cổng** thì phần trò chuyện AI
mới biết khoa mới — xem mục cuối.

---

## Kiểm tra trước khi mang lên robot

**1. Bộ thử tự động — bắt buộc.** Nó bắt đúng loại lỗi mà mắt người không thấy:

```powershell
node tools\thu-luong-dan-duong.mjs   # luồng dẫn đường + 7 phép kiểm an toàn
node tools\soi-man-hinh.mjs          # chụp 15 màn, bắt nút tàng hình / tràn khung
```

Bộ thứ nhất có phép kiểm *"Câu vô nghĩa → KHÔNG được bịa ra một khoa"* và
*"Tôi muốn đưa con đi khám → Khoa Nhi"*. Thêm khoa mới với `tu_dan` quá rộng là hai phép
này đỏ ngay — đó chính là lúc phải thu hẹp `tu_dan` lại.

**2. Mở bản thử, bấm tay.** Nháy đúp `demo\thu-nghiem.html` (bản có giả lập robot), rồi:

- Vào đúng ô nhóm của khoa mới → khoa phải có trong danh sách.
- Gõ vào ô tìm kiếm **đúng câu người dân hay nói** ("ngứa", "nổi mẩn") → phải ra khoa mới.
- Gõ mã phòng mới ("D25") → phải ra khoa mới.
- Bấm dẫn đường → xem màn chỉ đường ghi **đúng toà, đúng tầng, đúng thứ tự toà nhà**.
- Bấm nút loa nghe lại câu đọc — nghe có tự nhiên không, số có đọc đúng không.

**3. Thử vài câu vô nghĩa** ("thời tiết hôm nay", "bao giờ có tàu") → robot phải nói
**không biết**, tuyệt đối không được lôi ra một khoa nào.

---

## ⚠ Sửa xong PHẢI build lại APK và cài lại lên robot

Màn hình robot đọc `index.html` **nằm bên trong file APK**. Không có đường đẩy nội dung
rời sang robot — sửa chữ mà không build lại thì robot vẫn chạy y bản cũ.

```powershell
.\tools\build-apk.ps1                      # ra apk\le-tan-benh-vien-uong-bi-vX.Y.apk
.\tools\day-len-robot.ps1 -Ip <IP> -CaiApp
```

Rồi **mở app từ RobotOS Home**, không mở bằng `am start` — mở bằng `am start` thì `RobotApi`
trả `handleApiDisabled`, mất cả dẫn đường lẫn giọng nói.

---

## Nạp lại kho tri thức lên cổng OrionStar

Phần **trò chuyện AI** không đọc APK, nó đọc kho tri thức trên đám mây. Nên khoa mới chỉ
"tồn tại" với AI sau khi nạp lại:

1. Chạy `python dung-kho-tri-thuc.py`.
2. Vào cổng `global-robotmp.orionstar.com`, đúng appId `app_70eef22c4a6d4777af413ac942ea0153`.
3. Nạp lại `kho-tri-thuc\hoi-dap.csv` (mục Knowledge Q&A) và `kho-tri-thuc\kien-thuc.md`.
4. Ô persona ở `kho-tri-thuc\persona-robot.md` chỉ phải dán lại khi đổi tên bệnh viện hoặc
   đổi cách xưng hô — thêm khoa thì không cần.

Chưa nạp lại thì **màn hình vẫn đúng, dẫn đường vẫn đúng**, chỉ riêng phần hỏi bằng miệng
là chưa biết khoa mới. Không nguy hiểm, nhưng đừng để quên.

---

## Việc KHÔNG làm được bằng cách trên

| Muốn | Vì sao khó | Phải làm gì |
|---|---|---|
| Thêm một toà nhà HOÀN TOÀN mới (ngoài A · B · C · F · DI · DII · DIII) | Hai bảng `TOA_CHU` và `TOA_TEN` phải có cách đọc chữ cái toà nhà — thiếu là script dừng | Thêm một dòng vào mỗi bảng, ví dụ `"G": "giê"` và `"G": "Nhà G"`. Rồi khai chỗ đó trong `BANG_TOA_KHAC` như Việc 1b |
| Đổi **thứ tự** ba toà nhà | Robot chỉ đường bằng *"toà nhà thứ hai"*. Sai thứ tự là chỉ sai toà, người bệnh đi nhầm | Sửa bảng `TOA_THU_TU`, nhưng **phải ra hiện trường đếm lại** trước |
| Thêm ô mới trên màn hình chính | Lưới 5 cột đang đủ 10 ô = 2 hàng vừa khít màn. Ô thứ 11 đẩy xuống hàng ba, người già ít khi cuộn | Thêm vào bảng `NHOM` thì ô tự hiện, nhưng nên giữ tổng số ô là **10 hoặc 15** |
| Cho robot đi vào trong toà DI/DII/DIII | Ràng buộc vật lý, không phải phần mềm | Ngoài phạm vi bản 1 |
| Đổi giọng đọc | Giọng do máy robot phát, không nằm trong app | Cài đặt của robot |

---

## Lỗi hay gặp

| Hiện tượng | Nguyên nhân gần như chắc chắn |
|---|---|
| Chạy `dung-du-lieu.py` báo `SyntaxError` | Thiếu dấu phẩy cuối khối `dict(...)`, hoặc thiếu một dấu ngoặc. Xem số dòng trong thông báo |
| Chạy `dung-du-lieu.py` báo `KeyError: 'DIV'` | Toà nhà gõ sai — chỉ có `"DI"`, `"DII"`, `"DIII"` |
| Khoa mới không hiện trong ô nào | `nhom` gõ sai. Chép lại đúng ký tự từ bảng `NHOM` |
| Gõ đúng từ mà không ra khoa mới | `tu_dan` viết có dấu, hoặc có dấu phẩy. Phải không dấu, chỉ dấu cách |
| Ra khoa mới cả khi hỏi chuyện khác | `tu_dan` quá rộng, có từ quá phổ thông. Bỏ bớt, thay bằng cụm hai từ |
| Robot đọc sai số phòng | Chỉ xảy ra với `doc` gõ tay ở `BANG_TIEN_ICH` — số phải viết bằng chữ |
| Robot nhận lệnh dẫn rồi đứng im | Tên trong `diem_ban_do` không khớp tên điểm trên bản đồ robot. So từng ký tự |
| Sửa xong mà robot vẫn như cũ | Quên build lại APK, hoặc quên chạy `dung-app.py` trước khi build |

---

*Cập nhật 27/08/2026 — Roboworld.*
