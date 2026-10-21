package vn.roboworld.benhvien

import android.content.Context
import android.graphics.Bitmap
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.ainirobot.coreservice.client.Definition
import com.ainirobot.coreservice.client.RobotApi
import com.ainirobot.coreservice.client.StatusListener
import com.ainirobot.coreservice.client.ashmem.ShareMemoryApi
import com.ainirobot.coreservice.client.listener.CommandListener
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.io.File
import java.io.FileInputStream
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.MessageDigest
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * PHẦN MỀM QUẢN LÝ TỪ XA (v1.13, 21/10/2026) — robot báo trạng thái lên Cloud và nhận lệnh về.
 * Máy chủ: cloudflare/quan-ly-robot-uong-bi/ trong workspace Roboworld.
 *
 * Vì sao đi qua Cloud: robot chạy SIM 4G, máy tính quản lý của bệnh viện dùng Wi-Fi — hai mạng
 * khác nhau, không thấy nhau. Cả hai cùng gọi một máy chủ trên internet.
 *
 * Một vòng (2 giây khi đang đi, 3 giây khi đứng):
 *   POST <url>/api/robot/bao  {tt, diem?, ket_qua?}  →  {lenh:[{seq,loai,tham_so}], can_ban_do}
 * Bản đồ chỉ tải lên khi máy chủ đòi (bản đồ đổi md5): PUT <url>/api/robot/ban-do?… thân = PNG.
 *
 * Cấu hình ở THẺ NHỚ: files/cau-hinh/quan-ly.json {"url","robot","khoa"}.
 * ⚠ KHOÁ ROBOT KHÔNG ĐƯỢC NẰM TRONG MÃ: kho GitHub BVVNTDUB để PUBLIC. Không có khoá thì mô-đun
 *   này đứng im, app lễ tân vẫn chạy đủ như bản 1.12.
 * ⚠ Mất mạng KHÔNG được làm app chậm: mọi việc ở luồng riêng, hạn nối 5 giây.
 * ⚠ KHÔNG gửi gì liên quan người bệnh: không câu hỏi, không lời nói, không ảnh. Chỉ trạng thái máy.
 * ⚠ Khuôn dữ liệu phải khớp tools/gia-lap-robot.mjs phía Cloud — đổi một bên phải đổi bên kia.
 */
object QuanLyTuXa {

    private const val TAG = "BVQuanLy"
    private const val URL_MAC_DINH = "https://quan-ly-robot-uong-bi.pages.dev"
    private const val ROBOT_MAC_DINH = "nova-uong-bi"
    private const val ANH_TOI_DA = 1_800_000          // máy chủ D1 nhận tối đa ~1,9 MB

    private lateinit var ctx: Context
    private val main = Handler(Looper.getMainLooper())
    private val tho = Executors.newSingleThreadScheduledExecutor()
    private val ketQua = ConcurrentLinkedQueue<JSONObject>()

    @Volatile var url = ""; private set
    @Volatile var robot = ROBOT_MAC_DINH; private set
    @Volatile private var khoa = ""

    // ── Trạng thái đọc từ RobotOS ──
    @Volatile private var px = Double.NaN
    @Volatile private var py = Double.NaN
    @Volatile private var pt = Double.NaN
    @Volatile private var lucViTri = 0L
    @Volatile private var pinTho = ""
    @Volatile private var daDangKy = false

    // ── Việc đang làm — Cau.kt và chính lớp này cập nhật ──
    @Volatile private var viec: JSONObject = JSONObject().put("loai", "ranh")

    /** Đang chạy lệnh đi từ xa. Cau.kt đọc cờ này để không cho lượt dẫn khách / tự về sảnh chen vào. */
    @Volatile var dangTuXa = false; private set
    @Volatile private var luotTuXa = 0

    /** MainActivity gắn vào để hiện dải chữ "đang chạy theo lệnh từ xa" trên màn robot. null = ẩn. */
    @Volatile var hienBanner: ((String?) -> Unit)? = null

    // ── Bản đồ ──
    private class BanDo(val ten: String, val md5: String, val png: ByteArray, val res: Double,
                        val gocX: Double, val gocY: Double, val rong: Int, val cao: Int)
    @Volatile private var banDo: BanDo? = null
    @Volatile private var tenBanDoCuoi = ""
    @Volatile private var lucGuiDiem = 0L
    @Volatile private var lucDocBanDoHong = 0L

    // ── Chẩn đoán ──
    @Volatile var lucOkCuoi = 0L; private set
    @Volatile var loiCuoi = ""; private set
    @Volatile private var lucBaoLoi = 0L
    @Volatile private var lucLogOk = 0L

    fun batDau(c: Context) {
        ctx = c.applicationContext
        napCauHinh()
        lapLich(8_000)
    }

    private fun tepCauHinh() = File(ctx.getExternalFilesDir(null), "cau-hinh/quan-ly.json")

    fun napCauHinh() {
        url = URL_MAC_DINH; robot = ROBOT_MAC_DINH; khoa = ""
        val f = tepCauHinh()
        if (f.isFile) runCatching {
            val j = JSONObject(f.readText(Charsets.UTF_8))
            url = j.optString("url", URL_MAC_DINH).trim().trimEnd('/')
            robot = j.optString("robot", ROBOT_MAC_DINH).trim().ifEmpty { ROBOT_MAC_DINH }
            khoa = j.optString("khoa", "").trim()
        }.onFailure { Log.w(TAG, "quan-ly.json hỏng: ${it.message}") }
        Log.d(TAG, if (url.isEmpty() || khoa.isEmpty()) "Quản lý từ xa: TẮT (chưa có ${f.absolutePath})"
                   else "Quản lý từ xa: $url · robot=$robot")
    }

    fun datViec(loai: String, diem: String = "", tin: String = "") {
        viec = JSONObject().put("loai", loai).put("diem", diem).put("tin", tin).put("tu", System.currentTimeMillis())
    }

    // ───────────────────────── Vòng chính ─────────────────────────

    private fun dangDi() = viec.optString("loai") != "ranh"

    private fun lapLich(ms: Long) {
        tho.schedule({
            try { motVong() } catch (e: Throwable) {
                loiCuoi = e.message ?: e.javaClass.simpleName
                val bay = System.currentTimeMillis()
                if (bay - lucBaoLoi > 60_000) { lucBaoLoi = bay; Log.w(TAG, "Vòng đồng bộ lỗi: $loiCuoi") }
            } finally {
                lapLich(if (dangDi()) 2_000 else 3_000)
            }
        }, ms, TimeUnit.MILLISECONDS)
    }

    private fun motVong() {
        if (url.isEmpty() || khoa.isEmpty()) return
        if (RobotHelper.daKetNoi && !daDangKy) dangKyNghe()
        if (RobotHelper.daKetNoi && System.currentTimeMillis() - lucViTri > 10_000) hoiViTri()

        val api = RobotApi.getInstance()
        val ketNoi = RobotHelper.daKetNoi
        val tenBanDo = if (ketNoi) runCatching { api.mapName ?: "" }.getOrDefault("") else ""
        val dinhVi = if (ketNoi) runCatching { api.isRobotEstimate }.getOrDefault(false) else false

        // Bản đồ đổi (hoặc lần đầu) → đọc PGM, tính md5. Đọc hỏng thì 5 phút sau mới thử lại.
        if (tenBanDo.isNotEmpty() && (banDo?.ten != tenBanDo) &&
            System.currentTimeMillis() - lucDocBanDoHong > 5 * 60_000) {
            banDo = runCatching { docBanDo(tenBanDo) }.onFailure {
                lucDocBanDoHong = System.currentTimeMillis()
                Log.w(TAG, "Không đọc được bản đồ '$tenBanDo': ${it.message}")
            }.getOrNull()
        }

        val tt = JSONObject()
            .put("app", phienBanApp()).put("rom", Build.DISPLAY).put("mang", loaiMang())
            .put("ket_noi", ketNoi).put("bi_treo", RobotHelper.biTreo)
            .put("dinh_vi", dinhVi)
            .put("ban_do", JSONObject().put("ten", tenBanDo).put("md5", banDo?.takeIf { it.ten == tenBanDo }?.md5 ?: ""))
            .put("viec", viec)
            .put("man", tenMan(hoiManDang()))
        if (ketNoi) runCatching { api.batteryLevel }.getOrNull()?.takeIf { it in 0..100 }?.let { tt.put("pin", it) }
        dangSac()?.let { tt.put("sac", it) }
        if (pinTho.isNotEmpty()) tt.put("pin_tho", pinTho.take(300))
        if (!px.isNaN() && dinhVi) tt.put("vi_tri", JSONObject().put("x", r3(px)).put("y", r3(py)).put("t", r3(pt))
            .put("luc", lucViTri))

        val than = JSONObject().put("tt", tt)
        // Danh sách điểm: mỗi phút một lần, hoặc ngay khi đổi bản đồ
        if (ketNoi && (tenBanDo != tenBanDoCuoi || System.currentTimeMillis() - lucGuiDiem > 60_000)) {
            layDiem()?.let { than.put("diem", it); lucGuiDiem = System.currentTimeMillis(); tenBanDoCuoi = tenBanDo }
        }
        val gui = ArrayList<JSONObject>()
        while (true) gui += (ketQua.poll() ?: break)
        if (gui.isNotEmpty()) than.put("ket_qua", JSONArray(gui))

        val tra = try { goi("POST", "$url/api/robot/bao", than.toString().toByteArray(Charsets.UTF_8), "application/json; charset=utf-8") }
                  catch (e: Exception) { gui.forEach { ketQua.add(it) }; throw e }
        lucOkCuoi = System.currentTimeMillis(); loiCuoi = ""
        if (lucOkCuoi - lucLogOk > 60_000) {
            lucLogOk = lucOkCuoi
            Log.d(TAG, "Báo Cloud OK · bản đồ='$tenBanDo' định vị=$dinhVi vị trí=${if (px.isNaN()) "chưa có" else "%.2f,%.2f".format(px, py)}")
        }

        val ds = tra.optJSONArray("lenh")
        if (ds != null) for (i in 0 until ds.length()) {
            val l = ds.optJSONObject(i) ?: continue
            val seq = l.optLong("seq")
            val loai = l.optString("loai")
            val ts = l.optJSONObject("tham_so") ?: JSONObject()
            Log.d(TAG, "Lệnh từ xa #$seq $loai $ts")
            main.post { runCatching { thucHien(seq, loai, ts) }.onFailure { bao(seq, "loi", "Lỗi trong app: ${it.message}") } }
        }
        if (tra.optBoolean("can_ban_do")) banDo?.takeIf { it.ten == tenBanDo }?.let { taiBanDoLen(it) }
    }

    private fun r3(d: Double) = Math.round(d * 1000) / 1000.0

    private fun bao(seq: Long, trangThai: String, chu: String) {
        ketQua.add(JSONObject().put("seq", seq).put("trang_thai", trangThai).put("ket_qua", chu))
    }

    // ───────────────────────── Thi hành lệnh (luồng chính) ─────────────────────────

    private fun thucHien(seq: Long, loai: String, ts: JSONObject) {
        when (loai) {
            "di-toi" -> diTuXa(seq, ts.optString("diem").trim(), "tu-xa")
            "ve-cho" -> diTuXa(seq, Cau.diemVeCho(), "ve-cho")
            "ve-sac" -> {
                val luot = batDauTuXa("ve-sac", "Trạm sạc")
                bao(seq, "dang-lam", "Đang về trạm sạc")
                RobotHelper.veSac { ok, chu ->
                    if (luot != luotTuXa) return@veSac
                    xongTuXa(); bao(seq, if (ok) "xong" else "loi", chu)
                }
            }
            "dung" -> {
                luotTuXa++                                // vô hiệu callback của lệnh đi trước đó
                Cau.nhuongChoTuXa()
                RobotHelper.dungDieuHuong(); RobotHelper.dungVeSac(); RobotHelper.dungDoc()
                xongTuXa()
                bao(seq, "xong", "Robot đã dừng")
            }
            "noi" -> {
                val cau = ts.optString("cau").trim()
                if (cau.isEmpty()) { bao(seq, "loi", "Câu rỗng"); return }
                bao(seq, "dang-lam", "Đang nói")
                RobotHelper.doc(cau) { bao(seq, "xong", "Đã nói xong") }
            }
            "tai-ban-do" -> {
                tho.execute {
                    val ten = runCatching { RobotApi.getInstance().mapName ?: "" }.getOrDefault("")
                    runCatching { docBanDo(ten).also { banDo = it; taiBanDoLen(it) } }
                        .onSuccess { bao(seq, "xong", "Đã gửi lại bản đồ ${it.rong}×${it.cao}") }
                        .onFailure { bao(seq, "loi", "Không đọc được bản đồ: ${it.message}") }
                }
            }
            else -> bao(seq, "loi", "Robot không hiểu lệnh '$loai' — cần cập nhật phần mềm lễ tân")
        }
    }

    /** Dừng mọi lượt đang chạy (dẫn khách / tự về sảnh / lệnh trước), bật cờ từ xa. Trả số lượt. */
    private fun batDauTuXa(loai: String, diem: String): Int {
        Cau.nhuongChoTuXa()
        RobotHelper.dungDieuHuong()
        val luot = ++luotTuXa
        dangTuXa = true
        datViec(loai, diem)
        hienBanner?.invoke(
            if (loai == "ve-sac") "Robot đang về trạm sạc theo lệnh của bộ phận quản lý"
            else "Robot đang di chuyển theo lệnh của bộ phận quản lý")
        return luot
    }

    private fun xongTuXa() {
        dangTuXa = false
        datViec("ranh")
        hienBanner?.invoke(null)
    }

    private fun diTuXa(seq: Long, diem: String, loai: String) {
        if (diem.isEmpty()) { bao(seq, "loi", "Chưa có điểm đến"); return }
        RobotHelper.lyDoChuaSanSang()?.let { bao(seq, "loi", it); return }
        val luot = batDauTuXa(loai, diem)
        bao(seq, "dang-lam", "Đang đi tới $diem")
        // Chờ lệnh dừng của lượt cũ ngấm rồi mới phát lệnh đi — gửi ngay là RobotOS hay trả "đang bận".
        main.postDelayed({
            if (luot != luotTuXa) return@postDelayed
            RobotHelper.dieuHuongToi(diem,
                khiToiNoi = { if (luot == luotTuXa) { xongTuXa(); bao(seq, "xong", "Đã tới $diem") } },
                khiLoi = { loi -> if (luot == luotTuXa) { RobotHelper.dungDieuHuong(); xongTuXa(); bao(seq, "loi", loi) } },
                khiCapNhat = { tin -> if (luot == luotTuXa) datViec(loai, diem, tin) })
        }, 800)
    }

    // ───────────────────────── Đọc trạng thái RobotOS ─────────────────────────

    private fun dangKyNghe() {
        daDangKy = true
        val api = RobotApi.getInstance()
        runCatching {
            api.registerStatusListener(Definition.STATUS_POSE, object : StatusListener() {
                override fun onStatusUpdate(type: String?, value: String?) { docViTri(value) }
            })
            api.registerStatusListener(Definition.STATUS_BATTERY, object : StatusListener() {
                override fun onStatusUpdate(type: String?, value: String?) { pinTho = value.orEmpty() }
            })
        }.onFailure { daDangKy = false; Log.w(TAG, "Không đăng ký nghe vị trí/pin: ${it.message}") }
    }

    /** STATUS_POSE và getPosition cùng trả px/py/theta (mét, radian). */
    private fun docViTri(json: String?) {
        if (json.isNullOrBlank()) return
        runCatching {
            val j = JSONObject(json)
            val x = j.optDouble(Definition.JSON_NAVI_POSITION_X, Double.NaN)
            val y = j.optDouble(Definition.JSON_NAVI_POSITION_Y, Double.NaN)
            if (x.isNaN() || y.isNaN()) return
            px = x; py = y; pt = j.optDouble(Definition.JSON_NAVI_POSITION_THETA, 0.0)
            lucViTri = System.currentTimeMillis()
        }
    }

    /** Đường lui: vài ROM chỉ bắn STATUS_POSE khi robot nhúc nhích — đứng yên lâu là mất vị trí. */
    private fun hoiViTri() {
        runCatching {
            RobotApi.getInstance().getPosition(0, object : CommandListener() {
                override fun onResult(result: Int, message: String?) { docViTri(message) }
            })
        }
    }

    /** Pin đang sạc? Khuôn JSON của STATUS_BATTERY không có trong tài liệu hãng — dò khoá có chữ "charg". */
    private fun dangSac(): Boolean? {
        if (pinTho.isEmpty()) return null
        return runCatching {
            val j = JSONObject(pinTho)
            for (k in j.keys()) if (k.lowercase().contains("charg")) {
                when (val v = j.get(k)) {
                    is Boolean -> return v
                    is Number -> return v.toInt() != 0
                }
            }
            null
        }.getOrNull()
    }

    private fun layDiem(): JSONArray? {
        val latch = CountDownLatch(1)
        var tho_: String? = null
        runCatching {
            RobotApi.getInstance().getPlaceList(0, object : CommandListener() {
                override fun onResult(result: Int, message: String?) { tho_ = message; latch.countDown() }
            })
        }.onFailure { return null }
        if (!latch.await(4, TimeUnit.SECONDS)) return null
        return runCatching {
            val a = JSONArray(tho_)
            val ra = JSONArray()
            for (i in 0 until a.length()) {
                val o = a.optJSONObject(i) ?: continue
                val ten = o.optString("name")
                if (ten.isBlank()) continue
                ra.put(JSONObject().put("ten", ten).put("x", r3(o.optDouble("x"))).put("y", r3(o.optDouble("y")))
                    .put("t", r3(o.optDouble("theta", 0.0))))
            }
            ra
        }.getOrNull()
    }

    private fun hoiManDang(): String = Cau.manDang(1_000)

    private fun tenMan(id: String) = when (id) {
        "mh-cho" -> "Màn chờ"
        "mh-chinh" -> "Danh sách khoa phòng"
        "mh-ct" -> "Chi tiết khoa phòng"
        "mh-dan" -> "Đang dẫn đường"
        "mh-chi" -> "Chỉ đường"
        "mh-toa" -> "Chọn toà nhà"
        "mh-cc" -> "CẤP CỨU"
        "mh-chat" -> "Trò chuyện"
        "" -> ""
        else -> id
    }

    private fun phienBanApp(): String = runCatching {
        ctx.packageManager.getPackageInfo(ctx.packageName, 0).versionName ?: ""
    }.getOrDefault("")

    private fun loaiMang(): String = runCatching {
        val cm = ctx.getSystemService(Context.CONNECTIVITY_SERVICE) as? android.net.ConnectivityManager ?: return "?"
        val mang = cm.activeNetwork ?: return "mat"
        val kn = cm.getNetworkCapabilities(mang) ?: return "?"
        when {
            kn.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) -> "wifi"
            kn.hasTransport(android.net.NetworkCapabilities.TRANSPORT_CELLULAR) -> "4g"
            else -> "khac"
        }
    }.getOrDefault("?")

    // ───────────────────────── Bản đồ ─────────────────────────

    /**
     * Đọc map.pgm của OrionStar: PGM P5 chuẩn + 16 BYTE ĐUÔI sau dữ liệu điểm ảnh —
     *   [0..8) độ phân giải (double, little-endian, mét/điểm ảnh)
     *   [8..12) gốc x · [12..16) gốc y (float, little-endian, mét) = góc DƯỚI-TRÁI ảnh
     * Mã điểm ảnh: 0x96 chưa quét · 0xFF đi được · 0x05 vật cản · 0x00 vạch cấm.
     * Nguồn: MapppUtils.loadPFD2RoverMap trong github.com/OrionStarGIT/RobotSample.
     *
     * Đường chính: ShareMemoryApi.getMapPgmPFD (tài liệu hãng 09-ban-do-va-vi-tri.md).
     * Đường lui: tệp /sdcard/robot/map/<tên>/map.pgm — cổng OrionStar ghi mapPath đúng thư mục này.
     * ⚠ CHƯA ĐO trên máy thật — cả hai đường đều theo tài liệu/mã mẫu hãng.
     */
    private fun docBanDo(ten: String): BanDo {
        require(ten.isNotEmpty()) { "chưa có tên bản đồ" }
        val loi = StringBuilder()
        runCatching {
            val pfd = ShareMemoryApi.getInstance().getMapPgmPFD(ten) ?: error("getMapPgmPFD trả null")
            try { FileInputStream(pfd.fileDescriptor).use { return giaiMa(ten, it) } }
            finally { runCatching { ShareMemoryApi.getInstance().releaseGetMapPgmPFD() } }
        }.onFailure { loi.append("bộ nhớ chia sẻ: ${it.message}; ") }
        for (duong in listOf("/sdcard/robot/map/$ten/map.pgm", "/storage/emulated/0/robot/map/$ten/map.pgm")) {
            val f = File(duong)
            if (!f.isFile) continue
            runCatching { FileInputStream(f).use { return giaiMa(ten, it) } }
                .onFailure { loi.append("$duong: ${it.message}; ") }
        }
        error(loi.toString().ifEmpty { "không thấy map.pgm" })
    }

    private fun giaiMa(ten: String, vao: InputStream): BanDo {
        val d = DataInputStream(vao.buffered())
        fun dong(): String {
            while (true) {
                val sb = StringBuilder()
                while (true) { val b = d.read(); if (b < 0 || b == '\n'.code) break; sb.append(b.toChar()) }
                val s = sb.toString().trim()
                if (s.isNotEmpty() && !s.startsWith("#")) return s
            }
        }
        require(dong() == "P5") { "không phải PGM P5" }
        val kt = dong().split(Regex("\\s+"))
        val rong = kt[0].toInt(); val cao = kt[1].toInt()
        require(rong in 1..8000 && cao in 1..8000) { "kích thước lạ $rong×$cao" }
        dong()                                                        // 255
        val px = ByteArray(rong * cao); d.readFully(px)
        val duoi = ByteArray(16); d.readFully(duoi)
        val bb = java.nio.ByteBuffer.wrap(duoi).order(java.nio.ByteOrder.LITTLE_ENDIAN)
        val res = bb.getDouble(0); val gx = bb.getFloat(8).toDouble(); val gy = bb.getFloat(12).toDouble()
        require(res > 0 && res < 1) { "độ phân giải lạ $res" }

        val md = MessageDigest.getInstance("MD5"); md.update(px); md.update(duoi)
        val md5 = md.digest().joinToString("") { "%02x".format(it) }

        val mau = IntArray(rong * cao)
        for (i in mau.indices) {
            val v = px[i].toInt() and 0xFF
            mau[i] = when (v) {
                0xFF -> 0xFFFFFFFF.toInt()
                0x05 -> 0xFF3A3432.toInt()
                0x00 -> 0xFFE83636.toInt()
                0x96 -> 0x00000000
                else -> (0xFF shl 24) or (v shl 16) or (v shl 8) or v
            }
        }
        var bm = Bitmap.createBitmap(mau, rong, cao, Bitmap.Config.ARGB_8888)
        var heSo = 1
        var png = nenPng(bm)
        while (png.size > ANH_TOI_DA && heSo < 8) {       // bản đồ quá to: thu nhỏ, giữ nguyên gốc toạ độ
            heSo *= 2
            val nho = Bitmap.createScaledBitmap(bm, rong / heSo, cao / heSo, false)
            png = nenPng(nho); if (nho != bm) nho.recycle()
        }
        bm.recycle()
        Log.d(TAG, "Bản đồ '$ten' ${rong}×$cao res=$res gốc=($gx,$gy) → PNG ${png.size / 1024} KB (÷$heSo)")
        return BanDo(ten, md5, png, res * heSo, gx, gy, rong / heSo, cao / heSo)
    }

    private fun nenPng(bm: Bitmap): ByteArray = ByteArrayOutputStream().also { bm.compress(Bitmap.CompressFormat.PNG, 100, it) }.toByteArray()

    private fun taiBanDoLen(b: BanDo) {
        val q = listOf("ten" to b.ten, "md5" to b.md5, "res" to b.res.toString(), "goc_x" to b.gocX.toString(),
            "goc_y" to b.gocY.toString(), "rong" to b.rong.toString(), "cao" to b.cao.toString())
            .joinToString("&") { "${it.first}=${URLEncoder.encode(it.second, "UTF-8")}" }
        runCatching { goi("PUT", "$url/api/robot/ban-do?$q", b.png, "image/png") }
            .onSuccess { Log.d(TAG, "Đã tải bản đồ lên Cloud (${b.png.size / 1024} KB)") }
            .onFailure { Log.w(TAG, "Tải bản đồ lên lỗi: ${it.message}") }
    }

    // ───────────────────────── Mạng ─────────────────────────

    private fun goi(phuongThuc: String, diaChi: String, than: ByteArray, loai: String): JSONObject {
        val c = URL(diaChi).openConnection() as HttpURLConnection
        try {
            c.requestMethod = phuongThuc
            c.connectTimeout = 5_000
            c.readTimeout = if (phuongThuc == "PUT") 30_000 else 8_000
            c.doOutput = true
            c.setRequestProperty("Content-Type", loai)
            // ⚠ PHẢI đặt User-Agent tường minh — "Dalvik/2.1.0" mặc định từng bị chặn 403 (bài học Groq 27/08)
            c.setRequestProperty("User-Agent", "Roboworld-LeTanUongBi/${phienBanApp()}")
            c.setRequestProperty("x-robot-id", robot)
            c.setRequestProperty("x-robot-khoa", khoa)
            c.outputStream.use { it.write(than) }
            val ma = c.responseCode
            val chu = (if (ma < 400) c.inputStream else c.errorStream)?.bufferedReader()?.use { it.readText() } ?: ""
            if (ma != 200) throw IllegalStateException("HTTP $ma ${chu.take(120)}")
            return JSONObject(chu)
        } finally { c.disconnect() }
    }
}
