# Đặt tên điểm trên bản đồ robot — Bệnh viện Việt Nam – Thụy Điển Uông Bí

> 📄 **Bản HTML dễ nhìn hơn, có sơ đồ và danh sách kiểm, in ra mang theo được:**
> [`huong-dan-dat-ten-diem-ban-do.html`](huong-dan-dat-ten-diem-ban-do.html) — mở bằng trình duyệt.

> Dành cho kỹ thuật viên đi quét bản đồ tại bệnh viện. Đọc hết trang này **trước khi** ra hiện trường.

App gọi lệnh dẫn đường bằng **tên điểm**, không phải toạ độ. Đặt sai tên thì robot nhận lệnh
xong đứng im và báo `ERROR_DESTINATION_NOT_EXIST` — nhìn từ ngoài trông y như máy hỏng.

---

## Tám điểm phải đặt

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

**Bốn điều tuyệt đối phải giữ:**

1. **Không dấu tiếng Việt.** `Tiep don`, KHÔNG phải `Tiếp đón`.
2. **Đúng hoa/thường.** Chữ cái đầu viết hoa, phần còn lại viết thường. `Nha thuoc` ≠ `Nha Thuoc`.
3. **Đúng một dấu cách** giữa các chữ. `Truoc hanh lang` có ba chữ, hai dấu cách.
4. **Không thêm gì phía sau.** `Vien phi` ≠ `Vien phi - Tang 1`.

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
**Đối chiếu đủ tám tên ở bảng trên, từng ký tự một.**

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
