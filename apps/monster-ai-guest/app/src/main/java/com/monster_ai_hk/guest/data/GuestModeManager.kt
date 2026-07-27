package com.monster_ai_hk.guest.data

import android.content.Context
import android.content.SharedPreferences
import android.os.SystemClock
import com.monster_ai_hk.guest.BuildConfig
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.CopyOnWriteArrayList

/**
 * 訪客模式核心管理器
 * 開發者：Suckbob | 發行商：Monster_Ai_hk
 *
 * 硬性限制（必須維持可維護）：
 * 1. 僅 3 個公開角色可對話
 * 2. 每日試玩 30 分鐘（BuildConfig.DAILY_TRIAL_SECONDS）
 * 3. 不儲存聊天、不匯出、不自訂角色
 * 4. 關閉付費 / 雲端 / 帳號功能
 *
 * 計時策略：
 * - 以「日曆日」為單位累積已用秒數（SharedPreferences）
 * - 僅在對話畫面前景時累加（由 Activity 回報 tick）
 * - 換日自動重置
 */
class GuestModeManager(context: Context) {

    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private val listeners = CopyOnWriteArrayList<Listener>()

    /** 本 session 內角色親密度（僅記憶體，App 關閉即消失） */
    private val sessionIntimacy = mutableMapOf<String, Int>()

    /** 上次 tick 的 elapsedRealtime，用於累加實際經過秒數 */
    private var lastTickElapsed: Long = 0L
    private var ticking: Boolean = false

    // ───────────────────── 公開 API ─────────────────────

    /** 每日配額總秒數（預設 1800 = 30 分鐘） */
    val dailyQuotaSeconds: Int
        get() = BuildConfig.DAILY_TRIAL_SECONDS

    /** 今日已用秒數 */
    fun getUsedSecondsToday(): Int {
        ensureDayKey()
        return prefs.getInt(KEY_USED_SECONDS, 0).coerceIn(0, dailyQuotaSeconds)
    }

    /** 今日剩餘秒數 */
    fun getRemainingSeconds(): Int =
        (dailyQuotaSeconds - getUsedSecondsToday()).coerceAtLeast(0)

    fun isTrialExpired(): Boolean = getRemainingSeconds() <= 0

    /** 格式化剩餘時間 mm:ss */
    fun formatRemaining(): String {
        val s = getRemainingSeconds()
        val m = s / 60
        val r = s % 60
        return String.format(Locale.TAIWAN, "%02d:%02d", m, r)
    }

    /** 是否允許進入與某角色對話 */
    fun canChatWith(characterId: String): Boolean {
        if (isTrialExpired()) return false
        return GuestCharacters.findById(characterId) != null
    }

    fun isCharacterUnlocked(characterId: String): Boolean =
        GuestCharacters.findById(characterId) != null

    // ── 親密度（僅試玩角色、僅記憶體） ──

    fun getIntimacy(characterId: String): Int {
        val base = GuestCharacters.findById(characterId)?.baseIntimacy ?: 0
        return sessionIntimacy.getOrPut(characterId) { base }
    }

    fun addIntimacy(characterId: String, delta: Int = 1): Int {
        if (!isCharacterUnlocked(characterId)) return 0
        val next = (getIntimacy(characterId) + delta).coerceIn(0, 100)
        sessionIntimacy[characterId] = next
        return next
    }

    // ── 計時控制（由 ChatActivity 驅動） ──

    fun startTicking() {
        if (isTrialExpired()) {
            notifyExpired()
            return
        }
        ticking = true
        lastTickElapsed = SystemClock.elapsedRealtime()
    }

    fun stopTicking() {
        if (ticking) {
            flushElapsed()
            ticking = false
        }
    }

    /**
     * 建議每秒由 UI 呼叫一次。
     * @return 剩餘秒數；若 <=0 表示已到期
     */
    fun tick(): Int {
        if (!ticking) return getRemainingSeconds()
        if (isTrialExpired()) {
            ticking = false
            notifyExpired()
            return 0
        }
        flushElapsed()
        val remain = getRemainingSeconds()
        listeners.forEach { it.onRemainingChanged(remain) }
        if (remain <= 0) {
            ticking = false
            notifyExpired()
        }
        return remain
    }

    // ── 訪客禁止功能（明確 API，避免誤用） ──

    /** 訪客版禁止儲存聊天記錄 */
    fun isChatSaveAllowed(): Boolean = false

    /** 訪客版禁止匯出 */
    fun isExportAllowed(): Boolean = false

    /** 訪客版禁止自訂角色 */
    fun isCustomCharacterAllowed(): Boolean = false

    /** 訪客版禁止付費 */
    fun isBillingEnabled(): Boolean = false

    /** 訪客版禁止雲端同步 */
    fun isCloudSyncEnabled(): Boolean = false

    /** 訪客版禁止帳號登入 */
    fun isAccountLoginEnabled(): Boolean = false

    fun addListener(listener: Listener) {
        listeners.addIfAbsent(listener)
    }

    fun removeListener(listener: Listener) {
        listeners.remove(listener)
    }

    // ───────────────────── 內部 ─────────────────────

    private fun flushElapsed() {
        val now = SystemClock.elapsedRealtime()
        if (lastTickElapsed <= 0L) {
            lastTickElapsed = now
            return
        }
        val deltaMs = now - lastTickElapsed
        lastTickElapsed = now
        if (deltaMs < 200L) return // 防抖
        val addSec = (deltaMs / 1000L).toInt().coerceAtLeast(0)
        if (addSec <= 0) return
        ensureDayKey()
        val used = (getUsedSecondsToday() + addSec).coerceAtMost(dailyQuotaSeconds)
        prefs.edit().putInt(KEY_USED_SECONDS, used).apply()
    }

    private fun ensureDayKey() {
        val today = todayKey()
        val stored = prefs.getString(KEY_DAY, null)
        if (stored != today) {
            prefs.edit()
                .putString(KEY_DAY, today)
                .putInt(KEY_USED_SECONDS, 0)
                .apply()
        }
    }

    private fun todayKey(): String =
        SimpleDateFormat("yyyy-MM-dd", Locale.TAIWAN).format(Date())

    private fun notifyExpired() {
        listeners.forEach { it.onTrialExpired() }
    }

    interface Listener {
        fun onRemainingChanged(remainingSeconds: Int) {}
        fun onTrialExpired() {}
    }

    companion object {
        private const val PREFS_NAME = "monster_ai_guest_trial"
        private const val KEY_DAY = "trial_day"
        private const val KEY_USED_SECONDS = "trial_used_seconds"

        // 開發者 / 發行商標識（供除錯顯示）
        const val DEVELOPER = "Suckbob"
        const val PUBLISHER = "Monster_Ai_hk"
    }
}
