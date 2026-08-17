# Thử app trên máy tính — Robot lễ tân Bệnh viện Uông Bí

## Mở bản nào

| File | Dùng khi nào |
|---|---|
| **`demo\thu-nghiem.html`** | **Sếp thử ở đây.** Có giả lập robot — bấm được nút dẫn đường, xem được màn chỉ đường và robot tự về sảnh |
| `demo\index.html` | Bản sạch, giống hệt cái nằm trong APK. Không có nút dẫn đường vì máy tính không phải robot |

Nháy đúp `demo\thu-nghiem.html` là chạy. Không cần cài gì, không cần mạng.

**Bấm F11 cho toàn màn hình** — app thiết kế cho màn 1920×1080 nằm ngang của robot, xem trong
cửa sổ nhỏ thì chữ bé lại theo tỉ lệ, dễ tưởng là chữ nhỏ quá.

---

## Bảng thử ở góc dưới bên trái

Bấm vào **🔧 Bảng thử** để mở ra. Trong đó có:

| Nút | Làm gì |
|---|---|
| **Quãng đường dài 3s / 6s / 20s** | Robot thật đi từ sảnh ra trước toà DI mất khoảng 20–40 giây. Để 3s cho nhanh lúc thử, để 20s khi muốn cảm nhận đúng nhịp thật |
| **Tới nơi ngay** | Đang đi thì cho tới nơi luôn, khỏi chờ |
| **Báo lỗi** | Giả vờ robot không tìm được đường — xem app xử lý thế nào |
| **AI đám mây trả lời được** | Bật lên thì **nút micro hiện ra**. Đang tắt là đúng với thực tế hiện nay |
| **Robot sẵn sàng đi** | Tắt đi để xem app báo gì khi robot chưa định vị được |
| **Đồng hồ 5 phút vắng người** | Tắt cho đỡ bị nhảy về màn chờ giữa lúc đang xem |
| **Nhật ký phía dưới** | Robot nói câu gì, app gọi lệnh gì xuống — đọc ở đây |

Bảng này **không có trong APK cài lên robot**. Nó chỉ tồn tại ở bản thử.

---

## Mười việc nên thử

**1. Màn chờ.** Mở lên là mặt robot chớp mắt lặp lại. Chạm vào màn hình để vào menu.

**2. Menu chính.** Chín nhóm chia theo tiếng người bệnh + ô "Tìm theo mã phòng".
Băng cam phía trên là cho người đến khám lần đầu.

**3. Gõ tìm bằng lời của dân.** Gõ vào ô tìm kiếm: `đau bụng` · `đi đẻ` · `đau răng` ·
`lấy thuốc` · `ngất xỉu` · `đưa con đi khám`. Robot phải ra đúng khoa.

**4. Gõ mã phòng.** Gõ `D3` → ra thẳng Khoa Nhi. Gõ `D25` → phải báo không có mã đó.
Hoặc bấm ô **Tìm theo mã phòng** để dùng bàn phím số.

**5. Khoa có ở nhiều toà.** Bấm **Mẹ và bé → Khoa Phụ Sản**. App phải **hỏi lại**
"quý vị đang theo dõi ở toà nào" với ba nút DI / DII / DIII — không được tự chọn.

**6. Dẫn đường ra ngoài khu.** Chọn Khoa Nhi → toà DI → bấm **"Robot dẫn tôi ra trước
cửa toà nhà DI"**. Xem đủ chuỗi:
- Màn đang dẫn, robot nói đúng **một câu** "Xin mời đi theo tôi"
- Dọc đường chỉ **hiện chữ** (vật cản, sắp tới nơi) — robot **không nói thêm câu nào**
- Tới nơi → màn **chỉ đường** chữ khổng lồ, lúc này robot mới đọc
- Đọc xong → thanh **"Tôi về sảnh sau 20 giây"** hiện ra

**7. Dẫn trong khu lễ tân.** Chọn **Viện phí · Thuốc · Tiện ích → Nhà thuốc** → bấm dẫn.
Tới nơi là về thẳng trang chi tiết, **không** qua màn chỉ đường.

**8. Cấp cứu.** Bấm ô đỏ **CẤP CỨU**. Màn đỏ nhấp nháy, robot đọc to hai lần.
**Kiểm kỹ: màn này KHÔNG có nút dẫn đường** — đó là chủ ý, robot đi chậm hơn người chạy.

**9. Khám lần đầu.** Bấm băng cam **"Tôi đến khám lần đầu, chưa có phiếu"** → bốn bước đi khám.

**10. Chữ to hơn.** Nút góc trên bên phải, dành cho người già.

---

## Những gì bản thử này **không** kiểm được

Nói thẳng để Sếp không yên tâm nhầm:

- **Bản đồ và tên điểm thật.** Giả lập nhận mọi tên điểm. Ngoài bệnh viện, sai một ký tự
  trong `Truoc hanh lang` là robot đứng im.
- **Robot có đi lọt không.** Lối đi hẹp, bậc thềm, dốc, người đông — chỉ ra hiện trường mới biết.
- **Quãng đi ngoài trời.** Nova là robot trong nhà. Xem mục cảnh báo trong
  [huong-dan-dat-ten-diem-ban-do.md](huong-dan-dat-ten-diem-ban-do.md).
- **Giọng đọc thật.** Máy tính đọc bằng giọng Windows, nghe khác giọng robot.
  Máy nào chưa cài giọng tiếng Việt thì **không nghe thấy gì** — cứ đọc chữ trong ô
  "Robot đang nói" ở bảng thử, nội dung y hệt.
- **AI hội thoại.** Nút mic bật lên trong bảng thử chỉ là giả lập trả lời. AI thật của hãng
  hiện chưa chạy — xem mục "Vì sao nút micro chưa hiện" trong [README.md](README.md).

---

## Sếp thấy chỗ nào chưa ổn

Ghi lại **màn nào · bấm gì · mong đợi gì · thực tế ra gì**, tôi sửa. Sửa nội dung và giao diện
thì không phải build lại APK, chạy `python dung-app.py` là xong.

## Chạy lại bộ kiểm tự động

```powershell
cd D:\RBW_Claude\11-app-nova\le-tan-benh-vien-uong-bi
node tools\soi-man-hinh.mjs          # chụp 15 màn ở đúng 1920×1080, soi bố cục vỡ
node tools\thu-luong-dan-duong.mjs   # chạy trọn luồng dẫn đường, 19 phép kiểm
```

Bộ thứ hai kiểm đúng những thứ dễ hỏng nhất mà mắt khó bắt: robot có im lặng dọc đường không,
tới nơi có bật đúng màn không, đồng hồ về chỗ có chạy không, cấp cứu có lọt nút dẫn đường vào không.
