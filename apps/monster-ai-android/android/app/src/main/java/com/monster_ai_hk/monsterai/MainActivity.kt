package com.monster_ai_hk.monsterai

import android.os.Bundle
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity

/**
 * 主 Activity — Capacitor Bridge 殼
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * 完整 Capacitor 整合時請改為繼承 `com.getcapacitor.BridgeActivity`：
 *
 * ```
 * import com.getcapacitor.BridgeActivity
 * class MainActivity : BridgeActivity() {
 *   override fun onCreate(savedInstanceState: Bundle?) {
 *     // registerPlugin(BetaQuotaPlugin::class.java)
 *     super.onCreate(savedInstanceState)
 *   }
 * }
 * ```
 *
 * 在 `npx cap sync` 完成前，此殼以 WebView 載入 assets 或遠端公測頁，
 * 確保專案可開啟、可編譯；sync 後以 BridgeActivity 為準。
 */
class MainActivity : AppCompatActivity() {

    private var webView: WebView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        webView?.settings?.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            mediaPlaybackRequiresUserGesture = false
        }
        // 注入公測旗標，供 Web GuestContext 偵測
        webView?.evaluateJavascript(
            """
            window.__MONSTER_PUBLIC_BETA__ = true;
            window.__MONSTER_FORCE_GUEST__ = true;
            window.__MONSTER_PUBLISHER__ = 'Monster_Ai_hk';
            window.__MONSTER_DEVELOPER__ = 'suckbob';
            """.trimIndent(),
            null,
        )

        // Capacitor sync 後 assets/public/index.html 會存在；否則顯示本地引導頁
        val assetIndex = "file:///android_asset/public/index.html"
        try {
            assets.open("public/index.html").close()
            webView?.loadUrl(assetIndex)
        } catch (_: Exception) {
            webView?.loadDataWithBaseURL(
                null,
                FALLBACK_HTML,
                "text/html",
                "UTF-8",
                null,
            )
        }
    }

    override fun onDestroy() {
        webView?.destroy()
        webView = null
        super.onDestroy()
    }

    companion object {
        private val FALLBACK_HTML = """
            <!DOCTYPE html>
            <html><head><meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width,initial-scale=1"/>
            <style>
              body{font-family:sans-serif;background:#0B0F1A;color:#F2F5FF;
              display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:24px;text-align:center}
              h1{color:#00E5FF} .tag{color:#FF4D9A;font-size:14px}
            </style></head>
            <body>
              <div>
                <div class="tag">公測版 · 訪客免費</div>
                <h1>Monster AI 公測</h1>
                <p>請在 monorepo 根目錄執行：</p>
                <pre style="text-align:left;background:#151B2E;padding:12px;border-radius:8px;font-size:12px">
pnpm build
npx cap sync android
                </pre>
                <p style="opacity:.5;font-size:12px">開發者：suckbob · 發行商：Monster_Ai_hk</p>
              </div>
            </body></html>
        """.trimIndent()
    }
}
