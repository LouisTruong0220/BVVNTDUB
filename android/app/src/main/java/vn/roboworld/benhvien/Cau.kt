package vn.roboworld.benhvien

import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONObject
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * Cây cầu hai chiều giữa giao diện web (index.html) và phần cứng robot.
 *
 *   Web  →  Android :  đối tượng `CAU` trong JavaScript, xem các hàm gắn @JavascriptInterface
 *   Android  →  Web :  gọi hàm JS qua evaluateJavascript, xem guiGoiYSangManHinh / baoDocXong
 *
 * Vì sao làm giao diện bằng web thay vì layout Android:
 * bộ dữ liệu khoa phòng và toàn bộ cách trình bày đã chạy tốt trên máy tính, dùng lại
 * thì sửa nội dung sau này chỉ cần sửa HTML, không phải build lại app.
 *
 * ⚠ Mọi hàm @JavascriptInterface đều chạy trên LUỒNG RIÊNG của WebView, không phải luồng
 *   giao diện. Đụng tới WebView thì phải post về luồng chính, nếu không app văng.
 */
object Cau {

    private const val TAG = "BVCau"

    @Volatile
    private var web: WebView? = null

    fun gan(w: WebView) { web = w }
    fun go() { web = null }

    // ───────────────────── Android → Web ─────────────────────

    /**
     * Đẩy câu người bệnh vừa nói sang lớp web để nó tự dò trong kho khoa phòng
     * rồi bật pop-up gợi ý.
     *
     * @return số gợi ý tìm được — dùng để báo lại cho AI biết Action đã có tác dụng chưa.
     *         Trả về ngay 0 nếu chưa gắn WebView; con số thật lấy được ở lần đo sau.
     */
    fun guiGoiYSangManHinh(cauNoi: String?): Int {
        val w = web ?: return 0
        val t = cauNoi.orEmpty().trim()
        if (t.length < 2) return 0
        val js = "window.goiYTuRobot(${JSONObject.quote(t)})"
        w.post {
            w.evaluateJavascript(js) { kq -> Log.d(TAG, "goiYTuRobot('$t') -> $kq") }
        }
        return 1
    }

    /**
     * Báo cho lớp web biết AI của hãng đã trả lời được thật.
     *
     * Lớp web giấu nút micro cho tới lúc nhận được tin này. Nhờ vậy hôm nào hãng sửa
     * xong Agent SDK, nút micro tự hiện ra — không phải build lại APK.
     */
    fun baoAISanSang(sanSang: Boolean) {
        val w = web ?: return
        w.post { w.evaluateJavascript("window.baoAISanSang && window.baoAISanSang($sanSang)", null) }
    }

    /**
     * Kotlin vừa TỰ tắt mic — báo lên để nút micro thôi nhấp nháy.
     *
     * Có hai đường tự tắt, cả hai đều nằm bên Kotlin vì chỉ Kotlin thấy cờ `final` của
     * bộ nhận dạng: người bệnh dứt câu (1 giây sau), và bấm mic rồi bỏ đi (15 giây).
     * Không có hàm này thì mic đã tắt mà nút vẫn sáng "Tôi đang nghe…" — người bệnh cứ
     * nói tiếp vào một cái micro đã đóng.
     */
    fun baoMicTuTat() {
        val w = web ?: return
        w.post { w.evaluateJavascript("window.baoMicTuTat && window.baoMicTuTat()", null) }
    }

    /** Báo cho lớp web biết robot đã đọc xong, để nút đổi lại thành "Nghe đọc lại". */
    private fun baoDocXong() {
        val w = web ?: return
        w.post { w.evaluateJavascript("window.robotDocXong && window.robotDocXong()", null) }
    }

    /**
     * Đẩy từng mẩu lời nói lên màn hình trò chuyện.
     *
     * @param ai   "nguoi" (robot nghe được người dân nói) hoặc "robot" (robot đang đọc)
     * @param chu  nội dung
     * @param xong true = câu đã chốt · false = chữ còn đang chảy, sẽ được thay tiếp
     *
     * Gọi được từ luồng phụ — onTranscribe của Agent SDK chạy ở luồng phụ.
     */
    fun guiLoiNoi(ai: String, chu: String, xong: Boolean) {
        val w = web ?: return
        val js = "window.nhanLoiNoi && window.nhanLoiNoi(${JSONObject.quote(ai)}," +
                 "${JSONObject.quote(chu)},$xong)"
        w.post { w.evaluateJavascript(js, null) }
    }

    /**
     * Tra một khoa / phòng trong kho 24 mã phòng rồi TRẢ VỀ NỘI DUNG cho mô hình của hãng.
     *
     * Bộ tìm kiếm nằm ở lớp web (hiểu tiếng người bệnh: "đau bụng", "đi đẻ", "lấy thuốc"),
     * nên phải chạy JS rồi chờ kết quả. Chờ tối đa 1,2 giây — tài liệu hãng dặn không được
     * làm việc lâu trong callback của Action, quá hạn thì trả chuỗi rỗng còn hơn treo cả
     * cuộc hội thoại.
     *
     * ⚠ Không gọi hàm này từ luồng chính: nó chặn luồng gọi để chờ, mà công việc nó chờ lại
     *   chạy trên luồng chính — gọi từ luồng chính là tự khoá chính mình.
     */
    fun traKhoaChoAI(tuKhoa: String?): String {
        val w = web ?: return ""
        val t = tuKhoa.orEmpty().trim()
        if (t.length < 2) return ""
        if (Looper.myLooper() == Looper.getMainLooper()) {
            Log.w(TAG, "traKhoaChoAI gọi từ luồng chính — bỏ qua để khỏi treo")
            return ""
        }

        var kq = ""
        val cho = CountDownLatch(1)
        val js = "window.tomTatChoAI ? window.tomTatChoAI(${JSONObject.quote(t)}) : ''"
        Handler(Looper.getMainLooper()).post {
            w.evaluateJavascript(js) { raw ->
                // evaluateJavascript trả về chuỗi ĐÃ mã hoá JSON: "..." kèm dấu nháy
                kq = runCatching {
                    if (raw.isNullOrBlank() || raw == "null") "" else JSONObject("{\"v\":$raw}").getString("v")
                }.getOrDefault("")
                cho.countDown()
            }
        }
        val kip = cho.await(1200, TimeUnit.MILLISECONDS)
        if (!kip) Log.w(TAG, "traKhoaChoAI quá hạn 1,2 s")
        Log.d(TAG, "traKhoaChoAI('$t') -> ${kq.length} ký tự")
        return kq
    }

    // ───────────────────── Web → Android ─────────────────────

    /** Đọc thành tiếng bằng giọng của robot. Web gọi: CAU.doc("...") */
    @JavascriptInterface
    fun doc(vanBan: String?) {
        val t = vanBan.orEmpty()
        if (t.isBlank()) return
        RobotHelper.doc(t) { baoDocXong() }
    }

    /** Dừng đọc giữa chừng. Web gọi: CAU.dungDoc() */
    @JavascriptInterface
    fun dungDoc() = RobotHelper.dungDoc()

    // ───────────────── Micro & bộ não hội thoại của hãng ─────────────────
    //
    // Cả cụm này là cái mà app THIẾU suốt từ đầu. Trước đây phần nghe đi qua
    // webkitSpeechRecognition của trình duyệt — trên WebView robot nó ném
    // error=not-allowed ngay lập tức, nghĩa là nút micro chưa từng hoạt động một lần nào.
    // Xem chú thích dài ở MainApplication.setOnTranscribeListener.

    /** Mở mic robot — người dân nói là AI của hãng nghe và tự trả lời. */
    @JavascriptInterface
    fun batMic() = MainApplication.batMicro()

    /** Tắt mic — dùng khi rời màn trò chuyện, khi dẫn đường, khi về màn chờ. */
    @JavascriptInterface
    fun tatMic() = MainApplication.tatMicro()

    @JavascriptInterface
    fun micDangMo(): Boolean = MainApplication.micDangMo()

    /**
     * Gõ chữ — đi CÙNG MỘT ĐƯỜNG với nói miệng.
     *
     * ⚠ Cả hai đều vào `TraLoi.hoi`, để mọi lớp chặn (cấp cứu · hỏi bệnh · chưa có dữ
     *   liệu · kiểm id mô hình trả về) chỉ viết một lần. App tra cứu thủ tục đời trước
     *   cho gõ chữ đi `AgentCore.query()` còn nói miệng đi đường khác, nên mỗi lần thêm
     *   một lớp chặn là phải nhớ sửa hai chỗ — kiểu gì cũng có ngày quên một chỗ.
     *
     * ⚠ KHÔNG gọi `AgentCore.query()` nữa: app đã đặt `isDisablePlan = true` nên bộ
     *   hoạch định tắt, gọi query() sẽ không có gì xảy ra.
     */
    @JavascriptInterface
    fun hoiRobot(cau: String?) {
        /* Gõ chữ và nói miệng đi CÙNG một đường, nên cũng phải mở lượt hỏi ở đây —
           thiếu dòng này thì câu gõ tay bị chính chốt choPhepNoi() bịt lại. */
        MainApplication.batDauLuotMoi()
        TraLoi.hoi(cau.orEmpty())
    }

    /**
     * NGƯỜI BỆNH VỪA THAO TÁC — lớp web gọi ở mọi cửa: Quay lại · Thoát · Xoá đoạn
     * chat · bấm micro nói tiếp · rời màn Trò chuyện.
     *
     * Hai việc cùng lúc: cắt tiếng đang phát, và BỎ câu trả lời còn đang trên đường
     * về. Chỉ cắt tiếng là chưa đủ — câu về muộn chưa phát thì không có gì để cắt,
     * mấy giây sau nó vẫn cất lên giữa lúc người bệnh đang đọc thứ khác.
     */
    @JavascriptInterface
    fun nguoiDungThaoTac() = MainApplication.nguoiDungThaoTac()

    /** Bật màn cấp cứu đỏ — tầng Kotlin gọi khi chặn được từ khoá cấp cứu. */
    fun moManCapCuu() {
        val w = web ?: return
        w.post { w.evaluateJavascript("window.moManCapCuuTuAI && window.moManCapCuuTuAI()", null) }
    }

    /** Bắt đầu lượt khách mới — xoá ngữ cảnh để chuyện của người trước không dính sang. */
    @JavascriptInterface
    fun xoaNguCanh() { MainApplication.xoaNguCanh() }

    /** Kể cho mô hình biết màn hình đang hiện gì — xem MainApplication.moTaManHinh. */
    @JavascriptInterface
    fun moTaManHinh(mo: String?) {
        val t = mo.orEmpty()
        if (t.isNotBlank()) MainApplication.moTaManHinh(t)
    }

    /** Tự kiểm lúc lắp đặt: appId đang chạy, có Agent hay không, mic đang mở hay tắt. */
    @JavascriptInterface
    fun thongTinAI(): String = MainApplication.thongTinAI()

    /**
     * Chẩn đoán mô hình — xem MainApplication.thuLLM.
     * Gõ trong DevTools:  CAU.thuLLM('Xin chào', true)
     */
    @JavascriptInterface
    fun thuLLM(cauHoi: String?, dungKhoTriThuc: Boolean) {
        MainApplication.thuLLM(cauHoi.orEmpty().ifBlank { "Xin chào, bạn là ai?" }, dungKhoTriThuc)
    }

    /**
     * Robot dẫn người bệnh tới một điểm trên bản đồ.
     *
     * ⚠ Tên điểm do LỚP WEB truyền xuống, lấy nguyên từ app-data.json (trường
     *   `diem_ban_do`), KHÔNG ghép chuỗi ở đây. App tra cứu thủ tục đời trước ghi cứng
     *   "Quay $soQuay" trong mã Kotlin, nên mỗi lần bệnh viện đổi tên điểm là phải
     *   build lại APK. Ở đây đổi tên điểm chỉ cần sửa JSON rồi chạy dung-app.py.
     *
     * Tên phải trùng TỪNG KÝ TỰ với điểm kỹ thuật đặt lúc quét bản đồ — không dấu
     * tiếng Việt, đúng hoa/thường, đúng một dấu cách. Sai một ký tự là
     * ERROR_DESTINATION_NOT_EXIST. Xem huong-dan-dat-ten-diem-ban-do.md.
     *
     * Mọi diễn biến đều báo ngược lên màn hình bằng baoDanDuong() — chỉ đọc thành
     * tiếng thì người đứng xa không nghe rõ, tưởng bấm nút không ăn.
     *
     * ⚠ SUỐT QUÃNG ĐƯỜNG ĐI ROBOT IM LẶNG. Chỉ nói đúng một câu "Xin mời đi theo tôi"
     *   lúc bắt đầu, còn lại chỉ chiếu biểu cảm. Lý do: sảnh bệnh viện đã ồn sẵn, mà
     *   người đi theo robot còn phải nghe loa gọi tên mình ở quầy — robot lải nhải dọc
     *   đường là át mất. Diễn biến dọc đường (vật cản, sắp tới nơi) chỉ hiện thành chữ.
     *   Ngoại lệ duy nhất là LỖI: không đi được thì phải nói ra, không thì người bệnh
     *   cứ đứng chờ một con robot đã bỏ cuộc.
     */
    @JavascriptInterface
    fun danDuongToiDiem(tenDiem: String?) {
        val diem = tenDiem.orEmpty().trim()
        Log.d(TAG, "Xin dẫn đường tới '$diem'")
        if (diem.isEmpty()) {
            baoDanDuong("loi", "Chưa cấu hình điểm đến cho chỗ này.")
            return
        }

        val vuong = RobotHelper.lyDoChuaSanSang()
        if (vuong != null) {
            baoDanDuong("loi", vuong)
            RobotHelper.doc(vuong) {}
            return
        }

        dangVeCho = false
        baoDanDuong("bat-dau", "")
        RobotHelper.doc("Xin mời đi theo tôi.") {}

        RobotHelper.dieuHuongToi(
            diem,
            // Tới nơi: KHÔNG nói gì ở đây. Lớp web tự bật màn chỉ đường và cho robot
            // đọc câu hướng dẫn — nói thêm ở đây là chồng tiếng.
            khiToiNoi = { baoDanDuong("toi-noi", "") },
            khiLoi = { loi ->
                // Dừng hẳn lệnh đi, không để robot kẹt ở trạng thái "đang điều hướng"
                RobotHelper.dungDieuHuong()
                baoDanDuong("loi", loi)
                RobotHelper.doc(loi) {}
            },
            // Chỉ đẩy chữ lên màn hình, tuyệt đối không gọi RobotHelper.doc ở đây
            khiCapNhat = { tin -> baoDanDuong("dang-di", tin) }
        )
    }

    /** Dừng dẫn đường giữa chừng — người bệnh đổi ý hoặc bấm quay lại. */
    @JavascriptInterface
    fun dungDanDuong() {
        dangVeCho = false
        RobotHelper.dungDieuHuong()
        baoDanDuong("da-dung", "Tôi dừng lại rồi ạ.")
    }

    /* Đang trên đường tự về sảnh. Cờ này để chuyến về KHÔNG báo gì lên giao diện —
       lớp web lúc đó đã quay lại màn chờ, một cái baoDanDuong lạc đến sẽ kéo màn hình
       ra khỏi màn chờ ngay trước mặt người tiếp theo. */
    @Volatile private var dangVeCho = false

    /**
     * Robot tự đi về chỗ đứng đợi ở sảnh.
     *
     * Vì sao phải có hàm này: app tra cứu thủ tục đời trước dẫn tới quầy rồi robot đứng
     * luôn tại đó — chấp nhận được vì quầy nằm ngay trong phòng. Ở bệnh viện robot ra
     * tận trước cửa toà DI, đứng lại ngoài đó là cả buổi không ai ở sảnh thấy robot đâu.
     *
     * Chuyến về này ROBOT IM LẶNG HOÀN TOÀN, kể cả lúc gặp lỗi: nó đang đi một mình,
     * không có ai để nói cùng, mà bệnh viện thì không cần thêm tiếng ồn.
     */
    @JavascriptInterface
    fun veCho() {
        val diem = tenDiemVeCho
        Log.d(TAG, "Robot tự về '$diem'")
        if (diem.isEmpty() || RobotHelper.lyDoChuaSanSang() != null) return
        dangVeCho = true
        RobotHelper.dieuHuongToi(
            diem,
            khiToiNoi = { dangVeCho = false; Log.d(TAG, "Đã về tới $diem") },
            khiLoi = { loi -> dangVeCho = false; Log.w(TAG, "Về chỗ không thành: $loi") },
            khiCapNhat = { }
        )
    }

    /** Lớp web đặt tên điểm về chỗ lúc khởi động, lấy từ app-data.json → `diem_ve_cho`. */
    @Volatile private var tenDiemVeCho = "Sanh cho"

    @JavascriptInterface
    fun datDiemVeCho(ten: String?) {
        val t = ten.orEmpty().trim()
        if (t.isNotEmpty()) { tenDiemVeCho = t; Log.d(TAG, "Điểm về chỗ = '$t'") }
    }

    /**
     * Vì sao chưa dẫn đường được — trả chuỗi rỗng nghĩa là sẵn sàng.
     * Web dùng để hiện lời nhắc ngay dưới nút, thay vì giấu nút đi cho người dân khỏi thấy.
     */
    @JavascriptInterface
    fun lyDoChuaDanDuongDuoc(): String = RobotHelper.lyDoChuaSanSang() ?: ""

    /** Robot có đang sẵn sàng nhận lệnh không. */
    @JavascriptInterface
    fun robotSanSang(): Boolean = RobotHelper.lyDoChuaSanSang() == null

    /**
     * Hỏi robot: bản đồ đang có những điểm nào, đã định vị chưa.
     * Kết quả đẩy ngược lên web qua window.baoTinhTrangBanDo(json).
     *
     * Dùng lúc lắp đặt để biết chắc tám điểm — "Tiep don", "Vien phi", "Nha thuoc",
     * "Can tin", "Nha ve sinh", "Truoc hanh lang", "Sanh cho", "Tram sac" — đã đặt đúng
     * tên chưa, thay vì bấm dẫn đường rồi ngồi đoán vì sao robot đứng im.
     */
    @JavascriptInterface
    fun kiemTraBanDo() {
        RobotHelper.daDinhVi { dinhVi ->
            RobotHelper.layDanhSachDiem { ds ->
                val w = web ?: return@layDanhSachDiem
                val j = JSONObject()
                j.put("daDinhVi", dinhVi)
                j.put("danhSachDiem", ds ?: "")
                Log.d(TAG, "Bản đồ: đãĐịnhVị=$dinhVi điểm=$ds")
                val js = "window.baoTinhTrangBanDo && window.baoTinhTrangBanDo(${JSONObject.quote(j.toString())})"
                w.post { w.evaluateJavascript(js, null) }
            }
        }
    }

    private fun baoDanDuong(trangThai: String, loiNhan: String) {
        if (dangVeCho) return              // chuyến robot tự về sảnh: không báo gì lên màn hình
        val w = web ?: return
        val js = "window.baoDanDuong && window.baoDanDuong(${JSONObject.quote(trangThai)}," +
                 "${JSONObject.quote(loiNhan)})"
        w.post { w.evaluateJavascript(js, null) }
    }
}
