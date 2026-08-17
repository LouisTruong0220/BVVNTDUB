# -*- coding: utf-8 -*-
"""Ghép khung-app.html + du-lieu/app-data.json thành demo/index.html tự chứa,
rồi rải sang chỗ Android build APK.  (App lễ tân Bệnh viện Việt Nam – Thụy Điển Uông Bí)

Vì sao phải nhúng dữ liệu vào thẳng file HTML: Chromium chặn fetch() qua giao thức
file://, nên app mở bằng cách nháy đúp sẽ không tải được file JSON rời.
Nhúng vào rồi thì nháy đúp là chạy, không cần máy chủ web.

Vì sao script tự copy sang android/app/src/main/assets/: trước đây phải copy tay,
và LẦN NÀO CŨNG QUÊN — sửa giao diện xong build APK ra vẫn là bản cũ, ngồi soi
nửa buổi không hiểu vì sao. Video biểu cảm cũng đi theo đường này.

Video KHÔNG nhúng base64 vào HTML: 2,9 MB nhị phân nở thành ~4 MB chữ, WebView
phải phân tích cả file trước khi vẽ được gì. Để rời cạnh index.html, đường dẫn
tương đối chạy giống nhau ở cả file:// trên máy tính lẫn file:///android_asset/.
"""
import io, os, sys, shutil

# Windows mặc định cp1252 -> print tiếng Việt là lỗi charmap. Ép UTF-8 cho stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
KHUNG = os.path.join(HERE, "khung-app.html")
DULIEU = os.path.join(HERE, "du-lieu", "app-data.json")
BIEUCAM = os.path.join(HERE, "bieu-cam")
DEMO = os.path.join(HERE, "demo")
ASSETS = os.path.join(HERE, "android", "app", "src", "main", "assets")
RA = os.path.join(DEMO, "index.html")
os.makedirs(DEMO, exist_ok=True)

khung = io.open(KHUNG, encoding="utf-8").read()
data = io.open(DULIEU, encoding="utf-8").read()

MOC = "/*__DU_LIEU__*/"
if MOC not in khung:
    raise SystemExit("Không tìm thấy mốc %s trong khung-app.html" % MOC)

# </script> nằm trong chuỗi JSON sẽ cắt sớm thẻ script — chèn dấu thoát
data = data.replace("</", "<\\/")

html = khung.replace(MOC, "window.DU_LIEU=" + data + ";")
with io.open(RA, "w", encoding="utf-8") as f:
    f.write(html)

# ── Bản THỬ có giả lập robot ─────────────────────────────────────────────
#
# Sinh cùng lúc với bản thường, cố ý. Bản demo không có đối tượng CAU nên app tự
# ẩn nút dẫn đường — nghĩa là ba màn quan trọng nhất (đang dẫn · chỉ đường · robot
# tự về sảnh) không thử được trên máy tính. Bản này nhét gia-lap-robot.js vào để
# dựng lại CAU và trình tự báo trạng thái của Cau.kt.
#
# Nhét NGAY SAU khối dữ liệu, TRƯỚC mã chính: app kiểm coDanDuong() và coMicRobot()
# ngay lúc dựng màn hình, giả lập tới muộn thì nút vẫn ẩn.
#
# ⚠ Bản thử KHÔNG rải sang android assets. APK phải là mã thật, không mang giả lập.
GIALAP = os.path.join(HERE, "gia-lap-robot.js")
RA_THU = os.path.join(DEMO, "thu-nghiem.html")
if os.path.isfile(GIALAP):
    gl = io.open(GIALAP, encoding="utf-8").read()
    html_thu = html.replace(
        "</script>\n<script>\n'use strict';",
        "</script>\n<script>\n" + gl + "\n</script>\n<script>\n'use strict';", 1)
    if html_thu == html:
        raise SystemExit("Không tìm thấy chỗ chèn giả lập — khung-app.html đã đổi cấu trúc?")
    html_thu = html_thu.replace(
        "<title>", "<title>[BẢN THỬ] ", 1)
    with io.open(RA_THU, "w", encoding="utf-8") as f:
        f.write(html_thu)
else:
    RA_THU = None


def rai_bieu_cam(dich):
    """Copy thư mục video biểu cảm sang một chỗ, chỉ ghi đè file đã đổi.

    Không dùng shutil.rmtree rồi copy lại: theo quy tắc 2 của workspace, không xoá
    hàng loạt. Ở đây chỉ ghi đè từng file một."""
    if not os.path.isdir(BIEUCAM):
        return 0
    os.makedirs(dich, exist_ok=True)
    n = 0
    for ten in sorted(os.listdir(BIEUCAM)):
        nguon = os.path.join(BIEUCAM, ten)
        if not os.path.isfile(nguon):
            continue
        shutil.copy2(nguon, os.path.join(dich, ten))
        n += 1
    return n


so_bc = rai_bieu_cam(os.path.join(DEMO, "bieu-cam"))

print("→ %s" % RA)
print("   %.2f MB · %d đích đến · %d file biểu cảm"
      % (os.path.getsize(RA) / 1024 / 1024, data.count('"id":'), so_bc))
print("   Mở bằng cách nháy đúp file, hoặc: start %s" % RA)
if RA_THU:
    print("→ %s" % RA_THU)
    print("   BẢN THỬ — có giả lập robot, bấm được nút dẫn đường. Nháy đúp để mở.")

# ── Rải sang assets của Android để build APK ──
if os.path.isdir(ASSETS):
    shutil.copy2(RA, os.path.join(ASSETS, "index.html"))
    rai_bieu_cam(os.path.join(ASSETS, "bieu-cam"))
    print("→ %s  (index.html + bieu-cam/)" % ASSETS)
else:
    print("! Không thấy %s — bỏ qua bước chép sang Android" % ASSETS)
