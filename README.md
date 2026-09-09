# Robot lễ tân — Bệnh viện Việt Nam – Thụy Điển Uông Bí

App chạy trên **GreetingBot Nova** đặt ở sảnh lễ tân bệnh viện. Hai việc: **tư vấn** người bệnh
tìm đúng khoa theo cách họ tự mô tả, và **dẫn đường** tới nơi.

---

## 🚀 Kỹ thuật viên bắt đầu từ đây

**Chỉ cần cài lên robot, không cần build:**

1. Tải `apk/le-tan-benh-vien-uong-bi-v1.7.apk`
2. Nối cáp USB vào **đầu robot**, dùng **adb 1.0.41** của Android SDK
   (⚠ **không** dùng `C:\Windows\adb.exe` bản 1.0.39 của PUDU — hai bản giết tiến trình của nhau)
   ```powershell
   adb install -r le-tan-benh-vien-uong-bi-v1.7.apk
   ```
3. **Mở app từ RobotOS Home**, tuyệt đối không dùng `am start` — dùng `am start` thì `RobotApi`
   trả `handleApiDisabled`, mất cả dẫn đường lẫn giọng nói mà app không báo lỗi gì.
4. Quét bản đồ và đặt 12 điểm theo **hướng dẫn đặt điểm bản đồ**:
   - Bản dễ nhìn, có sơ đồ và danh sách kiểm, in ra mang theo được:
     [`huong-dan-dat-ten-diem-ban-do.html`](huong-dan-dat-ten-diem-ban-do.html)
     — ⚠ GitHub **không hiển thị** file HTML, nó chỉ hiện mã nguồn. Bấm nút **Download raw file**
     (mũi tên tải xuống ở góc phải) rồi mở bằng Chrome. Hoặc tải cả kho về bằng
     **Code → Download ZIP**, giải nén, nháy đúp file đó.
   - Bản chữ đọc thẳng trên GitHub được:
     [`huong-dan-dat-ten-diem-ban-do.md`](huong-dan-dat-ten-diem-ban-do.md)

**Muốn xem app trông thế nào mà chưa có robot:** mở `demo/thu-nghiem.html` bằng Chrome
(có giả lập robot, bấm được nút dẫn đường) — đọc [HUONG-DAN-THU-NGHIEM.md](HUONG-DAN-THU-NGHIEM.md).

---

Nguồn dữ liệu: tài liệu khoa phòng bệnh viện cung cấp (mã D1–D22 · C1 · CĐHA) + sơ đồ
mặt bằng vẽ tay + bản bổ sung bốn phòng ngày 08/09/2026.
Hồ sơ dự án đầy đủ nằm trong workspace nội bộ của Roboworld, không có trong kho này.

| | |
|---|---|
| Trạng thái | **Bản demo HTML xong, APK build xong. Chưa chạy trên robot thật, chưa khảo sát mặt bằng.** |
| APK | `apk/le-tan-benh-vien-uong-bi-v1.7.apk` — appId riêng · ba toà D dừng ở đầu hành lang · nhà A/B/F dẫn tới tận nơi |
| **Bản thử trên máy tính** | **`demo/thu-nghiem.html`** — có giả lập robot, bấm được nút dẫn đường. Đọc [HUONG-DAN-THU-NGHIEM.md](HUONG-DAN-THU-NGHIEM.md) |
| Demo bản sạch | `demo/index.html` — giống hệt cái nằm trong APK |
| Package | `vn.roboworld.benhvien` |
| Ngày | 11/08/2026 · cập nhật 08/09/2026 (bốn phòng mới + micro bấm-mới-nghe) |

---

## Phạm vi hoạt động — thứ quyết định toàn bộ thiết kế

Robot **chỉ đi trong khu lễ tân**, xa nhất là ra **đầu hành lang** — nó dừng ở đó, còn cách
các toà nhà một quãng. Nó **không vào** DI/DII/DIII, không lên thang máy. Đích đến chia bốn loại:

| Loại | Gồm | Robot làm gì |
|---|---|---|
| `trong-khu` | Quầy tiếp đón · Phòng thu viện phí · Nhà thuốc · Căn tin · Nhà vệ sinh | Dẫn **thẳng tới nơi** |
| `ngoai-khu` | 16 khoa trong 3 toà D, mã D1–D22 | Dẫn ra **`Truoc hanh lang`**, bật màn CHỈ ĐƯỜNG chữ khổng lồ, đọc câu hướng dẫn, rồi **tự quay về sảnh** |
| `toa-khac` | Khu Thăm dò chức năng (nhà A) · Khoa Răng Hàm Mặt (nhà B, D7) · Khoa Chẩn đoán hình ảnh (nhà F) | Dẫn **tới tận nơi** — bản đồ có điểm riêng. Tới nơi thì nhắc tầng và số phòng, **không** mở màn chỉ đường |
| `cap-cuu` | Khoa Cấp cứu (nhà C, C1, tầng 1) | **KHÔNG dẫn.** Màn đỏ, hô to, chỉ chỗ |

⚠ Ba toà D chỉ đường bằng **thứ tự** (“toà nhà thứ hai”). Nhà A · B · C · F **không** nằm dọc
hành lang đó nên tuyệt đối không đếm thứ tự cho chúng — bộ thử canh đúng chỗ này.

**Vì sao cấp cứu không dẫn:** robot đi 0,5–0,8 m/s, chậm hơn người đang chạy. Bảo người nhà
bệnh nhân cấp cứu đi theo robot là làm chậm họ. Màn cấp cứu vì thế **không có nút dẫn đường** —
đó là chủ ý, đừng "sửa" nó.

---

## Tám màn hình

| id | Màn | Ghi chú |
|---|---|---|
| `mh-cho` | Chờ — lặp `emoji_blink.mp4` | app mở lên vào đây, vắng người 5 phút thì tự về |
| `mh-chinh` | Menu 10 nhóm + ô tìm + băng "khám lần đầu" + dải mã phòng | |
| `mh-toa` | Hỏi lại toà nhà | chỉ hiện với khoa có ở nhiều toà (Phụ Sản 3 toà, Nhi 2 toà) |
| `mh-ct` | Chi tiết đích đến | thẻ toà/tầng/mã + sơ đồ + nút dẫn |
| `mh-dan` | Đang dẫn | **robot im lặng dọc đường** |
| `mh-chi` | **Chỉ đường** | bật khi tới `Truoc hanh lang` — chữ to nhất trong app |
| `mh-cc` | **Cấp cứu** | nền đỏ, không có nút dẫn |
| `mh-chat` | Trò chuyện | nút mic **tự ẩn** khi AI hãng chưa trả lời được · mic **bấm mới nghe** |

**Về màu:** giao diện dùng tông **xanh y tế**, không dùng đỏ Roboworld làm màu chính. Đây là
quyết định an toàn chứ không phải thẩm mỹ — màn cấp cứu đỏ toàn khung chỉ còn sức cảnh báo khi
phần còn lại của app không đỏ. Đỏ ở đây được giữ riêng cho cấp cứu.

---

## Dây chuyền dựng

```powershell
cd D:\RBW_Claude\11-app-nova\le-tan-benh-vien-uong-bi
python dung-du-lieu.py      # bảng khoa phòng  → du-lieu/app-data.json     (chỉ khi dữ liệu đổi)
python dung-app.py          # HTML + JSON      → demo/index.html + rải sang android assets
python dung-kho-tri-thuc.py # cùng nguồn       → kho-tri-thuc/ cho cổng OrionStar
node tools\soi-man-hinh.mjs # chụp 17 màn ở đúng 1920×1080 + tự soi bố cục
node tools\thu-luong-dan-duong.mjs   # trọn luồng dẫn đường + micro bấm-mới-nghe
node tools\thu-tim-kiem.mjs          # 51 câu hỏi → ra đúng khoa, hoặc phải nói không biết
.\tools\build-apk.ps1       # → android\app\build\outputs\apk\debug\app-debug.apk
```

`dung-app.py` sinh **hai** bản HTML: `demo/index.html` (bản sạch, đúng cái vào APK) và
`demo/thu-nghiem.html` (bản sạch + `gia-lap-robot.js` nhét vào). Giả lập **không** được rải sang
`android/…/assets` — APK phải là mã thật.

Giả lập dựng lại đúng bộ hàm `CAU` và đúng trình tự báo trạng thái của `Cau.kt`
(`bat-dau` → `dang-di` → `toi-noi`/`loi`), kèm bảng điều khiển để bắt robot gặp vật cản, gặp lỗi,
hoặc bật/tắt cờ AI sẵn sàng. Nhờ đó ba màn chỉ xuất hiện lúc đang dẫn đường — đang dẫn, chỉ đường,
thanh robot về chỗ — thử được ngay trên máy tính thay vì phải mang máy ra bệnh viện.

Xong thì copy tay APK sang `apk/le-tan-benh-vien-uong-bi-vX.Y.apk` (script không tự đổi tên).

`tools/soi-man-hinh.mjs` mượn Playwright của `tools/html-video`, không cài riêng. Nó bắt đúng
loại lỗi hay dính trên Nova: nút bị co về chiều cao 0, nút lọt khỏi khung 1080, và **nút bị một
luật CSS khác đè `display:none`** — cả ba đều không báo lỗi gì, chỉ biến mất khỏi màn hình.

---

## Nạp persona và kiến thức lên cổng OrionStar

`kho-tri-thuc/` chứa bốn file sinh tự động, dùng cho **global-robotmp.orionstar.com**:

| File | Nạp vào đâu |
|---|---|
| `kien-thuc.txt` | **Tải lên kho tri thức** — tài liệu kiến thức nền |
| `hoi-dap.txt` | **Tải lên kho tri thức** — 182 cặp hỏi–đáp |
| `persona-robot.md` | **Không tải lên.** Mở ra đọc rồi copy-dán vào từng ô ở **Robot Persona → Create Robot Persona**, kèm Transition Script và Common Role Greeting |
| `hoi-dap.csv` | **Không tải lên.** Cùng nội dung `hoi-dap.txt`, dạng bảng để mở bằng Excel mà rà soát (UTF-8 có BOM nên không loạn chữ) |

⚠ **Cổng chỉ nhận `.txt` · `.pdf` · `.docx`** (anh Trường kiểm 09/09/2026). Bản trước sinh
`.md` và `.csv` — cổng từ chối thẳng, không nạp được file nào. Nay hai file cần tải lên đều
là `.txt` **thuần**: không dấu `**`, không dấu `#`, không bảng kẻ bằng `|`. Thứ đọc chúng là
mô hình ngôn ngữ chứ không phải trình duyệt — bảng kẻ bằng gạch đứng chỉ làm nó phải đoán
cột nào là tầng, cột nào là toà nhà.

**Vì sao sinh bằng script chứ không gõ tay:** cùng một sự thật ("Khoa Nhi ở tầng 2 nhà DI")
giờ nằm ở hai nơi — màn hình robot đọc từ `app-data.json`, mô hình đám mây đọc từ kho tri thức
trên cổng. Gõ tay hai bản là sớm muộn lệch nhau, mà lúc lệch thì robot **nói một đằng, hiện
một nẻo** — người bệnh biết tin cái nào? Sinh từ cùng một nguồn thì không bao giờ lệch.

Script cũng **đếm ký tự và dừng lại** nếu vượt giới hạn ô nhập của cổng (Identity 2000 ·
Enterprise Introduction 900 · Additional Information 8000).

⚠ Trong `hoi-dap.csv` có một nhóm câu hỏi mà đáp án cố ý là *"thông tin này tôi chưa có"* —
giờ làm việc, giá khám, tên bác sĩ, kết quả xét nghiệm. Đó **không phải chỗ còn thiếu**, mà là
dạy sẵn mô hình cách từ chối. Bệnh viện có cung cấp mấy dữ liệu đó thì hãy thay, đừng để mô
hình tự nghĩ.

---

## Sửa nội dung ở đâu

| Muốn đổi | Sửa file | Rồi chạy |
|---|---|---|
| Khoa trong ba toà DI · DII · DIII | `dung-du-lieu.py` → `BANG_KHOA` | `dung-du-lieu.py` + `dung-app.py` |
| Chỗ ở nhà A · B · C · F (robot dẫn tới tận nơi) | `dung-du-lieu.py` → `BANG_TOA_KHAC` | như trên |
| Tên điểm bản đồ, chỗ robot về đứng | `dung-du-lieu.py` → `DIEM`, `DIEM_VE_CHO` | như trên |
| Nhóm trên màn hình chính | `dung-du-lieu.py` → `NHOM` | như trên |
| Quy trình khám lần đầu | `dung-du-lieu.py` → `QUY_TRINH_KHAM` | như trên |
| Persona, câu chào, kho hỏi–đáp trên cổng | `dung-kho-tri-thuc.py` | `dung-kho-tri-thuc.py` rồi nạp lại cổng |
| Giao diện, bố cục, luồng màn hình | `khung-app.html` | `dung-app.py` |
| Câu robot nói lúc dẫn đường | `Cau.kt` → `danDuongToiDiem` | build lại APK |

> 📄 **Thêm khoa mới, đổi tầng, đổi mã phòng, thêm chỗ robot dẫn tới — có hướng dẫn riêng
> viết cho người không lập trình:** [`huong-dan-them-phong-kham.html`](huong-dan-them-phong-kham.html)
> (bản chữ đọc trên GitHub: [`huong-dan-them-phong-kham.md`](huong-dan-them-phong-kham.md)).

⚠ **Đổi nội dung cũng phải build lại APK.** `index.html` nằm trong `assets/` của APK và
`MainActivity` nạp nó bằng `file:///android_asset/index.html` — không có đường đẩy file rời
sang robot. `day-len-robot.ps1` chỉ đẩy được thư mục `bieu-cam/`. Sửa chữ mà không build lại
thì robot vẫn chạy y bản cũ.

---

## Micro BẤM-MỚI-NGHE — anh Trường chốt 08/09/2026

> *"Người dùng cần bấm vào mic để nói, sau đó sẽ ngắt mic ngay, AI sẽ xử lý đúng giọng đó
> để tránh thu tạp âm."*

Chép lối đã chạy thật ở app Medinova (v1.6) và app sự kiện Tây Ninh.

**Bấm nút micro thì mới thu.** Nói xong cứ dừng, một giây sau mic tự tắt và câu được gửi đi.
Muốn nói tiếp thì bấm lại. Mic **chỉ** sống ở màn Trò chuyện.

### Ba đồng hồ

| | Việc | Ở đâu |
|---|---|---|
| **250 ms** — hoặc **1,4 giây** nếu robot đang nói | từ lúc bấm nút tới lúc mic mở thật. Đợi luồng chữ TTS chảy hết, không thì chính nó đóng lại cửa sổ nghe vừa mở | `moMic()` trong `khung-app.html` |
| **1 giây** sau mỗi `final` | dứt câu thì tắt mic và gửi câu đi | `MainApplication.henTatMicSauKhiDutCau` |
| **15 giây** trần cứng | bấm mic rồi bỏ đi thì tự tắt | `MainApplication.henTatMicNeuKhongAiNoi` |

⚠ **Trần 15 giây không phải cho đẹp.** Đồng hồ một giây chỉ khởi động **sau khi nghe được
một câu** — không có trần thì người bệnh bấm mic rồi bỏ đi là mic mở suốt, đúng cái "thu tạp
âm" mà cả chế độ này sinh ra để tránh.

### ⚠⚠ Quên vế phải đặt ở `batMicro`, KHÔNG phải `tatMicro`

Lỗi đã dính thật trên máy ngày 08/09/2026, bản v1.5: **mic thu tốt, chữ hiện đầy đủ, nút micro
tắt đúng lúc — nhưng robot không trả lời câu nào.**

Nguyên nhân là một dòng. Đường gửi câu đi là:

```
dứt câu → hẹn 1 giây → tatMicro() → guiCauDaGom() → TraLoi.hoi()
```

`tatMicro()` có gọi `quenVe()`, nên nó **xoá sạch vế vừa gom ngay trước khi** `guiCauDaGom()`
đọc tới. Hàm này lấy được chuỗi rỗng, `TraLoi.hoi` không bao giờ chạy, robot đứng im.

Nhìn từ ngoài y hệt "AI hỏng" — và đó là chỗ nguy hiểm: người ta sẽ đi tìm lỗi ở đám mây của
hãng, ở appId, ở mạng, chứ không nghĩ tới một dòng dọn dẹp đặt sai chỗ. Từ v1.6:

- `batMicro()` quên vế — bắt đầu lượt nói mới thì bỏ vế dở của lượt trước.
- `tatMicro()` **không** đụng vào vế.
- `guiCauDaGom()` ghi hẳn một dòng `WARN` khi tới nơi mà không còn vế nào.

Bộ thử `thu-luong-dan-duong.mjs` nay canh đúng chỗ này: giả lập gọi **chính** `CAU.tatMic()`
rồi mới lấy câu ra, đúng thứ tự bên Kotlin. Đã thử ngược — gây lại lỗi thì phép kiểm đỏ.

### Một lượt hỏi = một câu trả lời — anh Trường chốt 08/09/2026

> *"Trong một phiên ghi âm, hãy lưu lại y nguyên và toàn bộ thành một câu thôi, dù dài hay
> ngắn. Người hỏi 1 → Robot trả lời 1."*

Hai chốt, mỗi chốt bịt một lỗ khác nhau:

| Chốt | Ở đâu | Bịt lỗ gì |
|---|---|---|
| `daGuiTrongPhien` | `MainApplication` | Một lần bấm mic gửi **đúng một** câu. Bộ nhận dạng còn bắn thêm vế sau khi câu đã đi — không có chốt này là robot trả lời hai lần cho một lần bấm nút |
| `CHO_DUT_CAU_MS = 1800` | `MainApplication` | Người già kể bệnh ngắt giữa chừng lâu hơn khách hội chợ. Một giây là **xé câu làm đôi** |

### Lời AI chỉ phát khi người bệnh không thao tác

> *"Người dùng đang nghe robot trả lời, nhưng nếu có thao tác — quay lại, thoát ra, xoá đoạn
> chat, hay bấm mic thu tiếp — thì cần ngay lập tức dừng lời thoại đang phát."*

⚠ **Cắt tiếng một mình KHÔNG đủ.** Tầng hội thoại chạy luồng phụ: lúc người bệnh bấm Đóng
thì câu trả lời còn đang trên đường về, **chưa phát nên không có gì để cắt** — mấy giây sau
nó mới cất lên, giữa lúc họ đang đọc thứ khác. Nên phải làm hai việc:

1. **Cắt tiếng đang phát** — cả hai đường: `RobotHelper.dungDoc()` (app) và `AgentCore.stopTTS()` (hãng).
2. **Bỏ câu đang chờ** — cờ `nhanCauTraLoi`, kiểm ở `MainApplication.tuDoc()`, là cửa ra của
   mọi lời robot nói.

Lớp web gọi `CAU.nguoiDungThaoTac()` ở **mọi cửa**: nút Quay lại · Đóng · Xoá đoạn chat ·
bấm micro · rời màn Trò chuyện (đặt trong `ve()`, một chỗ duy nhất).

⚠ **Trừ khi CHÍNH APP chuyển màn.** Tra cứu chắc chắn thì tầng AI tự mở trang chi tiết —
`ve()` sẽ tưởng người bệnh vừa thao tác và bỏ luôn câu trả lời, robot mở đúng trang rồi đứng
câm. Cờ `appTuChuyenMan` trong `khung-app.html` phân biệt hai chuyện đó.

### ⚠ Gom vế trước khi gửi

Bộ nhận dạng của hãng bắn `final` ở **mỗi lần người bệnh ngắt hơi**, không phải chỉ ở cuối câu.
Gửi ngay từng vế thì *"cho tôi hỏi… khoa nhi ở đâu"* thành **hai câu hỏi**, mà nửa đầu tra ra
khoa sai. `MainApplication.gomVe()` gom lại; mỗi `final` mới **đặt lại** đồng hồ một giây.

### ⚠⚠ Đã gỡ `isMicrophoneMuted` — bẫy một chiều

Bản ≤ v1.4 đặt `AgentCore.isMicrophoneMuted = true` ở **hai chỗ** (lúc khởi động và mỗi lần
tắt mic). Đo trên máy thật 26/08/2026: đặt `= true` là **tắt luôn công tắc micro của MÁY**
(`Settings.Global microphone` 1 → 0), và đặt `= false` **không bật lại được**.

> **Máy nào đã chạy bản ≤ v1.4 thì đang bị bịt mic.** Chữa: bấm tay nút "Bật microphone"
> trên dải trạng thái của hãng, hoặc:
> ```
> adb shell settings put global microphone 1
> ```

Từ v1.5 app không đụng vào công tắc đó nữa. Chặn nghe nay bằng hai thứ **đảo chiều được**:
`isEnableWakeFree`, và cờ `dangChoNghe` chốt ở `onASRResult`.

### ⚠ Điều kiện vận hành — không sửa được bằng mã

Log ghi `isVisionEnable: true`: robot dùng **camera** để quyết định câu nói có hướng vào nó
không. **Người nói phải đứng đối diện robot, trong tầm camera.** Đứng cạnh sườn hay nói vọng
từ xa thì bị xếp là tiếng ồn môi trường và câu nói bị bỏ. Phải dặn người trực sảnh.

---

## Bốn cái bẫy đã biết

**1. Trùng tên lớp CSS làm nút biến mất.** Lớp nền của bàn phím mã phòng ban đầu đặt tên `.phu`,
trùng với modifier `.nut-to.phu` của nút phụ ở màn chi tiết. Hai luật cùng độ ưu tiên, luật khai
báo sau thắng, và nút "Nghe robot đọc lại" bị `display:none` nuốt mất — **không báo lỗi gì cả**.
Giờ lớp nền tên là `.lop-phu`. Bộ soi màn hình đã được vá để bắt phần tử `0×0`.

**2. Bỏ dấu tiếng Việt làm đụng chữ.** Ba vụ đã dính, đều đã vá và có ghi chú tại chỗ:
- `đóng` (đóng viện phí) ↔ `đông` (đông y) → đã bỏ mục `'dong'` khỏi bảng đồng nghĩa
- `ngất` (ngất xỉu) ↔ `ngạt` (ngạt mũi) → gõ "ngất xỉu" từng ra Tai Mũi Họng trước Cấp cứu
- `nào` (thế nào) ↔ `não` (u não) → không được đưa `nao` vào danh sách từ đệm

Thêm từ khoá mới thì chạy lại bộ thử ở cuối trang này.

**3. Màn Nova ngang 1920×1080 @560dpi → WebView chỉ cho khung 548×308 CSS px.** Cỡ chữ gốc tính
ra 4,56 px, Chrome nâng lên sàn 8 px, mọi thứ to lên 1,75 lần và tràn ra ngoài thẻ. Chữa bằng
`<meta viewport width=1920>` + bốn setting trong `MainActivity` (`useWideViewPort`,
`loadWithOverviewMode`, `minimumFontSize`, `minimumLogicalFontSize`). **Đừng đụng vào bốn dòng đó.**

**4. `robotservice.jar` cần Gson nhưng không đóng gói kèm.** Thiếu
`implementation("com.google.code.gson:gson:2.10.1")` thì `RobotApi.connectServer` ném
`ClassNotFoundException`, app văng ngay lúc kết nối.

---

## ⚠ Việc còn treo

**1. ~~appId đang mượn của app Mông Dương~~ — ĐÃ XONG 17/08/2026.**
`android/app/src/main/assets/actionRegistry.json` nay ghi appId riêng của app bệnh viện:
`app_70eef22c4a6d4777af413ac942ea0153`. Nạp persona lên cổng OrionStar không còn đè lên app
tra cứu thủ tục nữa. Kiểm sau khi cài: `CAU.thongTinAI()` phải trả đúng chuỗi appId trên;
ra chuỗi khác nghĩa là APK cũ chưa gỡ hẳn.

**2. Chưa khảo sát quãng sảnh → đầu hành lang, và chưa xác nhận THỨ TỰ ba toà nhà.** Xem
[`huong-dan-dat-ten-diem-ban-do.md`](huong-dan-dat-ten-diem-ban-do.md) mục cảnh báo. Không đạt
thì rút điểm `Truoc hanh lang` về cửa sảnh — sửa một dòng trong `dung-du-lieu.py`, không phải sửa code.
App chỉ đường bằng **thứ tự** toà nhà (`toà nhà thứ hai, đó là toà DII`) nên thứ tự sai là chỉ sai toà;
bảng thứ tự ở `TOA_THU_TU` trong `dung-du-lieu.py`.

---

## Phần AI — chép lối làm đã chạy được ở app Mông Dương

Bản 1.1 (17/08/2026) thay toàn bộ tầng AI theo đúng cách app tra cứu thủ tục Mông Dương đã
chạy được từ 11/08/2026. Bốn thứ then chốt:

**1. Agent SDK lấy từ GÓI OFFLINE, không lấy JitPack.** `app/libs/sdk-0.4.7.aar` +
`agent-base-0.2.10.aar`, nguồn ở `01-source-data/11-orionstar-agent-sdk-047/`.
Mọi bản `com.github.orionagent:agent-sdk` trên JitPack (0.2.2 → 0.2.5) đều **ghi cứng sai tên gói
dịch vụ**, nên `AgentCore.*` lặng lẽ không làm gì — không lỗi, không callback, không log.
**Đừng quay lại JitPack.** `jitpack.io` đã gỡ khỏi `settings.gradle.kts`.

**2. `businessInfo` phải là `null`, không được là `""`.** Truyền chuỗi rỗng thì máy chủ trả
`status=2, result=null` sau ~355 ms, không lỗi không lý do. Đây là hai ngày đứng hình ở app kia.
Xem `MainApplication.hoiMoHinh()`.

**3. Bốn công tắc của hãng đều mặc định SAI với app này** — đặt trong `AppAgent.onCreate`:
`isEnableVoiceBar=false` (thanh thoại hãng đè lên giao diện) · `isDisablePlan=true` (không thì
AgentOS và app cùng trả lời một câu) · `isMicrophoneMuted=true` · `isEnableWakeFree=false`
(không thì robot bắt lời người đi ngang giữa lúc đang dẫn người bệnh).

**4. Việc an toàn chặn bằng MÃ, không chặn bằng lời dặn trong prompt.** Ở app kia đã dặn rõ
trong `setObjective` mà mô hình vẫn tự bịa danh sách giấy tờ khai sinh. Ở bệnh viện cái giá cao hơn.

### Đường đi của một câu hỏi — `TraLoi.kt`

```
nghe được câu (onASRResult) hoặc gõ chữ (CAU.hoiRobot) — CÙNG MỘT ĐƯỜNG
  → ① CẤP CỨU?        → hô ngay + bật màn đỏ, KHÔNG hỏi mô hình
  → ② hỏi bệnh?        → từ chối, KHÔNG hỏi mô hình
  → ③ chưa có dữ liệu? → nói thẳng chưa có, KHÔNG hỏi mô hình
  → ④ tra bảng khoa phòng tại chỗ, lấy MỨC TIN CẬY
  → ⑤ dựng prompt kèm ĐÚNG danh sách ứng viên → AgentCore.llm()
  → ⑥ KIỂM dòng KHOA_ID → mới cho robot mở miệng
```

Bước ⑥: mô hình bắt buộc kết thúc bằng `KHOA_ID: <id>` / `KHONG_CO` / `TAM_SU`. Trả id không nằm
trong danh sách ứng viên, hoặc quên hẳn dòng đó, thì **app vứt cả câu trả lời** và đọc câu từ chối
của mình. Sai thì sai theo hướng im lặng.

Mô hình chỉ soạn **câu dẫn**; tên khoa, số tầng, mã phòng do app đọc nguyên văn từ bảng khoa phòng
bệnh viện cung cấp. Con số không đi qua mô hình lần nào.

### Ngưỡng tuyệt đối khi tra cứu

Bài học từ app kia: ngưỡng **tương đối** thì bộ tìm kiếm không bao giờ nói được "tôi không biết" —
hỏi "đăng ký kinh doanh" nó vẫn lấy thủ tục điểm cao nhất trong đám điểm thấp rồi đọc to.

Ở đây có hai ngưỡng, đo trên máy ngày 17/08/2026: **điểm sàn tuyệt đối** `TIN_SAN = 24`, và **độ phủ
từ** ≥ 0,5. Phủ từ là thứ bắt được ca `"thời tiết hôm nay thế nào"` → Khoa Ngoại Thần Kinh (28 điểm,
trên sàn) — bỏ dấu thì "nào" trùng "não". Khoa đó chỉ phủ 1/3 từ có nghĩa nên bị loại.
24 câu hỏi thật đều `chac`/`chua-chac`, 8 câu vô nghĩa đều `khong-thay`.

### Nút micro vẫn tự ẩn

`MainApplication.thamDoAI()` gọi thử mô hình sau khi khởi động 4 giây; chỉ khi trả về `status=1`
(hoặc nghe được một câu ASR thật) mới bật cờ `agentSanSang` → `Cau.baoAISanSang(true)` → lớp web
hiện nút mic. Giữ lại làm lưới an toàn: appId đã có nhưng chưa chạy thử trên robot thật.

Bài học đằng sau: `webkitSpeechRecognition` CÓ tồn tại trong WebView robot, `batMic()` gọi được,
`AppAgent` dựng được — nhưng bấm nút mic thì chết câm. **Mọi phép kiểm "có hàm không" đều đánh lừa.**

---

## Cài lên robot

```powershell
# adb 1.0.41 của Android SDK. KHÔNG dùng C:\Windows\adb.exe (bản 1.0.39 của PUDU) —
# hai bản lệch phiên bản sẽ giết tiến trình của nhau, rớt kết nối liên tục.
.\tools\day-len-robot.ps1 -Ip <IP-robot> -CaiApp
```

**⚠ Mở app từ RobotOS Home, KHÔNG dùng `am start`.** Mở bằng `am start` thì `RobotApi` trả
`handleApiDisabled` — mất cả dẫn đường lẫn giọng nói, mà app không báo lỗi gì.

**Soi giao diện trên robot:**
```powershell
adb shell cat /proc/net/unix | Select-String webview_devtools_remote
adb forward tcp:9222 localabstract:webview_devtools_remote_<pid>
# rồi mở chrome://inspect trên máy tính
```
Chụp màn hình: `adb shell screencap -p /sdcard/_s.png` rồi `adb pull` — **không** dùng
`adb exec-out screencap -p > file.png`, PowerShell chèn BOM làm hỏng PNG.

---

## Tự kiểm nhanh

Trong DevTools của WebView (hoặc Console của Chrome khi mở `demo/index.html`):

```js
CAU.kiemTraBanDo()              // mười hai điểm bản đồ đã đặt đúng tên chưa
CAU.thongTinAI()                // appId, Agent SDK bind chưa, mic đang mở/tắt
CAU.thuLLM('Xin chào', true)    // mô hình đám mây có trả lời không

timDich('đau bụng')             // → Khoa Nội Tiêu Hóa
timDich('đi đẻ')                // → Khoa Phụ Sản  (KHÔNG được ra nhà vệ sinh)
timDich('ngất xỉu')             // → Khoa Cấp cứu  (phải đứng trước Tai Mũi Họng)
timDich('đóng viện phí')        // → Phòng thu viện phí  (KHÔNG được ra đông y)
timDich('u não')                // → Khoa Ngoại Thần Kinh
timTheoMa('D3').dich.ten        // → Khoa Nhi
timTheoMa('C1').dich.ten        // → Khoa Cấp cứu
timTheoMa('D25').dich           // → null  (mã không có thật, phải báo không tìm thấy)
```

Bốn dòng `timDich` giữa là bộ thử hồi quy cho ba vụ đụng chữ ở mục "bẫy" phía trên.
Thêm từ khoá mới vào `dung-du-lieu.py` thì chạy lại cả bảy dòng.
