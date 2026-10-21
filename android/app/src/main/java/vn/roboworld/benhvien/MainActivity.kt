package vn.roboworld.benhvien

import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.TextView
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity

/**
 * Màn hình duy nhất của app: một WebView chạy toàn bộ giao diện tra cứu.
 *
 * Giao diện nằm ở assets/index.html — chính là file đã chạy trên máy tính, không sửa gì.
 * Nhờ vậy sửa nội dung hay bố cục về sau chỉ cần thay file HTML, không phải build lại app.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var banner: TextView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        web = WebView(this)
        /* Dải chữ đỏ ở đáy màn hình khi robot chạy theo lệnh của phần mềm quản lý (v1.13).
           Làm bằng View Android chứ không trong index.html: người bệnh thấy robot tự bỏ đi
           thì phải biết vì sao — và không phải dựng lại giao diện web chỉ vì một dòng chữ. */
        banner = TextView(this).apply {
            setBackgroundColor(Color.parseColor("#E6C13F28")); setTextColor(Color.WHITE)
            textSize = 15f; gravity = Gravity.CENTER; setPadding(24, 14, 24, 14)
            visibility = View.GONE
        }
        setContentView(FrameLayout(this).apply {
            addView(web, FrameLayout.LayoutParams(-1, -1))
            addView(banner, FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM))
        })
        QuanLyTuXa.hienBanner = { chu ->
            runOnUiThread { banner.text = chu.orEmpty(); banner.visibility = if (chu == null) View.GONE else View.VISIBLE }
        }
        anThanhHeThong()

        WebView.setWebContentsDebuggingEnabled(true)   // để soi lỗi bằng chrome://inspect

        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            // Toàn bộ dữ liệu nằm trong file, không gọi mạng — chặn hẳn cho chắc
            cacheMode = WebSettings.LOAD_NO_CACHE
            allowFileAccess = true
            textZoom = 100                              // không để cỡ chữ hệ thống làm vỡ bố cục
            mediaPlaybackRequiresUserGesture = false

            /*
             * ⚠ BA DÒNG DƯỚI ĐÂY QUYẾT ĐỊNH GIAO DIỆN CÓ VỠ HAY KHÔNG.
             *
             * Màn hình robot là 1920×1080 nhưng ở mật độ 560 dpi, nên WebView chỉ cho
             * trang một khung 548×308 CSS px. Bố cục này thiết kế theo tỉ lệ của khung
             * 1920×1080 nên cỡ chữ gốc tính ra chỉ 4,56 px — mà Chrome có SÀN cỡ chữ
             * tối thiểu 8 px, nó tự nâng lên 8. Mọi thứ to lên 1,75 lần, chữ tràn ra
             * ngoài thẻ, nhãn "20 thủ tục" bị cắt mất.
             *
             * Cách chữa: bảo WebView bố cục ở đúng 1920 px rồi thu nhỏ cả trang cho vừa
             * màn hình (meta viewport width=1920 trong index.html). Khi đó cỡ chữ gốc
             * là 16 px, nằm trên sàn, hiển thị y hệt bản chạy trên máy tính.
             * Hai dòng minimumFontSize là lớp chặn thứ hai, phòng khi meta bị bỏ qua.
             */
            useWideViewPort = true          // tôn trọng meta viewport width=1920
            loadWithOverviewMode = true     // thu nhỏ cả trang cho vừa bề ngang màn hình
            minimumFontSize = 1
            minimumLogicalFontSize = 1
        }

        // In lỗi JavaScript ra logcat — WebView trên máy Nova có thể cũ hơn trên máy tính,
        // cú pháp JS đời mới sẽ lỗi ở đây chứ không lỗi lúc build.
        web.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(m: ConsoleMessage): Boolean {
                Log.d("BVWeb", "${m.messageLevel()} ${m.message()} @${m.lineNumber()}")
                return true
            }
        }

        Cau.gan(web)
        web.addJavascriptInterface(Cau, "CAU")
        web.loadUrl("file:///android_asset/index.html")

        xinQuyenMicro()

        Log.d("BVWeb", "WebView: " + (Build.VERSION.SDK_INT.toString()) + " / " +
                (WebView.getCurrentWebViewPackage()?.versionName ?: "không đọc được"))
    }

    /**
     * Xin quyền thu âm LÚC CHẠY.
     *
     * ⚠ Khai <uses-permission RECORD_AUDIO> trong Manifest là CHƯA ĐỦ. Từ Android 6 trở đi
     *   quyền này phải xin lúc chạy. Không gọi hàm này thì `dumpsys package` hiện
     *   RECORD_AUDIO không có "granted=true", robot KHÔNG nghe được người dân nói —
     *   mà app không hề báo lỗi gì, thanh trạng thái chỉ hiện nút "Bật microphone".
     */
    private fun xinQuyenMicro() {
        val q = android.Manifest.permission.RECORD_AUDIO
        // Đọc thẻ nhớ (v1.13): đường lui đọc /sdcard/robot/map/<tên>/map.pgm cho phần mềm quản lý.
        // Xin CHUNG một lượt với micro — hai lượt requestPermissions chồng nhau thì lượt sau bị nuốt.
        val the = android.Manifest.permission.READ_EXTERNAL_STORAGE
        val thieu = listOf(q, the).filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (thieu.isNotEmpty()) {
            Log.d("BVWeb", "Đang xin quyền: $thieu")
            requestPermissions(thieu.toTypedArray(), 1001)
        }
        if (checkSelfPermission(q) == PackageManager.PERMISSION_GRANTED) {
            Log.d("BVWeb", "Đã có quyền micro")
            MainApplication.tatMicro()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1001) {
            val i = permissions.indexOf(android.Manifest.permission.RECORD_AUDIO)
            if (i < 0) return                       // lượt này chỉ xin quyền thẻ nhớ
            val duoc = grantResults.size > i && grantResults[i] == PackageManager.PERMISSION_GRANTED
            Log.d("BVWeb", "Kết quả xin quyền micro: $duoc")
            /*
             * Có quyền rồi vẫn TẮT mic — không phải quên.
             * App tự bật mic khi vào màn Trò chuyện và tắt lại khi ra. Để mic mở suốt thì
             * robot đứng ở sảnh sẽ xen vào mọi câu chuyện của người đang ngồi chờ, và lúc
             * dẫn đường thì phải im. Muốn robot nghe mọi lúc thì đổi dòng dưới thành
             * batMicro() — chỉ một chỗ này thôi.
             */
            if (duoc) MainApplication.tatMicro()
        }
    }

    /** Ra khỏi tiền cảnh thì đóng mic lại, khỏi nghe lén phòng chờ. */
    override fun onPause() {
        super.onPause()
        MainApplication.tatMicro()
    }

    /** Chạy toàn màn hình — robot không có thanh trạng thái để người dân bấm nhầm. */
    private fun anThanhHeThong() {
        window.decorView.systemUiVisibility =
            View.SYSTEM_UI_FLAG_FULLSCREEN or
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE or
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) anThanhHeThong()
    }

    /**
     * Nút Back của hệ thống: lùi trong trang trước, hết mới thoát app.
     * Lớp web tự quyết định lùi về đâu (xem window.luiHeThong) — chỉ khi nó đang
     * ở màn chờ biểu cảm mới trả '0' cho phép thoát ra RobotOS Home.
     */
    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        web.evaluateJavascript("window.luiHeThong ? window.luiHeThong() : '0'") { kq ->
            if (kq.contains("0")) super.onBackPressed()
        }
    }

    override fun onDestroy() {
        QuanLyTuXa.hienBanner = null
        Cau.go()
        RobotHelper.dungDoc()
        web.destroy()
        super.onDestroy()
    }
}
