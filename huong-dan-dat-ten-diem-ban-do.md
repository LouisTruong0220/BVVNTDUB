# Đặt tên điểm trên bản đồ robot — Bệnh viện Việt Nam – Thụy Điển Uông Bí

> 📄 **Bản HTML dễ nhìn hơn, có sơ đồ và danh sách kiểm, in ra mang theo được:**
> [`huong-dan-dat-ten-diem-ban-do.html`](huong-dan-dat-ten-diem-ban-do.html) — mở bằng trình duyệt.

> Dành cho kỹ thuật viên đi quét bản đồ tại bệnh viện. Đọc hết trang này **trước khi** ra hiện trường.

App gọi lệnh dẫn đường bằng **tên điểm**, không phải toạ độ. Đặt sai tên thì robot nhận lệnh
xong đứng im và báo `ERROR_DESTINATION_NOT_EXIST` — nhìn từ ngoài trông y như máy hỏng.

---

## Mười hai điểm phải đặt

| # | Tên điểm — gõ **đúng từng ký tự** | Đặt ở đâu |
|---|---|---|
| 1 | `Tiep don` | Cách quầy tiếp đón / đăng ký khám khoảng 1 m, mặt robot hướng vào quầy |
| 2 | `Vien phi` | Trước phòng thu viện phí |
| 3 | `Nha thuoc` | Trước nhà thuốc bệnh viện |
| 4 | `Can tin` | Trước cửa căn tin |
| 5 | `Nha ve sinh` | Đầu lối rẽ vào nhà vệ sinh khu lễ tân — **không** đặt sát cửa |
| 6 | `Truoc hanh lang` | **Đầu hành lang** dẫn ra ba toà nhà — chỗ đứng nhìn thẳng thấy được cả DI, DII, DIII xếp theo thứ tự |
| 7 | `Sanh cho` | Chỗ robot đứng đợi khách giữa sảnh lễ tân |
| 8 | `Tram sac` | Cọc sạc |

**Bốn điểm bổ sung 08/09/2026** — bệnh viện thêm bốn chỗ ở các toà A · B · C · F.
Khác tám điểm trên ở chỗ robot đi **tới tận nơi**, không dừng ở đầu hành lang:

| # | Tên điểm | Đặt ở đâu |
|---|---|---|
| 9 | `Khoa cap cuu` | Trước cửa Khoa Cấp cứu, Nhà C tầng 1 (phòng C1) |
| 10 | `Khu Tham do chuc nang` | Trước cửa Khu Thăm dò chức năng, Nhà A tầng 1 |
| 11 | `Khoa Rang Ham Mat` | Trước cửa Khoa Răng Hàm Mặt, Nhà B tầng 1 (phòng D7) |
| 12 | `Khoa chan doan hinh anh` | Trước cửa Khoa Chẩn đoán hình ảnh, Nhà F tầng 1 |

> 💡 **Bốn điểm này app dò tên MỀM.** Từ bản 1.4, trước khi gửi lệnh đi, app hỏi robot
> danh sách điểm thật rồi tự dò: bỏ dấu, không phân biệt hoa thường, gộp khoảng trắng.
> Nên `Khoa cap cuu`, `Khoa Cấp cứu` hay `KHOA CAP CUU` đều tìm ra nhau.

### ✅ Đặt tên CÓ DẤU tiếng Việt vẫn chạy

Anh Trường hỏi 09/09/2026. Câu trả lời: **có dấu không sao cả.** App bỏ dấu trước khi so tên,
nên bản đồ ghi `Khoa Chẩn đoán hình ảnh` mà app hỏi `Khoa chan doan hinh anh` thì vẫn khớp.
Đã đo cả **12/12 điểm** đặt tên có dấu, không điểm nào trượt.

Cột "gõ đúng từng ký tự" ở hai bảng trên là **khuyến nghị cho thống nhất**, không phải điều kiện
để chạy. Bản đồ đã đặt tên có dấu thì cứ để nguyên, đừng sửa lại cho mệt.

### ⚠ Thứ dò mềm KHÔNG cứu được: sai CHÍNH TẢ

Bỏ dấu chỉ bỏ **dấu thanh và dấu mũ** — nó không sửa **chữ**. Hai chuỗi này vẫn khác nhau:

```
bản đồ:  Khoa chuẩn đoán hình ảnh  →  khoa chuan doan hinh anh
app hỏi: Khoa chan doan hinh anh   →  khoa chan doan hinh anh
                                          ↑ khác một chữ "u"
```

Đây đúng là lỗi làm **Khoa Chẩn đoán hình ảnh** không dẫn đường được (09/09/2026) — trong khi
ba chỗ mới kia chạy bình thường, vì chúng được đặt theo đúng tên app đưa ra. *"Chuẩn đoán"* là
lỗi chính tả rất phổ biến của *"chẩn đoán"*; từ đúng trong y khoa là **chẩn đoán**.

Từ bản 1.9 app có thêm **bảng bí danh** (`BI_DANH_DIEM` trong `dung-du-lieu.py`) nên nó nhận cả
`Khoa chuẩn đoán hình ảnh`, `Chẩn đoán hình ảnh` (thiếu chữ "Khoa") và `Khoa CĐHA`. Cài bản 1.9
là chạy, **không phải sửa gì trên bản đồ**.

> Bí danh là **lưới đỡ**, không phải cách đặt tên. Điểm đặt mới thì cứ đặt đúng tên ở bảng trên.

### ⚠ Sửa tên điểm xong phải KHỞI ĐỘNG LẠI APP — hoặc dùng bản 1.9

App hỏi robot danh sách điểm **lúc khởi động**. Sửa tên hay đặt thêm điểm giữa chừng thì app vẫn
giữ danh sách cũ, nhìn y hệt *"sửa rồi mà vẫn không dẫn được"* — và người ta sẽ đi sửa thêm lần
nữa. Từ bản 1.9, dò tên không ra thì app **tự hỏi lại robot** rồi thử tiếp, nên không cần tắt mở
app nữa.

⚠ Dò mềm và bí danh **không cứu được tên khác nghĩa**. Cứ kiểm bằng `CAU.kiemTraBanDo()` cho chắc,
đừng tin bằng mắt.

⚠ **Robot đi thật tới bốn chỗ này**, nên quãng đường tới đó phải đạt điều kiện của máy
trong nhà — giống hệt phần khảo sát `Truoc hanh lang` bên dưới: bậc ≤ 2 cm, dốc ≤ 5°,
sàn phẳng liền mạch, có mái che. Chỗ nào không đạt thì **báo lại**, đừng đặt điểm rồi
để robot tự đi ra ngoài trời.

**Điều DUY NHẤT tuyệt đối phải giữ: đúng CHỮ.**

`Vien phi` ≠ `Vien phi - Tang 1`, và `chuan doan` ≠ `chan doan`. Thêm chữ, thiếu chữ, hay sai
chính tả là robot không tìm ra điểm.

Ba thứ dưới đây app **tự lo được**, ghi ra để khỏi ai mất công:

| Khác nhau ở | App có nhận không |
|---|---|
| Dấu tiếng Việt — `Tiếp đón` ↔ `Tiep don` | ✅ nhận |
| Hoa/thường — `Nha thuoc` ↔ `NHA THUOC` | ✅ nhận |
| Khoảng trắng thừa — `Truoc  hanh lang ` | ✅ nhận |
| **Sai một chữ** — `Khoa chuẩn đoán…` ↔ `Khoa chẩn đoán…` | ❌ **không**, trừ khi khai bí danh |

Vẫn khuyên đặt **không dấu, đúng như bảng trên** cho thống nhất và dễ đọc lại về sau — nhưng
bản đồ đã lỡ đặt có dấu thì **đừng sửa**, nó chạy bình thường.

Muốn dùng tên khác thì **không sửa mã Kotlin** — sửa trường `diem_ban_do` trong
`dung-du-lieu.py`, chạy `python dung-du-lieu.py` rồi `python dung-app.py`, build lại APK.
Tên điểm nằm trong dữ liệu chứ không ghi cứng trong mã.

> 📄 **Thêm một điểm MỚI** (ví dụ phòng xét nghiệm) thì phải khai thêm trong app rồi mới đặt
> trên robot — xem [`huong-dan-them-phong-kham.html`](huong-dan-them-phong-kham.html) mục 4.
> Đặt điểm trên robot mà quên khai trong app thì robot không bao giờ được lệnh đi tới đó.

---

## ⚠ Điểm `Truoc hanh lang` — phải khảo sát trước khi đặt

Đây là điểm xa nhất robot đi tới, và là điểm duy nhất có thể nằm **ngoài nhà**.
Nova là robot trong nhà. Trước khi đặt điểm này, đi bộ đúng quãng đường robot sẽ đi
và kiểm bốn thứ:

| Kiểm | Đạt thì | Không đạt thì |
|---|---|---|
| Bậc, gờ, ngưỡng cửa | ≤ 2 cm | **Không đặt điểm ngoài trời** |
| Độ dốc | ≤ 5° | như trên |
| Mặt sàn | phẳng, liền mạch, không rãnh thoát nước hở, không sỏi | như trên |
| Mái che | có, robot không dính mưa | như trên |

**Không đạt một mục nào cũng phải rút điểm về trong nhà:** đặt `Truoc hanh lang` ngay **cửa sảnh
nhìn ra sân**. App không cần sửa gì — người bệnh vẫn được dẫn tới đó, nghe câu chỉ đường,
rồi tự đi tiếp. Chỉ khác là quãng tự đi dài hơn vài chục mét.

Báo lại anh Trường kết quả khảo sát để ghi vào `10-project/Benh-vien-Uong-Bi/HO-SO.md` mục 2.

### ⚠ Và phải xác nhận THỨ TỰ ba toà nhà

App chỉ đường bằng **thứ tự** chứ không bằng tên: *"Xin mời đi thẳng, toà nhà thứ hai,
đó là toà DII."* Lý do là đứng ở đầu hành lang thì ba toà trông giống hệt nhau và biển
tên xa quá không đọc nổi — nhất là người già, người đang ôm con.

Nghĩa là **thứ tự phải đúng, không thì robot chỉ sai toà.** Đứng đúng chỗ đặt điểm
`Truoc hanh lang`, nhìn thẳng, đếm xem toà nào tới trước:

| Thứ tự tính từ đầu hành lang | App đang giả định là |
|---|---|
| Toà nhà đầu tiên | Nhà DI |
| Toà nhà thứ hai | Nhà DII |
| Toà nhà thứ ba | Nhà DIII |

Khác đi thì sửa bảng `TOA_THU_TU` trong `dung-du-lieu.py`, chạy lại `dung-du-lieu.py`
và `dung-app.py` — **không phải sửa mã Kotlin**, nhưng phải đẩy lại `index.html` lên robot.

---

## Quy trình quét bản đồ

**1. Quét map**
- Làm **ngoài giờ cao điểm**. Sảnh bệnh viện đông nhất 6h30–10h00; người đi lại liên tục làm
  bản đồ đầy vệt nhiễu.
- Đẩy robot đi **chậm**, bám sát tường một vòng, rồi đi lại giữa sảnh.
- Đừng bỏ sót góc khuất, hốc cột, khu ghế chờ — chỗ nào không quét thì robot coi như không có
  đường, và sẽ từ chối đi qua.

**2. Đặt điểm**
- Đứng **cách đích khoảng 1 m**, mặt robot **hướng về** đích. Hướng đứng cũng được lưu cùng điểm —
  đặt quay lưng thì robot tới nơi sẽ quay lưng vào quầy.
- Chỗ đặt phải chừa mỗi bên ~1 m để robot xoay được, và **không chắn lối đi**. Robot đứng chờ
  giữa lối vào khoa cấp cứu là chuyện nghiêm trọng.
- Gõ tên theo đúng bảng trên. Gõ xong đọc lại một lượt.

**3. Định vị**
- Bật máy tại `Tram sac` rồi cho định vị. Định vị ở chỗ khác thì robot dễ nhận nhầm vị trí ban đầu.

---

## Tự kiểm sau khi đặt — không cần vào Cài đặt

Mở app, nối DevTools vào WebView (xem README), gõ:

```js
CAU.kiemTraBanDo()
```

Kết quả trả về qua `window.baoTinhTrangBanDo(json)` gồm `daDinhVi` và `danhSachDiem`.
**Đối chiếu đủ mười hai tên ở bảng trên.**

Rồi thử dẫn đường theo thứ tự tăng dần độ rủi ro:

1. `Nha thuoc` hoặc `Tiep don` — gần, trong nhà, an toàn nhất.
2. `Nha ve sinh` — thường là chỗ hẹp nhất.
3. `Truoc hanh lang` — **đi bộ theo robot suốt quãng này**, canh xem có vướng bậc, dốc, người đông.
4. Xác nhận robot **tự quay về** `Sanh cho` sau khi đọc xong câu chỉ đường.

---

## Robot nhận lệnh nhưng không nhúc nhích

Xem logcat (`adb logcat -s BVCau BVApp RobotHelper`):

| Thấy gì | Nghĩa là | Làm gì |
|---|---|---|
| `startNavigation('Tiep don') trả mã = 0` | App gửi lệnh đúng, lỗi nằm ở máy | xem ba bước dưới |
| `ERROR_DESTINATION_NOT_EXIST` | **Tên điểm sai** | so lại từng ký tự với bảng trên |
| `status=1025 global path search failed` | Robot không tìm ra đường | ① nhả nút dừng khẩn cấp ② đẩy robot ra chỗ thoáng, chừa mỗi bên ~1 m ③ tắt nguồn bật lại hẳn |
| `STATUS_NAVI_OUT_MAP` | Robot đang đứng ngoài vùng đã quét | đẩy về trong sảnh rồi định vị lại |
| `can send failed` in ~1.500 dòng/giây | **KHÔNG phải lỗi** | bỏ qua, ROM Nova in thế cả lúc chạy tốt |

Không có dòng `startNavigation` nào trong log nghĩa là app chưa gửi lệnh — nhiều khả năng
app được mở bằng `am start` thay vì mở từ **RobotOS Home**. Mở bằng `am start` thì `RobotApi`
trả `handleApiDisabled`, mất cả dẫn đường lẫn giọng nói.
