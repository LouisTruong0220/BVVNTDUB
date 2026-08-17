package vn.roboworld.benhvien

import android.app.Application
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.ainirobot.agent.AgentCore
import com.ainirobot.agent.AppAgent
import com.ainirobot.agent.LLMCallback
import com.ainirobot.agent.OnTranscribeListener
import com.ainirobot.agent.action.Action
import com.ainirobot.agent.action.Actions
import com.ainirobot.agent.assit.LLMResponse
import com.ainirobot.agent.base.Transcription
import com.ainirobot.agent.base.llm.LLMConfig
import com.ainirobot.agent.base.llm.LLMMessage
import com.ainirobot.agent.base.llm.Role

/**
 * Điểm khởi động của app lễ tân bệnh viện.
 *
 * Phân vai giữa hai tầng — chỗ dễ hiểu nhầm nhất:
 *
 *   • RobotApi / SkillApi  → dẫn đường và đọc thành tiếng. Đây là phần app sống bằng,
 *                            không phụ thuộc Agent SDK.
 *   • Agent SDK 0.4.7      → nghe (ASR) và gọi mô hình ngôn ngữ. App KHÔNG để AgentOS
 *                            tự hoạch định — xem `isDisablePlan` bên dưới và TraLoi.kt.
 *
 * Toàn bộ phần AI ở đây chép lối làm đã chạy được trên app tra cứu thủ tục Mông Dương
 * (11/08/2026). Bốn thứ dưới đây từng làm mất nhiều ngày ở app kia, đừng đổi nếu chưa
 * đọc kỹ chú thích tại chỗ:
 *   ① SDK phải lấy từ gói offline, không lấy JitPack   (xem app/build.gradle.kts)
 *   ② `businessInfo` phải là null, không được là ""     (xem hoiMoHinh)
 *   ③ bốn công tắc của hãng đều mặc định SAI với app này (xem onCreate)
 *   ④ việc an toàn chặn bằng MÃ, không chặn bằng prompt  (xem ba hàm chan…NeuCan)
 *
 * LƯU Ý: mỗi app CHỈ ĐƯỢC CÓ MỘT thực thể AppAgent.
 */
class MainApplication : Application() {

    companion object {
        private const val TAG = "BVApp"

        @Volatile private var agent: AppAgent? = null

        /** Bối cảnh ứng dụng — TraLoi cần để ghi nhật ký ra thẻ nhớ. */
        @Volatile var boiCanh: android.content.Context? = null; private set

        /**
         * AI đám mây đã trả lời thật hay chưa. Lớp web đọc cờ này để quyết định có hiện
         * nút micro không.
         *
         * ⚠ KHÔNG suy ra từ "agent != null". Dựng được AppAgent chỉ nghĩa là hàm khởi tạo
         *   không ném lỗi — nó vẫn dựng thành công khi dịch vụ của hãng không bind được.
         *   Cờ này chỉ bật khi mô hình trả lời thật, hoặc khi nghe được một câu ASR thật.
         *   Một nút micro bấm vào không phản ứng, trước mặt lãnh đạo bệnh viện, tệ hơn
         *   nhiều so với việc không có nút.
         */
        @Volatile private var agentSanSang = false

        fun batMicro() = datMicro(false)
        fun tatMicro() = datMicro(true)

        /**
         * ⚠ Mic và "nghe không cần đánh thức" phải đi CÙNG NHAU, đặt ở đúng một chỗ này.
         *
         * `isEnableWakeFree` mặc định BẬT. Bật nghĩa là robot nghe và tự đáp mà không cần
         * từ đánh thức — ở app Mông Dương chính nó gây ra chuyện **lúc dẫn đường robot tự
         * nói bằng giọng AI**, chồng lên giọng đọc SkillApi của app: dọc đường có ai nói
         * câu gì là AgentOS bắt lời rồi trả lời luôn.
         *
         * Ở bệnh viện chuyện đó còn tệ hơn: sảnh đông, robot bắt lời người lạ giữa lúc
         * đang dẫn một người bệnh đi.
         *
         * Tắt hẳn thì màn Trò chuyện mất khả năng nghe liên tục. Nên buộc nó bám theo
         * trạng thái mic: mic mở mới cho nghe tự do, mic đóng là câm hẳn.
         */
        private fun datMicro(tat: Boolean) {
            runCatching {
                AgentCore.isMicrophoneMuted = tat
                AgentCore.isEnableWakeFree = !tat
                Log.d(TAG, "Micro: tắt tiếng=${AgentCore.isMicrophoneMuted} · " +
                           "nghe tự do=${AgentCore.isEnableWakeFree}")
            }.onFailure { Log.w(TAG, "Không đặt được trạng thái micro: ${it.message}") }
        }

        fun micDangMo(): Boolean = runCatching { !AgentCore.isMicrophoneMuted }.getOrDefault(false)

        /** Xoá ngữ cảnh hội thoại — gọi mỗi khi robot về màn chờ.
         *  Ở bệnh viện đây không chỉ là chuyện gọn gàng: chuyện bệnh tình của người trước
         *  không được dính sang lượt của người sau. */
        fun xoaNguCanh() = runCatching { AgentCore.clearContext() }.isSuccess

        /**
         * Kể cho mô hình biết trên màn hình đang có gì.
         *
         * ⚠ Kênh này CHỈ là mô tả màn hình đang hiện, KHÔNG phải kho tri thức. Hãng xác
         *   nhận (phản hồi 11/08/2026, câu A10) mô hình không dùng nó để trả lời câu hỏi
         *   kiến thức. Sự thật cố định (ba toà nhà, phạm vi robot đi được) phải đặt trong
         *   PERSONA; nội dung khoa phòng đi theo danh sách ứng viên trong prompt, xem TraLoi.
         */
        fun moTaManHinh(mo: String) {
            runCatching { AgentCore.uploadInterfaceInfo(mo) }
                .onSuccess { Log.d(TAG, "Đã gửi mô tả màn hình (${mo.length} ký tự)") }
                .onFailure { Log.w(TAG, "Không gửi được mô tả màn hình: ${it.message}") }
        }

        /**
         * Gọi thẳng mô hình ngôn ngữ, KHÔNG qua bộ hoạch định Action của AgentOS.
         * Đây là đường chính để robot trả lời, và là thứ chính hãng khuyên dùng.
         *
         * ⚠ Khác API 0.2.2 ở ba chỗ, sửa nhầm là không biên dịch được:
         *   · callback đổi từ `TaskCallback` sang `LLMCallback`
         *   · `llm()` thêm tham số `stream: Boolean` trước callback
         *   · callback nay trả về CẢ CÂU TRẢ LỜI (`LLMResponse`), không còn chỉ 0/1
         *
         * ⚠ `LLMConfig.fileSearch` (tham số thứ 4) đã bị BỎ — máy chủ ngừng đọc từ
         *   26/08/2025. Đặt true hay false đều vô nghĩa.
         *
         * ⚠⚠ `businessInfo` (tham số thứ 5) PHẢI là `null`, KHÔNG được là `""`.
         *   Đây là nguyên nhân của hai ngày đứng hình ở app Mông Dương: truyền chuỗi rỗng
         *   thì máy chủ hiểu là "có businessInfo" rồi đi tra một hồ sơ rỗng, tra không ra
         *   nên trả `status=2, result=null` sau ~355 ms — không lỗi, không lý do, không log.
         *   Quy ước mã trả về: **status=1 là thành công**, status=2 là máy chủ thất bại.
         *
         * @param khiXong gọi trên luồng phụ với (câu trả lời, lỗi). Một trong hai là null.
         */
        fun hoiMoHinh(danhSachTin: List<LLMMessage>, khiXong: (String?, String?) -> Unit) {
            val ok = runCatching {
                /* 400 token đủ cho hai câu dẫn cộng dòng KHOA_ID. 20 giây: quá mức đó thì
                   người bệnh đã bỏ đi rồi, chờ thêm vô nghĩa. */
                val cauHinh = LLMConfig(0.6f, 400, 20, false, null)
                AgentCore.llm(danhSachTin, cauHinh, 20_000L, false, object : LLMCallback {
                    override fun onTaskEnd(status: Int, result: LLMResponse?) {
                        val chu = result?.message?.content.orEmpty()
                        val tk = result?.tokenCost
                        Log.d(TAG, "hoiMoHinh: status=$status · ${result?.elapsedTime ?: -1f}s · " +
                                   "token prompt=${tk?.promptTokens ?: -1} " +
                                   "completion=${tk?.completionTokens ?: -1} " +
                                   "total=${tk?.totalTokens ?: -1}")
                        // In nguyên đối tượng trả về: lúc hãng từ chối, lý do nằm ở đây chứ
                        // không ở logcat của AgentService. Đây là thứ để gửi cho hãng.
                        Log.d(TAG, "hoiMoHinh: nguyên văn = $result")
                        if (status == 1 && chu.isNotBlank()) {
                            if (!agentSanSang) { agentSanSang = true; Cau.baoAISanSang(true) }
                            khiXong(chu, null)
                        } else khiXong(null,
                            listOfNotNull(
                                "status=$status",
                                result?.status?.takeIf { it.isNotBlank() }?.let { "trạng thái=$it" },
                                result?.error?.takeIf { it.isNotBlank() }?.let { "lỗi=$it" },
                                if (result == null) "không có dữ liệu trả về" else null
                            ).joinToString(" · "))
                    }
                })
            }.isSuccess
            if (!ok) khiXong(null, "không gọi được mô hình")
        }

        /**
         * CHẨN ĐOÁN — hỏi mô hình một câu vu vơ để biết đường lên đám mây có thông không.
         * Gõ trong DevTools:  CAU.thuLLM('Một cộng một bằng mấy?', false)
         * Xem kết quả:        adb logcat -s BVApp
         */
        fun thuLLM(cauHoi: String, @Suppress("UNUSED_PARAMETER") khongDungNua: Boolean) {
            Log.d(TAG, "thuLLM: hỏi '$cauHoi'")
            hoiMoHinh(
                listOf(
                    LLMMessage(Role.SYSTEM, "Bạn là robot lễ tân. Trả lời ngắn gọn bằng tiếng Việt."),
                    LLMMessage(Role.USER, cauHoi)
                )
            ) { chu, loi ->
                Log.d(TAG, "thuLLM: ${if (chu != null) "TRẢ LỜI ĐƯỢC: $chu" else "HỎNG: $loi"}")
                Cau.guiLoiNoi("robot",
                    if (chu != null) "[chẩn đoán] $chu" else "[chẩn đoán] Mô hình không trả lời: $loi",
                    true)
            }
        }

        /**
         * Thăm dò một lần lúc khởi động: mô hình đám mây có trả lời thật không.
         * Chỉ khi trả về status=1 thì lớp web mới hiện nút micro.
         *
         * Đây là phép thử ĐẦU-CUỐI, không phải kiểm tra "hàm có tồn tại không".
         * Bài học từ app Mông Dương: `webkitSpeechRecognition` CÓ tồn tại trong WebView
         * robot, `batMic()` gọi được, `AppAgent` dựng được — nhưng bấm nút mic thì chết
         * câm suốt hai tuần. **Mọi phép kiểm "có hàm không" đều đánh lừa.**
         */
        private fun thamDoAI() {
            Handler(Looper.getMainLooper()).postDelayed({
                hoiMoHinh(listOf(LLMMessage(Role.USER, "Xin chào"))) { chu, loi ->
                    Log.d(TAG, "Thăm dò AI: ${if (chu != null) "THÔNG — $chu" else "chưa thông — $loi"}")
                    Cau.baoAISanSang(chu != null)
                }
            }, 4_000L)   // chờ Agent SDK bind xong rồi mới thử
        }

        /** Thông tin để tự kiểm lúc lắp đặt, và để lớp web quyết định có hiện nút mic không. */
        fun thongTinAI(): String {
            val appId = runCatching { AgentCore.appId }.getOrNull()
            return """{"appId":${org.json.JSONObject.quote(appId ?: "")},""" +
                   """"coAgent":${agent != null},""" +
                   """"agentSanSang":$agentSanSang,""" +
                   """"micDangMo":${micDangMo()}}"""
        }

        /* ══════════════════════════════════════════════════════════════
           BA CHỐT AN TOÀN — chặn bằng MÃ, không chặn bằng lời dặn

           Vì sao không tin vào setObjective: ở app Mông Dương đã dặn rõ *"kho chưa có
           hộ tịch, gặp mấy việc đó phải nói rõ là chưa được nạp, tuyệt đối đừng đoán"*,
           nhưng đo ngày 11/08/2026: hỏi "tôi muốn làm giấy khai sinh cho con" thì robot
           KHÔNG gọi Action, tự trả lời luôn *"Anh cần chuẩn bị: tờ khai đăng ký khai
           sinh, giấy chứng…"* — bịa từ kiến thức nền của mô hình.

           Ở bệnh viện, cái giá của một câu bịa cao hơn nhiều so với ở uỷ ban.
           ══════════════════════════════════════════════════════════════ */

        /**
         * ① CẤP CỨU — chặn trước mọi thứ khác.
         *
         * Chỉ gồm những từ KHÔNG THỂ hiểu nhầm sang khám thường. Cố ý KHÔNG đưa "khó thở"
         * trơn vào đây: người hen phế quản đi khám định kỳ cũng nói "khó thở", mà đưa vào
         * thì Khoa Nội Phổi thành không tra được bằng giọng nói nữa. Chỉ bắt "khó thở quá",
         * "không thở được".
         */
        private val TU_CAP_CUU = Regex(
            "cấp cứu|cap cuu|nguy kịch|nguy kich|ngất|ngat xiu|bất tỉnh|bat tinh|" +
            "co giật|co giat|đột quỵ|dot quy|tai biến|tai bien|" +
            "không thở được|khong tho duoc|khó thở quá|kho tho qua|ngạt thở|ngat tho|" +
            "chảy máu nhiều|chay mau nhieu|băng huyết|bang huyet|" +
            "ngộ độc|ngo doc|hóc|sặc|tai nạn|tai nan|đau ngực dữ dội|dau nguc du doi",
            RegexOption.IGNORE_CASE
        )

        /**
         * ② HỎI BỆNH — robot không phải bác sĩ.
         *
         * Nhắm vào câu hỏi RÕ RÀNG là xin ý kiến y tế, không nhắm vào từ "bệnh" trơn —
         * "khoa này khám bệnh gì" là câu tra cứu hợp lệ, chặn nhầm là app hết dùng được.
         */
        private val TU_HOI_Y_TE = Regex(
            "tôi bị (bệnh )?gì|toi bi gi|em bị gì|cháu bị gì|" +
            "có nặng không|co nang khong|có nguy hiểm không|co nguy hiem khong|" +
            "có sao không|co sao khong|có việc gì không|" +
            "uống thuốc gì|uong thuoc gi|nên uống|nen uong|dùng thuốc gì|dung thuoc gi|" +
            "có phải mổ|co phai mo|có nên mổ|co nen mo|có cần mổ|" +
            "chẩn đoán|chan doan|xem (giúp|hộ|giùm).{0,12}kết quả|" +
            "kết quả (xét nghiệm|siêu âm|chụp).{0,20}(sao|thế nào|gì)",
            RegexOption.IGNORE_CASE
        )

        /**
         * ③ CHƯA CÓ DỮ LIỆU — bệnh viện chưa cung cấp.
         *
         * ⚠ Nhắm vào câu hỏi SỐ LIỆU, không nhắm vào từ khoá địa điểm. "Phòng thu viện phí
         *   ở đâu" là câu tra cứu hợp lệ và phải dẫn đường được; "khám hết bao nhiêu tiền"
         *   mới là câu chưa có dữ liệu.
         */
        private val TU_CHUA_CO = Regex(
            "bao nhiêu tiền|bao nhieu tien|hết bao nhiêu|het bao nhieu|giá khám|gia kham|" +
            "chi phí|chi phi|mất bao nhiêu|" +
            "mấy giờ|may gio|giờ làm việc|gio lam viec|giờ mở cửa|mở cửa lúc|đóng cửa lúc|" +
            "bác sĩ nào|bac si nao|bác sỹ nào|bác sĩ tên gì|ai trực|lịch trực|lich truc|" +
            "số điện thoại|so dien thoai|hotline|" +
            "đặt lịch|dat lich|đặt hẹn|dat hen|đăng ký online|dang ky online|" +
            "còn giường|con giuong|giường trống|giuong trong|còn chỗ nằm|" +
            "bao giờ (tới|đến) lượt|khi nào (tới|đến) lượt|lịch mổ|lich mo",
            RegexOption.IGNORE_CASE
        )

        /* ⚠ Chỉ đường bằng THỨ TỰ toà nhà, không bằng tên. Robot dừng ở đầu hành lang,
           còn cách các toà một quãng; đứng đó nhìn lên thì ba toà giống hệt nhau và biển
           tên xa quá không đọc nổi. Người đang hoảng lại càng không đọc được. */
        private const val LOI_CAP_CUU =
            "Cấp cứu thì quý vị đi ngay, đừng chờ tôi dẫn, tôi đi chậm hơn quý vị. " +
            "Khoa Hồi sức Cấp cứu Nội ở tầng hai, toà nhà đê ba, phòng đê hai mươi ba và " +
            "đê hai mươi tư. Xin mời đi thẳng, toà nhà thứ ba, đó là toà đê ba, rồi lên tầng hai."

        private const val LOI_HOI_Y_TE =
            "Tôi là robot chỉ đường, tôi không khám bệnh và không đoán bệnh được đâu ạ. " +
            "Quý vị cho tôi biết cần tới khoa nào, tôi chỉ đường giúp. Còn bệnh tình thì " +
            "bác sĩ ở phòng khám mới là người trả lời được."

        private const val LOI_CHUA_CO =
            "Phần này tôi chưa được nạp dữ liệu nên không dám nói, sợ sai thì quý vị mất công. " +
            "Mời quý vị hỏi quầy lễ tân giúp tôi ạ."

        /**
         * Câu mà CHÍNH APP vừa cho robot đọc.
         *
         * Robot đọc câu nào thì onTTSResult cũng bắn từng mẩu chữ về ("Phần này tôi",
         * "Phần này tôi chưa được nạp"…). Câu do app tự soạn thì app đã đưa lên màn hình
         * rồi; để mẩu chữ bắn về nữa là khung chat hiện lặp bốn năm lần cùng một câu.
         */
        @Volatile private var tuNoi: String = ""

        /**
         * ROBOT ĐỌC MỘT CÂU DO CHÍNH APP SOẠN.
         * Gom về một chỗ vì ba việc phải đi cùng nhau, thiếu một là lỗi:
         *   · nhớ câu vừa đọc (tuNoi) để onTTSResult khỏi đẩy lên màn hình lần nữa
         *   · đọc thành tiếng bằng SkillApi — đường này chạy tốt từ đầu, không đụng vào
         *   · hiện luôn lên khung chat cho người đứng xa đọc được
         */
        fun tuDoc(cau: String) {
            if (cau.isBlank()) return
            tuNoi = cau
            RobotHelper.doc(cau) {}
            Cau.guiLoiNoi("robot", cau, true)
        }

        /** Trả true nếu đã chặn xong — đừng hỏi mô hình nữa. */
        fun chanCapCuuNeuCan(cau: String): Boolean {
            if (!TU_CAP_CUU.containsMatchIn(cau)) return false
            Log.w(TAG, "CHẶN CẤP CỨU: '$cau'")
            runCatching { AgentCore.stopTTS() }
            Cau.moManCapCuu()          // bật màn đỏ để người đứng xa cũng thấy
            tuDoc(LOI_CAP_CUU)
            return true
        }

        fun chanHoiYTeNeuCan(cau: String): Boolean {
            if (!TU_HOI_Y_TE.containsMatchIn(cau)) return false
            Log.w(TAG, "CHẶN HỎI BỆNH: '$cau'")
            runCatching { AgentCore.stopTTS() }
            tuDoc(LOI_HOI_Y_TE)
            return true
        }

        fun chanChuaCoDuLieuNeuCan(cau: String): Boolean {
            if (!TU_CHUA_CO.containsMatchIn(cau)) return false
            Log.w(TAG, "CHẶN CHƯA CÓ DỮ LIỆU: '$cau'")
            runCatching { AgentCore.stopTTS() }
            tuDoc(LOI_CHUA_CO)
            return true
        }

        /* ══════════════════════════════════════════════════════════════
           LỜI DẶN GỬI MÔ HÌNH — dùng chung cho setPersona và cho TraLoi
           ══════════════════════════════════════════════════════════════ */

        /**
         * ⚠ NHỮNG SỰ THẬT CỐ ĐỊNH PHẢI ĐẶT Ở ĐÂY, KHÔNG ĐẶT Ở uploadInterfaceInfo.
         * Hãng xác nhận kênh uploadInterfaceInfo chỉ là MÔ TẢ MÀN HÌNH ĐANG HIỆN, mô hình
         * không dùng nó để trả lời câu hỏi kiến thức.
         *
         * Quy tắc: sự thật KHÔNG ĐỔI (ba toà nhà, phạm vi robot đi được) → đây.
         *          Thứ THAY ĐỔI theo màn hình → uploadInterfaceInfo.
         *          Vị trí khoa phòng → danh sách ứng viên trong prompt, xem TraLoi.kt.
         */
        val PERSONA =
            "Bạn là robot lễ tân của Bệnh viện Việt Nam – Thụy Điển Uông Bí, " +
            "đứng ở sảnh lễ tân.\n" +

            "Bệnh viện có ĐÚNG ba toà nhà điều trị, xếp dọc hành lang theo thứ tự: " +
            "toà nhà ĐẦU TIÊN là nhà DI (năm tầng), toà nhà THỨ HAI là nhà DII (năm tầng), " +
            "toà nhà THỨ BA là nhà DIII (tám tầng). Các khoa đánh mã phòng từ D1 đến D24.\n" +

            "Trong khu lễ tân có quầy tiếp đón và đăng ký khám, phòng thu viện phí, " +
            "nhà thuốc, căn tin và nhà vệ sinh.\n" +

            "PHẠM VI ĐI LẠI của bạn: chỉ trong khu lễ tân, xa nhất là ra ĐẦU HÀNH LANG. " +
            "Bạn dừng ở đó, còn cách các toà nhà một quãng. Bạn KHÔNG vào trong ba toà nhà, " +
            "KHÔNG lên thang máy, KHÔNG lên tầng. Tuyệt đối đừng hứa dẫn quý vị vào tận phòng khám.\n" +

            "Khi chỉ đường tới một toà nhà, hãy nói theo THỨ TỰ ('toà nhà thứ hai') rồi mới " +
            "nhắc tên ('đó là toà DII'). Đứng ở đầu hành lang thì ba toà trông giống hệt nhau " +
            "và biển tên xa quá không đọc nổi, nhưng đếm thứ tự thì ai cũng đếm được.\n" +

            "BẠN KHÔNG PHẢI BÁC SĨ: không chẩn đoán, không đoán bệnh, không khuyên dùng thuốc, " +
            "không nhận xét kết quả xét nghiệm.\n" +

            "Bạn lễ độ, kiên nhẫn, nói ngắn và dễ hiểu. Bạn xưng 'tôi', gọi người đối diện là " +
            "'quý vị'. Người tới đây phần nhiều đang mệt, đang lo, hoặc đang dắt theo trẻ nhỏ — " +
            "nên nói chậm rãi, mỗi lần một ý, mỗi câu trả lời không quá hai câu."

        /**
         * Luật gửi kèm mỗi lần gọi mô hình.
         *
         * ⚠ Luật số 4 — dòng KHOA_ID — là thứ để app KIỂM BẰNG MÃ, không phải cho đẹp.
         *   Mô hình trả id không nằm trong danh sách ứng viên, hoặc quên hẳn dòng này, thì
         *   app vứt cả câu trả lời và đọc câu từ chối của mình. Xem TraLoi.docCauTraLoi().
         *   Sai thì sai theo hướng im lặng.
         *
         * ⚠ Luật số 2 — cấm nói số tầng và mã phòng. Đây là phần KHÔNG được sai: chỉ lệch
         *   một tầng là người bệnh leo nhầm. App tự đọc phần đó nguyên văn từ bảng khoa
         *   phòng bệnh viện cung cấp, và trong prompt cũng không gửi câu đọc đó đi.
         */
        val LUAT_TRA_LOI =
            "LUẬT BẮT BUỘC:\n" +
            "1. Chỉ được nói về khoa có trong DANH SÁCH ỨNG VIÊN gửi kèm bên dưới. " +
            "Tuyệt đối không nhắc tên khoa nào khác, không nhớ từ chỗ khác, không suy ra.\n" +
            "2. KHÔNG tự nói số tầng, mã phòng, tên toà nhà. Ngay sau câu của bạn, máy sẽ tự " +
            "đọc vị trí lấy nguyên văn từ bảng khoa phòng của bệnh viện. Bạn nói nữa là quý vị " +
            "nghe hai lần, rất khó chịu, mà lệch một chữ là đi nhầm toà nhà.\n" +
            "3. Câu của bạn chỉ là CÂU DẪN ngắn, tối đa hai câu, dễ nghe với người đang mệt. " +
            "Ví dụ: \"Dạ tôi hiểu rồi ạ.\" hoặc \"Việc này quý vị làm ngay trong khu lễ tân được ạ.\"\n" +
            "4. DÒNG CUỐI CÙNG của câu trả lời BẮT BUỘC viết đúng dạng:\n" +
            "   KHOA_ID: X\n" +
            "   X là id của khoa bạn chọn trong danh sách ứng viên;\n" +
            "   hoặc KHONG_CO nếu quý vị hỏi chuyện khám chữa bệnh mà không ứng viên nào khớp;\n" +
            "   hoặc TAM_SU nếu quý vị chỉ nói chuyện ngoài lề.\n" +
            "Không hứa hẹn thay bác sĩ, không bàn chuyện bệnh tình, không bàn chuyện chính trị."
    }

    override fun onCreate() {
        super.onCreate()
        boiCanh = applicationContext

        // Tầng thấp: dẫn đường + đọc thành tiếng. Đây mới là phần app sống bằng.
        RobotHelper.ketNoi(this)

        // Tầng cao: nghe và gọi mô hình
        agent = object : AppAgent(this) {

            override fun onCreate() {

                /*
                 * ═══ BỐN CÔNG TẮC CỦA HÃNG, CẢ BỐN ĐỀU MẶC ĐỊNH SAI VỚI APP NÀY ═══
                 *
                 * Đặt ở đây là an toàn: `create$sdk_release` gán `api` rồi mới gọi `onCreate`,
                 * nên giá trị đặt tại đây nằm luôn trong gói `AppInfo` gửi sang AgentService.
                 *
                 * 1. isEnableVoiceBar — MẶC ĐỊNH BẬT. Đây là hộp trắng góc phải dưới màn hình
                 *    robot: phụ đề câu đang đọc kèm nút "Chạm để Ngắt". Nó ĐÈ LÊN giao diện
                 *    app. App đã có khung chat và video biểu cảm riêng nên thanh này chỉ vướng.
                 *
                 * 2. isDisablePlan — bật để TẮT bộ hoạch định của AgentOS. Bắt buộc phải tắt
                 *    khi app tự gọi `AgentCore.llm()`, không thì hai bên cùng trả lời một câu
                 *    hỏi và robot nói chồng lên chính nó.
                 *    ⚠ Đổi lại: từ đây AgentOS KHÔNG còn gọi Action nào nữa. Đường chính là
                 *      onASRResult → TraLoi.hoi(). App này vì thế KHÔNG đăng ký Action riêng.
                 *    ⚠ Chốt kiểm sau khi cài: nói vào robot vẫn phải thấy `Người bệnh nói: …`
                 *      trong logcat. Mất dòng đó nghĩa là tắt hoạch định giết luôn ASR —
                 *      đã đo ở app Mông Dương là KHÔNG giết, nhưng vẫn phải kiểm lại trên máy này.
                 *
                 * 3. isMicrophoneMuted — mặc định KHÔNG tắt tiếng, tức robot nghe cả ngày ngay
                 *    từ lúc mở app. Ở sảnh bệnh viện đó là nghe lỏm chuyện bệnh tình của người
                 *    ngồi chờ. Đóng lại từ đầu; chỉ mở ở màn Trò chuyện.
                 *
                 * 4. isEnableWakeFree — mặc định BẬT, robot tự bắt lời người đi ngang. Xem
                 *    chú thích dài ở datMicro().
                 */
                isEnableVoiceBar = false
                isDisablePlan = true
                isMicrophoneMuted = true
                isEnableWakeFree = false
                Log.d(TAG, "Công tắc hãng: voiceBar=$isEnableVoiceBar · disablePlan=$isDisablePlan · " +
                           "micTat=$isMicrophoneMuted · wakeFree=$isEnableWakeFree")

                /* Persona vẫn đặt dù đã tắt hoạch định: nó là đường lui nếu phải bật
                   disablePlan=false lại, và không tốn gì. */
                setPersona(PERSONA)
                setObjective(
                    "Việc của bạn là CHỈ ĐƯỜNG tới đúng khoa, đúng toà nhà, đúng tầng, và dẫn " +
                    "tận nơi những chỗ nằm trong khu lễ tân.\n" + LUAT_TRA_LOI
                )

                // Hai Action nói chuyện có sẵn của hệ thống. App KHÔNG đăng ký Action riêng:
                // đã tắt hoạch định thì AgentOS không gọi Action nào nữa, đăng ký cũng vô ích.
                registerAction(Actions.SAY)
                registerAction(Actions.KNOWLEDGE_QA)

                /*
                 * ĐÂY LÀ CÁI MIC.
                 *
                 * Đừng quay lại webkitSpeechRecognition của trình duyệt: trên WebView robot
                 * hàm đó TỒN TẠI nhưng gọi start() là ném ngay error=not-allowed (Android
                 * WebView không có dịch vụ nhận dạng giọng nói, chỉ Chrome thật mới có).
                 *
                 * ⚠ Bản 0.2.2 chỉ có MỘT hàm `onTranscribe`, phân biệt hai chiều bằng cờ
                 *   `isUserSpeaking`. Bản 0.4.7 tách hẳn làm hai hàm — trình biên dịch bắt
                 *   được ngay nếu viết nhầm.
                 *
                 * Trả false để hệ thống XỬ LÝ TIẾP như bình thường — trả true là nuốt mất
                 * câu nói.
                 *
                 * ⚠ Callback này chạy trên LUỒNG PHỤ. Đụng tới WebView phải post về luồng
                 *   chính — Cau.guiLoiNoi đã lo việc đó.
                 */
                setOnTranscribeListener(object : OnTranscribeListener {

                    override fun onASRResult(t: Transcription): Boolean {
                        val chu = t.text
                        if (chu.isNullOrBlank()) return false

                        // Nghe được chữ nghĩa là đường dây thật sự thông.
                        if (!agentSanSang) { agentSanSang = true; Cau.baoAISanSang(true) }

                        Cau.guiLoiNoi("nguoi", chu, t.final)

                        if (t.final) {
                            Log.d(TAG, "Người bệnh nói: $chu")
                            tuNoi = ""          // lượt mới, quên câu app tự đọc lần trước
                            /* ĐƯỜNG CHÍNH của cả cuộc hội thoại nằm ở đây. TraLoi tự lo:
                               cấp cứu → hỏi bệnh → chưa có dữ liệu → tra kho → chấm tin cậy
                               → hỏi mô hình → kiểm câu trả lời → mới cho robot đọc.
                               Nó tự đẩy sang luồng phụ nên callback này không bị chặn. */
                            TraLoi.hoi(chu)
                        }
                        return false
                    }

                    override fun onTTSResult(t: Transcription): Boolean {
                        val chu = t.text
                        if (chu.isNullOrBlank()) return false
                        /* Câu do chính app soạn thì đã hiện trên màn hình rồi — xem tuNoi.
                           ⚠ ĐỪNG xoá tuNoi ở đây khi t.final: robot đọc xong TỪNG CÂU là bắn
                           một gói final, nên xoá ngay câu đầu thì mấy câu sau lọt lưới và màn
                           hình lại hiện lặp. tuNoi chỉ xoá khi người bệnh mở miệng lần sau. */
                        if (tuNoi.isNotEmpty() && tuNoi.contains(chu.trim())) return false
                        Cau.guiLoiNoi("robot", chu, t.final)
                        return false
                    }
                })
            }

            /** App này không mở Action nào cho app khác gọi vào. */
            override fun onExecuteAction(action: Action, params: Bundle?): Boolean = false
        }

        thamDoAI()
    }
}
