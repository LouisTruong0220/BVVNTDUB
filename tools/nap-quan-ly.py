"""
Nạp cấu hình PHẦN MỀM QUẢN LÝ TỪ XA vào robot (app v1.13 trở lên) qua adb.

    python tools/nap-quan-ly.py --cau-hinh <tệp JSON {"robot","khoa"[,"url"]}>
    python tools/nap-quan-ly.py --cau-hinh <tệp> --cai      # cài luôn APK v1.13 trước
    python tools/nap-quan-ly.py --xem                        # xem robot đang báo lên Cloud ra sao (logcat)

Tệp cấu hình do Roboworld cấp riêng (khoá robot chỉ hiện MỘT LẦN lúc tạo, ở phần mềm quản lý:
tab Robot → "Cấp khoá mới"). TUYỆT ĐỐI KHÔNG đưa tệp đó vào kho này — kho để PUBLIC trên GitHub.

Robot cắm cáp USB ở đầu máy. Dùng adb 1.0.41 của Android SDK, không dùng C:\\Windows\\adb.exe.
"""
import argparse, hashlib, io, json, os, subprocess, sys, tempfile, time

GOI = "vn.roboworld.benhvien"
DICH = "/sdcard/Android/data/%s/files/cau-hinh/quan-ly.json" % GOI
URL_MAC_DINH = "https://quan-ly-robot-uong-bi.pages.dev"
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(GOC, "apk", "le-tan-benh-vien-uong-bi-v1.13.apk")

ADB = next((p for p in [
    os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb.exe"),
    r"D:\Android\Sdk\platform-tools\adb.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
] if p and os.path.isfile(p)), "adb")


def adb(*args):
    r = subprocess.run([ADB] + list(args), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip(), r.stderr.decode("utf-8", "replace").strip()


def in_(s):
    sys.stdout.buffer.write((s + "\n").encode("utf-8")); sys.stdout.flush()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cau-hinh")
    p.add_argument("--cai", action="store_true")
    p.add_argument("--xem", action="store_true")
    a = p.parse_args()

    ma, ra, _ = adb("devices")
    may = [d for d in ra.splitlines()[1:] if d.strip().endswith("device")]
    if not may:
        in_("✗ Không thấy robot. Cắm cáp USB ở đầu robot, bật gỡ lỗi USB, rồi chạy lại."); return 1
    in_("✓ Thấy robot: " + may[0].split()[0])

    if a.xem:
        in_("Đọc nhật ký BVQuanLy 20 giây (Ctrl+C để dừng sớm)…")
        adb("logcat", "-c")
        time.sleep(20)
        _, ra, _ = adb("logcat", "-d", "-s", "BVQuanLy")
        in_(ra or "(không có dòng nào — app chưa mở, hoặc chưa phải bản 1.13)")
        return 0

    if not a.cau_hinh or not os.path.isfile(a.cau_hinh):
        in_("✗ Thiếu --cau-hinh <tệp JSON> do Roboworld cấp."); return 1
    ch = json.load(io.open(a.cau_hinh, encoding="utf-8"))
    if not ch.get("robot") or not ch.get("khoa"):
        in_("✗ Tệp cấu hình phải có \"robot\" và \"khoa\"."); return 1
    ch = {"url": ch.get("url") or URL_MAC_DINH, "robot": ch["robot"], "khoa": ch["khoa"]}

    if a.cai:
        if not os.path.isfile(APK):
            in_("✗ Không thấy " + APK); return 1
        in_("Cài " + os.path.basename(APK) + " …")
        ma, ra, lo = adb("install", "-r", APK)
        if "Success" not in ra:
            in_("✗ Cài hỏng: " + (ra or lo)); return 1
        in_("✓ Đã cài")

    tam = os.path.join(tempfile.mkdtemp(), "quan-ly.json")
    io.open(tam, "w", encoding="utf-8").write(json.dumps(ch, ensure_ascii=False))
    adb("shell", "mkdir", "-p", os.path.dirname(DICH).replace("\\", "/"))
    ma, ra, lo = adb("push", tam, DICH)
    h_may = hashlib.sha1(open(tam, "rb").read()).hexdigest()
    _, h_rb, _ = adb("shell", "sha1sum", DICH)
    os.remove(tam)
    if ma != 0 or not h_rb.startswith(h_may):
        in_("✗ Đẩy cấu hình HỎNG: " + (lo or ra)); return 1
    # KHÔNG in khoá — chỉ mã robot + địa chỉ
    in_("✓ Đã nạp cấu hình: robot=%s → %s" % (ch["robot"], ch["url"]))
    adb("shell", "am", "force-stop", GOI)
    in_("\nMở lại app lễ tân BẰNG TAY từ màn hình chính RobotOS (không mở bằng adb —")
    in_("mở bằng adb thì RobotOS không uỷ quyền, robot không đi được).")
    in_("Khoảng 10 giây sau, phần mềm quản lý phải hiện robot \"Đang kết nối\".")
    in_("Kiểm tra: python tools/nap-quan-ly.py --xem")
    return 0


if __name__ == "__main__":
    sys.exit(main())
