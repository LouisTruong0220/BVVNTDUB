package vn.roboworld.benhvien

import android.util.Log
import com.ainirobot.agent.base.llm.LLMMessage
import com.ainirobot.agent.base.llm.Role
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors

/**
 * BỘ ĐIỀU PHỐI HỘI THOẠI — app tự cầm trịch, mô hình chỉ là một lời gọi CÓ KIỂM.
 *
 * Chép nguyên lối làm đã chạy được ở app tra cứu thủ tục Mông Dương (11/08/2026),
 * đổi phần dữ liệu sang khoa phòng bệnh viện và thêm một lớp chặn mà bên kia không cần.
 *
 * Vì sao KHÔNG để AgentOS tự hoạch định: hai chuyện hỏng đã đo được trên máy thật ở
 * app kia, không phải phỏng đoán —
 *   · hỏi giấy khai sinh, mô hình KHÔNG gọi Action mà tự bịa ra danh sách giấy tờ
 *   · gọi Action xong, nhận đủ nội dung, rồi IM LUÔN vì tưởng việc đã xong
 * Chính hãng cũng khuyên vậy (phản hồi 11/08/2026, câu A8): *"AgentOS is optimized for
 * our own business scenarios, so its NLP results may not be sufficiently accurate."*
 *
 * Đường đi bây giờ:
 *
 *   nghe được câu
 *     → ① CẤP CỨU?        → hô ngay, không hỏi mô hình
 *     → ② hỏi bệnh?        → từ chối, không hỏi mô hình
 *     → ③ chưa có dữ liệu? → nói thẳng chưa có, không hỏi mô hình
 *     → ④ tra kho khoa phòng tại chỗ, lấy cả MỨC TIN CẬY
 *     → ⑤ kho hỏi–đáp chung trong APK khớp chắc? → đọc nguyên văn, không hỏi mô hình
 *     → ⑥ dựng prompt kèm ĐÚNG danh sách ứng viên → AgentCore.llm()
 *     → ⑦ KIỂM câu trả lời (dòng KHOA_ID) → mới cho robot mở miệng
 *
 * Bốn trong bảy bước trên KHÔNG hỏi mô hình lần nào. Đó là chủ ý: mỗi câu tự trả lời
 * được là một câu không thể bịa, không tốn token, và không chết theo đường truyền.
 *
 * Nguyên tắc xuyên suốt: **việc an toàn chặn bằng MÃ, không chặn bằng lời dặn trong
 * prompt.** Prompt vẫn viết đầy đủ để mô hình cư xử đúng phần lớn thời gian, nhưng
 * không được tính là một lớp bảo vệ.
 */
object TraLoi {

    private const val TAG = "BVTraLoi"

    /** Mô hình chạy trên mạng, tra cứu chạy trên WebView — không được chặn luồng gọi. */
    private val tho = Executors.newSingleThreadExecutor()

    /* ── Những câu app TỰ soạn. Không câu nào đi qua mô hình. ── */

    private const val KHONG_CO_TRONG_KHO =
        "Việc này tôi chưa có trong dữ liệu nên không dám đoán, sợ chỉ sai thì quý vị đi nhầm " +
        "cả toà nhà. Mời quý vị hỏi quầy lễ tân giúp tôi ạ."

    private const val MO_HINH_HONG =
        "Xin lỗi quý vị, lúc này tôi chưa nghĩ ra câu trả lời. " +
        "Quý vị chạm vào màn hình để tự tra, hoặc hỏi quầy lễ tân giúp tôi ạ."

    /**
     * Điểm vào duy nhất. Gọi được từ luồng bất kỳ — bên trong tự đẩy sang luồng phụ.
     * Cả lời nói (onASRResult) lẫn chữ gõ (Cau.hoiRobot) đều vào đây.
     */
    fun hoi(cauHoi: String) {
        val cau = cauHoi.trim()
        /* ⚠ Ngưỡng cũ là hai ký tự — nó nuốt mất tiếng "ừ" và "ờ", đúng cách người già
           đồng ý khi robot hỏi "quý vị muốn tôi dẫn tới … đúng không ạ?". */
        if (cau.isEmpty()) return
        tho.execute { xuLy(cau) }
    }

    private fun xuLy(cau: String) {
        // ── Lớp 1: CẤP CỨU. Chặn trước mọi thứ, kể cả trước khi tra cứu.
        if (MainApplication.chanCapCuuNeuCan(cau)) { ghiNhatKy(cau, "cap-cuu", "", "", null); return }

        // ── Lớp 2: hỏi bệnh, hỏi thuốc. Robot không phải bác sĩ.
        if (MainApplication.chanHoiYTeNeuCan(cau)) { ghiNhatKy(cau, "hoi-y-te", "", "", null); return }

        // ── Lớp 3: những thứ bệnh viện chưa cung cấp (giờ làm việc, giá khám, tên bác sĩ…).
        if (MainApplication.chanChuaCoDuLieuNeuCan(cau)) { ghiNhatKy(cau, "chua-co", "", "", null); return }

        /* ── Lớp 3b: PHIÊN TRÒ CHUYỆN — trí nhớ ngữ cảnh + xác nhận trước khi dẫn ──
         *
         * Anh Trường báo 14/09/2026: đang trò chuyện mà bảo robot dẫn đường thì nó chỉ
         * trả lời bằng giọng nói chứ không đi. Đo lại trên bản thử: 6 trên 7 cách nói
         * tự nhiên không phát được lệnh đi, vì bản trước chỉ đi khi CHÍNH câu đó tra ra
         * mức chắc — mà "dẫn tôi tới đó" thì trong câu không có tên khoa nào.
         *
         * Lớp này đặt TRƯỚC lớp tra kho, và nó cũng là nơi giữ câu hỏi xác nhận: lời
         * đáp "đúng rồi" của người bệnh phải được hiểu là ĐỒNG Ý DẪN, chứ không phải
         * một câu hỏi mới đem đi tra bảng khoa phòng.
         *
         * Bộ máy nằm bên lớp web (window.xuLyCauNoi) vì ở đó mới có bảng đích đến, hàm
         * tra cứu, hàm mở màn và hàm phát lệnh đi. Dựng lại bên Kotlin là có hai bản
         * luật, mà hai bản luật thì sớm muộn lệch nhau.
         */
        val viec = runCatching { JSONObject(Cau.xuLyCauNoi(cau)) }.getOrNull()
        if (viec != null && viec.optBoolean("xong")) {
            val doc = viec.optString("doc")
            if (doc.isNotBlank()) MainApplication.tuDoc(doc)
            nhoLuot(cau, doc)
            ghiNhatKy(cau, "phien", viec.optString("viec"), "", null)
            return
        }

        // ── Lớp 4: tra trong bảng khoa phòng, lấy cả độ tin cậy.
        val kho = runCatching { JSONObject(Cau.traKhoaChoAI(cau)) }.getOrNull()
        if (kho == null) {
            Log.w(TAG, "Không đọc được kết quả tra cứu — trả lời dự phòng")
            MainApplication.tuDoc(MO_HINH_HONG)
            ghiNhatKy(cau, "loi-tra-cuu", "", "", null)
            return
        }

        val muc = kho.optString("muc")
        val ungVien = kho.optJSONArray("ung_vien") ?: JSONArray()

        // ── Lớp 5: đọc đúng mã phòng nhưng mã đó không có thật. Nói thẳng, không hỏi mô hình.
        if (muc == "ma-khong-co") {
            val ma = kho.optString("ma")
            /* ⚠ Dải mã lấy từ DỮ LIỆU, không ghi cứng. Câu này từng ghi thẳng "từ đê một đến
               đê hai mươi tư"; khi bệnh viện bỏ D23–D24 và thêm C1, CĐHA (08/09/2026) thì
               robot vẫn đọc dải cũ — sai mà không tầng nào báo, vì nó chỉ là một chuỗi. */
            val dai = kho.optString("mo_ta_ma_doc")
            val coDai = if (dai.isBlank()) "" else " Ở đây chỉ có mã phòng $dai."
            MainApplication.tuDoc(
                "Tôi không tìm thấy phòng $ma trong bệnh viện.$coDai " +
                "Quý vị xem lại phiếu khám, hoặc hỏi quầy lễ tân giúp tôi ạ."
            )
            ghiNhatKy(cau, muc, ma, "", null)
            return
        }

        // Chỉ mở trang chỉ đường khi thật sự chắc — mở nhầm còn rối hơn không mở.
        if (muc == "chac" && ungVien.length() > 0) Cau.guiGoiYSangManHinh(cau)

        /* ── Lớp 5b: KHO HỎI–ĐÁP CHUNG, nằm sẵn trong APK ────────────────────────
         *
         * Mấy chuyện không gắn với khoa nào — quy trình khám lần đầu, phạm vi robot đi
         * được, giới thiệu bệnh viện — trước đây chỉ có trên cổng OrionStar. Mà
         * `LLMConfig.fileSearch`, tham số cho phép `llm()` đọc kho tri thức trên cổng,
         * đã bị máy chủ hãng BỎ từ 26/08/2025 (xem MainApplication.hoiMoHinh). Nghĩa là
         * mô hình KHÔNG với tới kho đó nữa, và mấy câu này rơi vào khoảng trống: tra khoa
         * phòng không ra gì, mô hình thì hoặc chịu, hoặc tự bịa.
         *
         * Nay chúng đi theo app-data.json vào assets/ của APK. Lớp web tra rồi trả về ở
         * trường `hoi_dap` — và CHỈ trả khi tra khoa phòng không chắc, nên lớp này không
         * bao giờ cướp việc của màn chỉ đường.
         *
         * ⚠ ĐỌC NGUYÊN VĂN, KHÔNG HỎI MÔ HÌNH. Cùng một luật với trường `doc` của bảng
         *   khoa phòng: câu nào bệnh viện duyệt thì người bệnh nghe đúng câu đó. Đổi lại
         *   còn được hai thứ — trả lời tức thì, và trả lời được cả khi mạng đang chậm.
         */
        val hd = kho.optJSONObject("hoi_dap")
        if (hd != null) {
            val dap = hd.optString("dap")
            if (dap.isNotBlank()) {
                Log.d(TAG, "Trả lời từ kho hỏi–đáp trong máy: ${hd.optString("nhom")}")
                MainApplication.tuDoc(dap)
                ghiNhatKy(cau, "hoi-dap", hd.optString("nhom"), "", null)
                return
            }
            Log.w(TAG, "Mục hỏi–đáp '${hd.optString("nhom")}' rỗng câu đáp — bỏ qua, hỏi mô hình")
        }

        // ── Lớp 6: hỏi mô hình, kèm ĐÚNG danh sách ứng viên vừa tra được.
        MainApplication.hoiMoHinh(dungTinNhan(cau, muc, ungVien)) { chu, loi ->
            if (chu == null) {
                Log.w(TAG, "Mô hình không trả lời: $loi")
                // Còn ứng viên thì tự trả lời bằng dữ liệu trong máy, đừng bỏ mặc người bệnh.
                val duPhong = if (ungVien.length() > 0) ungVien.getJSONObject(0).optString("doc")
                              else KHONG_CO_TRONG_KHO
                MainApplication.tuDoc(duPhong.ifBlank { KHONG_CO_TRONG_KHO })
                ghiNhatKy(cau, muc, "", "loi:$loi", null)
            } else {
                docCauTraLoi(cau, muc, ungVien, chu)
            }
        }
    }

    /* ══════════════════════════════════════════════════════════════════
       TRÍ NHỚ TRONG MỘT PHIÊN — anh Trường chốt 14/09/2026

       > "Trong một phiên nói chuyện thì Robot ghi nhớ các dữ liệu, thông tin đã
       >  trao đổi trong phiên đó, chỉ khi kết thúc mới reset."

       ⚠ Gửi lịch sử dưới dạng CHỮ trong chính tin nhắn người dùng, không dùng thêm
         vai "trợ lý" của SDK. Lý do thực dụng: bộ vai của Agent SDK 0.4.7 chưa được
         kiểm trên máy thật, mà đoán sai một hằng số enum là cả lượt gọi hỏng lặng lẽ —
         đúng kiểu lỗi đã mất nhiều ngày ở app này. Dạng chữ thì chắc chắn chạy.

       ⚠ Chỉ giữ BỐN lượt gần nhất. Người bệnh kể bệnh dài dòng, nhét cả phiên vào mỗi
         lượt là phình token rất nhanh — bài học hạn mức 8.000 token mỗi phút ở app trước.

       ⚠ XOÁ khi hết phiên (Cau.ketThucPhien). Ở bệnh viện đây không chỉ là chuyện gọn
         gàng: chuyện bệnh của người trước không được dính sang người sau.
       ══════════════════════════════════════════════════════════════════ */
    private const val NHO_MAY_LUOT = 4
    private val lichSu = java.util.Collections.synchronizedList(ArrayList<Pair<String, String>>())

    /** Lớp web gọi qua Cau.ketThucPhien khi đóng chat · xoá đoạn chat · về màn chờ. */
    fun xoaLichSu() {
        val n = lichSu.size
        lichSu.clear()
        Log.d(TAG, "Kết thúc phiên — xoá $n lượt trong trí nhớ")
    }

    private fun nhoLuot(hoi: String, dap: String) {
        if (hoi.isBlank()) return
        synchronized(lichSu) {
            lichSu.add(hoi to dap)
            while (lichSu.size > NHO_MAY_LUOT) lichSu.removeAt(0)
        }
    }

    private fun lichSuChuoi(): String {
        val ban = synchronized(lichSu) { lichSu.toList() }
        if (ban.isEmpty()) return ""
        return "ĐÃ TRAO ĐỔI TRONG PHIÊN NÀY (cũ ở trên, mới ở dưới):\n" +
               ban.joinToString("\n") { (h, d) ->
                   "- Người bệnh: $h" + (if (d.isBlank()) "" else "\n  Bạn đã đáp: $d")
               } + "\n\n"
    }

    /**
     * Dựng danh sách tin nhắn gửi mô hình.
     *
     * ⚠ CHỈ gửi id, tên khoa và vị trí gọn. KHÔNG gửi câu `doc` — dù JSON có sẵn.
     *   Câu `doc` là thứ robot đọc thành tiếng, lấy nguyên văn từ bảng khoa phòng bệnh
     *   viện cung cấp. Gửi nó cho mô hình là mời mô hình diễn đạt lại, mà diễn đạt lệch
     *   một số tầng thôi là người bệnh leo nhầm tầng. App tự ghép câu đó vào sau câu dẫn.
     */
    private fun dungTinNhan(cau: String, muc: String, ungVien: JSONArray): List<LLMMessage> {
        val danhSach = if (ungVien.length() == 0) "(máy không tìm được khoa nào khớp)"
        else (0 until ungVien.length()).joinToString("\n") { i ->
            val t = ungVien.getJSONObject(i)
            "[id=${t.optInt("id")}] ${t.optString("ten")} — ${t.optString("vi_tri")}"
        }

        val nhac = when (muc) {
            "chac"      -> "Máy khá chắc ứng viên đầu tiên là đúng."
            "chua-chac" -> "Máy CHƯA CHẮC. Nếu bạn cũng chưa chắc thì hãy hỏi lại cho rõ " +
                           "thay vì khẳng định."
            else        -> "Máy không tìm được khoa nào khớp."
        }

        return listOf(
            LLMMessage(Role.SYSTEM, MainApplication.PERSONA + "\n\n" + MainApplication.LUAT_TRA_LOI),
            LLMMessage(Role.USER,
                lichSuChuoi() +
                "DANH SÁCH ỨNG VIÊN (máy vừa tra trong bảng khoa phòng cài sẵn trong robot):\n" +
                danhSach + "\n\n" + nhac + "\n\n" +
                "Người bệnh vừa nói: \"" + cau + "\"")
        )
    }

    /* ══════════════════════════════════════════════════════════════════
       CHỐT AN TOÀN — kiểm câu trả lời của mô hình TRƯỚC KHI robot mở miệng
       ══════════════════════════════════════════════════════════════════ */

    /** Dòng cuối bắt buộc, ví dụ `KHOA_ID: 3` hoặc `KHOA_ID: KHONG_CO`. */
    private val DONG_ID = Regex("""KHOA_ID\s*:\s*([A-Za-z0-9_]+)""", RegexOption.IGNORE_CASE)

    private fun docCauTraLoi(cau: String, muc: String, ungVien: JSONArray, chuGoc: String) {
        val khop = DONG_ID.find(chuGoc)
        val ma = khop?.groupValues?.get(1)?.uppercase().orEmpty()
        val chu = DONG_ID.replace(chuGoc, "").trim()

        // Thiếu hẳn dòng mã → coi như không hợp lệ. Sai theo hướng an toàn.
        if (ma.isEmpty()) {
            Log.w(TAG, "Mô hình bỏ dòng KHOA_ID — bỏ câu trả lời. Nguyên văn: $chuGoc")
            MainApplication.tuDoc(KHONG_CO_TRONG_KHO)
            ghiNhatKy(cau, muc, "", "thieu-ma", chuGoc)
            return
        }

        if (ma == "TAM_SU") {
            /* Chuyện ngoài lề: cứ để mô hình nói tự nhiên, nó không khẳng định gì về khoa phòng.
               Chặn kèm chữ số — số ở đây chỉ có thể là tầng hoặc mã phòng, hai thứ mô hình
               không được phép tự nói. */
            val an = chu.any { it.isDigit() }
            if (an) Log.w(TAG, "TAM_SU nhưng câu có chữ số — bỏ: $chu")
            MainApplication.tuDoc(if (an) "Dạ vâng ạ." else chu.ifBlank { "Dạ vâng ạ." })
            ghiNhatKy(cau, muc, "TAM_SU", "", chuGoc)
            return
        }

        if (ma == "KHONG_CO") {
            /* Hai tình huống rất khác nhau:
             *  a) Máy không tra ra gì → mô hình hay "giúp thêm" bằng kiến thức nền, đúng cái
             *     đã làm nó bịa giấy tờ ở app kia. Dùng CÂU CỨNG của app.
             *  b) Máy có ứng viên nhưng chưa chắc → mô hình hỏi lại rất đúng việc
             *     ("quý vị đau bụng trên hay bụng dưới ạ?"), mà bảng ứng viên đang hiện sẵn
             *     trên màn hình để người bệnh chọn. Cho nói.
             * Chặn kèm: câu hỏi lại mà có CHỮ SỐ thì vứt. */
            val hoiLai = ungVien.length() > 0 && chu.isNotBlank() && !chu.any { it.isDigit() }
            if (hoiLai) {
                MainApplication.tuDoc(chu)
            } else {
                if (chu.any { it.isDigit() }) Log.w(TAG, "KHONG_CO nhưng câu có chữ số — bỏ: $chu")
                MainApplication.tuDoc(KHONG_CO_TRONG_KHO)
            }
            ghiNhatKy(cau, muc, if (hoiLai) "KHONG_CO-hoi-lai" else "KHONG_CO", "", chuGoc)
            return
        }

        // Mã phải là id của MỘT trong những ứng viên vừa gửi đi.
        val id = ma.toIntOrNull()
        val chon = (0 until ungVien.length())
            .map { ungVien.getJSONObject(it) }
            .firstOrNull { it.optInt("id") == id }

        if (chon == null) {
            Log.w(TAG, "Mô hình trả id LẠC '$ma' — không nằm trong danh sách ứng viên. Bỏ câu trả lời.")
            MainApplication.tuDoc(KHONG_CO_TRONG_KHO)
            ghiNhatKy(cau, muc, "lac:$ma", "", chuGoc)
            return
        }

        /* Hợp lệ: robot đọc câu dẫn của mô hình, RỒI app tự đọc vị trí lấy thẳng từ bảng
           khoa phòng. Tên khoa, số tầng, mã phòng không đi qua mô hình lần nào. */
        val viTri = chon.optString("doc").ifBlank { KHONG_CO_TRONG_KHO }
        val noi = buildString {
            if (chu.isNotBlank()) { append(chu); if (!chu.endsWith(".")) append("."); append(" ") }
            append(viTri)
        }
        MainApplication.tuDoc(noi)
        nhoLuot(cau, noi)      // để câu sau nói "dẫn tôi tới đó" là robot biết đường
        ghiNhatKy(cau, muc, ma, "", chuGoc)
    }

    /* ══════════════════════════════════════════════════════════════════
       NHẬT KÝ — để hiệu chỉnh ngưỡng và để biết chi phí
       ══════════════════════════════════════════════════════════════════ */

    /**
     * Ghi mỗi lượt hỏi ra thẻ nhớ. Lấy về bằng:
     *
     *   adb pull /sdcard/Android/data/vn.roboworld.benhvien/files/nhat-ky
     *
     * Dùng getExternalFilesDir nên KHÔNG cần xin quyền lưu trữ, và gỡ app là dọn sạch theo.
     *
     * ⚠ Ở bệnh viện, file này có thể chứa lời người bệnh kể về bệnh tình mình. Đó là dữ
     *   liệu riêng tư. Lấy về để hiệu chỉnh xong thì XOÁ, đừng để tồn trên máy, và đừng
     *   gửi ra ngoài Roboworld khi chưa hỏi bệnh viện.
     */
    private fun ghiNhatKy(cau: String, muc: String, ma: String, loi: String, traLoi: String?) {
        runCatching {
            val ctx = MainApplication.boiCanh ?: return
            val thuMuc = File(ctx.getExternalFilesDir(null), "nhat-ky").apply { mkdirs() }
            val ngay = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
            val gio = SimpleDateFormat("HH:mm:ss", Locale.US).format(Date())
            val dong = listOf(gio, muc, ma, loi, cau.replace('\n', ' '),
                              (traLoi ?: "").replace('\n', ' ').take(400))
                .joinToString("\t") + "\n"
            File(thuMuc, "hoi-$ngay.tsv").appendText(dong)
        }.onFailure { Log.w(TAG, "Không ghi được nhật ký: ${it.message}") }
    }
}
