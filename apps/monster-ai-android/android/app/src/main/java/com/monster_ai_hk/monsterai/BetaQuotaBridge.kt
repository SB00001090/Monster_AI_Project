package com.monster_ai_hk.monsterai

import android.content.Context
import android.webkit.JavascriptInterface
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * 原生 ↔ Web 公測額度橋接（可選）
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * Web 端 GuestContext 已用 localStorage；此橋接用於
 * 跨 WebView 清除 / 原生設定同步時可呼叫。
 *
 * 使用：webView.addJavascriptInterface(BetaQuotaBridge(this), "MonsterBeta")
 */
class BetaQuotaBridge(context: Context) {

    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    @JavascriptInterface
    fun getQuotaJson(): String {
        ensureDay()
        val rp = prefs.getInt(KEY_RP, 0)
        val img = prefs.getInt(KEY_IMG, 0)
        return JSONObject()
            .put("rpUsed", rp)
            .put("imageUsed", img)
            .put("rpLimit", BuildConfig.DAILY_RP_LIMIT)
            .put("imageLimit", BuildConfig.DAILY_IMAGE_LIMIT)
            .put("rpRemaining", (BuildConfig.DAILY_RP_LIMIT - rp).coerceAtLeast(0))
            .put("imageRemaining", (BuildConfig.DAILY_IMAGE_LIMIT - img).coerceAtLeast(0))
            .put("publicBeta", BuildConfig.PUBLIC_BETA)
            .put("publisher", BuildConfig.PUBLISHER)
            .put("developer", BuildConfig.DEVELOPER)
            .toString()
    }

    @JavascriptInterface
    fun isPublicBeta(): Boolean = BuildConfig.PUBLIC_BETA

    private fun ensureDay() {
        val today = SimpleDateFormat("yyyy-MM-dd", Locale.TAIWAN).format(Date())
        if (prefs.getString(KEY_DAY, null) != today) {
            prefs.edit()
                .putString(KEY_DAY, today)
                .putInt(KEY_RP, 0)
                .putInt(KEY_IMG, 0)
                .apply()
        }
    }

    companion object {
        private const val PREFS = "monster_ai_beta_native"
        private const val KEY_DAY = "day"
        private const val KEY_RP = "rp"
        private const val KEY_IMG = "img"
    }
}
